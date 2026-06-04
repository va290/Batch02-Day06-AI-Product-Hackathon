"""
api.py — FastAPI: phục vụ web tĩnh + REST API trên JSON store + endpoint agent chat.
Web (user/admin) và AI agent dùng CHUNG store.py -> một nguồn sự thật duy nhất.

Chạy:  uvicorn api:app --reload --port 8000   (từ thư mục server/)
Mở:    http://localhost:8000/        (khách hàng)
        http://localhost:8000/admin.html (support)
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import policy
import store
from constants import REASON_OPTIONS, REFUND_DISCLAIMERS, CONFIRM_WARNINGS, STATUS_LABEL

WEB_ROOT = Path(__file__).resolve().parent.parent  # traveloka-refund-ai/

app = FastAPI(title="Traveloka Refund AI — CP2")


class EvalBody(BaseModel):
    bookingCode: str
    reasonCode: str
    reasonText: str = ""


class RejectBody(BaseModel):
    reason: str = ""


class ChatBody(BaseModel):
    message: str
    session_id: str = "default"


class ResetChatBody(BaseModel):
    session_id: str = "default"


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {"ok": True, "bookings": len(store.list_bookings()), "requests": len(store.list_requests())}


@app.get("/api/config")
def config() -> dict[str, Any]:
    return {
        "reasonOptions": REASON_OPTIONS,
        "disclaimers": REFUND_DISCLAIMERS,
        "confirmWarnings": CONFIRM_WARNINGS,
        "statusLabel": STATUS_LABEL,
    }


@app.get("/api/bookings")
def list_bookings() -> dict[str, Any]:
    return {"bookings": list(store.list_bookings().values())}


@app.get("/api/bookings/{code}")
def get_booking(code: str) -> dict[str, Any]:
    b = store.get_booking(code)
    if not b:
        raise HTTPException(404, "booking not found")
    return b


@app.post("/api/evaluate")
def evaluate(body: EvalBody) -> dict[str, Any]:
    return policy.evaluate_cancellation(body.bookingCode, body.reasonCode, body.reasonText)


@app.get("/api/requests")
def list_requests(status: str | None = None) -> dict[str, Any]:
    return {"requests": store.list_requests(status)}


@app.get("/api/requests/{rid}")
def get_request(rid: str) -> dict[str, Any]:
    r = store.get_request(rid)
    if not r:
        raise HTTPException(404, "request not found")
    return r


@app.post("/api/requests")
def create_request(body: EvalBody) -> dict[str, Any]:
    """Đánh giá lại (authoritative) rồi tạo yêu cầu. Trả về cả decision lẫn request."""
    decision = policy.evaluate_cancellation(body.bookingCode, body.reasonCode, body.reasonText)
    rec = policy.build_request(decision, body.reasonCode, body.reasonText)
    if rec is None:
        raise HTTPException(409, f"Không thể tạo yêu cầu cho trạng thái '{decision['status']}'")
    saved = store.create_request(rec)
    return {"request": saved, "decision": decision}


@app.post("/api/requests/{rid}/approve")
def approve(rid: str) -> dict[str, Any]:
    r = store.approve(rid)
    if not r:
        raise HTTPException(404, "request not found")
    return r


@app.post("/api/requests/{rid}/reject")
def reject(rid: str, body: RejectBody) -> dict[str, Any]:
    r = store.reject(rid, body.reason or None)
    if not r:
        raise HTTPException(404, "request not found")
    return r


@app.post("/api/requests/reset")
def reset() -> dict[str, Any]:
    store.reset()
    return {"ok": True, "requests": len(store.list_requests())}


@app.post("/api/agent/chat")
def agent_chat(body: ChatBody) -> dict[str, Any]:
    try:
        import memory
        out = memory.chat(body.session_id, body.message)  # có nhớ + tự nén context
        return {"reply": out["reply"], "trace": out["trace"],
                "session_id": out["session_id"], "memory": out["memory"]}
    except Exception as exc:  # thiếu key/SDK -> báo rõ thay vì 500 trắng
        return {"reply": f"(Agent chưa sẵn sàng: {type(exc).__name__}: {exc}. "
                         f"Kiểm tra CUSTOM_BASE_URL/CUSTOM_API_KEY/CUSTOM_MODEL trong .env và deps langchain.)",
                "trace": [], "session_id": body.session_id}


@app.post("/api/agent/reset")
def agent_reset(body: ResetChatBody) -> dict[str, Any]:
    import memory
    memory.reset(body.session_id)
    return {"ok": True, "session_id": body.session_id}


# Phục vụ web tĩnh ở "/" — đăng ký SAU cùng để không che các route /api.
app.mount("/", StaticFiles(directory=str(WEB_ROOT), html=True), name="web")
