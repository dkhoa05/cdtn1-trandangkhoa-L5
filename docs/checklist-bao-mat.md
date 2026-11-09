# Checklist bảo mật bảy mục (tự đánh giá), Bài tập 3

Tự đánh giá ngày 09/11/2026 trên hệ thống chạy bằng Docker Compose (hai dịch vụ `healthy`). Mỗi mục ghi một trong ba giá trị ĐÃ LÀM, CHƯA LÀM, KHÔNG ÁP DỤNG, kèm minh chứng là lệnh đã chạy và kết quả đọc được. Các mục được điền bằng cách chạy thử, không bằng cách nhớ lại.

## 1. Không có secret nào trong repo

Trạng thái: ĐÃ LÀM

Minh chứng: `git log --all --oneline -- .env` không ra dòng nào và `git check-ignore -v .env` in `.gitignore:4:.env`, nên `.env` thật chưa từng vào lịch sử; `docker-compose.yml` lấy `DB_PASSWORD` và `SECRET_KEY` từ `.env` (thiếu thì compose dừng với thông báo), `.dockerignore` chặn `.env` nên image không chứa nó (`docker compose exec app ls -a /app` không có `.env`).

Ghi chú trung thực: lịch sử Git còn hai giá trị chạy thử `demo_docker` và `khoa-chi-de-chay-thu` trong bản đầu của `docker-compose.yml` (commit `8c2a496`), đã bỏ ở commit `fd32c4f`; đó là giá trị cục bộ, không phải secret của dịch vụ thật. Khi chạy trực tiếp bằng Python mà thiếu `SECRET_KEY`, `src/config.py` dùng giá trị mặc định `dev-only-secret`; cách chạy bằng Docker không rơi vào trường hợp này.

## 2. Dữ liệu vào được kiểm ở tầng ứng dụng

Trạng thái: ĐÃ LÀM

Minh chứng: toàn bộ kiểm tra nằm ở `src/validators/stock.py` (kiểu, khoảng giá trị, độ dài, cận trên `MAX_INT` và `MAX_GIA`, danh sách giá trị cho phép của bộ lọc và sắp xếp); chạy thật `python tests/tc_api.py` cho TC-07 (`quantity` = 0) và TC-08 (`quantity` = 100000000000) đều trả HTTP 400 `VALIDATION_FAILED` nêu tên trường; gửi `q` = `'; DROP TABLE part;--` trả 200 với danh sách rỗng và bảng còn nguyên; ba lệnh grep tìm lỗ hổng chèn mã trên `src/` và `web/src` cho kết quả: câu SQL ghép chuỗi 0 dòng, `exec(`, `os.system`, `shell=True` 0 dòng, `innerHTML` 0 dòng dùng thật (một dòng duy nhất là chú thích nói rằng không dùng nó).

Ghi chú trung thực: `src/repositories/stock_repo.py` dòng 52 dựng câu SQL bằng f-string, nhưng chỉ chèn các đoạn lấy từ hai từ điển cố định `_LOC_TON` và `_SAP_XEP`; giá trị người dùng chỉ chọn khóa của từ điển, các giá trị còn lại đi qua tham số `%s`.

## 3. Kiểm soát truy cập theo chủ sở hữu

Trạng thái: ĐÃ LÀM

Minh chứng: quy tắc QT-14 (mọi thao tác giới hạn trong trung tâm của người dùng) và quyền theo vai trò nằm ở `src/services/stock_service.py`, có test TC-09; chạy thật trên Docker: người dùng 101 (trung tâm 1) xuất linh kiện cho phiếu 51 (trung tâm 4) nhận 403 `FORBIDDEN` "Bạn chỉ thao tác được trên dữ liệu của trung tâm mình", kỹ thuật viên gọi nhập kho nhận 403 "Chỉ quản lý trung tâm được ghi nhận nhập kho", gọi không kèm token nhận 401 `UNAUTHORIZED`.

## 4. Mật khẩu và dữ liệu nhạy cảm được băm hoặc mã hóa

Trạng thái: CHƯA LÀM

Minh chứng: hệ thống hiện chưa lưu mật khẩu nào, `grep -riE "password|mat_khau|hash" migrations seeds src` chỉ ra danh sách trường che trong `src/log_config.py`, bảng `app_user` không có cột mật khẩu; người dùng đăng nhập bằng mã người dùng ở mức prototype (TD-05 trong `docs/thay-doi-thiet-ke.md`).

Ghi chú trung thực: thêm mật khẩu băm làm thay đổi cách đăng nhập nên cần ghi vào `docs/thay-doi-thiet-ke.md` trước khi làm; đến lúc đó mục này mới được đổi sang ĐÃ LÀM.

## 5. Thông báo lỗi không lộ cấu trúc bên trong

Trạng thái: ĐÃ LÀM

Minh chứng: đã gây lỗi và đọc phản hồi trên Docker: đường dẫn lạ và `GET /api/parts/abc` đều 404 `NOT_FOUND` "Không có đường dẫn này"; body JSON hỏng 400 `VALIDATION_FAILED` chỉ nêu trường `body`; số lượng quá lớn 400 thay vì 500 (BUG-006); tắt container `db` rồi gọi `GET /api/parts` nhận 503 `DB_UNAVAILABLE` với câu chung và `requestId`, không có chuỗi kết nối hay tên bảng (BUG-001); trình xử lý lỗi chung chỉ trả `INTERNAL_ERROR`, ngăn xếp chỉ nằm trong log của máy chủ; `GET /console` trả 404 trên Docker và trên `python -m src.app` mặc định (trước khi sửa ở commit `43dfc29` lệnh này trả 200 vì chạy với `debug=True`, nay chỉ bật khi đặt `FLASK_DEBUG=1`).

## 6. Nhật ký không ghi secret hay dữ liệu cá nhân không cần thiết

Trạng thái: ĐÃ LÀM

Minh chứng: `src/log_config.py` che các trường `password`, `mat_khau`, `token`, `authorization`, `secret`, `so_dien_thoai` trước khi ghi, có test ở `tests/test_log.py`; sau khi gọi API với tiêu đề `Authorization: Bearer ...`, `docker compose logs app` lọc bằng mẫu `bearer|eyJ|authorization|password|demo_docker|mat_khau` cho 0 dòng; mỗi dòng log là JSON chỉ có `requestId`, phương thức, đường dẫn, mã trạng thái và thời gian xử lý.

## 7. Phụ thuộc được ghim phiên bản và đã kiểm cảnh báo lỗ hổng

Trạng thái: ĐÃ LÀM

Minh chứng: mọi dòng của `requirements.txt` dùng `==`; `pip-audit -r requirements.txt --no-deps` lần đầu báo 6 cảnh báo ở ba gói (Flask 3.0.3, pytest 8.3.3, python-dotenv 1.0.1); đã nâng lên Flask 3.1.3, pytest 9.0.3, python-dotenv 1.2.2 (commit `879f545`), chạy lại cho kết quả `No known vulnerabilities found`, và 54 test vẫn PASS trong container.
