import hashlib
import hmac
import json
import os
import secrets
from datetime import datetime, timedelta, timezone
from urllib.error import URLError
from urllib.request import Request, urlopen
from uuid import uuid4

import boto3
import jwt
from botocore.config import Config
from fastapi import HTTPException

from .model import AvatarUploadRequest, LoginRequest, TokenResponse, User

# for this homework, I will use a single user for simplicity. (no database hehe)
users = [User(id=1, name="Alice")]
JWT_SECRET = os.environ["JWT_SECRET"]
GATEWAY_SECRET = os.environ["GATEWAY_SECRET"]
LOGIN_USERNAME = os.getenv("LOGIN_USERNAME", "alice")
PASSWORD_SALT = secrets.token_bytes(16)
PASSWORD_HASH = hashlib.pbkdf2_hmac(
    "sha256", os.getenv("LOGIN_PASSWORD", "password").encode(), PASSWORD_SALT, 100_000
)


def list_users():
    return users


def get_user(user_id: int):
    for user in users:
        if user.id == user_id:
            return user
    raise HTTPException(status_code=404, detail="User not found")


def login(credentials: LoginRequest):
    password_hash = hashlib.pbkdf2_hmac(
        "sha256", credentials.password.encode(), PASSWORD_SALT, 100_000
    )
    if not (
        hmac.compare_digest(password_hash, PASSWORD_HASH)
        and hmac.compare_digest(credentials.username.encode(), LOGIN_USERNAME.encode())
    ):
        raise HTTPException(status_code=401, detail="Invalid username or password",
                            headers={"WWW-Authenticate": "Bearer"})
    now = datetime.now(timezone.utc)
    token = jwt.encode(
        {"sub": "1", "iat": now, "exp": now + timedelta(hours=1)},
        JWT_SECRET, algorithm="HS256",
    )
    return TokenResponse(access_token=token)


def get_dashboard(user: User):
    base_url = os.getenv("ORDER_SERVICE_URL", "http://order-service:8000").rstrip("/")
    request = Request(
        f"{base_url}/orders?user_id={user.id}",
        headers={"X-User-ID": str(user.id), "X-Gateway-Secret": GATEWAY_SECRET},
    )
    try:
        with urlopen(request, timeout=5) as response:
            orders = json.load(response)
        if not isinstance(orders, list) or any(not isinstance(order, dict) for order in orders):
            raise ValueError("Invalid orders response")
    except (URLError, OSError, ValueError):
        raise HTTPException(status_code=502, detail="Order service unavailable") from None
    return {
        "user": user,
        "orders": [order for order in orders if order.get("user_id") == user.id],
    }


def upload_avatar(upload: AvatarUploadRequest, user: User):
    extensions = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}
    if upload.content_type not in extensions:
        raise HTTPException(status_code=400, detail="Use a JPEG, PNG, or WebP image")

    bucket = os.getenv("MINIO_BUCKET", "avatars")
    key = f"{user.id}/{uuid4().hex}.{extensions[upload.content_type]}"
    signer = boto3.client(
        "s3",
        endpoint_url=os.getenv("MINIO_PUBLIC_ENDPOINT", "http://localhost:9000"),
        aws_access_key_id=os.getenv("MINIO_ROOT_USER", "localadmin"),
        aws_secret_access_key=os.getenv(
            "MINIO_ROOT_PASSWORD", "local-development-password"
        ),
        region_name="us-east-1",
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
    )
    url = signer.generate_presigned_url(
        "put_object",
        Params={"Bucket": bucket, "Key": key, "ContentType": upload.content_type},
        ExpiresIn=300,
    )
    return {
        "upload_url": url,
        "method": "PUT",
        "headers": {"Content-Type": upload.content_type},
        "expires_in": 300,
        "bucket": bucket,
        "key": key,
    }
