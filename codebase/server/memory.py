"""
memory.py — Bộ nhớ hội thoại theo phiên + nén/giải phóng context khi đầy.

- Nhớ user đã hỏi gì: lưu các lượt (user/assistant) theo session_id.
- Tránh tụt hiệu suất khi context phình: khi số lượt vượt MAX_TURNS, TÓM TẮT (compact)
  các lượt cũ thành một "ghi nhớ" ngắn (gọi LLM), chỉ giữ KEEP_RECENT lượt gần nhất.
  => Số message đưa vào LLM mỗi lần luôn bị chặn trần (summary + vài lượt gần đây).
- reset(session_id) để xoá hẳn (nút "Cuộc trò chuyện mới").

Lưu in-memory theo tiến trình server (mất khi restart) — đủ cho demo.
"""
from __future__ import annotations

from typing import Any

import agent_runner

MAX_TURNS = 12      # > ngưỡng này thì nén (12 = ~6 lượt hỏi-đáp)
KEEP_RECENT = 6     # số lượt gần nhất giữ nguyên sau khi nén

# session_id -> {"summary": str|None, "turns": [ {role, content}, ... ]}
_SESSIONS: dict[str, dict[str, Any]] = {}


def _sess(session_id: str) -> dict[str, Any]:
    return _SESSIONS.setdefault(session_id, {"summary": None, "turns": []})


def _history_for_llm(sess: dict[str, Any]) -> list[dict[str, str]]:
    """Ghi nhớ (nếu có) + các lượt hiện tại — đây là context truyền cho agent."""
    hist: list[dict[str, str]] = []
    if sess["summary"]:
        hist.append({"role": "system", "content": "Ghi nhớ hội thoại trước (tóm tắt): " + sess["summary"]})
    hist.extend(sess["turns"])
    return hist


def _summarize(prev_summary: str | None, old_turns: list[dict[str, str]]) -> str:
    """Nén các lượt cũ thành tóm tắt ngắn (tiếng Việt). Fallback an toàn nếu LLM lỗi."""
    convo = "\n".join(f'{t["role"]}: {t["content"]}' for t in old_turns)
    prompt = (
        "Tóm tắt NGẮN GỌN (tiếng Việt, tối đa 120 từ) cuộc hội thoại hỗ trợ đặt phòng dưới đây "
        "để làm bộ nhớ cho các lượt sau. Nêu: mã đặt phòng đã nhắc, ý định của khách, kết quả/quyết định, "
        "và mã yêu cầu (REQ-...) nếu có. Chỉ trả về đoạn tóm tắt, không thêm gì khác.\n\n"
        + (f"[Ghi nhớ trước đó]: {prev_summary}\n\n" if prev_summary else "")
        + f"[Hội thoại cần tóm tắt]:\n{convo}"
    )
    try:
        resp = agent_runner._model().invoke(prompt)
        return agent_runner._norm(getattr(resp, "content", "")) or (prev_summary or "")
    except Exception:
        # Fallback: nối ghi nhớ cũ + danh sách mã/ý định thô (không chặn luồng chat).
        joined = (prev_summary or "") + " " + " | ".join(t["content"][:80] for t in old_turns if t["role"] == "user")
        return joined.strip()[:600]


def _maybe_compact(sess: dict[str, Any]) -> bool:
    if len(sess["turns"]) <= MAX_TURNS:
        return False
    old = sess["turns"][:-KEEP_RECENT]
    sess["summary"] = _summarize(sess["summary"], old)
    sess["turns"] = sess["turns"][-KEEP_RECENT:]
    return True


def chat(session_id: str, message: str) -> dict[str, Any]:
    """Chạy 1 lượt chat có nhớ: nạp history -> agent -> lưu lại -> nén nếu đầy."""
    sess = _sess(session_id)
    out = agent_runner.run_agent(message, _history_for_llm(sess))
    sess["turns"].append({"role": "user", "content": message})
    sess["turns"].append({"role": "assistant", "content": out["reply"]})
    compacted = _maybe_compact(sess)
    return {
        "reply": out["reply"],
        "trace": out["trace"],
        "session_id": session_id,
        "memory": {"turns": len(sess["turns"]), "compacted": compacted, "hasSummary": bool(sess["summary"])},
    }


def reset(session_id: str) -> None:
    _SESSIONS.pop(session_id, None)
