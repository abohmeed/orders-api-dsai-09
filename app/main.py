"""Small FastAPI orders service backed by sqlite (DSAI lab baseline)."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

DB_PATH = Path(__file__).resolve().parent.parent / "orders.db"

SEED_ORDERS = [
    ("Alice Nguyen", "shipped", 42.50),
    ("Bob Martinez", "pending", 18.00),
    ("Carla Rossi", "shipped", 99.99),
    ("Diego Silva", "cancelled", 12.40),
    ("Elena Popov", "pending", 55.25),
    ("Farah Hassan", "shipped", 33.10),
    ("Gina Park", "shipped", 77.00),
    ("Hiro Tanaka", "pending", 21.75),
    ("Irene Costa", "shipped", 64.20),
    ("Jamal Okonkwo", "pending", 15.50),
    ("Keiko Sato", "shipped", 88.88),
    ("Luis Alvarez", "cancelled", 9.99),
    ("Maya Bergman", "pending", 120.00),
    ("Noah Pedersen", "shipped", 45.60),
    ("Omar Farouk", "pending", 27.30),
    ("Priya Sharma", "shipped", 61.15),
    ("Quinn Murphy", "pending", 39.40),
    ("Rosa Delgado", "shipped", 72.80),
    ("Samir Haddad", "cancelled", 14.20),
    ("Tina Weber", "shipped", 50.00),
]


class Order(BaseModel):
    id: int
    customer: str
    status: str
    total: float


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def get_db() -> Iterator[sqlite3.Connection]:
    conn = _connect()
    try:
        yield conn
    finally:
        conn.close()


def init_db() -> None:
    with get_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer TEXT NOT NULL,
                status TEXT NOT NULL,
                total REAL NOT NULL
            )
            """
        )
        count = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
        if count == 0:
            conn.executemany(
                "INSERT INTO orders (customer, status, total) VALUES (?, ?, ?)",
                SEED_ORDERS,
            )
        conn.commit()


def row_to_order(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "customer": row["customer"],
        "status": row["status"],
        "total": float(row["total"]),
    }


app = FastAPI(title="orders-api", version="0.1.0")


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/orders", response_model=list[Order])
def list_orders() -> list[dict[str, Any]]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, customer, status, total FROM orders ORDER BY id"
        ).fetchall()
    return [row_to_order(r) for r in rows]


@app.get("/orders/{order_id}", response_model=Order)
def get_order(order_id: int) -> dict[str, Any]:
    # Parameterised query — intentional baseline for DSAI-03 contrast.
    with get_db() as conn:
        row = conn.execute(
            "SELECT id, customer, status, total FROM orders WHERE id = ?",
            (order_id,),
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="order not found")
    return row_to_order(row)
