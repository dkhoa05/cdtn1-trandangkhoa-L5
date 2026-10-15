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
