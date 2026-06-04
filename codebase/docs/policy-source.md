# Nguồn chính sách hoàn tiền Traveloka (grounding cho engine & RAG ở CP2)

> Bảng quy tắc cô đọng cho engine. **Bản policy đầy đủ (nguyên văn 3 trang): [`refund-policy.md`](./refund-policy.md).**
> Engine CP1 và prompt AI CP2 phải bám đúng các con số dưới đây — KHÔNG bịa.
> Nguồn: refund/hotel · traveloka-accommodation-cancellation-nonrefundable · traveloka-accommodation-refundable.

## Các con số/quy tắc bắt buộc đúng

| Mã quy tắc | Nội dung |
|---|---|
| `P-REFUNDABLE-ONLY` | Hoàn tiền chỉ áp dụng cho đặt phòng **có thể hoàn tiền**. |
| `P-PROCESS-5D` | Quy trình hoàn tiền **lên đến 5 ngày** sau khi yêu cầu được **phê duyệt**. |
| `P-BANK-90D` | Tiền hiển thị trong tài khoản có thể mất **tới 90 ngày** tùy chính sách ngân hàng. |
| `P-FEE-10` | Phí xử lý hoàn tiền **10%**, **tối thiểu 32.000đ, tối đa 470.000đ**; cộng phí chuyển khoản ngân hàng (nếu có) và phí hủy do khách sạn áp dụng. |
| `P-FEE-COMPOSITE` | Phí hủy/hoàn được liệt kê = chi phí khách sạn thu trực tiếp **+** phí xử lý của Traveloka. |
| `P-NO-PARTIAL` | **Không** chấp nhận hoàn tiền một phần — áp cho **toàn bộ thời gian lưu trú và tất cả phòng** trong một mã đặt phòng. |
| `P-NO-VOUCHER` | Khoản hoàn **không** gồm tiền từ mã giảm giá; mọi mã giảm giá đã áp dụng **không được hoàn**. |
| `P-ONCE` | Yêu cầu hoàn tiền chỉ gửi **một lần**, sau khi gửi **không thể hoàn tác/hủy**; giữ chỗ tự động bị hủy. |
| `P-NR-FORWARD` | Đặt phòng **không hoàn**: khách vẫn có thể **gửi yêu cầu**, Traveloka chuyển tới đơn vị lưu trú; **đơn vị lưu trú** (không phải Traveloka) quyết định chấp nhận/từ chối. |
| `P-NR-2D` | Quy trình phê duyệt của đơn vị lưu trú **tối đa 2 ngày**; quá 2 ngày không phản hồi → yêu cầu **tự động bị hủy**. |
| `P-NR-ONCE` | Với đặt phòng không hoàn: yêu cầu phê duyệt chỉ thực hiện **một lần**, sau đó không còn lựa chọn hủy hay đổi ngày. |
| `P-METHOD` | Hoàn về **đúng phương thức thanh toán** đã dùng (thẻ tín dụng → về hạn mức thẻ; Paylater → khấu trừ hóa đơn; Xu Traveloka còn hạn → về tài khoản). |
| `P-NAMED-ACCOUNT` | Chỉ hoàn vào tài khoản của **người liên hệ / người có tên trên đặt phòng**; nếu không, yêu cầu bị đình chỉ. |
| `P-DISCLAIM` | Traveloka **không chịu trách nhiệm** về thời gian xử lý/quyết định phê duyệt/số tiền hoàn từ đơn vị lưu trú. |

## Hệ quả thiết kế cho prototype

- "Thời gian hoàn" hiển thị: **tối đa 5 ngày sau khi được phê duyệt** (không phải con số tùy ý).
- Phí xử lý: tính 10% rồi **kẹp trong [32.000đ, 470.000đ]**.
- Non-refundable: **không** hiển thị "mất 100%/hoàn 0đ" như kết luận cuối. Đúng là: **gửi yêu cầu → chờ đơn vị lưu trú quyết (tối đa 2 ngày)** → đây là lý do route sang **chuyển người/đơn vị lưu trú**, không phải auto-từ-chối.
- Trước khi xác nhận phải cảnh báo: **không hoàn một phần**, **mã giảm giá không hoàn**, **gửi rồi không hoàn tác**.

## Lựa chọn thiết kế của nhóm (KHÔNG nằm trong policy — phải ghi rõ)

- Việc route "phí cao / non-refundable → chuyển người" là **quyết định Auto/Aug của nhóm** (conditional automation), không phải quy tắc Traveloka.
- Các booking mẫu (`TRV…`, tên khách sạn, giá, ngày) là **dữ liệu hư cấu để demo**, không phải dữ liệu thật của Traveloka.
