from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from ..components.auth import check_login
from ..config.env import DIEnvConfig

router = APIRouter(prefix="/oauth2")


@router.post("/token")
async def login(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    env: DIEnvConfig,
) -> dict[str, str]:
    if u := await check_login(env, form):
        return {"access_token": u.username, "token_type": "bearer"}
    raise HTTPException(status_code=400, detail="Incorrect username or password")
