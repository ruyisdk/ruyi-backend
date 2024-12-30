from typing import Final

from fastapi import FastAPI

from .lifespan import lifespan

app: Final = FastAPI(lifespan=lifespan)
