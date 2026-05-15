import asyncio
from typing import Any

from ruyi_backend.config.env import DBConfig, EnvConfig
from ruyi_backend.db import conn as db_conn


def test_init_main_db_enables_stale_connection_guards(monkeypatch: Any) -> None:
    calls: dict[str, Any] = {}
    engine = FakeEngine()

    def fake_create_async_engine(dsn: str, **kwargs: Any) -> FakeEngine:
        calls["dsn"] = dsn
        calls["kwargs"] = kwargs
        return engine

    monkeypatch.setattr(db_conn, "create_async_engine", fake_create_async_engine)

    cfg = EnvConfig(
        debug=True,
        db_main=DBConfig(dsn="mysql+asyncmy://user:pass@example.invalid/ruyisdk"),
    )
    db_conn.init_main_db(cfg)

    assert db_conn.get_main_db() is engine
    assert calls == {
        "dsn": "mysql+asyncmy://user:pass@example.invalid/ruyisdk",
        "kwargs": {
            "echo": True,
            "pool_pre_ping": True,
            "pool_recycle": db_conn.DB_POOL_RECYCLE_SECONDS,
        },
    }

    asyncio.run(db_conn.dispose_main_db())
    assert engine.disposed is True


class FakeEngine:
    def __init__(self) -> None:
        self.disposed = False

    async def dispose(self) -> None:
        self.disposed = True
