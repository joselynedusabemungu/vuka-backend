from typing import Optional
from pydantic import BaseModel, EmailStr


class UserRegisterInput(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
    email: EmailStr
    password: str





class UserResponse(BaseModel):
    user_id: int
    email: str
    username: Optional[str] = None
    user_type: str
    is_active: bool
    mfa_enabled: bool = False

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str