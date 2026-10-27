# Nhật ký lỗi (Bug Log) – Bài tập 2

Mỗi mục có bảy dòng theo mẫu của học phần. Link commit trỏ tới repo công khai `dkhoa05/cdtn1-trandangkhoa-L5`. Lỗi nào được sửa ngay trước lần commit đầu của module thì nêu rõ commit chứa bản sửa và không có commit "trước khi sửa" riêng.

## BUG-001. Mất kết nối cơ sở dữ liệu trả 500 chung chung

| Dòng | Nội dung |
|---|---|
| 1. Mã và mức độ | BUG-001, Major |
| 2. Phát hiện bởi | Kiểm thử hồi quy `test_mat_ket_noi_csdl_tra_503_kem_ma_tra_cuu` trong `tests/test_api.py`, viết theo mục "tắt một thành phần phụ" của quy trình chấm |
| 3. Triệu chứng | Khi PostgreSQL không kết nối được, `GET /api/parts` trả HTTP 500 với mã `INTERNAL_ERROR`, người gọi không phân biệt được lỗi hạ tầng với lỗi chương trình |
| 4. Cách tái lập | Chạy `pytest tests/test_api.py -k mat_ket_noi` ở commit `04238a2`: test FAIL vì nhận 500 thay vì 503 |
| 5. Nguyên nhân | `psycopg.OperationalError` do `db.connect()` ném ra không có trình xử lý riêng ở `create_app`, nên rơi vào trình xử lý `Exception` chung vốn trả 500 |
| 6. Cách sửa | Thêm `errorhandler(psycopg.OperationalError)` ở một chỗ duy nhất trong `src/app.py`: ghi ERROR một lần kèm ngăn xếp và `requestId`, trả 503 với mã `DB_UNAVAILABLE`, không lộ chi tiết kết nối. Lớp service không bắt lỗi hạ tầng |
| 7. Commit và xác nhận | Test: [04238a2](https://github.com/dkhoa05/cdtn1-trandangkhoa-L5/commit/04238a2). Sửa: [4520fc8](https://github.com/dkhoa05/cdtn1-trandangkhoa-L5/commit/4520fc8). Sau sửa test PASS, toàn bộ 32 test PASS |

## BUG-002. Mỗi request chậm khoảng 4 giây trên Windows

| Dòng | Nội dung |
|---|---|
| 1. Mã và mức độ | BUG-002, Major |
| 2. Phát hiện bởi | Chạy tay giao diện trên PostgreSQL thật; đo thời gian bằng `performance.now()` trong trình duyệt |
| 3. Triệu chứng | Danh sách linh kiện ở màn hình xuất kho hiện "Đang tải…" nhiều giây, thời gian đo được 4,1 đến 4,4 giây mỗi lần gọi API, vượt ngưỡng 1 giây của NFR1 |
| 4. Cách tái lập | Đặt `DB_HOST=localhost`, chạy `python -m src.app`, gọi `GET /api/parts` bằng `curl -w "%{time_total}"` |
| 5. Nguyên nhân | Mỗi request mở hai kết nối CSDL (xác thực người dùng và truy vấn). Tên `localhost` được thử bằng IPv6 trước trong khi máy chủ chỉ nghe IPv4, mỗi kết nối chờ hết thời gian IPv6 rồi mới chuyển sang IPv4 |
| 6. Cách sửa | Đổi giá trị mặc định trong `.env.example` sang `DB_HOST=127.0.0.1` và ghi chú trong README. Sau sửa mỗi request còn khoảng 0,3 giây |
| 7. Commit và xác nhận | [277c05e](https://github.com/dkhoa05/cdtn1-trandangkhoa-L5/commit/277c05e). Đo lại: 351 ms và 266 ms cho hai lần gọi liên tiếp |

## BUG-003. Đơn giá trả về dạng chuỗi

| Dòng | Nội dung |
|---|---|
| 1. Mã và mức độ | BUG-003, Minor |
| 2. Phát hiện bởi | Chạy kịch bản curl CRUD trên PostgreSQL thật (`docs/export/curl-crud-linh-kien.txt`) |
| 3. Triệu chứng | `unit_price` trong phản hồi là `"120000"` (chuỗi) thay vì số, giao diện phải tự ép kiểu |
| 4. Cách tái lập | `curl -XPOST /api/parts` rồi `GET /api/parts/{id}` ở phiên bản đầu của `src/app.py` |
| 5. Nguyên nhân | Cột `NUMERIC(12,0)` được psycopg trả về kiểu `Decimal`, bộ chuyển JSON mặc định của Flask quy mọi kiểu lạ về chuỗi |
| 6. Cách sửa | Trong `create_app`, đổi `Decimal` nguyên về `int` (và số lẻ về `float`) khi tuần tự hóa JSON |
| 7. Commit và xác nhận | Bản sửa nằm trong [563075f](https://github.com/dkhoa05/cdtn1-trandangkhoa-L5/commit/563075f) (sửa trước lần commit đầu của module API). Chạy lại curl cho `"unit_price":120000` là số |

## BUG-004. Thông báo trạng thái rỗng dùng chung một câu

| Dòng | Nội dung |
|---|---|
| 1. Mã và mức độ | BUG-004, Minor |
| 2. Phát hiện bởi | Kiểm tra giao diện theo yêu cầu "phân biệt chưa có dữ liệu và bộ lọc không ra kết quả" của mục S4 |
| 3. Triệu chứng | Tìm một từ khóa không tồn tại ở màn hình Danh mục vẫn hiện câu "Kho trung tâm chưa có linh kiện nào" |
| 4. Cách tái lập | Mở `#/catalog`, gõ `zzz` vào ô tìm và bấm Tìm |
| 5. Nguyên nhân | `DataState` nhận `noiDungRong` là chuỗi cố định, được tính một lần lúc khởi tạo khi bộ lọc còn rỗng |
| 6. Cách sửa | Cho `noiDungRong` nhận một hàm, `DataState` gọi hàm mỗi lần hiển thị; ba màn hình truyền hàm dựa trên bộ lọc hiện tại |
| 7. Commit và xác nhận | Bản sửa nằm trong [dfe551d](https://github.com/dkhoa05/cdtn1-trandangkhoa-L5/commit/dfe551d) (`web/src/components/DataState.js`). Ảnh xác nhận: `docs/export/e2e-m1-trang-thai-rong.png` |
