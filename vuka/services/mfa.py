import os
from datetime import datetime,timedelta,timezone
import jwt
import pyotp
from fastapi import HTTPException
from vuka.models.registration import Registration
from vuka.security.crypto import encrypt_secret,decrypt_secret

SECRET_KEY=os.getenv("JWT_SECRET_KEY") or os.getenv("SECRET_KEY")
ALGORITHM=os.getenv("JWT_ALGORITHM") or os.getenv("ALGORITHM","HS256")

class MfaService:
    @staticmethod
    def setup(user:Registration):
        secret=pyotp.random_base32()
        user.mfa_secret_encrypted=encrypt_secret(secret)
        uri=pyotp.TOTP(secret).provisioning_uri(name=user.email,issuer_name=os.getenv("MFA_ISSUER","Vuka"))
        return {"secret":secret,"provisioning_uri":uri}

    @staticmethod
    def verify_setup(user:Registration,code:str):
        if not user.mfa_secret_encrypted:
            return False
        try:
            secret=decrypt_secret(user.mfa_secret_encrypted)
            totp=pyotp.TOTP(secret)
            return totp.verify(str(code).strip(),valid_window=1)
        except Exception:
            return False

    @staticmethod
    def create_challenge(user_id:int,user:Registration):
        now=datetime.now(timezone.utc)
        jti=os.urandom(16).hex()
        user.mfa_challenge_jti=jti
        payload={
            "sub":str(user_id),
            "token_type":"mfa_challenge",
            "iat":now,
            "exp":now+timedelta(minutes=5),
            "jti":jti
        }
        return jwt.encode(payload,SECRET_KEY,algorithm=ALGORITHM)

    @staticmethod
    def decode_challenge(token:str):
        try:
            payload=jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM],options={"require":["sub","exp","iat","jti","token_type"]})
        except jwt.PyJWTError as exc:
            raise HTTPException(status_code=401,detail="Invalid or expired MFA challenge") from exc

        if payload.get("token_type")!="mfa_challenge":
            raise HTTPException(status_code=401,detail="Invalid MFA challenge")

        try:
            user_id=int(payload["sub"])
        except (ValueError,TypeError,KeyError) as exc:
            raise HTTPException(status_code=401,detail="Invalid MFA challenge") from exc

        return user_id,payload

    @staticmethod
    def validate_challenge(token:str,user:Registration):
        user_id,payload=MfaService.decode_challenge(token)

        if user_id!=user.user_id:
            raise HTTPException(status_code=401,detail="Invalid MFA challenge")

        jti=payload.get("jti")

        if not user.mfa_challenge_jti:
            raise HTTPException(status_code=401,detail="MFA challenge has already been used")

        if user.mfa_challenge_jti!=jti:
            raise HTTPException(status_code=401,detail="Invalid MFA challenge")

        return True

    @staticmethod
    def consume_challenge(token:str,user:Registration):
        MfaService.validate_challenge(token,user)
        user.mfa_challenge_jti=None
        return user.user_id