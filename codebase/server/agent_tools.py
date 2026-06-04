"""
agent_tools.py — Tool cho AI agent (vai "support"), thao tác trên CÙNG store.py với web.
Theo pattern Day04: mỗi tool là hàm trả dict; đăng ký trong TOOL_FUNCTIONS; schema ở TOOL_SCHEMAS.

Agent gọi tool -> tool đọc/ghi data/db.json -> web thấy thay đổi (cùng nguồn).
"""
from __future__ import annotations

from typing import Any

import policy
import store
from constants import REASON_OPTIONS

REASON_CODES = [r["code"] for r in REASON_OPTIONS]


def search_booking(booking_code: str) -> dict[str, Any]:
    """Tìm đặt phòng theo mã."""
    b = store.get_booking(booking_code)
    if not b:
        return {"found": False, "booking_code": (booking_code or "").strip().upper()}
    return {"found": True, "booking": b}


def evaluate_cancellation(booking_code: str, reason_code: str, reason_text: str = "") -> dict[str, Any]:
    """Đánh giá điều kiện hủy/hoàn theo chính sách (không ghi DB)."""
    d = policy.evaluate_cancellation(booking_code, reason_code, reason_text)
    return {
        "status": d["status"],
        "recommendedAction": d["recommendedAction"],
        "eligible": d.get("eligible"),
        "feeAmount": d.get("feeAmount"),
        "refundAmount": d.get("refundAmount"),
        "timelineText": d.get("timelineText"),
        "headline": d["headline"],
        "detail": d["detail"],
        "policySource": d.get("policySource"),
    }


def create_refund_request(booking_code: str, reason_code: str, reason_text: str = "") -> dict[str, Any]:
    """Đánh giá rồi TẠO yêu cầu hoàn/hủy trong DB. Trả về yêu cầu + quyết định."""
    d = policy.evaluate_cancellation(booking_code, reason_code, reason_text)
    rec = policy.build_request(d, reason_code, reason_text)
    if rec is None:
        return {
            "created": False,
            "reason": d["status"],
            "message": d["detail"],
        }
    saved = store.create_request(rec)
    return {"created": True, "request": saved, "decision_status": d["status"]}


def decide_request(request_id: str, action: str, reason: str = "") -> dict[str, Any]:
    """Vai duyệt (support/đơn vị lưu trú): action = 'approve' | 'reject'."""
    req = store.get_request(request_id)
    if not req:
        return {"ok": False, "message": f"Không tìm thấy yêu cầu {request_id}"}
    if action == "approve":
        return {"ok": True, "request": store.approve(request_id)}
    if action == "reject":
        return {"ok": True, "request": store.reject(request_id, reason or None)}
    return {"ok": False, "message": "action phải là 'approve' hoặc 'reject'"}


def list_requests(status: str = "") -> dict[str, Any]:
    """Liệt kê yêu cầu, lọc theo status nếu có ('pending'|'approved'|'rejected'|'auto_approved')."""
    return {"requests": store.list_requests(status or None)}


TOOL_FUNCTIONS = {
    "search_booking": search_booking,
    "evaluate_cancellation": evaluate_cancellation,
    "create_refund_request": create_refund_request,
    "decide_request": decide_request,
    "list_requests": list_requests,
}

TOOL_SCHEMAS = [
    {
        "name": "search_booking",
        "description": "Tra cứu thông tin một đặt phòng theo mã (vd TRV12345).",
        "input_schema": {
            "type": "object",
            "properties": {"booking_code": {"type": "string", "description": "Mã đặt phòng"}},
            "required": ["booking_code"],
        },
    },
    {
        "name": "evaluate_cancellation",
        "description": "Đánh giá điều kiện hủy/hoàn theo chính sách (chưa ghi DB). Trả về đủ điều kiện, phí, số tiền hoàn, thời gian, nguồn chính sách.",
        "input_schema": {
            "type": "object",
            "properties": {
                "booking_code": {"type": "string"},
                "reason_code": {"type": "string", "enum": REASON_CODES,
                                "description": "Mã lý do; dùng 'other' nếu nằm ngoài danh sách (vd visa bị từ chối)."},
                "reason_text": {"type": "string", "description": "Mô tả tự do khi reason_code='other'"},
            },
            "required": ["booking_code", "reason_code"],
        },
    },
    {
        "name": "create_refund_request",
        "description": "Tạo yêu cầu hoàn/hủy trong hệ thống (ghi DB) sau khi đã đánh giá. Hủy miễn phí sẽ tự duyệt; các trường hợp khác ở trạng thái chờ duyệt.",
        "input_schema": {
            "type": "object",
            "properties": {
                "booking_code": {"type": "string"},
                "reason_code": {"type": "string", "enum": REASON_CODES},
                "reason_text": {"type": "string"},
            },
            "required": ["booking_code", "reason_code"],
        },
    },
    {
        "name": "decide_request",
        "description": "Duyệt hoặc từ chối một yêu cầu đang chờ (vai support/đơn vị lưu trú).",
        "input_schema": {
            "type": "object",
            "properties": {
                "request_id": {"type": "string", "description": "Mã yêu cầu, vd REQ-1001"},
                "action": {"type": "string", "enum": ["approve", "reject"]},
                "reason": {"type": "string", "description": "Lý do từ chối (khi action='reject')"},
            },
            "required": ["request_id", "action"],
        },
    },
    {
        "name": "list_requests",
        "description": "Liệt kê các yêu cầu hoàn/hủy, lọc theo trạng thái nếu cần.",
        "input_schema": {
            "type": "object",
            "properties": {
                "status": {"type": "string", "enum": ["pending", "approved", "rejected", "auto_approved"]},
            },
        },
    },
]
