from fastapi.testclient import TestClient

from ruyi_backend import app


client = TestClient(app)


def test_current_api_version():
    resp = client.get("/api-version")
    assert resp.status_code == 200
    assert resp.json() == {"v": 1}
