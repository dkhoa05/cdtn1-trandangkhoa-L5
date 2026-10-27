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
- PostgreSQL 16 trở lên (đã chạy thử trên PostgreSQL 18)
- Biến môi trường: xem .env.example

Track SE gợi ý Node/Express hoặc Spring Boot, nhưng tôi chọn Python/Flask vì đã quen Python,
đỡ mất thời gian học ngôn ngữ mới mà tập trung được vào nghiệp vụ.

## 3. Hướng dẫn chạy
Chạy lần lượt từng lệnh trong thư mục gốc của repo (PowerShell trên Windows). Bước 5 yêu cầu PostgreSQL đang chạy.

1. `python -m venv venv`
2. `venv\Scriptsctivate`
3. `pip install -r requirements.txt`
4. `copy .env.example .env` rồi mở `.env` điền `DB_PASSWORD` của PostgreSQL
5. `psql -U postgres -c "CREATE DATABASE cdtn1_l5_dev;"`
6. `python -m src.db_init` (tạo bảng và nạp dữ liệu mẫu, chạy lại lần hai không lỗi)
7. `python -m src.app`
8. Mở http://localhost:5000, đăng nhập bằng mã người dùng `2` (kỹ thuật viên trung tâm Ninh Kiều) hoặc `101` (quản lý trung tâm Quận 10). Kiểm tra backend: http://localhost:5000/health trả `{"db":"ok","status":"ok"}`.

Nếu mỗi request mất vài giây trên Windows, đặt `DB_HOST=127.0.0.1` trong `.env` (tên `localhost` có thể được thử bằng IPv6 trước).

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

## 5. Kiểm thử
`pytest` chạy 31 test, không cần PostgreSQL (dùng repository giả), gồm ba loại: luồng đúng, giá trị biên (xuất đúng bằng tồn, vượt tồn 1 đơn vị, tồn bằng ngưỡng), dữ liệu sai và kiểm soát truy cập theo trung tâm.

## 6. Trạng thái hiện tại (buổi 10)
- [x] Điều chỉnh thiết kế theo phản hồi BT1 (docs/thay-doi-thiet-ke.md)
- [x] Khung src/ theo sơ đồ kiến trúc, requirements.txt khóa phiên bản, /health
- [x] Migration và dữ liệu mẫu
- [x] Tra cứu tồn kho, xuất, nhập kho và lịch sử qua 3 lớp (routes, services, repositories)
- [x] Xuất, nhập kho với quy tắc QT-09, QT-14
- [x] 31 kiểm thử thuộc ba loại
- [x] Màn hình M1, M2, M3 gọi API thật, có trạng thái đang tải, rỗng, lỗi
- [x] CRUD linh kiện và tồn kho (xóa mềm, migration 002), màn hình M4 Danh mục
- [ ] Phần còn lại của BT2 và BT3: kiểm thử ngắt lỗi giữa chừng, xuất đồng thời (TD-02)

Ảnh chạy toàn luồng trên dữ liệu mẫu thật: docs/export/e2e-*.png. Bản ghi gọi API bằng curl: docs/export/curl-crud-linh-kien.txt.
