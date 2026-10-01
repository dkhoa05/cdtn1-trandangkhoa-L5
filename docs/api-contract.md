# Hợp đồng API — Luồng L5: Kho linh kiện thay thế

## A1. Danh sách endpoint

| Phương thức | Đường dẫn | Mục đích | User Story |
|---|---|---|---|
| GET | `/api/parts?center_id={id}&q={keyword}` | Tra cứu / tìm kiếm linh kiện theo tên hoặc mã, kèm tồn kho hiện tại | US1 |
| POST | `/api/tickets/{ticket_id}/parts` | Xuất linh kiện cho một phiếu bảo hành | US2, US3 |
| POST | `/api/parts/{part_id}/stock-in` | Ghi nhận nhập kho linh kiện | US5 |
| GET | `/api/parts/low-stock?center_id={id}` | Danh sách linh kiện đang dưới ngưỡng cảnh báo | US6 |
| GET | `/api/parts/{part_id}/transactions?center_id={id}` | Lịch sử chi tiết từng giao dịch nhập–xuất của một linh kiện | US7 |
| GET | `/api/parts/{part_id}/transactions/summary?center_id={id}&from={date}&to={date}` | Tổng hợp số lượng nhập/xuất của linh kiện trong khoảng thời gian | US8 |

## A2. Quy ước chung

- Định dạng trao đổi: JSON, mã hoá UTF-8. Header bắt buộc: `Content-Type: application/json`.
- Tên trường dùng `snake_case`, khớp đúng tên cột trong ERD.
- Thời gian dùng chuẩn ISO 8601 kèm múi giờ, ví dụ `2026-10-01T09:30:00+07:00`.
- Số lượng linh kiện: số nguyên dương.
- Phân trang: tham số `page` (bắt đầu từ 1) và `size` (mặc định 20, tối đa 100). Response kèm `total`.
- Mọi lỗi trả về cùng cấu trúc: `{ "error": { "code": "...", "message": "...", "fields": {...} } }`.

## A3. Chi tiết endpoint — POST /api/tickets/{ticket_id}/parts

Xuất linh kiện cho phiếu bảo hành · US2, US3 · liên quan UC2, QT-09

**REQUEST BODY**
```json
{
  "part_id": 45,
  "quantity": 2
}
```

**RESPONSE 201 Created**
```json
{
  "transaction_id": 9981,
  "ticket_id": 231,
  "part_id": 45,
  "quantity": 2,
  "remaining_stock": 3,
  "low_stock_alert": false,
  "created_at": "2026-10-01T09:30:00+07:00"
}
```

**RESPONSE 400 Bad Request** — dữ liệu không hợp lệ
```json
{
  "error": {
    "code": "VALIDATION_FAILED",
    "message": "Du lieu khong hop le",
    "fields": { "quantity": "Phai la so nguyen duong" }
  }
}
```

**RESPONSE 404 Not Found** — `ticket_id` hoặc `part_id` không tồn tại
**RESPONSE 409 Conflict** — số lượng xuất vượt quá tồn kho hiện tại (QT-09)
**RESPONSE 422 Unprocessable** — phiếu không ở trạng thái "Đang xử lý"

### Bảng validation

| Trường | Bắt buộc | Kiểu / ràng buộc | Thông báo lỗi khi vi phạm |
|---|---|---|---|
| part_id | Có | Số nguyên dương, phải tồn tại trong `part_stock` của trung tâm chứa phiếu | Không tìm thấy linh kiện tại trung tâm này |
| quantity | Có | Số nguyên dương, ≤ tồn kho hiện tại của linh kiện (QT-09) | Số lượng xuất vượt quá tồn kho |

## A4. Chi tiết endpoint — GET /api/parts

Tra cứu / tìm kiếm linh kiện · US1 · liên quan UC1

**RESPONSE 200 OK**
```json
{
  "data": [
    {
      "part_id": 45,
      "part_code": "MH-IP13-001",
      "part_name": "Man hinh iPhone 13",
      "quantity": 5,
      "min_threshold": 3
    }
  ],
  "page": 1,
  "size": 20,
  "total": 1
}
```

**RESPONSE 403 Forbidden** — `center_id` trong query không khớp trung tâm của người dùng đăng nhập (QT-14)

## A5. Chi tiết endpoint — POST /api/parts/{part_id}/stock-in

Nhập kho linh kiện · US5 · liên quan UC3

**REQUEST BODY**
```json
{
  "center_id": 2,
  "quantity": 10
}
```

**RESPONSE 201 Created**
```json
{
  "transaction_id": 9982,
  "part_id": 45,
  "center_id": 2,
  "quantity": 10,
  "new_stock": 13,
  "created_at": "2026-10-01T09:45:00+07:00"
}
```

### Bảng validation

| Trường | Bắt buộc | Kiểu / ràng buộc | Thông báo lỗi khi vi phạm |
|---|---|---|---|
| center_id | Có | Số nguyên dương, phải tồn tại | Trung tâm không hợp lệ |
| quantity | Có | Số nguyên dương | Số lượng nhập phải lớn hơn 0 |

## A6. Chi tiết endpoint — GET /api/parts/{part_id}/transactions/summary

Tổng hợp nhập–xuất theo khoảng thời gian · US8 · liên quan UC5 (mở rộng)

**RESPONSE 200 OK**
```json
{
  "part_id": 45,
  "center_id": 2,
  "from": "2026-09-01",
  "to": "2026-09-30",
  "total_in": 15,
  "total_out": 8,
  "net_change": 7
}
```

**RESPONSE 403 Forbidden** — `center_id` không khớp trung tâm của người dùng đăng nhập (QT-14)

### Bảng validation

| Trường | Bắt buộc | Kiểu / ràng buộc | Thông báo lỗi khi vi phạm |
|---|---|---|---|
| from, to | Có | Ngày hợp lệ (ISO 8601), `from` ≤ `to` | Khoảng thời gian không hợp lệ |

## Tự kiểm hợp đồng API trước khi nộp BT1

- [x] Mỗi endpoint nối được về ít nhất một User Story trong bảng truy vết.
- [x] Endpoint MUST (xuất linh kiện) có đủ 1 response thành công + nhiều response lỗi.
- [x] Mọi trường trong request body tồn tại trong mô hình dữ liệu (ERD — làm ở buổi 5).
- [x] Quy tắc QT-09, QT-14 đã xuất hiện trong bảng validation / mã lỗi.
