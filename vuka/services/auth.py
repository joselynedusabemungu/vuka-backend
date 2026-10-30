import os
from datetime import datetime,timedelta,timezone
from typing import Optional
import jwt
from fastapi import HTTPException
from vuka.models.registration import Registration
from vuka.repositories.auth import AuthRepository
from vuka.security.password import hash_password,verify_password
from vuka.services.email import send_password_reset_email
from vuka.services.mfa import MfaService
from vuka.services.security import locked,record_login,recent_ip_failures
from vuka.security.audit import record_event

SECRET_KEY=os.getenv("JWT_SECRET_KEY") or os.getenv("SECRET_KEY")
ALGORITHM=os.getenv("JWT_ALGORITHM") or os.getenv("ALGORITHM","HS256")

if not SECRET_KEY or len(SECRET_KEY)<32 or SECRET_KEY in {"your_secret_key_here"}:
    raise RuntimeError("A strong JWT_SECRET_KEY must be configured")

ACCESS_TOKEN_EXPIRE_MINUTES=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES","30"))
REFRESH_TOKEN_EXPIRE_DAYS=int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS","7"))
PASSWORD_RESET_TOKEN_EXPIRE_MINUTES=int(os.getenv("PASSWORD_RESET_TOKEN_EXPIRE_MINUTES","30"))

class AuthService:
    def __init__(self,repo:AuthRepository):
        self.repo=repo

    def hash_password(self,password):
        return hash_password(password)

    def verify_password(self,plain_password,hashed_password):
        return verify_password(plain_password,hashed_password)

    def _create_token(self,user_id,token_type,ttl):
        now=datetime.now(timezone.utc)
        return jwt.encode(
            {
                "sub":str(user_id),
                "token_type":token_type,
                "iat":now,
                "exp":now+ttl
            },
            SECRET_KEY,
            algorithm=ALGORITHM
        )

    def create_access_token(self,user_id):
        return self._create_token(
            user_id,
            "access",
            timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )

    def create_refresh_token(self,user_id):
        return self._create_token(
            user_id,
            "refresh",
            timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        )

    def create_token_pair(self,user_id):
        return {
            "access_token":self.create_access_token(user_id),
            "refresh_token":self.create_refresh_token(user_id),
            "token_type":"bearer"
        }

    def refresh_token(self,refresh_token):
        try:
            decoded=jwt.decode(
                refresh_token,
                SECRET_KEY,
                algorithms=[ALGORITHM],
                options={"require":["sub","exp","iat","token_type"]}
            )
        except jwt.PyJWTError as exc:
            raise HTTPException(401,"Invalid refresh token") from exc

        if decoded.get("token_type")!="refresh":
            raise HTTPException(401,"Invalid refresh token")

        try:
            user=self.repo.get_by_id(int(decoded["sub"]))
        except (KeyError,ValueError,TypeError):
            user=None

        if not user or not user.is_active:
            raise HTTPException(401,"Invalid refresh token")

        return {
            "access_token":self.create_access_token(user.user_id),
            "token_type":"bearer"
        }

    def authenticate(self,username,password)->Optional[Registration]:
        user=self.repo.get_by_email(username) or self.repo.get_by_username(username)
        if not user or not verify_password(password,user.pass_hash) or not user.is_active:
            return None
        return user

    def login(self,username,password,ip_address=None):
        identifier=username.strip().lower()
        user=self.repo.get_by_email(identifier) or self.repo.get_by_username(identifier)

        if recent_ip_failures(self.repo.db,ip_address)>=20:
            raise HTTPException(401,"Incorrect username or password",headers={"WWW-Authenticate":"Bearer"})

        if user and locked(user):
            record_event(
                self.repo.db,
                event_type="ACCOUNT_LOCKED",
                action="login_blocked",
                user_id=user.user_id,
                ip_address=ip_address,
                success=False,
                severity="HIGH",
                alert=True
            )
            self.repo.db.commit()
            raise HTTPException(401,"Incorrect username or password",headers={"WWW-Authenticate":"Bearer"})

        if not user or not verify_password(password,user.pass_hash) or not user.is_active:
            record_login(self.repo.db,user,identifier,ip_address,False)
            record_event(
                self.repo.db,
                event_type="LOGIN_FAILED",
                action="login",
                user_id=user.user_id if user else None,
                ip_address=ip_address,
                success=False,
                severity="MEDIUM",
                alert=bool(user and (user.failed_login_attempts or 0)>=5)
            )
            self.repo.db.commit()
            raise HTTPException(401,"Incorrect username or password",headers={"WWW-Authenticate":"Bearer"})

        challenge_token=MfaService.create_challenge(user.user_id,user)
        self.repo.db.commit()

        if user.mfa_enabled:
            return {"mfa_required":True,"challenge_token":challenge_token}

        tokens=self.create_token_pair(user.user_id)
        return {**tokens,"mfa_required":False,"challenge_token":challenge_token}

    def setup_mfa(self,challenge_token):
        if not challenge_token:
            raise HTTPException(401,"MFA challenge token required")

        user_id,_=MfaService.decode_challenge(challenge_token)
        user=self.repo.get_by_id(user_id)

        if not user or not user.is_active:
            raise HTTPException(401,"Invalid MFA challenge")

        MfaService.validate_challenge(challenge_token,user)
        result=MfaService.setup(user)
        self.repo.db.commit()

        record_event(
            self.repo.db,
            event_type="MFA_SETUP_STARTED",
            action="mfa_setup",
            user_id=user.user_id
        )
        self.repo.db.commit()
        return result

    def enable_mfa(self,challenge_token,code):
        if not challenge_token:
            raise HTTPException(401,"MFA challenge token required")

        user_id,_=MfaService.decode_challenge(challenge_token)
        user=self.repo.get_by_id(user_id)

        if not user or not user.is_active:
            raise HTTPException(401,"Invalid MFA challenge")

        MfaService.validate_challenge(challenge_token,user)

        if not user.mfa_secret_encrypted:
            raise HTTPException(400,"MFA setup has not been completed")

        if not MfaService.verify_setup(user,code):
            raise HTTPException(400,"Invalid MFA code")

        user.mfa_enabled=True
        self.repo.db.commit()

        record_event(
            self.repo.db,
            event_type="MFA_ENABLED",
            action="mfa_enable",
            user_id=user.user_id
        )
        self.repo.db.commit()

        return {"detail":"MFA enabled","challenge_token":challenge_token}

    def verify_mfa(self,challenge_token,code,ip_address=None):
        if not challenge_token:
            raise HTTPException(401,"MFA challenge token required")

        user_id,_=MfaService.decode_challenge(challenge_token)
        user=self.repo.get_by_id(user_id)

        if not user or not user.is_active:
            raise HTTPException(401,"Invalid MFA challenge")

        if not user.mfa_enabled:
            raise HTTPException(401,"MFA is not enabled")

        MfaService.validate_challenge(challenge_token,user)

        if not MfaService.verify_setup(user,code):
            record_event(
                self.repo.db,
                event_type="MFA_FAILED",
                action="mfa_login",
                user_id=user.user_id,
                ip_address=ip_address,
                success=False,
                severity="HIGH",
                alert=True
            )
            self.repo.db.commit()
            raise HTTPException(401,"Invalid MFA code")

        MfaService.consume_challenge(challenge_token,user)
        record_login(self.repo.db,user,user.username,ip_address,True)

        record_event(
            self.repo.db,
            event_type="LOGIN_SUCCESS",
            action="login_mfa",
            user_id=user.user_id,
            ip_address=ip_address,
            success=True
        )
        self.repo.db.commit()
        return self.create_token_pair(user.user_id)

    def disable_mfa(self,user,code):
        if not user.mfa_secret_encrypted:
            raise HTTPException(400,"MFA is not configured")

        if not MfaService.verify_setup(user,code):
            raise HTTPException(400,"Invalid MFA code")

        user.mfa_enabled=False
        user.mfa_secret_encrypted=None
        user.mfa_challenge_jti=None
        self.repo.db.commit()

        record_event(
            self.repo.db,
            event_type="MFA_DISABLED",
            action="mfa_disable",
            user_id=user.user_id
        )
        self.repo.db.commit()
        return {"detail":"MFA disabled"}

    def register_new_user(self,data):
        normalized_email=str(data.email).strip().lower()

        if self.repo.get_by_email(normalized_email):
            raise HTTPException(400,"Email already registered")

        username=(data.username or normalized_email.split("@",1)[0]).strip().lower()

        if self.repo.get_by_username(username):
            raise HTTPException(400,"Username already registered")

        new_user=Registration(
            first_name=(data.first_name or "User").strip(),
            last_name=(data.last_name or "").strip(),
            username=username,
            email=normalized_email,
            pass_hash=hash_password(data.password),
            preferred_language="en",
            country=None,
            user_type="user"
        )
        return self.repo.create_user(new_user)

    def create_password_reset_token(self,user_id):
        return self._create_token(
            user_id,
            "password_reset",
            timedelta(minutes=PASSWORD_RESET_TOKEN_EXPIRE_MINUTES)
        )

    def request_password_reset(self,email):
        user=self.repo.get_by_email(email)
        if user:
            send_password_reset_email(
                user.email,
                self.create_password_reset_token(user.user_id)
            )

    def reset_password(self,token,new_password):
        try:
            decoded=jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM])
        except (jwt.ExpiredSignatureError,jwt.PyJWTError) as exc:
            raise HTTPException(400,"Invalid or expired reset link") from exc

        if decoded.get("token_type")!="password_reset":
            raise HTTPException(400,"Invalid or expired reset link")

        try:
            user=self.repo.get_by_id(int(decoded["sub"]))
        except (KeyError,ValueError,TypeError):
            user=None

        if not user or not user.is_active:
            raise HTTPException(400,"Invalid or expired reset link")

        return self.repo.update_password(
            user,
            hash_password(new_password)
        )

