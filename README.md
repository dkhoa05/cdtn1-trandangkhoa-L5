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
Node.js 20 LTS
PostgreSQL 16
Biến môi trường: xem .env.example

## 3. Hướng dẫn chạy
(BT2 yêu cầu ≤ 4 bước — cập nhật đầy đủ ở buổi 8–12)
1. cp .env.example .env và điền giá trị
2. npm install
3. npm run db:migrate
4. npm run dev → mở http://localhost:3000/health

## 4. Cấu trúc thư mục
- docs/ — tài liệu kỹ thuật (SRS, ERD, kiến trúc, khai báo AI)
- src/api/ — endpoint Express
- src/service/ — business logic (kiểm tra tồn kho, sinh cảnh báo)
- src/repository/ — truy vấn PostgreSQL
- tests/ — unit test và integration test
- data/sample/ — mẫu nhỏ từ parts.csv/part_stock.csv/part_transactions.csv (không commit dữ liệu gốc)

## 5. Kiểm thử
npm test → hiển thị số test PASS

## 6. Trạng thái hiện tại
[ ] Khởi tạo project, smoke test chạy được (buổi 2)
[ ] Module xem/xuất tồn kho (buổi 8–10)
[ ] Module cảnh báo & nhập kho (buổi 10–12)
