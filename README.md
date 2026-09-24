# Quản lý kho linh kiện thay thế cho trung tâm bảo hành

Sinh viên:
Trần Đăng Khoa - 2374802010240 - Track SE

Học phần:
Chuyên đề Tốt nghiệp 1, HK1 2026-2027

Luồng nghiệp vụ:
L5 – Kho linh kiện thay thế

## 1. Mục tiêu
Theo dõi tồn kho linh kiện theo từng trung tâm bảo hành, kiểm soát xuất kho không vượt tồn,
cảnh báo khi tồn dưới ngưỡng, và ghi nhận nhập kho — giải quyết vấn đề V6 (kỹ thuật viên nhận
phiếu rồi mới biết hết linh kiện, phải hẹn lại khách).

## 2. Yêu cầu môi trường
Python 3.11+
PostgreSQL 16
Biến môi trường: xem .env.example

Ghi chú lựa chọn công nghệ: track SE gợi ý Node/Express hoặc Spring Boot; chọn Python/Flask
thay thế vì đã có kinh nghiệm sẵn với Python, giúp tập trung vào logic nghiệp vụ thay vì học
ngôn ngữ mới.

## 3. Hướng dẫn chạy
(BT2 yêu cầu ≤ 4 bước — cập nhật đầy đủ ở buổi 8–12)
1. python -m venv venv && venv\Scripts\activate (Windows) rồi cp .env.example .env và điền giá trị
2. pip install -r requirements.txt
3. flask db upgrade (hoặc script migrate tương ứng)
4. flask run → mở http://localhost:5000/health

## 4. Cấu trúc thư mục
- docs/ — tài liệu kỹ thuật (SRS, ERD, kiến trúc, khai báo AI)
- src/api/ — route/endpoint Flask
- src/service/ — business logic (kiểm tra tồn kho, sinh cảnh báo)
- src/repository/ — truy vấn PostgreSQL
- tests/ — unit test và integration test
- data/sample/ — mẫu nhỏ từ parts.csv/part_stock.csv/part_transactions.csv (không commit dữ liệu gốc)

## 5. Kiểm thử
pytest → hiển thị số test PASS

## 6. Trạng thái hiện tại
[ ] Khởi tạo project, smoke test chạy được (buổi 2)
[ ] Module xem/xuất tồn kho (buổi 8–10)
[ ] Module cảnh báo & nhập kho (buổi 10–12)
