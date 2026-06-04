# Flow — Luồng hủy/đổi booking (Checkpoint 1)

Flow end-to-end gồm **happy path + error path**. Ở CP1 khối quyết định là rule-based mock;
ở CP2 khối `evaluateCancellation()` được thay bằng AI (LLM + RAG chính sách) — phần còn lại giữ nguyên.

## Sơ đồ quyết định (as-is của prototype)

```mermaid
flowchart TD
  A([User nhập mã booking + lý do]) --> B{Tìm thấy mã?}
  B -->|Không| ERR[["❌ not_found<br/>Chuyển hỗ trợ kèm ngữ cảnh<br/>(KHÔNG tự từ chối)"]]

  B -->|Có| C{Lý do nằm trong<br/>danh sách chuẩn?}
  C -->|other, chưa mô tả| ASK[["❓ needs_clarification<br/>Hỏi lại, không ép chọn sai"]]
  C -->|other, có mô tả| HUMAN1[["👤 needs_human<br/>Bất khả kháng → nhân viên xác minh"]]

  C -->|Lý do chuẩn| D{Loại chính sách?}
  D -->|free_cancellation & còn hạn| HAPPY[["✅ auto_eligible<br/>Phí 0 → cho hủy ngay"]]
  D -->|refundable| FEE[["💳 eligible_with_fee<br/>Phí KS + phí xử lý 10% (32k–470k)<br/>→ user xác nhận"]]
  D -->|non_refundable| HUMAN2[["👤 needs_human<br/>Chuyển đơn vị lưu trú xét (≤2 ngày)"]]

  HAPPY --> CONF{User bấm xác nhận?}
  FEE --> CONF
  CONF -->|Có| OK[["📨 Đã gửi yêu cầu hủy<br/>(chỉ báo thành công khi đã xác nhận)"]]
  CONF -->|Để sau| A

  ERR --> HO[[Bàn giao nhân viên<br/>+ toàn bộ context]]
  HUMAN1 --> HO
  HUMAN2 --> HO
```

## Vòng đời yêu cầu sau khi gửi (USER ↔ SUPPORT)

Sau khi user gửi, yêu cầu được lưu vào kho dùng chung (localStorage). Bộ phận hỗ trợ /
đơn vị lưu trú duyệt hoặc từ chối ở `admin.html`; trạng thái cập nhật ngay sang trang user.

```mermaid
stateDiagram-v2
  [*] --> auto_approved: free_cancellation\n(tự duyệt, miễn phí)
  [*] --> pending: fee / non_refundable / force_majeure\n(chờ support)
  pending --> approved: Support DUYỆT\n→ hoàn tiền (tối đa 5 ngày)
  pending --> rejected: Support TỪ CHỐI\n+ lý do gửi cho khách
  auto_approved --> [*]
  approved --> [*]
  rejected --> [*]
```

- User xem trạng thái ở panel **"Yêu cầu của tôi"** (trang khách hàng).
- Support thao tác ở **Trang hỗ trợ** (`admin.html`): hàng đợi `pending` + nút Duyệt/Từ chối.
- Hai trang đồng bộ realtime qua sự kiện `storage` (mở 2 tab để thấy).

## Map sang 4 paths của SPEC

| Path | Nhánh trong sơ đồ | Trạng thái engine |
|---|---|---|
| **Happy** | free_until còn hạn → xác nhận → gửi yêu cầu | `auto_eligible` → `confirm` |
| **Low-confidence** | lý do "other" → hỏi lại / cần xác minh | `needs_clarification`, `needs_human` |
| **Failure** | mã sai → chuyển hỗ trợ, không từ chối oan | `not_found` |
| **Correction** | "Để sau" / quay lại nhập lại; escalate kèm context để người sửa | nút `reset`, handoff bundle |

## Phân công task CP1 (theo slide Day 06)

| Task | File / việc | Trạng thái |
|---|---|---|
| Vẽ flow (Mermaid) | `docs/flow.md` | ✅ |
| Dựng mockup end-to-end | `index.html`, `styles.css`, `src/app.js` | ✅ |
| Lấy data | `src/data.js` (booking + chính sách mẫu) | ✅ |
| Tối ưu prompt (chuẩn bị AI) | `docs/ai-prompt.md` | ✅ |
| Code phần AI (điểm cắm) | `src/decision-engine.js → evaluateCancellation()` | ✅ stub, CP2 thay bằng AI |
| Chọn 1 flow để gắn AI | Flow hủy/đổi booking | ✅ |
