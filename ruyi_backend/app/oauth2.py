from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from ..components.auth import (
    DIUser,
    Token,
    TokenData,
    User,
    check_login,
    create_access_token,
)
from ..config.env import DIEnvConfig

router = APIRouter(prefix="/oauth2")


@router.post("/token")
async def login(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    env: DIEnvConfig,
) -> Token:
    if u := await check_login(env, form):
        return Token(
            access_token=create_access_token(
                env.auth.site_secret,
                data=TokenData(
                    sub=u.username,
                    is_admin=u.is_admin,
                ),
            ),
            token_type="bearer",
        )
    raise HTTPException(status_code=400, detail="Incorrect username or password")


@router.get("/current-user")
async def current_user(user: DIUser) -> User:
    return user
