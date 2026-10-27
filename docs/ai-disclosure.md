# Phụ lục — Bảng khai báo sử dụng công cụ AI (Bài tập 1)

| Công cụ | Dùng vào việc gì | Áp dụng ở phần nào | Đã kiểm chứng thế nào |
|---|---|---|---|
| Claude Code | Gợi ý ý tưởng, bố cục và làm bản nháp đầu cho SRS, User Story, đặc tả use case | `docs/srs.md` | Tôi đối chiếu lại với case study, sửa theo ý mình, tự chốt danh sách User Story và mức MoSCoW |
| Claude Code | Gợi ý cách vẽ và làm bản nháp đầu các sơ đồ use case, kiến trúc, ERD, wireframe | `docs/*.drawio`, `docs/wireframe.png` | Tôi mở bằng draw.io vẽ bổ sung, chỉnh sửa theo mong muốn; so ERD với dữ liệu mẫu, so từng trường wireframe với cột ERD |
| Claude Code | Gợi ý và làm bản nháp đầu DDL, API contract, bảng ánh xạ trong tài liệu thiết kế | `migrations/001_init.sql`, `docs/api-contract.md`, `docs/design.md` | Tôi đối soát với ERD, bảng truy vết và 5 lỗi ERD buổi 5, sửa lại theo ý mình |
| Claude Code | Góp ý 3 câu lập luận của tôi (sai khuôn, lệch mã NFR, thiếu đánh đổi), không viết thay | `docs/design.md` mục 3.2 | Tôi tự sửa lại theo khuôn của đề |
| Claude (claude.ai) | Hỗ trợ diễn đạt 3 câu lập luận; ý quyết định và đánh đổi do tôi tự nghĩ từ NFR1–NFR3 | `docs/design.md` mục 3.2 | So từng câu với NFR trong SRS và sơ đồ kiến trúc; tự giải thích được từng câu |
| Claude Code | Góp ý và hỗ trợ sửa bài theo nhận xét chấm BT1: gộp US7 với US8, thêm ngưỡng cho NFR2, trích DDL | `docs/srs.md`, `docs/design.md`, `docs/api-contract.md` | Tôi tự chọn hướng sửa, sau đó kiểm tra lại với nhận xét của thầy và bảng truy vết |
| — không dùng — | Chọn track SE, luồng L5, công nghệ Python/Flask/PostgreSQL; chốt phạm vi; peer review buổi 4 | Phiếu phạm vi, README | Không áp dụng |

Tôi xác nhận đã đọc, hiểu và chịu trách nhiệm về toàn bộ nội dung nộp.

Trần Đăng Khoa — MSSV 2374802010240 — ngày 08/10/2026

# Phụ lục – Bảng khai báo sử dụng công cụ AI (Bài tập 2)

Bài tập 2 là mã nguồn nên bảng có cột "Đã kiểm chứng thế nào" ghi đúng những phép kiểm chứng đã chạy. Công cụ AI duy nhất dùng trong giai đoạn này là Claude Code (mô hình Claude), chạy trong ứng dụng desktop trên máy cá nhân.

| Công cụ | Dùng vào việc gì | Áp dụng ở tệp / hàm | Đã kiểm chứng thế nào |
|---|---|---|---|
| Claude Code | Viết bản nháp đầu và chỉnh theo yêu cầu: tầng routes, services, repositories, validators cho luồng kho linh kiện, gồm hàm `xuat_linh_kien`, `nhap_kho`, kiểm tra QT-09 và QT-14 | `src/routes/api.py`, `src/services/stock_service.py`, `src/repositories/stock_repo.py`, `src/validators/stock.py`, `src/auth.py` | Chạy `pytest` (32 test PASS, ba loại); chạy `grep` kiểm ranh giới tầng (service không có `request`, `jsonify`, `SELECT`); gọi API bằng curl trên PostgreSQL 18 thật với dữ liệu mẫu, kết quả lưu ở `docs/export/curl-crud-linh-kien.txt`; so từng mã lỗi với `docs/api-contract.md` |
| Claude Code | Viết bản nháp bộ kiểm thử và repository giả | `tests/conftest.py`, `tests/test_xuat_kho.py`, `tests/test_crud.py`, `tests/test_api.py` | Chạy `pytest` trước và sau khi sửa: test mất kết nối CSDL FAIL ở commit `e01be7a`, PASS ở `64ef464`; đối chiếu từng test với quy tắc trong `docs/srs.md` (xuất đúng bằng tồn, vượt tồn 1 đơn vị, tồn bằng ngưỡng, sai vai trò, sai trung tâm) |
| Claude Code | Viết bản nháp frontend JS thuần: lớp gọi API, thành phần ba trạng thái, bốn màn hình | `web/src/api/client.js`, `web/src/components/DataState.js`, `web/src/pages/*.js` | Chạy giao diện trên PostgreSQL thật với hai tài khoản (kỹ thuật viên và quản lý); xác nhận ba trạng thái bằng cách tắt backend rồi bấm "Thử lại"; `grep "fetch("` trong `web/src/pages` trả rỗng; ảnh chụp ở `docs/export/e2e-*.png` |
| Claude Code | Viết bản nháp migration 002 và kịch bản nạp lại dữ liệu | `migrations/002_soft_delete.sql`, `src/db_init.py` | Chạy `python -m src.db_init` hai lần liên tiếp: số dòng mỗi bảng không đổi (không nhân đôi dữ liệu) |
| Claude Code | Soạn nhật ký thay đổi thiết kế, bug log, README | `docs/thay-doi-thiet-ke.md`, `docs/bug-log.md`, `README.md` | Đối chiếu từng bug với test và commit thật trong `git log`; chạy từng lệnh của README trên bản sao sạch (không có venv) |
| Claude Code | Giải thích cách xử lý lỗi hạ tầng và logging theo tài liệu Buổi 11 | `src/app.py` (`errorhandler`, `logging.basicConfig`) | Đọc lại tài liệu Buổi 11; test hồi quy BUG-001; kiểm tra log không chứa mật khẩu hay chuỗi kết nối |
| – không dùng – | Quyết định thiết kế, chọn luồng và track, chọn ngưỡng và tên mã lỗi, chạy kiểm tra trên máy của mình | Phiếu phạm vi, BT1, các quyết định TD-01 đến TD-13 | Không áp dụng |
