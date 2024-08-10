from fastapi import FastAPI
from fastapi_health import health


app = FastAPI()


@app.get("/api-version")
async def api_version() -> dict[str, int]:
    return {"v": 1}


app.add_api_route("/health", endpoint=health([]))
