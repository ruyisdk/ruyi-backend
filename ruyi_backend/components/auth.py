import base64
import datetime
from hashlib import pbkdf2_hmac
from hmac import compare_digest
from os import GRND_RANDOM, getrandom
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import jwt
from pydantic import BaseModel

from ..config.env import DIEnvConfig

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="oauth2/token")

JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_SECONDS = 3600 * 1  # 1 hour


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


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    sub: str | None = None


def create_access_token(
    site_secret: str,
    data: TokenData,
    expires_in: datetime.timedelta | None = None,
) -> str:
    expires_in = expires_in or datetime.timedelta(seconds=JWT_EXPIRATION_SECONDS)
    expire = datetime.datetime.now(datetime.timezone.utc) + expires_in

    to_encode = data.model_dump()
    to_encode.update({"exp": expire})
    return jwt.encode(
        to_encode,
        site_secret,
        algorithm=JWT_ALGORITHM,
    )


def decode_token(site_secret: str, token: str) -> User | None:
    try:
        payload = jwt.decode(
            token,
            site_secret,
            algorithms=[JWT_ALGORITHM],
        )
    except jwt.PyJWTError:
        return None

    username: str = payload.get("sub")
    if username is None:
        return None

    return User(username=username, is_admin=True)


async def get_current_user(
    env: DIEnvConfig,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> User:
    if u := decode_token(env.auth.site_secret, token):
        return u

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def check_login(
    env: DIEnvConfig,
    form: OAuth2PasswordRequestForm,
) -> User | None:
    if creds := env.auth.admins_by_name.get(form.username):
        if check_password(creds.psw_hash, form.password):
            return User(username=creds.name, is_admin=True)

    return None
