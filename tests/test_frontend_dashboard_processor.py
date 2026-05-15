import datetime
from typing import Any

import pytest

from ruyi_backend.cache import KEY_TELEMETRY_DATA_LAST_PROCESSED
from ruyi_backend.components.frontend_dashboard_processor import (
    crunch_and_cache_dashboard_numbers,
)


class EmptyAsyncRows:
    def __aiter__(self) -> "EmptyAsyncRows":
        return self

    async def __anext__(self) -> Any:
        raise StopAsyncIteration


class FakeDB:
    def __init__(self) -> None:
        self.scalar_statements: list[Any] = []
        self.stream_statements: list[Any] = []

    async def scalar(self, statement: Any) -> int:
        self.scalar_statements.append(statement)
        return 7

    async def stream(self, statement: Any) -> EmptyAsyncRows:
        self.stream_statements.append(statement)
        return EmptyAsyncRows()


class FakeES:
    async def count(self, **_: Any) -> dict[str, int]:
        return {"count": 0}


class FakeCache:
    def __init__(self) -> None:
        self.values: dict[str, Any] = {
            KEY_TELEMETRY_DATA_LAST_PROCESSED: datetime.datetime(
                2026, 5, 15, tzinfo=datetime.timezone.utc
            ),
        }

    async def get(self, key: str) -> Any:
        return self.values.get(key)

    async def set(self, key: str, value: Any) -> None:
        self.values[key] = value


@pytest.mark.asyncio
async def test_dashboard_counts_distinct_installation_report_uuids() -> None:
    db = FakeDB()

    result = await crunch_and_cache_dashboard_numbers(db, FakeES(), FakeCache())

    assert result.installs is not None
    assert result.installs.total == 7
    install_count_sql = str(db.scalar_statements[0]).lower()
    assert "count(distinct(telemetry_installation_infos.report_uuid))" in install_count_sql
