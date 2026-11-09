# Nhật ký lỗi (Bug Log) – Bài tập 3

Bug Log này ghi các lỗi nằm trong mã nguồn (`src/`, `web/`) đã được sửa. Mỗi mục có bảy dòng theo mẫu của học phần, link commit trỏ tới repo công khai `dkhoa05/cdtn1-trandangkhoa-L5`. Mã lỗi giữ theo thứ tự phát hiện trong dự án nên không liền nhau.

## BUG-001. Mất kết nối cơ sở dữ liệu trả 500 chung chung

| Dòng | Nội dung |
|---|---|
| 1. Mã và mức độ | BUG-001, Major |
| 2. Phát hiện bởi | Kiểm thử hồi quy `test_mat_ket_noi_csdl_tra_503_kem_ma_tra_cuu` trong `tests/test_api.py`, viết theo mục "tắt một thành phần phụ" của quy trình chấm |
| 3. Triệu chứng | Khi PostgreSQL không kết nối được, `GET /api/parts` trả HTTP 500 với mã `INTERNAL_ERROR`, người gọi không phân biệt được lỗi hạ tầng với lỗi chương trình |
| 4. Cách tái lập | Chạy `pytest tests/test_api.py -k mat_ket_noi` ở commit `04238a2`: test FAIL vì nhận 500 thay vì 503 |
| 5. Nguyên nhân | `psycopg.OperationalError` do `db.connect()` ném ra không có trình xử lý riêng ở `create_app`, nên rơi vào trình xử lý `Exception` chung vốn trả 500 |
| 6. Cách sửa | Thêm `errorhandler(psycopg.OperationalError)` ở một chỗ duy nhất trong `src/app.py`: ghi ERROR một lần kèm ngăn xếp và `requestId`, trả 503 với mã `DB_UNAVAILABLE`, không lộ chi tiết kết nối. Lớp service không bắt lỗi hạ tầng |
| 7. Commit và xác nhận | Test: [04238a2](https://github.com/dkhoa05/cdtn1-trandangkhoa-L5/commit/04238a2). Sửa: [4520fc8](https://github.com/dkhoa05/cdtn1-trandangkhoa-L5/commit/4520fc8). Sau sửa test PASS, toàn bộ 32 test lúc đó PASS |

## BUG-003. Đơn giá trả về dạng chuỗi

| Dòng | Nội dung |
|---|---|
| 1. Mã và mức độ | BUG-003, Minor |
| 2. Phát hiện bởi | Chạy kịch bản curl CRUD trên PostgreSQL thật (`docs/export/curl-crud-linh-kien.txt`) |
| 3. Triệu chứng | `unit_price` trong phản hồi là `"120000"` (chuỗi) thay vì số, giao diện phải tự ép kiểu |
| 4. Cách tái lập | `curl -XPOST /api/parts` rồi `GET /api/parts/{id}` ở phiên bản đầu của `src/app.py` |
| 5. Nguyên nhân | Cột `NUMERIC(12,0)` được psycopg trả về kiểu `Decimal`, bộ chuyển JSON mặc định của Flask quy mọi kiểu lạ về chuỗi |
| 6. Cách sửa | Trong `create_app`, đổi `Decimal` nguyên về `int` (và số lẻ về `float`) khi tuần tự hóa JSON |
| 7. Commit và xác nhận | Bản sửa nằm trong [563075f](https://github.com/dkhoa05/cdtn1-trandangkhoa-L5/commit/563075f), được sửa trước lần commit đầu của module API nên không có bản "FAIL trước". Chạy lại curl cho `"unit_price":120000` là số. Test hồi quy bổ sung ở [1c86910](https://github.com/dkhoa05/cdtn1-trandangkhoa-L5/commit/1c86910) (`test_api_chi_tiet_linh_kien_gia_la_so_...`, PASS) |

## BUG-004. Thông báo trạng thái rỗng dùng chung một câu

| Dòng | Nội dung |
|---|---|
| 1. Mã và mức độ | BUG-004, Minor |
| 2. Phát hiện bởi | Kiểm tra giao diện theo yêu cầu "phân biệt chưa có dữ liệu và bộ lọc không ra kết quả" của mục S4 ở đề Bài tập 2 |
| 3. Triệu chứng | Tìm một từ khóa không tồn tại ở màn hình Danh mục vẫn hiện câu "Kho trung tâm chưa có linh kiện nào" |
| 4. Cách tái lập | Mở `#/catalog`, gõ `zzz` vào ô tìm và bấm Tìm |
| 5. Nguyên nhân | `DataState` nhận `noiDungRong` là chuỗi cố định, được tính một lần lúc khởi tạo khi bộ lọc còn rỗng |
| 6. Cách sửa | Cho `noiDungRong` nhận một hàm, `DataState` gọi hàm mỗi lần hiển thị; ba màn hình truyền hàm dựa trên bộ lọc hiện tại |
| 7. Commit và xác nhận | Bản sửa nằm trong [dfe551d](https://github.com/dkhoa05/cdtn1-trandangkhoa-L5/commit/dfe551d) (`web/src/components/DataState.js`). Ảnh xác nhận: `docs/export/e2e-m1-trang-thai-rong.png` |

## BUG-006. Nhập kho với số lượng quá lớn trả 500

| Dòng | Nội dung |
|---|---|
| 1. Mã và mức độ | BUG-006, Major, một đầu vào sai của người dùng làm lộ lỗi nội bộ thay vì bị từ chối đúng cách (mục C7 của đề Bài tập 2) |
| 2. Phát hiện bởi | Test case TC-08 trong `docs/test-report.md` (FAIL ở lần chạy ngày 05/11/2026) |
| 3. Triệu chứng | `POST /api/parts/1/stock-in` với `quantity` = 100000000000 trả HTTP 500 với mã `INTERNAL_ERROR` thay vì 400 nêu trường `quantity`; tồn kho không bị thay đổi |
| 4. Cách tái lập | Khi hệ thống đang chạy ở commit `b6353fe` (ngay trước bản sửa), chạy `python tests/tc_api.py TC-08` và nhận HTTP 500. Hai test hồi quy của bản sửa cũng FAIL ở commit này: `pytest tests/test_api.py` báo 2 failed, 15 passed |
| 5. Nguyên nhân | `validators.nhap_kho` chỉ kiểm `quantity` lớn hơn 0 mà không có cận trên theo kiểu cột `INT` (2147483647). Giá trị 100000000000 lọt qua validator tới câu `UPDATE`, PostgreSQL ném `psycopg.errors.NumericValueOutOfRange` (lớp `psycopg.DataError`), không có trình xử lý nào cho lớp lỗi này nên rơi vào trình xử lý `Exception` chung và trả 500 |
| 6. Cách sửa | Thêm cận trên `MAX_INT` và `MAX_GIA` vào `src/validators/stock.py` cho `quantity`, `min_threshold` và `unit_price`, để dữ liệu sai bị từ chối ngay ở validator với tên trường. Thêm `errorhandler(psycopg.DataError)` trong `src/app.py` làm lớp chặn cuối: trả 400 `VALIDATION_FAILED`, chi tiết kiểu dữ liệu chỉ ghi log, không đưa ra người gọi |
| 7. Commit và xác nhận | Sửa kèm hai test hồi quy: [ec44f38](https://github.com/dkhoa05/cdtn1-trandangkhoa-L5/commit/ec44f38). Xác nhận ngày 09/11/2026: chạy lại TC-08 trên Docker (`healthy`) cho HTTP 400, `VALIDATION_FAILED`, trường `quantity` "Số lượng nhập tối đa là 2147483647", tồn 40 sang 40; hai test hồi quy PASS |
