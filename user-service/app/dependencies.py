# HMAC
import hmac
from typing import Annotated

from fastapi import Header, HTTPException

from . import service


def current_user(
    x_user_id: Annotated[str | None, Header()] = None,
    x_gateway_secret: Annotated[str | None, Header()] = None,
):
    if not x_gateway_secret or not hmac.compare_digest(
        x_gateway_secret.encode(), service.GATEWAY_SECRET.encode()
    ):
        raise HTTPException(status_code=401, detail="Trusted gateway required")
    try:
        user_id = int(x_user_id)
        if user_id <= 0:
            raise ValueError
    except (ValueError, TypeError):
        raise HTTPException(status_code=401, detail="Invalid user identity") from None
    try:
        return service.get_user(user_id)
    except HTTPException:
        raise HTTPException(status_code=401, detail="Unknown user") from None
