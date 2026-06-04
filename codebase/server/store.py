"""
store.py — Kho dữ liệu JSON (single source of truth) dùng chung cho REST API và agent.

Toàn bộ booking + refund_requests nằm trong data/db.json (tạo từ db.seed.json lần đầu).
Đây là "DB" của hệ thống — cả web (qua REST) lẫn AI agent (qua tools) đều đọc/ghi ở đây.
"""
from __future__ import annotations

import json
import shutil
import threading
from pathlib import Path
from typing import Any

from constants import today

DATA_DIR = Path(__file__).resolve().parent / "data"
DB = DATA_DIR / "db.json"
SEED = DATA_DIR / "db.seed.json"
_lock = threading.RLock()


def _ensure() -> None:
    if not DB.exists():
        shutil.copy(SEED, DB)


def _load() -> dict[str, Any]:
    _ensure()
    with open(DB, encoding="utf-8") as f:
        return json.load(f)


def _save(db: dict[str, Any]) -> None:
    with open(DB, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)


def reset() -> None:
    """Khôi phục DB về seed (cho nút Reset demo)."""
    with _lock:
        shutil.copy(SEED, DB)


# ---- Bookings ----
def get_booking(code: str) -> dict[str, Any] | None:
    return _load()["bookings"].get((code or "").strip().upper())


def list_bookings() -> dict[str, Any]:
    return _load()["bookings"]


# ---- Refund requests ----
def list_requests(status: str | None = None) -> list[dict[str, Any]]:
    reqs = _load()["refund_requests"]
    return [r for r in reqs if status is None or r["status"] == status]


def get_request(rid: str) -> dict[str, Any] | None:
    return next((r for r in _load()["refund_requests"] if r["id"] == rid), None)


def _next_id(db: dict[str, Any]) -> str:
    n = int(db.get("seq", 1004))
    db["seq"] = n + 1
    return f"REQ-{n}"


def create_request(rec: dict[str, Any]) -> dict[str, Any]:
    with _lock:
        db = _load()
        full = {
            "id": _next_id(db),
            "createdAt": today(),
            "status": "pending",
            "decidedAt": None,
            "rejectReason": None,
            **rec,
        }
        db["refund_requests"].insert(0, full)
        _save(db)
        return full


def update_request(rid: str, patch: dict[str, Any]) -> dict[str, Any] | None:
    with _lock:
        db = _load()
        for i, r in enumerate(db["refund_requests"]):
            if r["id"] == rid:
                db["refund_requests"][i] = {**r, **patch}
                _save(db)
                return db["refund_requests"][i]
    return None


def approve(rid: str) -> dict[str, Any] | None:
    return update_request(rid, {"status": "approved", "decidedAt": today(), "rejectReason": None})


def reject(rid: str, reason: str | None = None) -> dict[str, Any] | None:
    return update_request(
        rid,
        {
            "status": "rejected",
            "decidedAt": today(),
            "refundAmount": 0,
            "rejectReason": reason or "Không đủ điều kiện theo chính sách.",
        },
    )
