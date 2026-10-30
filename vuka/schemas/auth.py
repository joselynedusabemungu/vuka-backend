from pydantic import BaseModel, EmailStr


class UserRegisterInput(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    user_id: int
    email: str
    username: str | None = None
    user_type: str
    is_active: bool
    mfa_enabled: bool = False

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
