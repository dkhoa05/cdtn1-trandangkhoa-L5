# Phụ lục — Bảng khai báo sử dụng công cụ AI (Bài tập 1)

| Công cụ | Dùng vào việc gì | Áp dụng ở phần nào | Đã kiểm chứng thế nào |
|---|---|---|---|
| Claude Code | Gợi ý ý tưởng, bố cục và làm bản nháp đầu cho SRS, User Story, đặc tả use case | `docs/srs.md` | Tôi đối chiếu lại với case study, sửa theo ý mình, tự chốt giữ 8 User Story và mức MoSCoW |
| Claude Code | Gợi ý cách vẽ và làm bản nháp đầu các sơ đồ use case, kiến trúc, ERD, wireframe | `docs/*.drawio`, `docs/wireframe.png` | Tôi mở bằng draw.io vẽ bổ sung, chỉnh sửa theo mong muốn; so ERD với dữ liệu mẫu, so từng trường wireframe với cột ERD |
| Claude Code | Gợi ý và làm bản nháp đầu DDL, API contract, bảng ánh xạ trong tài liệu thiết kế | `db/schema.sql`, `docs/api-contract.md`, `docs/design.md` | Tôi đối soát với ERD, bảng truy vết và 5 lỗi ERD buổi 5, sửa lại theo ý mình |
| Claude Code | Góp ý 3 câu lập luận của tôi (sai khuôn, lệch mã NFR, thiếu đánh đổi), không viết thay | `docs/design.md` mục 3.2 | Tôi tự sửa lại theo khuôn của đề |
| Claude (claude.ai) | Hỗ trợ diễn đạt 3 câu lập luận; ý quyết định và đánh đổi do tôi tự nghĩ từ NFR1–NFR3 | `docs/design.md` mục 3.2 | So từng câu với NFR trong SRS và sơ đồ kiến trúc; tự giải thích được từng câu |
| — không dùng — | Chọn track SE, luồng L5, công nghệ Python/Flask/PostgreSQL; chốt phạm vi; peer review buổi 4 | Phiếu phạm vi, README | Không áp dụng |

Tôi xác nhận đã đọc, hiểu và chịu trách nhiệm về toàn bộ nội dung nộp.

Trần Đăng Khoa — MSSV 2374802010240 — ngày 08/10/2026
