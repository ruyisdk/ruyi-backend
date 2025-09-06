import base64
from hashlib import pbkdf2_hmac
from hmac import compare_digest
from os import GRND_RANDOM, getrandom
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel

from ..config.env import EnvConfig

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="oauth2/token")


def check_password(psw_hash: str, password: str) -> bool:
    if psw_hash.startswith("pbkdf2-sha512:"):
        # input like: "pbkdf2-sha512:210000:base64(salt):base64(hash)"
        try:
            _, iter_s, salt_b64, hash_b64 = psw_hash.split(":")
            iters = int(iter_s)
            salt = base64.b64decode(salt_b64)
            hash_val = base64.b64decode(hash_b64)
            calc_hash = pbkdf2_hmac("sha512", password.encode("utf-8"), salt, iters)
            return compare_digest(calc_hash, hash_val)
        except Exception:
            return False

    return False


def gen_password_hash(password: str, salt: bytes | None = None) -> str:
    iters = 1000000
    salt = salt or getrandom(16, GRND_RANDOM)
    salt_b64 = base64.b64encode(salt).decode("utf-8")
    hash_val = pbkdf2_hmac("sha512", password.encode("utf-8"), salt, iters)
    hash_b64 = base64.b64encode(hash_val).decode("utf-8")
    return f"pbkdf2-sha512:{iters}:{salt_b64}:{hash_b64}"


class User(BaseModel):
    username: str
    is_admin: bool


def fake_decode_token(token: str) -> User | None:
    # This doesn't provide any security at all
    # Check the next version
    return User(username=token + "fakedecoded", is_admin=(token == "admin-token"))


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> User:
    if u := fake_decode_token(token):
        return u

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def check_login(
    env: EnvConfig,
    form: OAuth2PasswordRequestForm,
) -> User | None:
    if creds := env.auth.admins_by_name.get(form.username):
        if check_password(creds.psw_hash, form.password):
            return User(username=creds.name, is_admin=True)

    return None
