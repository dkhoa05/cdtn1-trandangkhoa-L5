# Nhật ký thay đổi thiết kế

Mọi sai lệch so với thiết kế Bài tập 1 được ghi lại ở đây. Mỗi thay đổi có mã TD-xx và bốn dòng: phản hồi hoặc lý do phát sinh, quyết định, lý do, ảnh hưởng.

Chỉ những chỗ Bài tập 1 đã viết một điều và Bài tập 2 làm khác đi mới là sai lệch. Những phần bổ sung mà Bài tập 1 chưa nhắc tới (mã lỗi nghiệp vụ, xử lý lỗi hạ tầng, log JSON có requestId, hàm chuyển đổi ở ranh giới, chú thích trong mã) không phải sai lệch nên không đánh mã TD; chúng được mô tả ở docs/api-contract.md, docs/bug-log.md và README.md.

## Sau phản hồi Bài tập 1 (buổi 8, ngày 15/10/2026)

### TD-01. Gộp US7 và US8 thành một User Story

- Phản hồi của GV: SRS có 8 User Story trong khi đề yêu cầu 5–7, gợi ý gộp US7 và US8 vì cùng phục vụ đối chiếu nhập–xuất.
- Quyết định: SỬA.
- Lý do: US7 (xem lịch sử từng giao dịch) và US8 (xem tổng nhập, tổng xuất) cùng một người dùng, cùng màn hình M3 và cùng mục đích đối chiếu khi tồn kho lệch, nên gộp lại không làm mất yêu cầu nào.
- Ảnh hưởng: srs.md còn 7 User Story, FR7 và FR8 gộp thành FR7, bảng truy vết bớt một dòng; api-contract.md endpoint /transactions/summary trỏ về US7; design.md, schema.sql, erd.drawio, wireframe.drawio đổi nhãn FR8/US8 thành FR7/US7.

### TD-02. Bổ sung ngưỡng đo được cho NFR2 và kiểm thử đi kèm

- Phản hồi của GV: NFR2 chưa có con số đo được; gợi ý viết kiểm thử hai giao dịch xuất đồng thời để kiểm chứng khóa dòng và kiểm thử cho AC3.1, AC3.2.
- Quyết định: SỬA ngưỡng thành "0 giao dịch để tồn kho lệch với log giao dịch trong 1.000 lần thử ngắt lỗi giữa chừng", rồi thực hiện bằng `tests/test_tich_hop_pg.py` gồm hai kiểm thử trên PostgreSQL thật: 1.000 lần ngắt lỗi sau khi trừ tồn (tồn và log không lệch) và tám luồng cùng xuất khi chỉ còn 1 (đúng một luồng thành công). Hai kiểm thử biên AC3.2 (xuất đúng bằng tồn, vượt tồn 1 đơn vị) nằm ở `tests/test_xuat_kho.py`.
- Lý do: ngưỡng cũ chỉ mô tả cách làm (ghi theo transaction) chứ không kiểm tra được; ngưỡng mới viết được thành kiểm thử. Kiểm thử tích hợp mặc định bị bỏ qua để bộ kiểm thử chính không phụ thuộc CSDL có sẵn; bật bằng `RUN_PG_TESTS=1`, và mỗi kiểm thử tự xóa hẳn dữ liệu nó tạo nên không để lại dòng thừa trong CSDL.
- Kiểm tra độ nhạy: bỏ `FOR UPDATE` khỏi truy vấn khóa dòng thì kiểm thử đồng thời FAIL 4 trong 5 lần chạy (lỗi tranh chấp không xảy ra mọi lần); giữ nguyên mã thì PASS cả 3 lần.
- Ảnh hưởng: srs.md mục 4; tests/test_tich_hop_pg.py, tests/test_xuat_kho.py; README mục 5.

### TD-03. Đưa DDL các bảng chính vào tài liệu thiết kế

- Phản hồi của GV: mục 4 chỉ dẫn tới db/schema.sql, chưa trích DDL vào bài.
- Quyết định: SỬA.
- Lý do: người đọc tài liệu cần thấy khóa chính, khóa ngoại và ràng buộc CHECK ngay trong bài mà không phải mở repo.
- Ảnh hưởng: design.md mục 4 có thêm DDL của part_stock, part_transaction và hai chỉ mục.

## Khi hiện thực Bài tập 2 (buổi 8 đến buổi 10, tháng 10/2026)

### TD-04. Cấu trúc repo, phiên bản và dữ liệu mẫu khác với README Bài tập 1

- Lý do phát sinh: README của BT1 ghi Python 3.11+, thư mục src/api, src/service, src/repository và db/schema.sql; đề BT2 quy định src/routes, src/services, src/repositories, src/validators và thư mục migrations/ dựng được CSDL từ trạng thái trống, chạy lại lần hai không lỗi; máy làm bài có Python 3.10.11 và PostgreSQL 18; bộ dữ liệu case study không có bảng người dùng hệ thống và bảng phiếu bảo hành có 7.800 dòng, phần lớn đã đóng.
- Quyết định: SỬA bốn điểm. (1) README ghi Python 3.10+ và PostgreSQL 16+. (2) Đổi tên thư mục theo đề và tách lớp kiểm tra định dạng dữ liệu vào ra src/validators thay vì để trong route. (3) Chuyển db/schema.sql thành migrations/001_init.sql, thêm IF NOT EXISTS cho mọi CREATE TABLE và CREATE INDEX, nội dung bảng, khóa và ràng buộc giữ nguyên như BT1. (4) Dữ liệu mẫu: kỹ thuật viên lấy từ technicians.csv (giữ nguyên mã), mỗi trung tâm thêm một tài khoản quản lý; bảng ticket chỉ nạp các phiếu đang xử lý và các phiếu có giao dịch xuất từ 01/07/2026; giao dịch kho chỉ nạp từ 01/07/2026.
- Lý do: mã nguồn không dùng tính năng riêng của Python 3.11 và các câu lệnh SQL chạy giống nhau trên PostgreSQL 16 và 18; vẫn là bốn lớp như sơ đồ kiến trúc BT1, chỉ đổi tên để giảng viên kiểm ranh giới lớp đúng chỗ; chạy migration lần hai sẽ báo "relation already exists" nếu thiếu IF NOT EXISTS; dữ liệu mẫu đủ để ba màn hình có nội dung mà tệp seed vẫn nhỏ, đọc được.
- Ảnh hưởng: README.md mục 2 và 4; cấu trúc src/; migrations/001_init.sql; seeds/001_demo.sql và seeds/gen_seed.py; đường dẫn trong design.md và ai-disclosure.md. Số dòng dữ liệu mẫu ít hơn bảng ở mục 4 của design.md (ví dụ giao dịch kho chỉ nạp từ 01/07/2026).

### TD-05. Thêm đăng nhập và hai endpoint phục vụ giao diện

- Lý do phát sinh: API contract BT1 không có cách xác định người dùng, trong khi QT-14 và NFR3 cần biết trung tâm của người gọi; màn hình M2 cần chọn phiếu đang xử lý và xem linh kiện đã dùng (AC2.2) nhưng contract chưa có endpoint tương ứng.
- Quyết định: THÊM `POST /api/auth/login` (nhận `user_id`, trả token ký bằng SECRET_KEY, hạn 8 giờ), `GET /api/tickets?status=` và `GET /api/tickets/{id}/parts`. Mọi endpoint khác đòi header `Authorization: Bearer`.
- Lý do: tối thiểu để giao diện chạy được với dữ liệu thật mà không đổi mô hình dữ liệu.
- Ảnh hưởng: docs/api-contract.md. Hạn chế đã biết: bảng app_user chưa có mật khẩu nên đăng nhập chỉ bằng mã người dùng, chỉ phù hợp mức prototype. Hết hạn hoặc sai token trả 401, frontend xóa token và về trang đăng nhập. Cách lưu token: `sessionStorage` của trình duyệt (mất khi đóng tab, không ghi trong mã nguồn). Hạn chế: mã JavaScript trên cùng trang đọc được token nếu trang có lỗ hổng chèn mã (XSS); giao diện giảm rủi ro này bằng cách chỉ dựng DOM bằng textContent, không dùng innerHTML. Hướng nâng cấp: cookie HttpOnly do máy chủ đặt.

### TD-06. Thêm CRUD linh kiện và tồn kho, xóa mềm

- Lý do phát sinh: đề BT2 và checklist buổi 8 yêu cầu ít nhất hai thực thể có đủ tạo, đọc, sửa, xóa; thiết kế BT1 chỉ có nhập, xuất và tra cứu.
- Quyết định: THÊM CRUD cho `part` và `part_stock` qua migration 002 (cột `is_active` ở hai bảng). "Xóa" là xóa mềm theo QT-13; giao dịch cũ vẫn tham chiếu được. Hai quy tắc nghiệp vụ mới: không ngừng linh kiện khi còn trung tâm giữ tồn (`PART_HAS_STOCK`), không gỡ khỏi kho khi tồn lớn hơn 0 (`STOCK_NOT_EMPTY`). Thêm vào kho luôn bắt đầu từ tồn 0, số lượng chỉ đổi qua giao dịch nhập, xuất để tồn kho khớp log (NFR2).
- Lý do: giữ nguyên bất biến "tồn kho bằng tổng giao dịch" và không mất dấu hàng thật khi xóa.
- Ảnh hưởng: migrations/002_soft_delete.sql, các truy vấn đọc và khóa dòng lọc `is_active`, màn hình M4 "Danh mục" (web/src/pages/CatalogPage.js), docs/api-contract.md. Danh mục `part` dùng chung toàn hệ thống nên quản lý trung tâm nào cũng sửa được tên và đơn giá; chưa có vai trò quản trị hệ thống.
- Hạn chế đã biết: giao diện chỉ tạo linh kiện mới kèm tồn kho; đưa một linh kiện có sẵn trong danh mục vào kho trung tâm khác mới dùng được qua API (`POST /api/stock`), chưa có màn hình.

### TD-07. Cảnh báo dưới ngưỡng chỉ hiển thị, không gửi đi

- Lý do phát sinh: đặc tả UC2 bước 7a trong BT1 viết hệ thống "tạo cảnh báo gửi tới quản lý trung tâm"; BT1 đồng thời loại trừ SMS và email khỏi phạm vi (mục WON'T), nên chưa có kênh gửi.
- Quyết định: SỬA cách hiện thực. Phản hồi xuất kho trả cờ `low_stock_alert` để màn hình M2 hiện cảnh báo ngay cho người xuất; quản lý thấy danh sách dưới ngưỡng ở màn hình M1 (bộ lọc "dưới ngưỡng") và endpoint `GET /api/parts/low-stock`.
- Lý do: cảnh báo tính từ `quantity < min_threshold` nên luôn đúng với tồn thật, không cần lưu bảng cảnh báo hay hạ tầng gửi tin.
- Ảnh hưởng: UC7 trong docs/srs.md được hiểu là "hiển thị cảnh báo", không phải "gửi thông báo".

### TD-08. Một StockService thay cho IssueService và ReceiptService

- Lý do phát sinh: thiết kế BT1 (docs/design.md mục 3) chia lớp nghiệp vụ thành StockService, IssueService, ReceiptService.
- Quyết định: SỬA, gộp thành một lớp `StockService` trong `src/services/stock_service.py`.
- Lý do: xuất kho, nhập kho và tra cứu cùng dùng chung quy tắc QT-14 và cùng khóa dòng tồn kho trong một transaction; tách ba lớp chỉ làm lặp phần kiểm tra trung tâm mà không thêm ranh giới nào.
- Ảnh hưởng: không đổi API hay hợp đồng; các repository đúng như sơ đồ BT1 (Part, Stock, Transaction, Ticket, User).

### TD-09. Giao diện JavaScript thuần thay cho Flask templates

- Lý do phát sinh: BT1 ghi lớp trình bày là "Flask routes + templates"; buổi 9 yêu cầu giao diện gọi API qua lớp client riêng.
- Quyết định: SỬA, giao diện nằm ở `web/` (JavaScript thuần, không cần bước build) gọi API qua `web/src/api/client.js`; Flask chỉ phục vụ tệp tĩnh và API, nên giao diện và API cùng origin và không cần cấu hình CORS.
- Lý do: tách hẳn lớp trình bày khỏi lớp nghiệp vụ, đúng yêu cầu "mọi lệnh gọi mạng đi qua một lớp client" và kiểm bằng `grep "fetch(" web/src/pages` cho kết quả rỗng; một lệnh chạy được cả hệ thống, tránh lỗi CORS hay gặp ở buổi tích hợp.
- Ảnh hưởng: wireframe M1, M2, M3 giữ nguyên; thêm màn hình M4 (TD-06); README mục 3 và 4; src/app.py. Vì cùng origin nên địa chỉ API không cấu hình bằng biến môi trường; nếu sau này tách giao diện sang máy chủ riêng thì khi đó mới cần biến này.
