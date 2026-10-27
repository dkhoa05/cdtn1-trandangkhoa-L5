# Hợp đồng API luồng L5: Kho linh kiện thay thế

## A1. Danh sách endpoint

| Phương thức | Đường dẫn | Mục đích | User Story |
|---|---|---|---|
| GET | `/api/parts?center_id={id}&q={keyword}` | Tra cứu / tìm kiếm linh kiện theo tên hoặc mã, kèm tồn kho hiện tại | US1 |
| POST | `/api/tickets/{ticket_id}/parts` | Xuất linh kiện cho một phiếu bảo hành | US2, US3 |
| POST | `/api/parts/{part_id}/stock-in` | Ghi nhận nhập kho linh kiện | US5 |
| GET | `/api/parts/low-stock?center_id={id}` | Danh sách linh kiện đang dưới ngưỡng cảnh báo | US6 |
| GET | `/api/parts/{part_id}/transactions?center_id={id}` | Lịch sử chi tiết từng giao dịch nhập–xuất của một linh kiện | US7 |
| GET | `/api/parts/{part_id}/transactions/summary?center_id={id}&from={date}&to={date}` | Tổng nhập, tổng xuất của linh kiện trong khoảng thời gian | US7 |

Bổ sung ở buổi 10 (xem TD-08): `POST /api/auth/login` (body `{"user_id": 2}`, trả `{"token", "user"}`), `GET /api/tickets?status=DANG_XU_LY` (phiếu của trung tâm người dùng), `GET /api/tickets/{ticket_id}/parts` (linh kiện đã xuất cho phiếu, AC2.2). Mọi endpoint còn lại đòi header `Authorization: Bearer <token>`; thiếu hoặc sai token trả 401.

CRUD linh kiện và tồn kho (buổi 10, xem TD-12), chỉ vai trò quản lý trung tâm được ghi, kỹ thuật viên nhận 403:

| Phương thức | Đường dẫn | Mục đích | Mã lỗi chính |
|---|---|---|---|
| POST | `/api/parts` | Tạo linh kiện trong danh mục: `part_code`, `part_name`, `unit_price` | 400, 409 `PART_CODE_EXISTS` |
| GET | `/api/parts/{part_id}` | Đọc một linh kiện kèm tồn kho của trung tâm người dùng | 404 |
| PUT | `/api/parts/{part_id}` | Sửa `part_name`, `unit_price` (mã không đổi) | 400, 404 |
| DELETE | `/api/parts/{part_id}` | Ngừng sử dụng (xóa mềm, QT-13) | 409 `PART_HAS_STOCK` khi còn trung tâm giữ tồn |
| POST | `/api/stock` | Đưa linh kiện vào kho trung tâm với tồn 0: `part_id`, `min_threshold` | 404, 409 `STOCK_EXISTS` |
| PATCH | `/api/stock/{part_id}` | Đổi `min_threshold` | 400, 404 |
| DELETE | `/api/stock/{part_id}` | Gỡ khỏi kho trung tâm (xóa mềm) | 409 `STOCK_NOT_EMPTY` khi tồn lớn hơn 0 |

Bản ghi chạy thật các endpoint này nằm ở `docs/export/curl-crud-linh-kien.txt`.

### Truy vết từng endpoint về User Story

| Endpoint | User Story | Ghi chú |
|---|---|---|
| `GET /api/parts` | US1 | Tra cứu theo mã hoặc tên, giới hạn trong trung tâm của người dùng |
| `GET /api/parts/low-stock` | US6 | Danh sách dưới ngưỡng cảnh báo |
| `POST /api/tickets/{id}/parts` | US2, US3, US4 | Xuất kho; từ chối vượt tồn (QT-09); cờ `low_stock_alert` là cảnh báo của US4 |
| `GET /api/tickets`, `GET /api/tickets/{id}/parts` | US2 | Chọn phiếu đang xử lý và xem linh kiện đã dùng (AC2.2) |
| `POST /api/parts/{id}/stock-in` | US5 | Chỉ quản lý trung tâm |
| `GET /api/parts/{id}/transactions`, `.../summary` | US7 | Lịch sử và tổng hợp nhập xuất |
| `POST /api/auth/login` | không có User Story riêng | Hạ tầng cho QT-14 và NFR3, thêm ở TD-08 |
| `POST/GET/PUT/DELETE /api/parts`, `POST/PATCH/DELETE /api/stock` | không có User Story riêng | Thêm để đáp ứng yêu cầu hai thực thể CRUD của BT2 (TD-12); phục vụ US1 và US5 vì phải có linh kiện trong kho mới tra cứu và nhập được |

### Hợp đồng dữ liệu phía giao diện

Phản hồi được dựng bằng các hàm `to_*_view` trong `src/routes/views.py`; mỗi hàm ghi rõ hình dạng, ý nghĩa và hành vi khi dữ liệu thiếu. Hai điểm hay nhầm: `stock` trong `GET /api/parts/{id}` là `null` khi linh kiện chưa có trong kho trung tâm (khác với tồn bằng 0); `ticket_id` trong lịch sử là `null` với giao dịch nhập. Mọi phản hồi có header `X-Request-Id` để tra log; lỗi 5xx kèm `requestId` trong thân.

## A2. Quy ước chung

- Định dạng trao đổi: JSON, mã hoá UTF-8. Header bắt buộc: `Content-Type: application/json`.
- Tên trường dùng `snake_case`, khớp đúng tên cột trong ERD.
- Thời gian dùng chuẩn ISO 8601 kèm múi giờ, ví dụ `2026-10-01T09:30:00+07:00`.
- Số lượng linh kiện: số nguyên dương.
- Phân trang: tham số `page` (bắt đầu từ 1) và `size` (mặc định 20, tối đa 100). Response kèm `total`.
- Mọi lỗi trả về cùng cấu trúc: `{ "error": { "code": "...", "message": "...", "fields": {...} } }`.

## A3. POST /api/tickets/{ticket_id}/parts

Xuất linh kiện cho phiếu bảo hành (US2, US3, UC2, QT-09).

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

**RESPONSE 400 Bad Request**: dữ liệu không hợp lệ  
```json
{
  "error": {
    "code": "VALIDATION_FAILED",
    "message": "Du lieu khong hop le",
    "fields": { "quantity": "Phai la so nguyen duong" }
  }
}
```

**RESPONSE 404 Not Found**: `ticket_id` hoặc `part_id` không tồn tại  
**RESPONSE 409 Conflict**: số lượng xuất vượt quá tồn kho hiện tại (QT-09), mã lỗi `INSUFFICIENT_STOCK`  
**RESPONSE 422 Unprocessable**: phiếu không ở trạng thái "Đang xử lý"  

### Bảng validation

| Trường | Bắt buộc | Kiểu / ràng buộc | Thông báo lỗi khi vi phạm |
|---|---|---|---|
| part_id | Có | Số nguyên dương, phải tồn tại trong `part_stock` của trung tâm chứa phiếu | Không tìm thấy linh kiện tại trung tâm này |
| quantity | Có | Số nguyên dương, ≤ tồn kho hiện tại của linh kiện (QT-09) | Số lượng xuất vượt quá tồn kho |

## A4. GET /api/parts

Tra cứu / tìm kiếm linh kiện (US1, UC1).

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

**RESPONSE 403 Forbidden**: `center_id` trong query không khớp trung tâm của người dùng đăng nhập (QT-14)  

## A5. POST /api/parts/{part_id}/stock-in

Nhập kho linh kiện (US5, UC3).

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

## A6. GET /api/parts/{part_id}/transactions/summary

Tổng hợp nhập–xuất theo khoảng thời gian (US7, UC5).

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

**RESPONSE 403 Forbidden**: `center_id` không khớp trung tâm của người dùng đăng nhập (QT-14)  

### Bảng validation

| Trường | Bắt buộc | Kiểu / ràng buộc | Thông báo lỗi khi vi phạm |
|---|---|---|---|
| from, to | Có | Ngày hợp lệ (ISO 8601), `from` ≤ `to` | Khoảng thời gian không hợp lệ |

## Tự kiểm hợp đồng API trước khi nộp BT1

- [x] Mỗi endpoint nối được về ít nhất một User Story trong bảng truy vết.
- [x] Endpoint MUST (xuất linh kiện) có đủ 1 response thành công + nhiều response lỗi.
- [x] Mọi trường trong request body tồn tại trong mô hình dữ liệu (ERD).
- [x] Quy tắc QT-09, QT-14 đã xuất hiện trong bảng validation / mã lỗi.
