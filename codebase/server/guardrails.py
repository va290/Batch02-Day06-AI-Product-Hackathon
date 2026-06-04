"""
guardrails.py — Các lớp bảo vệ giữ chatbot trong phạm vi cho phép.

Lớp 1 (input, deterministic): chặn prompt-injection / jailbreak / đòi lộ system prompt,
       và yêu cầu RÕ RÀNG lệch chủ đề (không liên quan hủy/đổi/hoàn đặt phòng).
Lớp 2 (prompt): khóa phạm vi + chính sách từ chối trong agent_prompts.SYSTEM_PROMPT.
Lớp 3 (output, deterministic): chặn rò rỉ chỉ dẫn hệ thống, đảm bảo phản hồi không rỗng.
"""
from __future__ import annotations

import re

REFUSAL = (
    "Mình là trợ lý hỗ trợ HỦY/ĐỔI/HOÀN TIỀN đặt phòng khách sạn trên Traveloka, "
    "nên chỉ có thể giúp trong phạm vi đó. Bạn cho mình biết mã đặt phòng (vd TRV12345) "
    "và việc cần hỗ trợ nhé."
)

# --- Lớp 1a: prompt-injection / jailbreak / đòi lộ chỉ dẫn ---
_INJECTION = [
    r"\bignore\b.*\b(previous|above|all|instruction|prompt|rule)",
    r"\bdisregard\b.*\b(previous|above|instruction|rule)",
    r"bỏ qua.*(hướng dẫn|chỉ dẫn|chỉ thị|lệnh|quy tắc|mọi|tất cả|ở trên|phía trên)",
    r"quên.*(hướng dẫn|chỉ dẫn|mọi thứ|tất cả|những gì)",
    r"(system\s*prompt|prompt\s*hệ thống|system\s*message|chỉ dẫn hệ thống)",
    r"(in ra|tiết lộ|cho.*xem|đọc|reveal|show|repeat|lặp lại).*(prompt|hướng dẫn|chỉ dẫn|system|cấu hình)",
    r"(developer mode|jailbreak|\bDAN\b|sudo mode)",
    r"(đóng vai|giả vờ|giả làm|act as|pretend|roleplay).*(?!.*đặt phòng)",
    r"(vô hiệu h?o?á|bypass|vượt qua).*(an toàn|bảo vệ|guardrail|kiểm duyệt)",
    r"bạn (là|đang là) (chatgpt|gpt|gemini|claude|bot gì)",
]

# --- Lớp 1b: lệch chủ đề (chỉ chặn khi CÓ tín hiệu off-topic và KHÔNG có tín hiệu nghiệp vụ) ---
_DOMAIN = [
    "hủy", "huỷ", "hoàn", "đổi", "refund", "cancel", "reschedule", "booking",
    "đặt phòng", "đặt chỗ", "phòng", "khách sạn", "vé", "mã", "trv", "tiền",
    "yêu cầu", "nhận phòng", "check-in", "traveloka", "vinpearl", "đơn",
]
_OFFTOPIC = [
    "code", "python", "javascript", "lập trình", "thời tiết", "weather", "nấu ăn",
    "công thức", "bài thơ", "làm thơ", "bài hát", "chính trị", "bầu cử", "translate",
    "dịch giúp", "giải toán", "phương trình", "crypto", "bitcoin", "chứng khoán",
    "kể chuyện", "truyện cười", "tán gẫu", "người yêu", "tình yêu",
]


def _norm(text: str) -> str:
    return (text or "").lower().strip()


def check_input(message: str) -> tuple[bool, str | None]:
    """Trả (allowed, refusal). allowed=False => trả thẳng refusal, không gọi LLM."""
    m = _norm(message)
    for pat in _INJECTION:
        if re.search(pat, m):
            return False, REFUSAL
    has_domain = any(k in m for k in _DOMAIN)
    has_offtopic = any(k in m for k in _OFFTOPIC)
    if has_offtopic and not has_domain:
        return False, REFUSAL
    return True, None


# --- Lớp 3: lọc output ---
_LEAK_MARKERS = ["QUY TRÌNH:", "QUY TẮC CỨNG", "SYSTEM_PROMPT", "Bạn là trợ lý hỗ trợ (support) của Traveloka"]


def scrub_output(reply: str) -> str:
    r = (reply or "").strip()
    if not r:
        return "Xin lỗi, mình chưa xử lý được yêu cầu này. Bạn thử lại với mã đặt phòng nhé."
    if any(marker in r for marker in _LEAK_MARKERS):
        return REFUSAL
    return r
