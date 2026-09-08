import uuid

import pytest
from fastapi import Depends, FastAPI
from httpx import ASGITransport, AsyncClient

from app.auth import CurrentUser, get_current_user
from tests.conftest import make_token


@pytest.fixture
def probe_app():
    probe = FastAPI()

    @probe.get("/whoami")
    async def whoami(user: CurrentUser = Depends(get_current_user)):
        return {"user_id": str(user.user_id), "email": user.email}

    return probe


@pytest.fixture
async def probe_client(probe_app):
    transport = ASGITransport(app=probe_app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


async def test_valid_token_returns_user(probe_client):
    uid = str(uuid.uuid4())
    token = make_token(uid, "alice@example.com")
    resp = await probe_client.get("/whoami", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json() == {"user_id": uid, "email": "alice@example.com"}


async def test_missing_token_is_401(probe_client):
    resp = await probe_client.get("/whoami")
    assert resp.status_code == 401


async def test_malformed_token_is_401(probe_client):
    resp = await probe_client.get("/whoami", headers={"Authorization": "Bearer not-a-jwt"})
    assert resp.status_code == 401


async def test_expired_token_is_401(probe_client):
    token = make_token(str(uuid.uuid4()), expired=True)
    resp = await probe_client.get("/whoami", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401
