# Day06 — 4Tuner · AI hỗ trợ Hủy đặt phòng & Hoàn tiền (Traveloka)

**Track:** Travel & Hospitality · **App soi:** Traveloka

Trợ lý AI giúp khách **hủy / đổi / hoàn tiền** đặt phòng khách sạn một cách **minh bạch và có lối thoát** —
cải thiện đúng chỗ Traveloka đang làm chưa tốt (chatbot chạy vòng quanh, hoàn tiền mờ ám, ép chọn lý do sai).

AI **tra chính sách thật** theo mã đặt phòng + lý do → trả "thẻ quyết định" (đủ điều kiện · phí · thời gian hoàn) →
**conditional automation** theo 4 nhánh: **HAPPY · CÓ PHÍ · CHUYỂN NGƯỜI · HỎI LẠI**, con người giữ quyền duyệt cuối.

## Thành viên

> ⚠️ **CẦN ĐIỀN mã học viên + họ tên đầy đủ** trước khi nộp.

| Thành viên | Mã HV | Vai trò |
|-----------|-------|---------|
| Hưng | _[điền]_ | Research / evidence · demo |
| Việt Anh | _[điền]_ | SPEC · grounding chính sách |
| Toàn | _[điền]_ | Prototype web · backend |
| Lân | _[điền]_ | AI agent + tools · test |

## Cấu trúc repo

```
├── README.md        ← file này (thành viên + mô tả sản phẩm)
├── spec/
│   ├── spec.md          ← SPEC sản phẩm (8 mục)
│   └── demo-slides.pdf   ← slide thuyết trình
└── codebase/        ← toàn bộ code prototype (xem codebase/README.md để chạy)
```

## Chạy nhanh

```bash
cd codebase/server
pip install -r requirements.txt
cp .env.example .env        # điền CUSTOM_BASE_URL / CUSTOM_API_KEY / CUSTOM_MODEL
uvicorn api:app --reload --port 8000
```

Mở **http://localhost:8000/** (khách hàng, có chatbot AI 💬) · **/admin.html** (support).
Chi tiết kiến trúc, công cụ/API, demo: xem [`codebase/README.md`](codebase/README.md). SPEC: [`spec/spec.md`](spec/spec.md).
