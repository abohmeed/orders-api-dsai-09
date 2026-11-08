"""Baseline tests for the safe orders-api endpoints."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Isolate each test run on its own sqlite file.
os.environ.setdefault("ORDERS_DB", "")


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_path = tmp_path / "orders.db"
    import app.main as main

    monkeypatch.setattr(main, "DB_PATH", db_path)
    main.init_db()
    with TestClient(main.app) as c:
        yield c


def test_list_orders_returns_twenty(client: TestClient) -> None:
    resp = client.get("/orders")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 20
    assert body[0]["customer"] == "Alice Nguyen"
    assert body[19]["id"] == 20


def test_get_order_by_id(client: TestClient) -> None:
    resp = client.get("/orders/3")
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == 3
    assert body["customer"] == "Carla Rossi"
    assert body["status"] == "shipped"


def test_get_order_not_found(client: TestClient) -> None:
    resp = client.get("/orders/999")
    assert resp.status_code == 404


def test_get_order_rejects_non_int(client: TestClient) -> None:
    resp = client.get("/orders/not-an-id")
    assert resp.status_code == 422


def test_list_orders_schema(client: TestClient) -> None:
    resp = client.get("/orders")
    order = resp.json()[0]
    assert set(order.keys()) == {"id", "customer", "status", "total"}
    assert isinstance(order["total"], float)


def test_seed_totals_are_positive(client: TestClient) -> None:
    totals = [o["total"] for o in client.get("/orders").json()]
    assert all(t > 0 for t in totals)
