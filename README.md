# Quản lý kho linh kiện thay thế cho trung tâm bảo hành

Sinh viên:
Trần Đăng Khoa - 2374802010240 - Track SE

Học phần:
Chuyên đề Tốt nghiệp 1, HK1 2026-2027

Luồng nghiệp vụ:
L5 – Kho linh kiện thay thế

## 1. Mục tiêu
Theo dõi tồn kho linh kiện theo từng trung tâm bảo hành, kiểm soát xuất kho không vượt tồn,
cảnh báo khi tồn dưới ngưỡng, và ghi nhận nhập kho. Mục tiêu là giải quyết vấn đề V6 (kỹ thuật viên nhận
phiếu rồi mới biết hết linh kiện, phải hẹn lại khách).

## 2. Yêu cầu môi trường
- Python 3.10 trở lên
- PostgreSQL 16 trở lên đang chạy (đã chạy thử trên PostgreSQL 18); người dùng PostgreSQL có quyền tạo CSDL, nếu không thì tạo sẵn CSDL tên `cdtn1_l5_dev` bằng pgAdmin
- Môi trường ảo Python, tạo một lần trước khi chạy các bước ở mục 3: `python -m venv venv` rồi `venv\Scripts\activate`
- Biến môi trường: xem .env.example

Track SE gợi ý Node/Express hoặc Spring Boot, nhưng tôi chọn Python/Flask vì đã quen Python,
đỡ mất thời gian học ngôn ngữ mới mà tập trung được vào nghiệp vụ.

## 3. Hướng dẫn chạy
Bốn bước, mỗi bước một lệnh, chạy trong thư mục gốc của repo sau khi đã bật môi trường ảo ở mục 2.

1. `copy .env.example .env` rồi mở `.env` điền `DB_PASSWORD` (và `DB_USER` nếu khác `postgres`)
2. `pip install -r requirements.txt`
3. `python -m src.db_init` (tự tạo CSDL nếu chưa có, tạo bảng và nạp dữ liệu mẫu; chạy lại lần hai không lỗi)
4. `python -m src.app`

Kiểm tra hệ thống chạy đúng: mở http://localhost:5000/health phải trả `{"db":"ok","status":"ok"}`; mở http://localhost:5000 và đăng nhập bằng mã người dùng `2` (kỹ thuật viên trung tâm Ninh Kiều) hoặc `101` (quản lý trung tâm Quận 10).

Giao diện web không có bước chạy riêng: `python -m src.app` phục vụ cả API lẫn trang web trên cùng một cổng, nên chỉ cần mở http://localhost:5000 sau bước 4 và không phải cài hay chạy thêm gì cho `web/`. Giao diện luôn gọi API ở cùng địa chỉ với trang, nên không có biến cấu hình địa chỉ API; nếu tắt bước 4 thì giao diện hiện thông báo lỗi kèm nút Thử lại.

Nếu mỗi request mất vài giây trên Windows, đặt `DB_HOST=127.0.0.1` trong `.env` (tên `localhost` có thể được thử bằng IPv6 trước).

Nếu báo cổng 5000 đang bận, đặt `PORT=5001` trong `.env` rồi chạy lại `python -m src.app` và mở http://localhost:5001.

Biến môi trường (xem `.env.example`): `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` để nối PostgreSQL; `SECRET_KEY` để ký token đăng nhập; `PORT` là cổng ứng dụng (mặc định 5000); `LOG_LEVEL` là mức log (`INFO` mặc định, `DEBUG` khi cần điều tra, log ghi ra stdout và không chứa mật khẩu hay chuỗi kết nối).

## 4. Cấu trúc thư mục
- docs/: tài liệu (SRS, thiết kế, sơ đồ, nhật ký thay đổi thiết kế, khai báo AI)
- src/routes/: nhận request HTTP, đổi lỗi nghiệp vụ thành mã HTTP
- src/services/: quy tắc nghiệp vụ, không chứa gì về HTTP
- src/repositories/: đọc ghi PostgreSQL, không chứa quy tắc nghiệp vụ
- src/validators/: kiểm tra định dạng dữ liệu vào
- web/: frontend JS thuần (không cần build): `src/api/` gọi API (chỉ `client.js` được dùng `fetch`), `src/components/` (DataState), `src/pages/` bốn màn hình M1-M4
- migrations/: tạo bảng từ cơ sở dữ liệu trống
- seeds/: dữ liệu mẫu rút từ bộ dữ liệu của case study
- tests/: bộ kiểm thử

Quy ước đặt tên: tên bảng, cột, đường dẫn API và mã lỗi dùng tiếng Anh theo bảng thuật ngữ mục 1 của SRS (`part`, `part_stock`, `ticket`, `INSUFFICIENT_STOCK`); tên hàm và biến trong mã nghiệp vụ dùng tiếng Việt không dấu (`xuat_linh_kien`, `ton`); thông báo hiển thị cho người dùng viết tiếng Việt có dấu.

## 5. Kiểm thử
Kiểm thử tích hợp trên PostgreSQL thật (ngắt lỗi giữa chừng 1.000 lần, tám luồng xuất đồng thời) mặc định bị bỏ qua; chạy bằng `$env:RUN_PG_TESTS="1"; pytest tests/test_tich_hop_pg.py` sau khi đã chạy `python -m src.db_init`. Hai kiểm thử này mất khoảng một phút và tự xóa dữ liệu chúng tạo, nên chạy nhiều lần không làm đầy CSDL.

`pytest` chạy 47 test, không cần PostgreSQL (dùng repository giả), gồm ba loại: luồng đúng, giá trị biên (xuất đúng bằng tồn, vượt tồn 1 đơn vị, tồn bằng ngưỡng), dữ liệu sai và kiểm soát truy cập theo trung tâm.

## 6. Trạng thái hiện tại
- [x] Điều chỉnh thiết kế theo phản hồi BT1 (docs/thay-doi-thiet-ke.md)
- [x] Khung src/ theo sơ đồ kiến trúc, requirements.txt khóa phiên bản, /health
- [x] Migration và dữ liệu mẫu
- [x] Tra cứu tồn kho, xuất, nhập kho và lịch sử qua 3 lớp (routes, services, repositories)
- [x] Xuất, nhập kho với quy tắc QT-09, QT-14
- [x] 32 kiểm thử thuộc ba loại, cộng 2 kiểm thử tích hợp PostgreSQL (NFR2)
- [x] Màn hình M1, M2, M3 gọi API thật, có trạng thái đang tải, rỗng, lỗi
- [x] CRUD linh kiện và tồn kho (xóa mềm, migration 002), màn hình M4 Danh mục
- [x] Kiểm thử ngắt lỗi giữa chừng và xuất đồng thời (TD-02)

Ảnh chạy toàn luồng trên dữ liệu mẫu thật: docs/export/e2e-*.png. Bản ghi gọi API bằng curl: docs/export/curl-crud-linh-kien.txt.
