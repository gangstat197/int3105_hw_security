import os

import jwt
from fastapi import Depends, FastAPI, HTTPException, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
JWT_SECRET = os.environ["JWT_SECRET"]
bearer = HTTPBearer(auto_error=False)


@app.get("/verify")
def verify(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)):
    try:
        if credentials is None:
            raise ValueError("Missing bearer token")
        claims = jwt.decode(
            credentials.credentials, JWT_SECRET, algorithms=["HS256"],
            options={"require": ["sub", "iat", "exp"]},
        )
        user_id = int(claims["sub"])
        if user_id <= 0:
            raise ValueError("Invalid subject")
    except (jwt.InvalidTokenError, ValueError, TypeError, OverflowError):
        raise HTTPException(
            status_code=401, detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None
    return Response(status_code=204, headers={"X-User-ID": str(user_id)})
