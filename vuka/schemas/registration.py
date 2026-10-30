from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class RegistrationCreate(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    username: str = Field(min_length=3, max_length=50, pattern=r"^[A-Za-z0-9_.-]+$")
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    preferred_language: Optional[str] = Field(None, max_length=10)
    country: Optional[str] = Field(None, max_length=100)

class RegistrationUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    username: Optional[str] = Field(None, min_length=3, max_length=50, pattern=r"^[A-Za-z0-9_.-]+$")
    email: Optional[EmailStr] = None
    preferred_language: Optional[str] = Field(None, max_length=10)
    country: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None
    user_type: Optional[str] = Field(None, pattern=r"^(user|verifier|admin)$")

class RegistrationResponse(BaseModel):
    user_id: int; first_name: str; last_name: str; username: str; email: EmailStr
    preferred_language: Optional[str]=None; country: Optional[str]=None; user_type: str; is_active: bool
    model_config={"from_attributes":True}

class RegistrationSelfUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    username: Optional[str] = Field(None, min_length=3, max_length=50, pattern=r"^[A-Za-z0-9_.-]+$")
    email: Optional[EmailStr] = None
