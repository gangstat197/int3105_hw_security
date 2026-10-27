from fastapi import Depends, FastAPI

from . import service
from .dependencies import current_user
from .model import AvatarUploadRequest, LoginRequest, TokenResponse, User

app = FastAPI()


@app.post("/login", response_model=TokenResponse)
def login(credentials: LoginRequest):
    return service.login(credentials)


@app.get("/users", response_model=list[User])
def list_users(user: User = Depends(current_user)):
    return service.list_users()


@app.get("/users/{user_id}", response_model=User)
def get_user(user_id: int, user: User = Depends(current_user)):
    return service.get_user(user_id)


@app.get("/dashboard")
def dashboard(user: User = Depends(current_user)):
    return service.get_dashboard(user)


@app.post("/users/me/avatar-upload-url")
def avatar_upload_url(upload: AvatarUploadRequest, user: User = Depends(current_user)):
    return service.upload_avatar(upload, user)
