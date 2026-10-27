from pydantic import BaseModel


class User(BaseModel):
    id: int
    name: str


class LoginRequest(BaseModel):
    username: str
    password: str


class AvatarUploadRequest(BaseModel):
    content_type: str = "image/jpeg"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 3600
