"""
agent_runner.py — Agent loop bằng langchain + langgraph (create_agent), như Day04 E403.
LLM tùy biến OpenAI-compatible (ChatOpenAI + base_url) qua CUSTOM_BASE_URL/KEY/MODEL.

run_agent(message, history) -> {"reply": str, "trace": [...], "messages": [...]}.
CLI: python agent_runner.py
"""
from __future__ import annotations

import json
import os
from typing import Any

import guardrails
import agent_tools as T
from agent_prompts import SYSTEM_PROMPT

try:  # nạp .env nếu có python-dotenv
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
except Exception:
    pass


def _cfg() -> dict[str, Any]:
    base_url = os.getenv("CUSTOM_BASE_URL") or os.getenv("OPENAI_BASE_URL")
    api_key = os.getenv("CUSTOM_API_KEY") or os.getenv("OPENAI_API_KEY")
    model = os.getenv("CUSTOM_MODEL") or os.getenv("AGENT_MODEL") or "gpt-4o-mini"
    # Mirror Day04: mặc định temperature=1.0 (model extended-thinking từ chối != 1).
    custom_temp = os.getenv("CUSTOM_TEMPERATURE")
    try:
        temperature = float(custom_temp) if custom_temp not in (None, "") else 1.0
    except ValueError:
        temperature = 1.0
    return {"base_url": base_url, "api_key": api_key, "model": model, "temperature": temperature}


def _model():
    """ChatOpenAI cho gateway tùy biến — giống build_chat_model('custom') của Day04."""
    from langchain_openai import ChatOpenAI
    cfg = _cfg()
    if not cfg["api_key"]:
        raise RuntimeError("Thiếu CUSTOM_API_KEY (hoặc OPENAI_API_KEY) trong .env")
    return ChatOpenAI(
        model=cfg["model"],
        api_key=cfg["api_key"],
        base_url=cfg["base_url"],
        temperature=cfg["temperature"],
        max_retries=int(os.getenv("CUSTOM_MAX_RETRIES", "3")),
    )


def _build_tools():
    """Bọc các hàm tool (agent_tools) thành langchain @tool. Trả JSON string như Day04."""
    from langchain_core.tools import tool

    @tool
    def search_booking(booking_code: str) -> str:
        """Tra cứu thông tin một đặt phòng theo mã (vd TRV12345)."""
        return json.dumps(T.search_booking(booking_code), ensure_ascii=False)

    @tool
    def evaluate_cancellation(booking_code: str, reason_code: str, reason_text: str = "") -> str:
        """Đánh giá điều kiện hủy/hoàn theo chính sách (chưa ghi DB). reason_code thuộc
        {schedule_change, illness, weather_disaster, other}; dùng 'other' + reason_text nếu
        lý do nằm ngoài danh sách (vd visa bị từ chối)."""
        return json.dumps(T.evaluate_cancellation(booking_code, reason_code, reason_text), ensure_ascii=False)

    @tool
    def create_refund_request(booking_code: str, reason_code: str, reason_text: str = "") -> str:
        """Tạo yêu cầu hoàn/hủy trong hệ thống (ghi DB) sau khi đã đánh giá và khách đồng ý.
        Hủy miễn phí sẽ tự duyệt; các trường hợp khác ở trạng thái chờ duyệt."""
        return json.dumps(T.create_refund_request(booking_code, reason_code, reason_text), ensure_ascii=False)

    @tool
    def decide_request(request_id: str, action: str, reason: str = "") -> str:
        """Duyệt hoặc từ chối một yêu cầu đang chờ (vai support). action = 'approve' | 'reject'."""
        return json.dumps(T.decide_request(request_id, action, reason), ensure_ascii=False)

    @tool
    def list_requests(status: str = "") -> str:
        """Liệt kê các yêu cầu hoàn/hủy, lọc theo trạng thái nếu cần."""
        return json.dumps(T.list_requests(status), ensure_ascii=False)

    return [search_booking, evaluate_cancellation, create_refund_request, decide_request, list_requests]


def _agent():
    from langchain.agents import create_agent
    from constants import today
    # Inject ngày hiện tại để agent trả lời đúng các truy vấn liên quan thời gian.
    system = (
        SYSTEM_PROMPT
        + f"\n\nNGÀY HIỆN TẠI: {today()}. Khi có câu hỏi liên quan thời gian "
        "(còn mấy ngày, hôm nay, hạn hủy...), hãy tính dựa trên ngày này."
    )
    return create_agent(model=_model(), tools=_build_tools(), system_prompt=system)


def _norm(content: Any) -> str:
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = [(_norm(x.get("text", "")) if isinstance(x, dict) else _norm(x)) for x in content]
        return "\n".join(p for p in parts if p).strip()
    return str(content).strip()


def run_agent(message: str, history: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    # Lớp 1: guardrail input — chặn injection/lệch chủ đề TRƯỚC khi gọi LLM.
    allowed, refusal = guardrails.check_input(message)
    if not allowed:
        hist = (history or []) + [{"role": "user", "content": message}, {"role": "assistant", "content": refusal}]
        return {"reply": refusal, "trace": [{"tool": "guardrail", "input": {"blocked": True}, "result": {"refused": True}}],
                "messages": hist}

    from langchain_core.messages import AIMessage, ToolMessage

    convo = list(history or []) + [{"role": "user", "content": message}]
    result = _agent().invoke({"messages": convo})
    msgs = result["messages"] if isinstance(result, dict) else result

    # trace: gom tool_calls (tên + args) và kết quả tool tương ứng.
    tool_results: dict[str, str] = {}
    for m in msgs:
        if isinstance(m, ToolMessage):
            tool_results[m.tool_call_id] = _norm(m.content)
    trace: list[dict[str, Any]] = []
    for m in msgs:
        if isinstance(m, AIMessage):
            for tc in (m.tool_calls or []):
                raw = tool_results.get(tc.get("id"))
                try:
                    res = json.loads(raw) if raw else {}
                except Exception:
                    res = {"raw": raw}
                trace.append({"tool": tc.get("name"), "input": tc.get("args", {}), "result": res})

    reply = ""
    for m in reversed(msgs):
        if isinstance(m, AIMessage):
            txt = _norm(m.content)
            if txt:
                reply = txt
                break
    reply = guardrails.scrub_output(reply)

    # history rút gọn (role/content text) cho lượt sau.
    out_hist = list(history or []) + [{"role": "user", "content": message}, {"role": "assistant", "content": reply}]
    return {"reply": reply, "trace": trace, "messages": out_hist}


if __name__ == "__main__":
    print("AI support agent (langgraph) — Ctrl-C để thoát. VD: 'Tôi muốn hủy TRV12345 vì đổi lịch'")
    hist: list[dict[str, Any]] = []
    try:
        while True:
            msg = input("\nBạn: ").strip()
            if not msg:
                continue
            out = run_agent(msg, hist)
            hist = out["messages"]
            for t in out["trace"]:
                print(f"  · tool {t['tool']}({t.get('input')})")
            print("Agent:", out["reply"])
    except (KeyboardInterrupt, EOFError):
        print("\nTạm biệt.")
