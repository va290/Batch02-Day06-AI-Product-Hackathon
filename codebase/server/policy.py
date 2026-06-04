"""
policy.py — Bộ đánh giá hủy/hoàn (authoritative). Port từ decision-engine.js, bám
chính sách thật (constants). Dùng bởi REST API và agent tool evaluate_cancellation.

evaluate_cancellation() trả về Decision; build_request() chuyển Decision -> bản ghi
refund_request để lưu vào store.
"""
from __future__ import annotations

from datetime import date
from typing import Any

import store
from constants import (
    CONFIRM_WARNINGS,
    POLICY,
    POLICY_TEXTS,
    REASON_OPTIONS,
    today,
)


def money(amount: float, currency: str = "VND") -> str:
    return f"{round(amount):,}".replace(",", ".") + " " + (currency or "VND")


def _days_between(from_iso: str, to_iso: str) -> int:
    a = date.fromisoformat(from_iso)
    b = date.fromisoformat(to_iso)
    return (b - a).days


def processing_fee(amount: float) -> int:
    raw = amount * POLICY["PROCESSING_FEE_PERCENT"] / 100
    return int(min(POLICY["PROCESSING_FEE_MAX"], max(POLICY["PROCESSING_FEE_MIN"], raw)))


def _timeline() -> str:
    return f"tối đa {POLICY['PROCESS_DAYS_AFTER_APPROVAL']} ngày sau khi được phê duyệt"


def reason_label(reason_code: str, reason_text: str = "") -> str:
    if reason_code == "other":
        return (reason_text or "").strip() or "Lý do khác"
    found = next((r for r in REASON_OPTIONS if r["code"] == reason_code), None)
    return found["label"] if found else reason_code


def evaluate_cancellation(booking_code: str, reason_code: str, reason_text: str = "") -> dict[str, Any]:
    code = (booking_code or "").strip().upper()
    booking = store.get_booking(code)
    base: dict[str, Any] = {"warnings": [], "decidedBy": "policy-engine (server)"}

    # FAILURE: không tìm thấy mã -> không tự từ chối, chuyển hỗ trợ.
    if not booking:
        return {
            **base,
            "status": "not_found",
            "recommendedAction": "escalate",
            "eligible": None,
            "policySource": None,
            "headline": "Chưa xác định được mã đặt phòng",
            "detail": (
                f'Hệ thống chưa tìm thấy mã "{code or "(trống)"}". Để tránh xử lý sai, yêu cầu được '
                "chuyển nhân viên hỗ trợ kèm thông tin bạn đã nhập — bạn KHÔNG cần kể lại từ đầu."
            ),
        }

    base["booking"] = booking
    base["policySource"] = POLICY_TEXTS[booking["policyType"]]

    # LOW-CONFIDENCE: lý do ngoài danh sách -> hỏi lại / xét bất khả kháng.
    if reason_code == "other":
        txt = (reason_text or "").strip()
        if len(txt) < 4:
            return {
                **base,
                "status": "needs_clarification",
                "recommendedAction": "clarify",
                "eligible": None,
                "headline": "Cần bạn nói rõ lý do",
                "detail": (
                    "Lý do của bạn nằm ngoài danh sách có sẵn. Vui lòng mô tả ngắn gọn "
                    '(vd: "visa bị từ chối") để được xét đúng diện, thay vì buộc chọn một lý do không đúng.'
                ),
            }
        return {
            **base,
            "status": "needs_human",
            "recommendedAction": "escalate",
            "eligible": None,
            "headline": "Lý do đặc biệt — cần xét diện bất khả kháng",
            "detail": (
                f'Lý do "{txt}" có thể thuộc diện ngoài tầm kiểm soát. Yêu cầu được chuyển đơn vị lưu trú '
                f"xét (tối đa {POLICY['HOTEL_DECISION_DAYS']} ngày) kèm toàn bộ ngữ cảnh, tránh từ chối oan."
            ),
        }

    # NON-REFUNDABLE: đơn vị lưu trú quyết -> chuyển người.
    if booking["policyType"] == "non_refundable":
        return {
            **base,
            "status": "needs_human",
            "recommendedAction": "escalate",
            "eligible": None,
            "headline": "Đặt phòng không hoàn tiền — chuyển đơn vị lưu trú xét",
            "detail": (
                "Đây là giá ưu đãi không hoàn tiền. Bạn vẫn có thể gửi yêu cầu: Traveloka chuyển tới đơn vị "
                f"lưu trú để xét trong tối đa {POLICY['HOTEL_DECISION_DAYS']} ngày (quá hạn không phản hồi, "
                "yêu cầu tự hủy). Traveloka không tự quyết chấp nhận/từ chối."
            ),
            "warnings": [
                "Với đặt phòng không hoàn: sau khi gửi yêu cầu, bạn không còn lựa chọn hủy/đổi ngày khác."
            ],
        }

    # HAPPY: còn hạn miễn phí hủy.
    if booking["policyType"] == "free_cancellation":
        days_left = _days_between(today(), booking["freeUntil"])
        if days_left >= 0:
            return {
                **base,
                "status": "auto_eligible",
                "recommendedAction": "auto_cancel",
                "eligible": True,
                "feePercent": 0,
                "feeAmount": 0,
                "refundAmount": booking["amount"],
                "timelineText": _timeline(),
                "headline": "Đủ điều kiện hủy miễn phí",
                "detail": (
                    f'Còn {days_left} ngày trong hạn hủy miễn phí (tới {booking["freeUntil"]}). '
                    f'Bạn được hoàn {money(booking["amount"], booking["currency"])} (phí 0đ), hoàn tiền {_timeline()}.'
                ),
                "warnings": list(CONFIRM_WARNINGS),
            }
        booking = {**booking, "hotelCancelFeePercent": booking.get("hotelCancelFeePercent", 100)}

    # REFUNDABLE: phí = phí khách sạn + phí xử lý 10% (kẹp).
    hotel_pct = booking.get("hotelCancelFeePercent", 0)
    hotel_fee = round(booking["amount"] * hotel_pct / 100)
    proc_fee = processing_fee(booking["amount"])
    fee_amount = hotel_fee + proc_fee
    refund_amount = max(0, booking["amount"] - fee_amount)
    fee_percent = round(fee_amount / booking["amount"] * 100)

    return {
        **base,
        "status": "eligible_with_fee",
        "recommendedAction": "confirm",
        "eligible": True,
        "feePercent": fee_percent,
        "feeAmount": fee_amount,
        "hotelFee": hotel_fee,
        "procFee": proc_fee,
        "refundAmount": refund_amount,
        "timelineText": _timeline(),
        "headline": f"Hủy được — có phí (~{fee_percent}%)",
        "detail": (
            f'Phí gồm: phí khách sạn {money(hotel_fee, booking["currency"])} ({hotel_pct}%) + '
            f'phí xử lý Traveloka {money(proc_fee, booking["currency"])} (10%, kẹp 32k–470k). '
            f'Bạn được hoàn {money(refund_amount, booking["currency"])}, hoàn tiền {_timeline()}.'
        ),
        "warnings": list(CONFIRM_WARNINGS),
    }


def build_request(decision: dict[str, Any], reason_code: str, reason_text: str = "") -> dict[str, Any] | None:
    """Chuyển Decision -> bản ghi refund_request. None nếu không nên tạo (not_found/clarify)."""
    b = decision.get("booking")
    if not b or decision["status"] in ("not_found", "needs_clarification"):
        return None
    if decision["status"] == "auto_eligible":
        rtype, rstatus = "free", "auto_approved"
    elif decision["status"] == "eligible_with_fee":
        rtype, rstatus = "fee", "pending"
    else:  # needs_human
        rtype = "force_majeure" if reason_code == "other" else "non_refundable"
        rstatus = "pending"
    return {
        "bookingCode": b["code"],
        "hotel": b["hotel"],
        "room": b["room"],
        "amount": b["amount"],
        "currency": b["currency"],
        "reasonLabel": reason_label(reason_code, reason_text),
        "type": rtype,
        "status": rstatus,
        "feeAmount": decision.get("feeAmount"),
        "refundAmount": decision.get("refundAmount"),
        "timelineText": decision.get("timelineText"),
        "policySource": decision.get("policySource"),
    }
