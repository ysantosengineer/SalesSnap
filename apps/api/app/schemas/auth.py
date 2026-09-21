import uuid

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    company_name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class CompanyResponse(BaseModel):
    id: uuid.UUID
    name: str


class UserResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    company: CompanyResponse


class SessionResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
