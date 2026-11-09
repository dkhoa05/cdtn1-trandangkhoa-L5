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
- Cách chạy khuyến nghị (Docker): chỉ cần Docker Desktop và Git, đã thử trên Docker Engine 29.9 và Compose 5.6; không cần Python hay PostgreSQL. Các mục còn lại của mục 2 chỉ cần cho cách chạy trực tiếp bằng Python
- Python 3.10 trở lên
- PostgreSQL 16 trở lên đang chạy (đã chạy thử trên PostgreSQL 18); người dùng PostgreSQL có quyền tạo CSDL, nếu không thì tạo sẵn CSDL tên `cdtn1_l5_dev` bằng pgAdmin
- Môi trường ảo Python, tạo một lần trước khi chạy các bước ở mục 3: `python -m venv venv` rồi `venv\Scripts\activate`
- Biến môi trường: xem .env.example

Track SE gợi ý Node/Express hoặc Spring Boot, nhưng tôi chọn Python/Flask vì đã quen Python,
đỡ mất thời gian học ngôn ngữ mới mà tập trung được vào nghiệp vụ.

## 3. Hướng dẫn chạy
Chọn một trong hai cách. Cách A (khuyến nghị) chỉ cần Docker Desktop và Git; cách B cần Python và PostgreSQL cài sẵn.

### Cách A: Docker Compose (khuyến nghị)
Docker Desktop đang chạy. Trong thư mục gốc của repo chạy đúng hai lệnh sau (PowerShell và Git Bash đều dùng được; trong cmd thay `cp` bằng `copy`):

```
cp .env.example .env
docker compose up -d --build
```

Giá trị mẫu trong `.env.example` chạy được ngay, không cần sửa. Lệnh thứ hai dựng hai container, `db` (PostgreSQL 16) và `app` (Flask). `app` chờ `db` sẵn sàng rồi tự chạy `python -m src.db_init` (tạo bảng và nạp dữ liệu mẫu) trước khi mở máy chủ, nên hệ thống không lên trống. Lần đầu mất vài phút để tải image.

Kiểm tra hệ thống chạy đúng:

```
docker compose ps
docker compose exec app pytest
```

`docker compose ps` phải cho cả hai dịch vụ ở trạng thái `healthy`; mở http://localhost:5000/health phải trả `{"db":"ok","status":"ok"}`; `pytest` phải báo `54 passed, 3 skipped` (3 kiểm thử tích hợp PostgreSQL mặc định bị bỏ qua, chạy bằng `docker compose exec -e RUN_PG_TESTS=1 app pytest tests/test_tich_hop_pg.py`, kết quả `3 passed`). Số dòng dữ liệu mẫu để đối chiếu nằm ở log của `app` (`docker compose logs app`): service_center 6, app_user 44, part 180, part_stock 717, ticket 874, part_transaction 387.

Dừng bằng `docker compose down`; thêm `-v` để xóa luôn dữ liệu và dựng lại từ trống. Nếu cổng 5000 đang bận, đặt `PORT=5001` trong `.env`, chạy lại lệnh thứ hai và mở http://localhost:5001.

### Cách B: chạy trực tiếp bằng Python (không dùng Docker)
Bốn bước, mỗi bước một lệnh, chạy trong thư mục gốc của repo sau khi đã bật môi trường ảo ở mục 2.

1. `copy .env.example .env` rồi mở `.env` điền `DB_PASSWORD` (và `DB_USER` nếu khác `postgres`)
2. `pip install -r requirements.txt`
3. `python -m src.db_init` (tự tạo CSDL nếu chưa có, tạo bảng và nạp dữ liệu mẫu; chạy lại lần hai không lỗi)
4. `python -m src.app`

Lệnh kiểm thử của cách B là `pytest` (mục 5). Nếu mỗi request mất vài giây trên Windows, đặt `DB_HOST=127.0.0.1` trong `.env` (tên `localhost` có thể được thử bằng IPv6 trước). Nếu báo cổng 5000 đang bận, đặt `PORT=5001` trong `.env` rồi chạy lại `python -m src.app` và mở http://localhost:5001. Muốn bật trình gỡ lỗi của Flask trên máy phát triển, đặt `FLASK_DEBUG=1` trong `.env`; mặc định nó đóng.

### Dùng thử hệ thống (cả hai cách)
Mở http://localhost:5000 và bấm "Kỹ thuật viên" (mã `2`, trung tâm Ninh Kiều) hoặc "Quản lý trung tâm" (mã `101`, trung tâm Quận 10) để đăng nhập ngay; tài khoản khác thì nhập mã ở mục "Đăng nhập bằng mã người dùng khác". Kỹ thuật viên chỉ thấy Tồn kho và Xuất linh kiện, quản lý thấy thêm Nhập kho và lịch sử, Danh mục. Màn hình Tồn kho lọc được theo từ khóa, tình trạng tồn (tất cả, dưới ngưỡng, hết hàng, còn đủ), sắp xếp và số dòng mỗi trang.

Giao diện web không có bước chạy riêng: máy chủ Flask phục vụ cả API lẫn trang web trên cùng một cổng, nên không phải cài hay chạy thêm gì cho `web/`. Giao diện luôn gọi API ở cùng địa chỉ với trang, nên không có biến cấu hình địa chỉ API; nếu máy chủ tắt thì giao diện hiện thông báo lỗi kèm nút Thử lại.

Biến môi trường (xem `.env.example`, mỗi biến có chú thích): `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` để nối PostgreSQL (Docker tự đặt `DB_HOST=db`); `SECRET_KEY` để ký token đăng nhập; `PORT` là cổng ứng dụng (mặc định 5000); `LOG_LEVEL` là mức log (`INFO` mặc định, `DEBUG` khi cần điều tra, log ghi ra stdout và không chứa mật khẩu hay chuỗi kết nối); `FLASK_DEBUG` bật trình gỡ lỗi (mặc định `0`).

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
- Dockerfile, docker-compose.yml, .dockerignore: đóng gói hệ thống chạy bằng hai lệnh (mục 3, cách A)

Quy ước đặt tên: tên bảng, cột, đường dẫn API và mã lỗi dùng tiếng Anh theo bảng thuật ngữ mục 1 của SRS (`part`, `part_stock`, `ticket`, `INSUFFICIENT_STOCK`); tên hàm và biến trong mã nghiệp vụ dùng tiếng Việt không dấu (`xuat_linh_kien`, `ton`); thông báo hiển thị cho người dùng viết tiếng Việt có dấu.

## 5. Kiểm thử
Trong Docker: `docker compose exec app pytest`. Chạy trực tiếp: `pytest`. Kế hoạch, kết quả thật và nhật ký lỗi nằm ở docs/test-plan.md, docs/test-report.md, docs/bug-log.md.

Kiểm thử tích hợp trên PostgreSQL thật (ngắt lỗi giữa chừng 1.000 lần, tám luồng xuất đồng thời, lọc và sắp xếp tồn kho trên dữ liệu thật) mặc định bị bỏ qua; chạy bằng `$env:RUN_PG_TESTS="1"; pytest tests/test_tich_hop_pg.py` sau khi đã chạy `python -m src.db_init`. Ba kiểm thử này mất khoảng một phút; hai kiểm thử có ghi dữ liệu tự xóa hẳn dữ liệu chúng tạo và kiểm thử còn lại chỉ đọc, nên chạy nhiều lần không làm đầy CSDL.

`pytest` chạy 54 test, không cần PostgreSQL (dùng repository giả), gồm ba loại: luồng đúng, giá trị biên (xuất đúng bằng tồn, vượt tồn 1 đơn vị, tồn bằng ngưỡng), dữ liệu sai và kiểm soát truy cập theo trung tâm.

## 6. Trạng thái hiện tại
- [x] Điều chỉnh thiết kế theo phản hồi BT1 (docs/thay-doi-thiet-ke.md)
- [x] Khung src/ theo sơ đồ kiến trúc, requirements.txt khóa phiên bản, /health
- [x] Migration và dữ liệu mẫu
- [x] Tra cứu tồn kho, xuất, nhập kho và lịch sử qua 3 lớp (routes, services, repositories)
- [x] Xuất, nhập kho với quy tắc QT-09, QT-14
- [x] 54 kiểm thử thuộc ba loại, cộng 3 kiểm thử tích hợp PostgreSQL (NFR2, bộ lọc tồn kho)
- [x] Màn hình M1, M2, M3 gọi API thật, có trạng thái đang tải, rỗng, lỗi
- [x] CRUD linh kiện và tồn kho (xóa mềm, migration 002), màn hình M4 Danh mục
- [x] Màn hình Tồn kho có bộ lọc tình trạng tồn và sắp xếp; đăng nhập nhanh; menu theo vai trò; giao diện dùng được bằng bàn phím, có chế độ tối
- [x] Kiểm thử ngắt lỗi giữa chừng và xuất đồng thời (TD-02)
- [x] Đóng gói Docker Compose có healthcheck, dữ liệu mẫu tự nạp, chạy pytest được trong container
- [x] Test Plan, Test Report 12 test case, Bug Log, checklist bảo mật (docs/)

Ảnh chụp giao diện đang chạy trên dữ liệu mẫu thật: docs/export/e2e-*.png (đăng nhập, bộ lọc tồn kho, ba trạng thái đang tải, rỗng, lỗi, xuất linh kiện, nhập kho và lịch sử, danh mục). Bản ghi gọi API bằng curl: docs/export/curl-crud-linh-kien.txt.
