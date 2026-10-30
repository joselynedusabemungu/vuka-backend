from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from database import get_db
from vuka.dependency import get_current_user
from vuka.models.registration import Registration
from vuka.repositories.auth import AuthRepository
from vuka.schemas.auth import TokenResponse, UserRegisterInput, UserResponse
from vuka.schemas.authextended import (
    ForgotPasswordRequest,
    LoginRequest,
    RefreshTokenRequest,
    ResetPasswordRequest,
    TokenPair,
)
from vuka.schemas.mfa import MfaChallengeRequest, MfaSetupResponse, MfaVerifyRequest
from vuka.schemas.registration import RegistrationResponse, RegistrationSelfUpdate
from vuka.security.audit import record_event
from vuka.services import registration as registration_service
from vuka.services.auth import AuthService

router = APIRouter(tags=["Registration"])


def get_auth_service(db: Session = Depends(get_db)):
    return AuthService(AuthRepository(db))


@router.post("/register", response_model=UserResponse, status_code=201)
def register(
    data: UserRegisterInput,
    auth_service: AuthService = Depends(get_auth_service),
    db: Session = Depends(get_db),
    request: Request = None,
):
    user = auth_service.register_new_user(data)
    record_event(
        db,
        event_type="USER_REGISTERED",
        action="register",
        user_id=user.user_id,
        ip_address=request.client.host if request and request.client else None,
    )
    db.commit()
    return user


@router.post("/login")
def login(
    credentials: LoginRequest,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
):
    return auth_service.login(
        credentials.username,
        credentials.password,
        request.client.host if request.client else None,
    )


@router.post("/mfa/setup", response_model=MfaSetupResponse)
def mfa_setup(
    challenge_token: str, auth_service: AuthService = Depends(get_auth_service)
):
    return auth_service.setup_mfa(challenge_token)


@router.post("/mfa/enable")
def mfa_enable(
    payload: MfaVerifyRequest,
    challenge_token: str,
    auth_service: AuthService = Depends(get_auth_service),
):
    return auth_service.enable_mfa(challenge_token, payload.code)


@router.post("/mfa/verify", response_model=TokenPair)
def verify_mfa(
    payload: MfaChallengeRequest,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
):
    return auth_service.verify_mfa(
        payload.challenge_token,
        payload.code,
        request.client.host if request.client else None,
    )


@router.post("/mfa/disable")
def mfa_disable(
    payload: MfaVerifyRequest,
    current_user: Registration = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    return auth_service.disable_mfa(current_user, payload.code)


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(
    payload: RefreshTokenRequest, auth_service: AuthService = Depends(get_auth_service)
):
    return auth_service.refresh_token(payload.refresh_token)


@router.post("/logout")
def logout(
    current_user: Registration = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record_event(db, event_type="LOGOUT", action="logout", user_id=current_user.user_id)
    db.commit()
    return {"message": "Logged out."}


@router.post("/forgot-password")
def forgot_password(
    payload: ForgotPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    auth_service.request_password_reset(str(payload.email))
    return {
        "detail": "If an account with that email exists, a password reset link has been sent."
    }


@router.post("/reset-password")
def reset_password(
    payload: ResetPasswordRequest, auth_service: AuthService = Depends(get_auth_service)
):
    auth_service.reset_password(payload.token, payload.new_password)
    return {"detail": "Password has been reset successfully"}


@router.get("/me", response_model=UserResponse)
def get_me(current_user: Registration = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=RegistrationResponse)
def update_me(
    payload: RegistrationSelfUpdate,
    current_user: Registration = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return registration_service.update_registration(db, current_user.user_id, payload)


@router.delete("/me")
def delete_me(
    current_user: Registration = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    registration_service.delete_registration(db, current_user.user_id)
    return {"detail": "Account deactivated"}
