import json
from collections.abc import Iterator
from types import TracebackType
from typing import Any

import pytest
from fastapi.testclient import TestClient

from ruyi_backend import app
from ruyi_backend.db.conn import get_main_db
from ruyi_backend.schema.client_telemetry import UploadPayload


UPLOAD_PAYLOAD: dict[str, Any] = {
    "fmt": 1,
    "nonce": "f051065f71d94b5bb7b336ba0b782983",
    "ruyi_version": "0.44.0-beta.20251219",
    "events": [
        {
            "time_bucket": "202604031223",
            "kind": "cli:invocation-v1",
            "params": [["key", "version"]],
            "count": 1,
        },
        {
            "time_bucket": "202605112234",
            "kind": "cli:invocation-v1",
            "params": [["key", "<bare>"]],
            "count": 1,
        },
    ],
    "installation": {
        "v": 1,
        "report_uuid": "7a5ac670847648f98fc9d453591d145e",
        "arch": "x86_64",
        "ci": "maybe-not",
        "libc_name": "glibc",
        "libc_ver": "2.41",
        "os": "linux",
        "os_release_id": "gentoo",
        "os_release_version_id": "2.17",
        "shell": "zsh",
    },
}


class FakeConnection:
    def __init__(self) -> None:
        self.executions: list[tuple[str, dict[str, Any]]] = []
        self.committed = False

    async def __aenter__(self) -> "FakeConnection":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        return None

    async def execute(self, statement: Any, params: dict[str, Any]) -> None:
        self.executions.append((str(statement), params))

    async def commit(self) -> None:
        self.committed = True


class FakeEngine:
    def __init__(self) -> None:
        self.connection = FakeConnection()

    def connect(self) -> FakeConnection:
        return self.connection


@pytest.fixture(name="fake_db")
def fake_db_fixture() -> Iterator[FakeEngine]:
    db = FakeEngine()
    app.dependency_overrides[get_main_db] = lambda: db

    yield db

    app.dependency_overrides.pop(get_main_db, None)


client = TestClient(app)


@pytest.mark.parametrize("request_json", [UPLOAD_PAYLOAD, json.dumps(UPLOAD_PAYLOAD)])
def test_telemetry_upload_accepts_json_object_and_json_string(
    request_json: dict[str, Any] | str,
    fake_db: FakeEngine,
) -> None:
    resp = client.post("/telemetry/pm/upload-v1", json=request_json)

    assert resp.status_code == 204
    assert fake_db.connection.committed is True
    assert len(fake_db.connection.executions) == 3
    assert fake_db.connection.executions[0][1] == {
        "version": UPLOAD_PAYLOAD["ruyi_version"],
    }

    raw_upload_params = fake_db.connection.executions[-1][1]
    assert raw_upload_params["nonce"] == UPLOAD_PAYLOAD["nonce"]
    expected_raw_events = UploadPayload.model_validate(UPLOAD_PAYLOAD).model_dump(
        mode="json",
    )
    assert json.loads(raw_upload_params["raw_events"]) == expected_raw_events
