# Thiết kế luồng L5: Kho linh kiện thay thế

## 3. Thiết kế kiến trúc

Sơ đồ nằm ở docs/architecture.drawio. Tôi chia hệ thống thành 4 lớp, lớp trên gọi lớp dưới, lớp dưới không gọi ngược lên.

| Lớp | Thành phần | Làm gì | Trao đổi với lớp dưới bằng |
|---|---|---|---|
| 1. Trình bày | Flask routes + templates (M1, M2, M3) | Nhận form, kiểm tra trường rỗng, đổi lỗi nghiệp vụ thành mã HTTP | HTTP + JSON theo api-contract.md |
| 2. Nghiệp vụ | StockService, IssueService, ReceiptService | Chứa các quy tắc QT-09, QT-13, QT-14 và kiểm tra ngưỡng sau khi xuất (UC6, UC7) | Gọi hàm của Repository |
| 3. Truy cập dữ liệu | PartRepository, StockRepository, TransactionRepository, TicketRepository, UserRepository | Chỉ đọc/ghi dữ liệu, không chứa quy tắc | SQL |
| 4. Lưu trữ | PostgreSQL (db/schema.sql) | Giữ ràng buộc ở mức CSDL: khóa ngoại, NOT NULL, CHECK | Không có |

Những phần không làm (WON'T): dự báo nhu cầu linh kiện, tự đặt hàng với nhà cung cấp, gửi SMS/email cảnh báo, quản lý giá nhập theo thời gian.

### 3.2. Ba câu lập luận lựa chọn kiến trúc

1. Vì NFR1 yêu cầu phản hồi dưới 1 giây với ≤200 linh kiện/trung tâm, tôi chọn truy vấn trực tiếp qua khóa chính (center_id, part_id) trên database thay vì quét toàn bảng, đánh đổi là tốn thêm bộ nhớ để duy trì index phức hợp.

2. Vì NFR2 yêu cầu trừ tồn và ghi log cùng thành công hoặc không cái nào, tôi chọn mở transaction kèm khóa dòng (row-level lock) ở lớp Service thay vì xử lý rời rạc, đánh đổi là giảm tốc độ xử lý đồng thời vì giao dịch sau phải chờ giao dịch trước.

3. Vì NFR3 yêu cầu thao tác khác trung tâm thì trả về 403, tôi chọn truyền thêm tham số `center_id` vào mỗi hàm để kiểm tra quyền tại Backend Service thay vì chỉ ẩn nút trên UI, đánh đổi là mã nguồn cồng kềnh hơn do các hàm phải gánh thêm tham số và logic đối chiếu.

## 4. Mô hình dữ liệu (Track SE)

ERD vẽ ở docs/erd.drawio theo ký pháp chân chim, câu lệnh tạo bảng để ở db/schema.sql (PostgreSQL).

| Bảng | Phục vụ yêu cầu | Lấy dữ liệu mẫu từ |
|---|---|---|
| service_center | QT-14, NFR3 (giới hạn theo trung tâm) | service_centers.csv (6 dòng) |
| part | FR1 | parts.csv (180 dòng) |
| part_stock | FR1, FR3, FR4, FR6 | part_stock.csv (717 dòng) |
| part_transaction | FR2, FR5, FR7, FR8 | part_transactions.csv (4.954 dòng) |
| ticket | FR2 (phiếu phải đang xử lý), bảng tham chiếu từ luồng L2 | tickets_history.csv |
| app_user | NFR3, biết ai thực hiện giao dịch | tạo từ technicians.csv |

Có 6 bảng, 7 khóa ngoại, không bảng nào đứng riêng lẻ. Khóa chính dùng số tự tăng, còn mã nghiệp vụ như part_code, center_code, ticket_code thì chỉ đặt UNIQUE.

| Index | Dùng cho |
|---|---|
| PK part_stock(center_id, part_id) | NFR1, tra cứu tồn kho theo trung tâm |
| idx_txn_part_time(center_id, part_id, created_at) | FR7, FR8, xem lịch sử và cộng tổng theo thời gian |
| idx_txn_ticket(ticket_id) | AC2.2, xem linh kiện đã dùng cho một phiếu |

Một số điểm tôi cân nhắc khi thiết kế dữ liệu:
- Không làm bảng cảnh báo riêng. Cảnh báo dưới ngưỡng (FR4, FR6) tính luôn từ quantity < min_threshold, vì lưu thêm một chỗ thì dễ bị lệch với số tồn thật.
- Bảng part_transaction chỉ thêm dòng mới (QT-13). Nếu ghi sai thì thêm một giao dịch bù, không sửa hay xóa dòng cũ.
- part_stock có CHECK (quantity >= 0) để chặn thêm một lớp ở CSDL cho QT-09, ngoài phần kiểm tra ở lớp nghiệp vụ.
- Ràng buộc chk_ticket_by_type: giao dịch XUAT phải có ticket_id, còn NHAP thì để trống.

## 5. Wireframe 3 màn hình

Wireframe vẽ ở docs/wireframe.drawio, ảnh xuất ra là docs/wireframe.png.

### M1: Tồn kho linh kiện (UC1, UC4)

| Trường trên màn hình | Cột ERD | Nguồn |
|---|---|---|
| Trung tâm | service_center.center_name | QT-14 |
| Ô tìm theo mã / tên linh kiện | part.part_code, part.part_name | FR1, US1 |
| Tồn | part_stock.quantity | FR1 |
| Ngưỡng | part_stock.min_threshold | FR6, US6 |
| Ô lọc "dưới ngưỡng cảnh báo" | tính từ quantity < min_threshold | FR6 |
| Thông báo "Không tìm thấy linh kiện" | không lưu | AC1.2 |

### M2: Xuất linh kiện cho phiếu bảo hành (UC2)

| Trường trên màn hình | Cột ERD | Nguồn |
|---|---|---|
| Phiếu bảo hành, trạng thái | ticket.ticket_code, ticket.status | FR2 |
| Chọn linh kiện, xem tồn hiện tại | part_stock (center_id, part_id), quantity | FR2 |
| Số lượng | part_transaction.quantity | FR2, FR3 |
| Lỗi "vượt quá tồn kho" | không lưu | UC2 luồng 4a, QT-09 |
| Cảnh báo "dưới ngưỡng cảnh báo" | tính, không lưu | UC2 luồng 7a, UC7 |
| Nút "Xác nhận xuất" | thêm dòng part_transaction (XUAT) và cập nhật part_stock | US2 |
| Bảng "Linh kiện đã dùng cho phiếu" | part_transaction lọc theo ticket_id | AC2.2 |

### M3: Nhập kho và lịch sử nhập–xuất (UC3, UC5)

| Trường trên màn hình | Cột ERD | Nguồn |
|---|---|---|
| Linh kiện, số lượng nhập | part_transaction.part_id, quantity | FR5, US5 |
| Lỗi "Số lượng nhập phải lớn hơn 0" | CHECK quantity > 0 | FR5 |
| Thời điểm, loại, số lượng, phiếu | part_transaction.created_at, txn_type, quantity, ticket_id | FR7, US7 |
| Người thực hiện | app_user.full_name (qua created_by) | FR7 |
| Tổng nhập / tổng xuất | SUM(quantity) theo txn_type | FR8, US8 |
