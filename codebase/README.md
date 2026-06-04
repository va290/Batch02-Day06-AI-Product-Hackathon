# Traveloka — AI hỗ trợ hủy/đổi booking

Nhóm **4Tuner** · Track B Travel & Hospitality · Day 06 AI Product Hackathon.
Luồng chọn để gắn AI: **hủy/hoàn đặt phòng khách sạn** (xem thin-spec Day 05).

## Kiến trúc (cách A — JSON DB + backend dùng chung)

```
              data/db.json   (bookings + refund_requests)
                     │  single source of truth
              server/store.py  (đọc/ghi JSON)
                ▲                         ▲
   FastAPI (api.py)              AI Agent (agent_runner.py — pattern Day04)
   REST + phục vụ web            tools: search_booking · evaluate_cancellation
        ▲                                · create_refund_request · decide_request
   Web tĩnh (index.html, admin.html)
   gọi REST qua src/api-client.js
```

- Web (khách hàng + support) và AI agent **dùng chung 1 DB** → ai thao tác, bên kia thấy.
- `policy.py` là bộ đánh giá chính sách **authoritative** (bám `docs/refund-policy.md`), dùng bởi cả REST lẫn agent.

## Chạy thủ công

```bash
cd server
pip install -r requirements.txt          # fastapi, uvicorn, openai, python-dotenv

# (chỉ cần nếu dùng Trợ lý AI) tạo .env và điền LLM tùy biến (giống Day04)
cp .env.example .env
#   CUSTOM_BASE_URL / CUSTOM_API_KEY / CUSTOM_MODEL  (tái dùng được .env của Day04)

uvicorn api:app --reload --port 8000
```

Mở (chatbot AI ở nút 💬 góc dưới phải mọi trang khách hàng):
- **Phòng đã đặt (home):** http://localhost:8000/  → chọn phòng → Hủy/Đổi
- **Hủy / Đổi:** http://localhost:8000/cancel.html
- **Yêu cầu của tôi:** http://localhost:8000/requests.html  → bấm mã REQ để xem chi tiết
- **Support/Admin:** http://localhost:8000/admin.html (tab 2)

> Web (hủy/duyệt/từ chối) chạy đầy đủ không cần AI. Chatbot AI dùng LLM tùy biến OpenAI-compatible
> (CUSTOM_BASE_URL/CUSTOM_API_KEY/CUSTOM_MODEL) — giống provider 'custom' của Day04.

Chạy agent bằng CLI (không cần web):
```bash
cd server && python3 agent_runner.py
# gõ: Tôi muốn hủy TRV12345 vì đổi lịch
```

## Kịch bản demo (happy + error path)

| Mã mẫu | Lý do | Kết quả | Path |
|---|---|---|---|
| `TRV12345` | Đổi lịch | Hủy miễn phí → xác nhận → tự duyệt | **Happy** |
| `TRV55555` | Sức khỏe | Có phí (KS 15% + xử lý 10% kẹp 32k–470k) → user xác nhận → chờ duyệt | **Có phí (augment)** |
| `TRV67890` | Đổi lịch | Không hoàn → chuyển đơn vị lưu trú xét (≤2 ngày) | **Escalate** |
| `TRV12345` | "Lý do khác" trống | Hỏi lại, không ép chọn sai | **Low-confidence** |
| `TRV12345` | "Lý do khác" = visa bị từ chối | Xét diện bất khả kháng → chuyển người | **Low-confidence → escalate** |
| `TRV00000` | bất kỳ | "Chưa xác định được mã" → chuyển hỗ trợ, không từ chối oan | **Error / not found** |

### Vòng lặp duyệt (USER ↔ SUPPORT ↔ AGENT)

1. User gửi yêu cầu (web) hoặc nhờ **Trợ lý AI** ("hủy TRV12345 vì đổi lịch") → tạo yêu cầu trong `db.json`.
2. Mở **admin.html** → hàng đợi → **Duyệt** / **Từ chối** (kèm lý do). *(Agent cũng có thể duyệt qua `decide_request`.)*
3. Trang user (và admin) **tự cập nhật** sau ~3.5s (polling) → *Đã duyệt — đang hoàn tiền* hoặc *Bị từ chối*.
4. Seed sẵn 3 yêu cầu mẫu. Nút **"Reset dữ liệu demo"** ở admin để chạy lại từ đầu.

## Quyết định Auto/Aug

**Conditional automation:** auto khi hủy miễn phí; user xác nhận khi có phí; chuyển người (đơn vị lưu trú)
khi non-refundable / bất khả kháng / mã sai. Human role = rescuer + decider. Agent tuân đúng quy tắc này (xem `agent_prompts.py`).

## Khớp chính sách thật

Mọi con số (phí xử lý 10% kẹp 32k–470k, hoàn tối đa 5 ngày sau phê duyệt, non-refundable đơn vị lưu trú xét ≤2 ngày,
ngân hàng tới 90 ngày, không hoàn một phần, mã giảm giá không hoàn, hoàn đúng tên tài khoản) bám
`docs/refund-policy.md`. **Booking mẫu (`TRV…`) là dữ liệu hư cấu để demo.**

## Cấu trúc

```
traveloka-refund-ai/
├── index.html       # Phòng đã đặt (home)
├── cancel.html      # Hủy / Đổi (luồng quyết định)
├── requests.html    # Yêu cầu của tôi (danh sách)
├── request.html     # Chi tiết 1 yêu cầu (?id=REQ-xxxx)
├── admin.html       # Support console
├── styles.css
├── src/
│   ├── api-client.js     # client REST (chung)
│   ├── chat.js           # chatbot AI nổi (chung mọi trang)
│   ├── bookings.js       # trang Phòng đã đặt
│   ├── cancel.js         # trang Hủy/Đổi
│   ├── requests.js       # trang Yêu cầu của tôi
│   ├── request-detail.js # trang chi tiết yêu cầu
│   └── admin.js           # trang support
├── server/
│   ├── api.py            # FastAPI: REST + phục vụ web + /api/agent/chat
│   ├── store.py          # JSON store (single source of truth)
│   ├── policy.py         # đánh giá chính sách (authoritative)
│   ├── constants.py      # hằng số chính sách + text UI
│   ├── agent_tools.py    # tools cho agent (Day04 pattern)
│   ├── agent_prompts.py  # system prompt
│   ├── agent_runner.py   # vòng lặp tool-use (LLM custom OpenAI-compatible, như Day04) + CLI
│   ├── requirements.txt, .env.example
│   └── data/db.seed.json # seed (db.json sinh ra từ đây, đã gitignore)
└── docs/
    ├── flow.md, refund-policy.md, policy-source.md, ai-prompt.md
```

## Lưu ý
- `db.json` và `.env` đã được gitignore (server/.gitignore).
- Đồng bộ giữa các tab dùng polling 3.5s (không phải realtime) — đủ cho demo.

## Công cụ & API đã dùng
- **LLM:** gateway tùy biến OpenAI-compatible, cấu hình qua `CUSTOM_BASE_URL` / `CUSTOM_API_KEY` / `CUSTOM_MODEL` (đổi model chỉ bằng sửa `.env`).
- **Agent framework:** LangChain + LangGraph (`create_agent`, tool-calling) — `server/agent_runner.py`.
- **Backend:** FastAPI + Uvicorn; "DB" là file JSON (`server/store.py`) dùng chung cho web và agent.
- **Frontend:** HTML/CSS/JavaScript thuần (không framework), gọi REST.
- **Dữ liệu grounding:** chính sách hoàn tiền thật của Traveloka (`docs/refund-policy.md`).

## Phân công
> ⚠️ Điền mã HV + họ tên đầy đủ ở `README.md` gốc của repo.

| Thành viên | Phụ trách |
|-----------|-----------|
| Hưng | Research / evidence · kịch bản demo |
| Việt Anh | SPEC · grounding chính sách |
| Toàn | Prototype web · backend / JSON store |
| Lân | AI agent + tools · test failure path |
