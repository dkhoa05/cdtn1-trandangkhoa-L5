# Test Report: Luồng L5, Kho linh kiện thay thế (Track SE)

Lần chạy: 05/11/2026, trên máy sinh viên. Kết quả: 12 test case đã chạy, 11 PASS, 1 FAIL (TC-08). Ảnh chụp nằm ở `docs/screenshots/`.

| Mã | Tiền điều kiện | Các bước | Dữ liệu thử | Kết quả mong đợi | Ưu tiên | Kết quả thực tế | P/F |
|---|---|---|---|---|---|---|---|
| TC-01 | Repository giả: linh kiện 45, trung tâm 1, tồn 5; phiếu 231 đang xử lý | Kỹ thuật viên gọi `xuat_linh_kien` | ticket 231, part 45, quantity 2 | Tồn còn 3; một giao dịch XUAT gắn phiếu 231 | Cao | Test `test_xuat_du_ton_thi_giam_ton_va_ghi_giao_dich` PASSED | PASS |
| TC-02 | Docker `healthy`, dữ liệu mẫu đã nạp | `python tests/tc_api.py TC-02` | user 2 (trung tâm 4), `GET /api/parts?size=1` | 200, có dữ liệu của trung tâm mình | Cao | HTTP 200, `total` = 128 | PASS |
| TC-03 | Repository giả: linh kiện mới, không có tồn | Quản lý tạo rồi ngừng linh kiện; đọc lại | part_code `LK-NEW-2` | Dòng vẫn còn, `is_active` false; đọc lại báo `PART_NOT_FOUND` | Cao | Test `test_linh_kien_khong_con_ton_thi_ngung_mem_va_khong_xoa_vat_ly` PASSED | PASS |
| TC-04 | Repository giả: linh kiện 45, tồn 5 | Quản lý gọi `nhap_kho` | part 45, trung tâm 1, quantity 10 | Tồn mới 15; có giao dịch NHAP | Cao | Test `test_quan_ly_nhap_kho_thi_tang_ton` PASSED | PASS |
| TC-05 | Repository giả: tồn 5, ngưỡng 3 | Kỹ thuật viên xuất đúng bằng tồn | quantity 5 | Cho phép, tồn về 0, `low_stock_alert` true | Cao | Test `test_xuat_dung_bang_ton_thi_cho_xuat_ton_ve_0_va_canh_bao` PASSED | PASS |
| TC-06 | Repository giả: tồn 5 | Kỹ thuật viên xuất vượt 1 đơn vị | quantity 6 | `INSUFFICIENT_STOCK`; tồn vẫn 5; không có giao dịch | Cao | Test `test_xuat_vuot_ton_dung_1_don_vi_thi_bi_tu_choi_va_khong_tru_ton` PASSED | PASS |
| TC-07 | Docker `healthy`, dữ liệu mẫu đã nạp | `python tests/tc_api.py TC-07` | user 2, phiếu 51, part 64, quantity 0 | 400, `VALIDATION_FAILED`, nêu trường `quantity` | Cao | HTTP 400, `VALIDATION_FAILED`, `quantity`: "Phải là số nguyên dương" | PASS |
| TC-08 | Docker `healthy`; part 1 trung tâm 1 tồn 40 | `python tests/tc_api.py TC-08` | user 101, part 1, quantity 100000000000 | 400, nêu trường `quantity`, tồn không đổi | Trung bình | HTTP 500, `INTERNAL_ERROR`; tồn 40 -> 40. Ghi ở BUG-006 | FAIL |
| TC-09 | Repository giả: phiếu 231 thuộc trung tâm 1 | Người dùng trung tâm 5 xuất cho phiếu 231 | user trung tâm 5, quantity 1 | `FORBIDDEN`; tồn vẫn 5 | Cao | Test `test_xuat_cho_phieu_cua_trung_tam_khac_bi_chan` PASSED | PASS |
| TC-10 | Docker `healthy`, `db_init` đã chạy khi khởi động | `docker compose exec app python -m src.db_init` | Không | Không lỗi; số dòng không đổi | Cao | Không lỗi; 6, 44, 180, 717, 874, 387 dòng | PASS |
| TC-11 | PostgreSQL thật đã chạy `db_init`; `RUN_PG_TESTS=1` | Ép lỗi sau khi trừ tồn, lặp 1.000 lần | Tồn 5, xuất 1 mỗi lần | Tồn vẫn 5; không có giao dịch XUAT | Cao | Test `test_ngat_loi_giua_chung_khong_de_ton_kho_lech_voi_log` PASSED | PASS |
| TC-12 | PostgreSQL thật đã chạy `db_init`; `RUN_PG_TESTS=1` | Tám luồng cùng xuất | Tồn 1, xuất 1 mỗi luồng | Đúng một luồng thành công; tồn 0; một giao dịch XUAT | Cao | Test `test_nhieu_giao_dich_xuat_dong_thoi_chi_mot_thanh_cong` PASSED | PASS |

Chạy lại TC-08 ngày 09/11/2026 sau bản sửa `ec44f38` (BUG-006), trên Docker `healthy`: HTTP 400, `VALIDATION_FAILED`, trường `quantity` "Số lượng nhập tối đa là 2147483647", tồn 40 -> 40, kết quả PASS. Dòng TC-08 ở bảng giữ nguyên kết quả của lần chạy đầu để truy vết bug.

Ảnh: TC-01, 03, 04, 05, 06, 09 ở `TC-01-03-04-05-06-09.png`; TC-02, 07 ở `TC-02-07.png`; TC-08 ở `TC-08.png`; TC-10 ở `TC-10.png`; TC-11, 12 ở `TC-11-12.png`.
