import io
import uuid

import pytest

from app import supabase_client
from app.models import Membership, Receipt, Tenant
from tests.conftest import make_token


@pytest.fixture(autouse=True)
def _mock_storage(monkeypatch):
    async def _upload(path, data, content_type):
        return None

    async def _delete(path):
        return None

    monkeypatch.setattr(supabase_client, "upload_object", _upload)
    monkeypatch.setattr(supabase_client, "delete_object", _delete)


async def _seed(db_session, owner_id, name):
    tenant = Tenant(name=name, created_by_user_id=owner_id)
    db_session.add(tenant)
    await db_session.flush()
    db_session.add(Membership(tenant_id=tenant.id, user_id=owner_id, role="owner"))
    await db_session.commit()
    return tenant


def _png() -> dict:
    return {"file": ("r.png", io.BytesIO(b"\x89PNG\r\n\x1a\n" + b"0" * 32), "image/png")}


async def test_upload_stamps_tenant_and_submitter(client, db_session, user_a_id):
    tenant = await _seed(db_session, uuid.UUID(user_a_id), "AceCo")
    token = make_token(user_a_id)
    resp = await client.post(
        "/api/v1/receipts/upload",
        files=_png(),
        headers={"Authorization": f"Bearer {token}", "X-Tenant-ID": str(tenant.id)},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["tenant_id"] == tenant.id
    assert body["submitted_by_user_id"] == user_a_id
    assert body["image_path"].startswith(f"{tenant.id}/")


async def test_list_only_returns_active_tenant(client, db_session, user_a_id, user_b_id):
    ace = await _seed(db_session, uuid.UUID(user_a_id), "AceCo")
    bee = await _seed(db_session, uuid.UUID(user_b_id), "BeeCo")
    db_session.add(Receipt(
        image_path="x", tenant_id=bee.id,
        submitted_by_user_id=uuid.UUID(user_b_id), status="pending",
    ))
    await db_session.commit()

    token = make_token(user_a_id)
    resp = await client.get(
        "/api/v1/receipts",
        headers={"Authorization": f"Bearer {token}", "X-Tenant-ID": str(ace.id)},
    )
    assert resp.status_code == 200
    assert resp.json()["total"] == 0


async def test_get_other_tenant_receipt_is_404(client, db_session, user_a_id, user_b_id):
    ace = await _seed(db_session, uuid.UUID(user_a_id), "AceCo")
    bee = await _seed(db_session, uuid.UUID(user_b_id), "BeeCo")
    other = Receipt(
        image_path="x", tenant_id=bee.id,
        submitted_by_user_id=uuid.UUID(user_b_id), status="pending",
    )
    db_session.add(other)
    await db_session.commit()

    token = make_token(user_a_id)
    resp = await client.get(
        f"/api/v1/receipts/{other.id}",
        headers={"Authorization": f"Bearer {token}", "X-Tenant-ID": str(ace.id)},
    )
    assert resp.status_code == 404


async def test_upload_without_tenant_header_is_400(client, db_session, user_a_id):
    await _seed(db_session, uuid.UUID(user_a_id), "AceCo")
    token = make_token(user_a_id)
    resp = await client.post(
        "/api/v1/receipts/upload", files=_png(),
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400
