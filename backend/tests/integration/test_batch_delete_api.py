# backend/tests/integration/test_batch_delete_api.py
"""Integration tests for POST /api/history/batch-delete."""
from __future__ import annotations

import json
from unittest.mock import patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


@pytest.fixture(scope="module", autouse=True)
def patch_async_session(engine):
    """Redirect app.database.async_session to the test engine's session factory."""
    import app.database as db_module
    import app.routers.optimize as opt_module

    TestSession = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    with (
        patch.object(db_module, "async_session", TestSession),
        patch.object(opt_module, "async_session", TestSession),
    ):
        yield


async def _create_optimization(client: AsyncClient, headers: dict, raw_prompt: str = "Test prompt") -> str:
    """Stream /api/optimize and return the created optimization id."""
    opt_id = None
    async with client.stream(
        "POST", "/api/optimize",
        json={"prompt": raw_prompt},
        headers=headers,
        timeout=30,
    ) as resp:
        assert resp.status_code == 200
        async for line in resp.aiter_lines():
            if line.startswith("data:") and '"optimization_id"' in line:
                data = json.loads(line[5:].strip())
                if "optimization_id" in data:
                    opt_id = data["optimization_id"]
    assert opt_id, "optimization_id not found in SSE stream"
    return opt_id


async def test_batch_delete_requires_auth(client: AsyncClient):
    resp = await client.post("/api/history/batch-delete", json={"ids": ["fake-id"]})
    assert resp.status_code == 401


async def test_batch_delete_single_item(client: AsyncClient, auth_headers):
    opt_id = await _create_optimization(client, auth_headers, "Batch delete single")
    resp = await client.post(
        "/api/history/batch-delete",
        json={"ids": [opt_id]},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["deleted_count"] == 1
    assert body["ids"] == [opt_id]

    # Verify not in listing
    list_resp = await client.get("/api/history", headers=auth_headers)
    ids = [item["id"] for item in list_resp.json()["items"]]
    assert opt_id not in ids


async def test_batch_delete_multiple_items(client: AsyncClient, auth_headers):
    id1 = await _create_optimization(client, auth_headers, "Batch multi 1")
    id2 = await _create_optimization(client, auth_headers, "Batch multi 2")
    id3 = await _create_optimization(client, auth_headers, "Batch multi 3")

    resp = await client.post(
        "/api/history/batch-delete",
        json={"ids": [id1, id2, id3]},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["deleted_count"] == 3
    assert set(body["ids"]) == {id1, id2, id3}


async def test_batch_delete_404_when_id_missing(client: AsyncClient, auth_headers):
    opt_id = await _create_optimization(client, auth_headers, "Batch 404 test")
    resp = await client.post(
        "/api/history/batch-delete",
        json={"ids": [opt_id, "nonexistent-id-12345"]},
        headers=auth_headers,
    )
    assert resp.status_code == 404

    # Original record must NOT have been deleted (all-or-nothing)
    list_resp = await client.get("/api/history", headers=auth_headers)
    ids = [item["id"] for item in list_resp.json()["items"]]
    assert opt_id in ids


async def test_batch_delete_403_when_not_owner(client: AsyncClient, auth_headers, other_auth_headers):
    opt_id = await _create_optimization(client, auth_headers, "Batch 403 test")
    resp = await client.post(
        "/api/history/batch-delete",
        json={"ids": [opt_id]},
        headers=other_auth_headers,
    )
    assert resp.status_code == 403


async def test_batch_delete_rejects_over_50_ids(client: AsyncClient, auth_headers):
    fake_ids = [f"fake-id-{i}" for i in range(51)]
    resp = await client.post(
        "/api/history/batch-delete",
        json={"ids": fake_ids},
        headers=auth_headers,
    )
    assert resp.status_code == 422


async def test_batch_delete_rejects_empty_ids(client: AsyncClient, auth_headers):
    resp = await client.post(
        "/api/history/batch-delete",
        json={"ids": []},
        headers=auth_headers,
    )
    assert resp.status_code == 422


async def test_batch_delete_items_appear_in_trash(client: AsyncClient, auth_headers):
    opt_id = await _create_optimization(client, auth_headers, "Batch trash check")
    await client.post(
        "/api/history/batch-delete",
        json={"ids": [opt_id]},
        headers=auth_headers,
    )
    trash_resp = await client.get("/api/history/trash", headers=auth_headers)
    trash_ids = [item["id"] for item in trash_resp.json()["items"]]
    assert opt_id in trash_ids
