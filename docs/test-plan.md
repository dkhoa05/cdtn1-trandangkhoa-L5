# Test Plan rút gọn: Luồng L5, Kho linh kiện thay thế (Track SE)

## 1. Phạm vi kiểm thử và phần chủ ý không kiểm

Được kiểm:

- QT-09: không xuất vượt tồn; cảnh báo khi tồn xuống dưới ngưỡng.
- QT-13: xóa mềm linh kiện, không xóa vật lý.
- QT-14: mọi truy cập giới hạn trong trung tâm của người dùng (NFR3).
- Phân quyền theo vai trò ở mục 2 của SRS: nhập kho chỉ dành cho quản lý trung tâm.
- NFR2: trừ tồn và ghi giao dịch cùng thành công hoặc cùng không xảy ra.
- Dữ liệu vào sai bị từ chối đúng mã; chạy lại `db_init` không nhân đôi dữ liệu.

Chủ ý không kiểm, kèm lý do:

- Giao diện: không có quy tắc nghiệp vụ riêng, máy chủ mới là nơi chặn. Ba trạng thái màn hình đã có minh chứng ở Bài tập 2.
- Hiệu năng dưới tải: thuộc Chuyên đề tốt nghiệp 2.

## 2. Loại test và số lượng mỗi tầng

Tổng 12 test case: 6 unit tầng service (repository giả), 3 integration (PostgreSQL thật), 3 API qua HTTP trên hệ thống chạy thật.

Kỹ thuật chọn dữ liệu: phân vùng tương đương cho số lượng (hợp lệ, không hợp lệ, vượt giới hạn cột); giá trị biên cho QT-09 ở hai bên ranh giới "bằng tồn". Với tồn 5: xuất 5 được phép, xuất 6 bị từ chối.

| Mã | Loại | Tầng | Quy tắc | Nội dung | Cách chạy |
|---|---|---|---|---|---|
| TC-01 | Luồng đúng | Unit | QT-09 | Xuất 2 khi tồn 5: tồn còn 3, có một giao dịch XUAT | `test_xuat_du_ton_thi_giam_ton_va_ghi_giao_dich` |
| TC-02 | Luồng đúng | API | QT-14 | Kỹ thuật viên tra cứu kho trung tâm mình: 200, có dữ liệu | `curl GET /api/parts` |
| TC-03 | Luồng đúng | Unit | QT-13 | Ngừng linh kiện không còn tồn: dòng vẫn còn, `is_active` là false | `test_linh_kien_khong_con_ton_thi_ngung_mem_va_khong_xoa_vat_ly` |
| TC-04 | Luồng đúng | Unit | Vai trò | Quản lý nhập 10 khi tồn 5: tồn mới 15, có giao dịch NHAP | `test_quan_ly_nhap_kho_thi_tang_ton` |
| TC-05 | Giá trị biên | Unit | QT-09 | Xuất đúng bằng tồn (5): cho phép, tồn về 0, có cảnh báo | `test_xuat_dung_bang_ton_thi_cho_xuat_ton_ve_0_va_canh_bao` |
| TC-06 | Giá trị biên | Unit | QT-09 | Xuất 6 khi tồn 5: `INSUFFICIENT_STOCK`, tồn không đổi, không có giao dịch | `test_xuat_vuot_ton_dung_1_don_vi_thi_bi_tu_choi_va_khong_tru_ton` |
| TC-07 | Dữ liệu sai | API | Validator | Số lượng xuất là 0: 400, `VALIDATION_FAILED`, thông báo nêu trường `quantity` | `curl POST /api/tickets/{id}/parts` |
| TC-08 | Dữ liệu sai | API | Validator | Số lượng nhập 100000000000 vượt giới hạn cột: 400 nêu trường `quantity`, tồn không đổi | `curl POST /api/parts/{id}/stock-in` |
| TC-09 | Bảo mật (A01) | Unit | QT-14 | Người dùng trung tâm khác xuất cho phiếu không thuộc trung tâm mình: `FORBIDDEN`, tồn không đổi | `test_xuat_cho_phieu_cua_trung_tam_khac_bi_chan` |
| TC-10 | Tái lập | Integration | C8 | Chạy `python -m src.db_init` lần hai: không lỗi, số dòng sáu bảng không đổi | `docker compose exec app python -m src.db_init` |
| TC-11 | Luồng ngoại lệ | Integration | NFR2 | Ngắt lỗi sau khi trừ tồn 1.000 lần: tồn không đổi, không có giao dịch XUAT | `test_ngat_loi_giua_chung_khong_de_ton_kho_lech_voi_log` |
| TC-12 | Luồng ngoại lệ | Integration | NFR2 | Tám luồng cùng xuất khi còn 1: đúng một luồng thành công, tồn về 0 | `test_nhieu_giao_dich_xuat_dong_thoi_chi_mot_thanh_cong` |

Kiểm thử được coi là đủ khi bốn quy tắc đều có test luồng đúng, QT-09 có hai test biên, và có đủ test dữ liệu sai, bảo mật, tái lập.

## 3. Tiêu chí thành công đo được

- 12/12 test case có kết quả thực tế và ảnh chụp trong `docs/screenshots/`.
- Mỗi quy tắc ở mục 1 có ít nhất một test luồng đúng PASS.
- `pytest -q` chạy một lệnh, toàn bộ PASS sau khi đã sửa bug.
- Không còn bug Critical đang mở; bug Major chưa sửa phải ghi lý do và hướng xử lý.
- Phép thử máy trắng: từ thư mục trống, tối đa hai lệnh, mọi dịch vụ ở trạng thái `healthy`.

## 4. Môi trường và dữ liệu thử

- Test unit: chạy bằng `pytest` trên Python 3.10 trở lên, không cần cơ sở dữ liệu. Dữ liệu do `tests/conftest.py` dựng trong bộ nhớ (linh kiện 45 tại trung tâm 1, tồn 5, ngưỡng 3).
- Test integration TC-11, TC-12: chạy bằng `RUN_PG_TESTS=1` trên PostgreSQL thật đã chạy `db_init`. Mỗi test tự tạo linh kiện riêng và xóa hẳn khi xong.
- Test API và TC-10: chạy trên hệ thống dựng bằng `docker compose up -d --build`, dữ liệu mẫu do `seeds/001_demo.sql` nạp tự động. Dựng lại từ trạng thái sạch bằng `docker compose down -v` trước mỗi đợt chạy.
- Tài khoản mẫu: `2` là kỹ thuật viên trung tâm 4, `101` là quản lý trung tâm 1.
