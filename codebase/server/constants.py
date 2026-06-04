"""
constants.py — Hằng số chính sách + text UI (single source, no imports).

Số liệu chính sách bám đúng chính sách thật của Traveloka — xem
docs/refund-policy.md và docs/policy-source.md. KHÔNG bịa.
"""

from datetime import date


def today() -> str:
    """Ngày hiện tại THẬT (ISO yyyy-mm-dd) — dùng cho mọi tính toán/truy vấn thời gian."""
    return date.today().isoformat()

# Hằng số chính sách thật.
POLICY = {
    "PROCESS_DAYS_AFTER_APPROVAL": 5,   # P-PROCESS-5D
    "PROCESSING_FEE_PERCENT": 10,       # P-FEE-10
    "PROCESSING_FEE_MIN": 32000,        # P-FEE-10 (tối thiểu)
    "PROCESSING_FEE_MAX": 470000,       # P-FEE-10 (tối đa)
    "HOTEL_DECISION_DAYS": 2,           # P-NR-2D
}

# Lý do chuẩn — CỐ TÌNH thiếu "visa bị từ chối" để tái hiện pain ép-chọn-sai.
REASON_OPTIONS = [
    {"code": "schedule_change", "label": "Đổi lịch / kẹt công việc"},
    {"code": "illness", "label": "Lý do sức khỏe"},
    {"code": "weather_disaster", "label": "Thời tiết xấu / thiên tai"},
    {"code": "other", "label": "Lý do khác (tự mô tả)"},
]

POLICY_TEXTS = {
    "free_cancellation": (
        'Chính sách hủy phòng: Đặt phòng được hủy miễn phí trước "Hạn hủy miễn phí". '
        "Hoàn tiền lên đến 5 ngày sau khi được phê duyệt."
    ),
    "refundable": (
        "Chính sách hoàn tiền (đặt phòng có thể hoàn): Khoản hoàn = số tiền sau khi trừ "
        "phí hủy của khách sạn + phí xử lý 10% (tối thiểu 32.000đ, tối đa 470.000đ) + "
        "phí chuyển khoản (nếu có)."
    ),
    "non_refundable": (
        "Đặt phòng không hoàn tiền: Bạn vẫn có thể gửi yêu cầu; Traveloka chuyển tới đơn vị "
        "lưu trú để xét (tối đa 2 ngày). Đơn vị lưu trú — không phải Traveloka — quyết định "
        "chấp nhận/từ chối."
    ),
}

# Cảnh báo bắt buộc trước khi xác nhận (P-NO-PARTIAL, P-NO-VOUCHER, P-ONCE).
CONFIRM_WARNINGS = [
    "Không hoàn tiền một phần: yêu cầu áp cho TOÀN BỘ mã đặt phòng (mọi đêm, mọi phòng).",
    "Mã giảm giá đã áp dụng sẽ không được hoàn lại.",
    "Yêu cầu hoàn tiền chỉ gửi một lần và không thể hoàn tác sau khi gửi.",
]

# Disclaimer sau khi gửi yêu cầu (P-BANK-90D, P-NAMED-ACCOUNT).
REFUND_DISCLAIMERS = [
    "Tiền hoàn có thể mất tới 90 ngày để hiển thị trong tài khoản, tùy chính sách ngân hàng của bạn.",
    "Khoản hoàn chỉ được chuyển vào tài khoản đứng tên người liên hệ/người đặt phòng; "
    "nếu khác tên, yêu cầu có thể bị đình chỉ.",
]

STATUS_LABEL = {
    "pending": "Chờ duyệt",
    "approved": "Đã duyệt — đang hoàn tiền",
    "rejected": "Bị từ chối",
    "auto_approved": "Đã duyệt (tự động, miễn phí)",
}
