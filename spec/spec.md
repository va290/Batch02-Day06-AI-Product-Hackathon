# SPEC — AI hỗ trợ Hủy đặt phòng & Hoàn tiền (Traveloka)

**Nhóm:** 4Tuner · **Track:** Travel & Hospitality · **App soi:** Traveloka

> Đây là bản SPEC hoàn thiện từ thin-SPEC Day 5, phản ánh đúng sản phẩm nhóm đã **build và demo** ở Day 6
> (xem `spec/demo-slides.pdf` và code ở `codebase/`).

---

## 1. Bằng chứng

Nỗi đau đến từ luồng **hủy phòng / hoàn tiền** của Traveloka — chỗ khách cần hỗ trợ nhất thì lại gãy.

**Trải nghiệm trực tiếp (self-use).** Nhóm dùng thử app Traveloka và bản chính sách hoàn tiền thật, thấy:
khi muốn hủy, khách phải tự dán mã, chính sách phí/thời gian không hiện rõ trước khi bấm, và chatbot không có lối thoát lên người thật.

**Nguồn ngoài nhóm (review thật).** Điểm trung bình chỉ **1.5–2.0 sao** trên Trustpilot / App Store / CH Play (ảnh chụp trong slide demo):

- *"app quá tệ. Hủy phòng không chịu trả lại tiền cho khách"* — CH Play, 22/04/2026
- *"rất tệ hãng hủy vé traveloka bên trung gian không chịu giải quyết"* — 13/03/2026
- *"dịch vụ tối tệ, chậm chạp"* — 04/05/2026
- Phản hồi của Traveloka phần lớn là mẫu copy-paste "vui lòng gửi mã đặt chỗ qua…".

Gom lại thành 3 cụm pain:
1. **Chatbot chạy vòng quanh** — không gặp được hỗ trợ viên thật.
2. **Hoàn tiền mờ ám** — chờ tới 90 ngày, có lúc báo "thành công" giả.
3. **Ép chọn lý do sai & thông tin mù mờ** — thiếu lựa chọn lý do thực tế (vd "visa bị từ chối"); phí phạt và thời gian hoàn **không hiện trước** khi khách quyết định.

**Competitor / analog.** Trip.com (TripGenie), Expedia (Romie), Booking.com (AI Trip Planner), Klook (K.AI) đều mạnh ở **gợi ý lịch trình/đặt chỗ**, nhưng **hiếm app làm tốt AI cho luồng hủy/hoàn có minh bạch + lối thoát người thật** → đây là khoảng trống nhóm nhắm tới.

*(Các con số chính sách dùng trong sản phẩm bám đúng chính sách thật của Traveloka — xem `codebase/docs/refund-policy.md`.)*

## 2. Lát cắt để build

> Cho **khách đã đặt phòng khách sạn Traveloka đang muốn hủy/hoàn**, AI **tra chính sách thật** theo mã đặt phòng và lý do, trả về một **"thẻ quyết định"** (đủ điều kiện? phí bao nhiêu? bao lâu tiền về?), rồi **tự xử lý ca rõ ràng / chuyển người ca rủi ro** (conditional automation), tạo ra một **yêu cầu hủy có trạng thái theo dõi được**.

Đây là phần nhóm thật sự dựng và mang đi demo — không làm cả app Traveloka.

## 3. AI Product Canvas

| Ô | Trả lời |
|---|---------|
| **Value — Giá trị** | Cho khách đang hủy/hoàn đặt phòng. Họ đau ở chỗ không biết **điều kiện · phí · thời gian hoàn** và bị chatbot bỏ rơi. AI tra **chính sách thật** rồi giải thích minh bạch **trước khi** khách quyết — điều luồng hiện tại của Traveloka chưa làm tốt. |
| **Trust — Niềm tin** | Khi AI sai/không chắc, khách nhận ra vì: hệ thống **dẫn nguồn chính sách**, **không báo "đã hoàn"** khi yêu cầu chưa được duyệt, và mọi ca rủi ro được **chuyển người thật**. Sửa lỗi: support **duyệt/từ chối kèm lý do**; khách theo dõi trạng thái và có thể yêu cầu hỗ trợ tiếp. |
| **Feasibility — Khả thi** | Mỗi lượt là một lời gọi LLM (gateway OpenAI-compatible) + vài lời gọi tool nội bộ (rẻ, độ trễ thấp). Dữ liệu cần: **chính sách hoàn tiền thật** + thông tin booking. Rủi ro lớn nhất: AI **bịa chính sách/phí** → chặn bằng grounding. Ngưỡng dừng: ca không hoàn / phí lớn / mã sai → **không tự quyết**, chuyển người. |
| **Tín hiệu học** | Mỗi quyết định duyệt/từ chối của support được **ghi vào DB** (trạng thái + lý do). Đây là tín hiệu để chỉnh chính sách hiển thị và tập kiểm thử cho các ca tranh chấp. |

## 4. Tăng năng lực hay tự động hóa

**Quyết định: Conditional automation** (tự động hóa có điều kiện) — **không** full-auto.

- **Auto**: chỉ ca **hủy miễn phí** rõ ràng → tự duyệt ngay.
- **Augment (khách quyết)**: ca **có phí** → hiện rõ phí/hoàn/thời gian, **khách tự xác nhận** mới thực hiện.
- **Human (người quyết)**: ca **không hoàn / bất khả kháng / mã sai** → chuyển **đơn vị lưu trú / support** xét, kèm toàn bộ ngữ cảnh.

**Con người giữ quyền quyết định cuối** ở các ca rủi ro. Lý do chọn mức này: việc liên quan **tiền và chính sách phạt** — sai thì hậu quả nặng và khó hoàn tác — nên chỉ tự động phần rõ ràng & an toàn.

## 5. Bốn đường đi của trải nghiệm

| Đường đi | Sản phẩm thể hiện gì |
|----------|----------------------|
| **Đường thuận** | Mã đúng + đủ điều kiện → "thẻ quyết định" hiện rõ điều kiện/phí/thời gian → xác nhận chỉ 1 thao tác (HAPPY / CÓ PHÍ). |
| **Khi AI không chắc** | Lý do nằm ngoài danh sách (vd "visa bị từ chối") → **hỏi lại** để làm rõ, **không ép chọn lý do sai** (HỎI LẠI). |
| **Khi AI sai** | Mã sai / không tìm thấy chính sách → **không từ chối oan**, không báo trạng thái giả; **chuyển người kèm ngữ cảnh** (CHUYỂN NGƯỜI). |
| **Khi người dùng sửa** | Support **duyệt / từ chối (kèm lý do)** → trạng thái yêu cầu cập nhật realtime cho khách; quyết định được **log lại** để cải thiện. |

→ Đây chính là **"Hệ thống 4 nhánh quyết định"** trong slide demo: **HAPPY · CÓ PHÍ · CHUYỂN NGƯỜI · HỎI LẠI**.

## 6. Những kiểu lỗi đáng lo nhất

1. **AI bịa chính sách / phí (hallucination).**
   - Khi nào: đầu vào mơ hồ, hỏi chính sách hệ thống không có dữ liệu.
   - Hậu quả: khách mất tiền oan hoặc bỏ lỡ hạn hủy miễn phí, mất niềm tin.
   - Xử lý: **grounding** — AI chỉ kết luận từ chính sách thật được truyền vào; **dẫn nguồn**; ca không chắc → **chuyển người**, không tự từ chối.

2. **Báo trạng thái sai ("đã hoàn tiền" khi chưa duyệt).**
   - Hậu quả: khách hiểu nhầm đã xong, khiếu nại tăng.
   - Xử lý: hệ thống **chỉ báo "đã gửi/đang chờ duyệt"**; chỉ chuyển "đã duyệt" sau khi support/đơn vị lưu trú thực sự duyệt.

3. **Mã đặt phòng sai / câu hỏi ngoài phạm vi.**
   - Hậu quả: nếu đoán bừa → xử lý nhầm; nếu trả lời linh tinh → lệch vai trò.
   - Xử lý: mã sai → trạng thái **không tìm thấy → chuyển hỗ trợ**; câu ngoài phạm vi → AI **từ chối lịch sự, giữ đúng vai** trợ lý hủy/hoàn (qua system prompt).

## 7. Kế hoạch kiểm thử & bằng chứng demo

Hai đầu vào chuẩn bị sẵn để demo:

- **Đầu vào thuận:** `TRV12345` + "đổi lịch" → đủ điều kiện hủy **miễn phí** → xác nhận → tự duyệt.
- **Đầu vào khó / gây nhiễu:**
  - `TRV67890` (non-refundable) → **chuyển đơn vị lưu trú** xét (≤2 ngày), không tự quyết.
  - `TRV00000` (mã sai) → **không tìm thấy**, không từ chối oan.
  - "visa bị từ chối" (lý do ngoài danh sách) → **xét diện bất khả kháng → chuyển người** kèm ngữ cảnh.

Bằng chứng giữ lại: ảnh chụp màn hình các luồng, nhật ký lời gọi tool của agent (search → evaluate → create/decide), bộ test case ở trên, và các con số chính sách đối chiếu `codebase/docs/refund-policy.md`. Đánh đổi đã cân nhắc: dùng **JSON store + backend nhỏ** thay vì DB lớn để kịp demo end-to-end; auto chỉ giới hạn ca miễn phí để giảm rủi ro.

## 8. Phân công

> ⚠️ **CẦN ĐIỀN mã học viên + họ tên đầy đủ** cho từng thành viên trước khi nộp.

| Thành viên | Mã HV | Phụ trách |
|-----------|-------|-----------|
| Hưng | _[điền]_ | Research / evidence · kịch bản demo |
| Việt Anh | _[điền]_ | SPEC · chính sách (grounding) |
| Toàn | _[điền]_ | Prototype web · backend / store |
| Lân | _[điền]_ | Phần AI (agent + tools) · test failure path |

Mỗi thành viên cần ≥ 1 commit thực chất và tự giải thích được phần của mình khi demo.
