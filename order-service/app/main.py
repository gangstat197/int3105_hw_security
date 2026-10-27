import hmac
import os
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException

app = FastAPI()
GATEWAY_SECRET = os.environ["GATEWAY_SECRET"]
orders = [{"id": 1, "user_id": 1, "item": "Notebook"}]


def current_user_id(
    x_user_id: Annotated[str | None, Header()] = None,
    x_gateway_secret: Annotated[str | None, Header()] = None,
):
    if not x_gateway_secret or not hmac.compare_digest(
        x_gateway_secret.encode(), GATEWAY_SECRET.encode()
    ):
        raise HTTPException(status_code=401, detail="Trusted gateway required")
    try:
        user_id = int(x_user_id)
        if user_id <= 0:
            raise ValueError
        return user_id
    except (ValueError, TypeError):
        raise HTTPException(status_code=401, detail="Invalid user identity") from None


@app.get("/orders")
def list_orders(user_id: int | None = None, identity: int = Depends(current_user_id)):
    if user_id is not None and user_id != identity:
        raise HTTPException(status_code=403, detail="Cannot access another user's orders")
    return [order for order in orders if order["user_id"] == identity]
