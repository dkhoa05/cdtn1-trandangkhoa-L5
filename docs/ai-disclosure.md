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

Công cụ AI duy nhất dùng trong giai đoạn này là Claude Code (mô hình Claude), chạy trong ứng dụng desktop trên máy cá nhân. Gần như toàn bộ mã nguồn, bộ kiểm thử và tài liệu của Bài tập 2 do Claude Code sinh ra theo yêu cầu bằng lời, sau đó được chỉnh nhiều lần qua hội thoại; không có tệp mã nào được viết tay hoàn toàn. Cột "Đã kiểm chứng thế nào" chỉ ghi những lệnh đã chạy thật.

| Công cụ | Dùng vào việc gì | Áp dụng ở tệp / hàm | Đã kiểm chứng thế nào |
|---|---|---|---|
| Claude Code | Sinh toàn bộ bản mã đầu tiên của backend: routes, services, repositories, validators, xác thực token, gồm hàm `xuat_linh_kien`, `nhap_kho` và quy tắc QT-09, QT-14, QT-13 | `src/routes/api.py`, `src/services/stock_service.py`, `src/repositories/stock_repo.py`, `src/validators/stock.py`, `src/auth.py` | `pytest` (47 test PASS, ba loại, thêm 2 test tích hợp trên PostgreSQL thật); `grep` kiểm service không chứa dấu vết HTTP hay SQL; gọi 14 lời gọi API trên PostgreSQL 18 (ảnh Hình 3.2 trong PDF); so từng mã lỗi với `docs/api-contract.md` |
| Claude Code | Sinh lớp hợp đồng dữ liệu, log JSON, tự tạo CSDL trong `db_init` sau khi đối chiếu tài liệu Buổi 9, 11 | `src/routes/views.py` (commit `0e5ca1f`), `src/log_config.py` (commit `030c6f8`), `src/db_init.py` | `tests/test_hop_dong.py` (đổi tên một trường trong hợp đồng thì test vỡ); `tests/test_log.py`; chạy `db_init` trên máy chủ PostgreSQL trống hai lần; đọc dòng log thật, không chứa token |
| Claude Code | Sinh bộ kiểm thử và repository giả trong bộ nhớ | `tests/conftest.py`, `tests/test_xuat_kho.py`, `tests/test_crud.py`, `tests/test_api.py`, `tests/test_hop_dong.py`, `tests/test_log.py`, `tests/test_tai_lieu.py`, `tests/test_tich_hop_pg.py` | Chạy `pytest` trước và sau khi sửa (test mất kết nối CSDL FAIL ở commit `04238a2`, PASS ở `4520fc8`); thử đổi tên trường và bỏ `FOR UPDATE` để xác nhận test phát hiện được lỗi (bỏ khóa thì test đồng thời FAIL 4 trong 5 lần) |
| Claude Code | Sinh frontend JavaScript thuần: lớp gọi API, thành phần ba trạng thái, bốn màn hình, nút Xóa bộ lọc, giao diện màn hình hẹp | `web/src/api/client.js`, `web/src/components/DataState.js`, `web/src/pages/*.js`, `web/styles.css` | Chạy giao diện trên PostgreSQL thật với hai tài khoản; tắt backend rồi bấm Thử lại; đo không tràn ngang ở 375px trên cả bốn màn hình; `grep "fetch("` trong `web/src/pages` rỗng |
| Claude Code | Sinh migration 002 và kịch bản nạp dữ liệu có thể chạy lại | `migrations/002_soft_delete.sql`, `src/db_init.py` | Chạy `python -m src.db_init` hai lần: số dòng mỗi bảng không đổi |
| Claude Code | Soạn bản nháp README, nhật ký thay đổi thiết kế, bug log, báo cáo PDF; phát hiện ký tự hỏng ở README (BUG-005, sửa ở `a9f5395`, test ở `43fa513`) | `README.md`, `docs/thay-doi-thiet-ke.md`, `docs/bug-log.md`, `docs/api-contract.md` | Đối chiếu từng bug với test và commit thật trong `git log`; clone sạch từ tag rồi chạy các lệnh của README |
| – không dùng – | Chọn luồng L5 và track SE, phạm vi, thiết kế kiến trúc và mô hình dữ liệu ở Bài tập 1 (đã khai báo ở phụ lục Bài tập 1) | Phiếu phạm vi, `docs/srs.md`, `docs/design.md`, `docs/erd.drawio` | Không áp dụng |
