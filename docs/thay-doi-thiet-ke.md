# Nhật ký thay đổi thiết kế

Mọi sai lệch so với thiết kế Bài tập 1 được ghi lại ở đây. Mỗi thay đổi có mã TD-xx và bốn dòng: phản hồi hoặc lý do phát sinh, quyết định, lý do, ảnh hưởng.

## Sau phản hồi Bài tập 1 (buổi 8, ngày 15/10/2026)

### TD-01. Gộp US7 và US8 thành một User Story

- Phản hồi của GV: SRS có 8 User Story trong khi đề yêu cầu 5–7, gợi ý gộp US7 và US8 vì cùng phục vụ đối chiếu nhập–xuất.
- Quyết định: SỬA.
- Lý do: US7 (xem lịch sử từng giao dịch) và US8 (xem tổng nhập, tổng xuất) cùng một người dùng, cùng màn hình M3 và cùng mục đích đối chiếu khi tồn kho lệch, nên gộp lại không làm mất yêu cầu nào.
- Ảnh hưởng: srs.md còn 7 User Story, FR7 và FR8 gộp thành FR7, bảng truy vết bớt một dòng; api-contract.md endpoint /transactions/summary trỏ về US7; design.md, schema.sql, erd.drawio, wireframe.drawio đổi nhãn FR8/US8 thành FR7/US7.

### TD-02. Bổ sung ngưỡng đo được cho NFR2

- Phản hồi của GV: NFR2 chưa có con số đo được.
- Quyết định: SỬA.
- Lý do: ngưỡng cũ chỉ mô tả cách làm (ghi theo transaction) chứ không kiểm tra được. Ngưỡng mới "0 giao dịch để tồn kho lệch với log giao dịch trong 1.000 lần thử ngắt lỗi giữa chừng" có thể viết thành kiểm thử.
- Ảnh hưởng: srs.md mục 4; bộ kiểm thử BT2 và BT3 thêm kiểm thử ngắt lỗi giữa chừng và kiểm thử hai giao dịch xuất đồng thời.

### TD-03. Đưa DDL các bảng chính vào tài liệu thiết kế

- Phản hồi của GV: mục 4 chỉ dẫn tới db/schema.sql, chưa trích DDL vào bài.
- Quyết định: SỬA.
- Lý do: người đọc tài liệu cần thấy khóa chính, khóa ngoại và ràng buộc CHECK ngay trong bài mà không phải mở repo.
- Ảnh hưởng: design.md mục 4 có thêm DDL của part_stock, part_transaction và hai chỉ mục.

## Khi bắt đầu hiện thực Bài tập 2 (buổi 8, ngày 15/10/2026)

### TD-04. Hạ yêu cầu phiên bản Python và PostgreSQL

- Lý do phát sinh: README của BT1 ghi Python 3.11+ và PostgreSQL 16, máy dùng để làm bài có Python 3.10.11 và PostgreSQL 18.
- Quyết định: SỬA README thành Python 3.10+ và PostgreSQL 16+.
- Lý do: mã nguồn không dùng tính năng riêng của Python 3.11, và các câu lệnh SQL trong schema chạy giống nhau trên PostgreSQL 16 và 18.
- Ảnh hưởng: README.md mục 2.

### TD-05. Đổi tên thư mục mã nguồn theo quy ước của Bài tập 2

- Lý do phát sinh: README của BT1 dự kiến src/api, src/service, src/repository; đề BT2 quy định src/routes, src/services, src/repositories, src/validators cho track SE.
- Quyết định: SỬA theo quy ước của đề.
- Lý do: cùng bốn lớp như sơ đồ kiến trúc BT1, chỉ đổi tên để giảng viên kiểm ranh giới lớp đúng chỗ. Lớp kiểm tra định dạng dữ liệu vào được tách riêng ra src/validators thay vì nằm trong route.
- Ảnh hưởng: README.md mục 4; cấu trúc src/; sơ đồ kiến trúc thực tế của BT2.

### TD-06. Chuyển db/schema.sql thành migration chạy lại được

- Lý do phát sinh: đề BT2 yêu cầu thư mục migrations/ dựng được CSDL từ trạng thái trống và chạy lại lần hai không lỗi.
- Quyết định: SỬA, chuyển db/schema.sql thành migrations/001_init.sql và thêm IF NOT EXISTS cho mọi CREATE TABLE, CREATE INDEX. Nội dung bảng, khóa và ràng buộc giữ nguyên như BT1.
- Lý do: chạy migration lần hai trên CSDL đã có bảng sẽ báo lỗi "relation already exists" nếu không có IF NOT EXISTS.
- Ảnh hưởng: migrations/001_init.sql; đường dẫn trong design.md và ai-disclosure.md.

### TD-07. Dữ liệu mẫu cho app_user và ticket

- Lý do phát sinh: bộ dữ liệu case study không có bảng người dùng hệ thống và không có quản lý trung tâm; bảng phiếu bảo hành có 7.800 dòng, phần lớn đã đóng.
- Quyết định: kỹ thuật viên lấy từ technicians.csv (giữ nguyên mã), mỗi trung tâm thêm một tài khoản quản lý; bảng ticket chỉ nạp các phiếu đang xử lý và các phiếu có giao dịch xuất từ 01/07/2026; giao dịch kho chỉ nạp từ 01/07/2026.
- Lý do: đủ dữ liệu để ba màn hình có nội dung mà tệp seed vẫn nhỏ, đọc được.
- Ảnh hưởng: seeds/001_demo.sql, seeds/gen_seed.py.

## Khi hiện thực giao diện và tích hợp (buổi 10, ngày 22/10/2026)

### TD-08. Thêm đăng nhập và hai endpoint phục vụ giao diện

- Lý do phát sinh: API contract BT1 không có cách xác định người dùng, trong khi QT-14 và NFR3 cần biết trung tâm của người gọi; màn hình M2 cần chọn phiếu đang xử lý và xem linh kiện đã dùng (AC2.2) nhưng contract chưa có endpoint tương ứng.
- Quyết định: THÊM `POST /api/auth/login` (nhận `user_id`, trả token ký bằng SECRET_KEY, hạn 8 giờ), `GET /api/tickets?status=` và `GET /api/tickets/{id}/parts`. Mọi endpoint khác đòi header `Authorization: Bearer`.
- Lý do: tối thiểu để giao diện chạy được với dữ liệu thật mà không đổi mô hình dữ liệu.
- Ảnh hưởng: docs/api-contract.md. Hạn chế đã biết: bảng app_user chưa có mật khẩu nên đăng nhập chỉ bằng mã người dùng, chỉ phù hợp mức prototype. Hết hạn hoặc sai token trả 401, frontend xóa token và về trang đăng nhập.

### TD-09. Mã lỗi nghiệp vụ và nội dung thông báo

- Quyết định: dùng mã lỗi tiếng Anh (VALIDATION_FAILED, UNAUTHORIZED, FORBIDDEN, TICKET_NOT_FOUND, PART_NOT_FOUND, INSUFFICIENT_STOCK, TICKET_NOT_PROCESSING) và thông báo tiếng Việt có dấu, giữ cấu trúc `{"error": {"code", "message", "fields"}}` của contract. Ví dụ thông báo không dấu trong contract được hiểu là nội dung minh họa.
- Ảnh hưởng: src/routes/api.py (bảng HTTP_BY_CODE), docs/api-contract.md.

### TD-10. Phân quyền theo vai trò và frontend cùng origin

- Quyết định: nhập kho, xem lịch sử và tổng hợp nhập–xuất chỉ cho vai trò QUAN_LY_TT (đúng bảng vai trò mục 2 của SRS), kỹ thuật viên nhận 403. Flask phục vụ luôn thư mục `web/` nên frontend và API cùng origin, không cần cấu hình CORS.
- Lý do: một lệnh chạy được cả hệ thống, tránh lỗi CORS hay gặp ở buổi tích hợp.
- Ảnh hưởng: README mục 3, src/app.py.

### TD-11. Phần đã cắt ở Sprint 2

- Quyết định: CẮT biểu tượng, hiệu ứng và tối ưu hiệu năng giao diện; không làm trang quản lý người dùng. Danh sách chọn linh kiện ở M2 và M3 hiển thị tối đa 100 dòng, người dùng gõ để lọc thêm.
- Lý do: ưu tiên luồng chính end-to-end, ba trạng thái màn hình, unit test và README chạy được trên bản clone mới.
- Ảnh hưởng: không có yêu cầu MUST nào bị bỏ.

### TD-12. Thêm CRUD linh kiện và tồn kho, xóa mềm

- Lý do phát sinh: đề BT2 và checklist buổi 8 yêu cầu ít nhất hai thực thể có đủ tạo, đọc, sửa, xóa; thiết kế BT1 chỉ có nhập, xuất và tra cứu.
- Quyết định: THÊM CRUD cho `part` và `part_stock` qua migration 002 (cột `is_active` ở hai bảng). "Xóa" là xóa mềm theo QT-13; giao dịch cũ vẫn tham chiếu được. Hai quy tắc nghiệp vụ mới: không ngừng linh kiện khi còn trung tâm giữ tồn (`PART_HAS_STOCK`), không gỡ khỏi kho khi tồn lớn hơn 0 (`STOCK_NOT_EMPTY`). Thêm vào kho luôn bắt đầu từ tồn 0, số lượng chỉ đổi qua giao dịch nhập, xuất để tồn kho khớp log (NFR2).
- Lý do: giữ nguyên bất biến "tồn kho bằng tổng giao dịch" và không mất dấu hàng thật khi xóa.
- Ảnh hưởng: migrations/002_soft_delete.sql, các truy vấn đọc và khóa dòng lọc `is_active`, màn hình M4 "Danh mục" (web/src/pages/CatalogPage.js), docs/api-contract.md. Danh mục `part` dùng chung toàn hệ thống nên quản lý trung tâm nào cũng sửa được tên và đơn giá; chưa có vai trò quản trị hệ thống.
- Hạn chế đã biết: giao diện chỉ tạo linh kiện mới kèm tồn kho; đưa một linh kiện có sẵn trong danh mục vào kho trung tâm khác mới dùng được qua API (`POST /api/stock`), chưa có màn hình.

### TD-13. Xử lý lỗi hạ tầng và logging theo Buổi 11

- Lý do phát sinh: buổi 11 yêu cầu phân biệt lỗi nghiệp vụ với lỗi hạ tầng, ghi log một lần ở một chỗ và tuyệt đối không ghi dữ liệu nhạy cảm; kiểm thử hồi quy cho thấy mất kết nối CSDL đang trả 500 chung chung (BUG-001).
- Quyết định: THÊM một trình xử lý ở `create_app`: mất kết nối CSDL trả 503 `DB_UNAVAILABLE` kèm `requestId`, lỗi nghiệp vụ ghi INFO, lỗi lạ ghi ERROR kèm ngăn xếp và trả 500. Mức log lấy từ biến môi trường `LOG_LEVEL`.
- Lý do: người dùng thấy mã tra cứu thay vì chi tiết kỹ thuật, người vận hành tra log bằng `requestId`, log chỉ ghi mã lỗi và định danh chứ không ghi tên hay số điện thoại.
- Ảnh hưởng: src/app.py, .env.example, tests/test_api.py, docs/bug-log.md.

