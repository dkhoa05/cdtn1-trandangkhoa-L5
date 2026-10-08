# SRS rút gọn: Quản lý kho linh kiện thay thế cho trung tâm bảo hành

Sinh viên: Trần Đăng Khoa – 2374802010240 – Track SE
Luồng nghiệp vụ: L5 – Kho linh kiện thay thế
Case study: Smart CRM – Mekong Mobile

## 1. Giới thiệu và phạm vi

**Bối cảnh:** Mekong Mobile có 6 trung tâm bảo hành, mỗi trung tâm tự quản lý tồn kho linh kiện
bằng sổ giấy, cộng dồn cuối ngày và thường lệch với thực tế 3–8% (vấn đề V6). Kỹ thuật viên
nhận phiếu sửa chữa rồi mới phát hiện hết linh kiện, phải hẹn lại khách, khoảng 20
lần mỗi tháng.

**Phạm vi:** Quản lý tồn kho linh kiện theo từng trung tâm bảo hành: kỹ thuật viên xuất
linh kiện cho phiếu sửa chữa trong giới hạn tồn kho hiện có, hệ thống cảnh báo khi tồn xuống
dưới ngưỡng, và quản lý trung tâm ghi nhận nhập kho.

**Không làm (WON'T):**
- Không dự báo nhu cầu linh kiện hoặc gợi ý số lượng đặt hàng.
- Không tích hợp đặt hàng tự động với nhà cung cấp.
- Không quản lý giá nhập/giá bán linh kiện theo thời gian (chỉ có đơn giá hiện hành).

**Thuật ngữ:**

| Thuật ngữ | Định nghĩa | Tên kỹ thuật |
|---|---|---|
| Linh kiện | Bộ phận thay thế dùng trong sửa chữa, có mã và tồn kho theo trung tâm | part |
| Tồn kho | Số lượng linh kiện hiện có tại một trung tâm | part_stock |
| Giao dịch kho | Một lần nhập hoặc xuất linh kiện, gắn với trung tâm | part_transaction |
| Phiếu bảo hành | Yêu cầu sửa chữa đang được xử lý, có thể gắn với giao dịch xuất linh kiện | ticket |
| Ngưỡng cảnh báo | Mức tồn tối thiểu, dưới mức này hệ thống phải cảnh báo | min_threshold |
| Trung tâm bảo hành | Nơi giữ tồn kho; mỗi người dùng thuộc đúng một trung tâm | service_center |
| Người dùng | Kỹ thuật viên hoặc quản lý trung tâm thực hiện giao dịch kho | app_user |

## 2. Các bên liên quan và vai trò

| Vai trò | Làm được | Không được làm |
|---|---|---|
| Kỹ thuật viên | Tra cứu tồn kho, xuất linh kiện cho phiếu mình xử lý, tìm kiếm linh kiện | Nhập kho, xem tồn kho trung tâm khác |
| Quản lý trung tâm | Tất cả quyền của kỹ thuật viên + ghi nhận nhập kho, xem cảnh báo, xem lịch sử nhập–xuất | Sửa/xóa giao dịch đã ghi nhận (chỉ soft-delete theo QT-13) |

## 3. Yêu cầu chức năng

| Mã | Yêu cầu chức năng | User Story | MoSCoW |
|---|---|---|---|
| FR1 | Hệ thống cho phép tra cứu tồn kho linh kiện theo mã hoặc tên, giới hạn trong trung tâm của người dùng | US1 | MUST |
| FR2 | Hệ thống cho phép ghi nhận xuất linh kiện cho một phiếu bảo hành cụ thể | US2 | MUST |
| FR3 | Hệ thống từ chối giao dịch xuất nếu số lượng vượt quá tồn kho hiện tại (QT-09) | US3 | MUST |
| FR4 | Hệ thống cảnh báo khi tồn kho một linh kiện xuống dưới ngưỡng cảnh báo | US4 | SHOULD |
| FR5 | Hệ thống cho phép ghi nhận nhập kho linh kiện mới | US5 | SHOULD |
| FR6 | Hệ thống hiển thị danh sách linh kiện đang dưới ngưỡng cảnh báo theo trung tâm | US6 | SHOULD |
| FR7 | Hệ thống hiển thị lịch sử chi tiết từng giao dịch nhập–xuất của một linh kiện theo thời gian | US7 | COULD |
| FR8 | Hệ thống hiển thị số liệu tổng hợp (tổng nhập, tổng xuất cộng dồn) của linh kiện theo khoảng thời gian | US8 | COULD |

### User Story chi tiết

**US1 (MUST)** Là kỹ thuật viên, tôi muốn tra cứu tồn kho linh kiện của trung tâm mình để biết
linh kiện có sẵn trước khi nhận sửa.
- AC1.1 GIVEN linh kiện "Màn hình iPhone 13" còn 5 trong tồn kho trung tâm Q10, WHEN kỹ thuật
  viên tìm theo mã linh kiện, THEN hệ thống hiển thị đúng số lượng tồn hiện tại.
- AC1.2 GIVEN linh kiện không tồn tại trong danh mục, WHEN kỹ thuật viên tìm theo mã không hợp
  lệ, THEN hệ thống báo "không tìm thấy linh kiện".

**US2 (MUST)** Là kỹ thuật viên, tôi muốn xuất linh kiện cho một phiếu bảo hành cụ thể để ghi
nhận linh kiện đã dùng trong sửa chữa.
- AC2.1 GIVEN phiếu đang ở trạng thái Đang xử lý và linh kiện còn đủ tồn, WHEN kỹ thuật viên
  chọn linh kiện + số lượng rồi xác nhận xuất, THEN hệ thống ghi nhận giao dịch xuất và giảm
  tồn kho tương ứng.
- AC2.2 GIVEN đã xuất linh kiện cho phiếu, WHEN xem lại phiếu, THEN danh sách linh kiện đã dùng
  hiển thị đúng với giao dịch xuất.

**US3 (MUST, QT-09)** Là kỹ thuật viên, tôi muốn hệ thống từ chối xuất linh kiện vượt quá số
lượng tồn kho hiện có để tránh sai lệch dữ liệu.
- AC3.1 GIVEN tồn kho hiện tại là 3, WHEN kỹ thuật viên nhập số lượng xuất là 5, THEN hệ thống
  từ chối giao dịch và hiển thị "vượt quá tồn kho".
- AC3.2 (NGOẠI LỆ) GIVEN tồn kho vừa đủ bằng số lượng cần xuất, WHEN kỹ thuật viên xác nhận
  xuất, THEN hệ thống cho xuất, tồn về 0, và kiểm tra luôn có dưới ngưỡng cảnh báo không.

**US4 (SHOULD)** Là quản lý trung tâm, tôi muốn nhận cảnh báo khi tồn kho một linh kiện xuống
dưới ngưỡng cảnh báo để chủ động đặt hàng bổ sung.

**US5 (SHOULD)** Là quản lý trung tâm, tôi muốn ghi nhận nhập kho linh kiện mới để cập nhật số
lượng tồn chính xác.

**US6 (SHOULD)** Là quản lý trung tâm, tôi muốn xem danh sách linh kiện đang dưới ngưỡng cảnh
báo của trung tâm mình để biết cần đặt hàng gì.

**US7 (COULD)** Là quản lý trung tâm, tôi muốn xem lịch sử chi tiết từng giao dịch nhập–xuất
của một linh kiện để đối chiếu khi có sai lệch.

**US8 (COULD)** Là quản lý trung tâm, tôi muốn xem tổng số lượng nhập và xuất của từng linh
kiện trong một khoảng thời gian để phục vụ đối chiếu tồn kho tổng hợp.

## 4. Yêu cầu phi chức năng

| Mã | Loại | Yêu cầu phi chức năng | Ngưỡng đo được |
|---|---|---|---|
| NFR1 | Hiệu năng | Tra cứu tồn kho linh kiện của một trung tâm phải trả về kết quả nhanh | Dưới 1 giây với danh sách ≤200 linh kiện/trung tâm, trên máy 8 GB RAM |
| NFR2 | Tin cậy | Giao dịch xuất/nhập linh kiện không được để lại trạng thái nửa vời khi lỗi | Mỗi giao dịch xuất/nhập được ghi theo transaction: hoặc cả (giảm/tăng tồn kho + ghi log giao dịch) cùng thành công, hoặc không cái nào được lưu |
| NFR3 | Bảo mật | Dữ liệu tồn kho chỉ hiển thị cho đúng trung tâm của người dùng (QT-14) | 100% request tra cứu/xuất/nhập bị chặn nếu center_id của linh kiện khác center_id của người dùng đăng nhập, trả về 403 |


## 5. Ràng buộc và quy tắc nghiệp vụ

- QT-09: Không được xuất linh kiện vượt quá số lượng tồn kho hiện tại của trung tâm. Khi tồn
  xuống dưới min_threshold, hệ thống phải cảnh báo.
- QT-13: Không được xóa vật lý giao dịch kho. Chỉ đánh dấu ngừng sử dụng (soft delete).
- QT-14: Nhân viên chỉ xem được dữ liệu của trung tâm mình làm việc.


## 6. Bảng truy vết yêu cầu

| Mã FR | Yêu cầu chức năng | User Story | Use Case | MoSCoW | Bảng dữ liệu | Màn hình | Test case (BT3) |
|---|---|---|---|---|---|---|---|
| FR1 | Tra cứu tồn kho linh kiện | US1 | UC1 | MUST | part, part_stock, service_center | M1 | Bổ sung ở BT3 |
| FR2 | Xuất linh kiện cho phiếu | US2 | UC2 | MUST | part_transaction, part_stock, ticket | M2 | Bổ sung ở BT3 |
| FR3 | Từ chối xuất vượt tồn (QT-09) | US3 | UC2 (ngoại lệ 4a) | MUST | part_stock (CHECK quantity ≥ 0) | M2 (lỗi 4a) | Bổ sung ở BT3 |
| FR4 | Cảnh báo dưới ngưỡng | US4 | UC7 | SHOULD | part_stock (tính quantity < min_threshold) | M2 (cảnh báo 7a) | Bổ sung ở BT3 |
| FR5 | Nhập kho linh kiện | US5 | UC3 | SHOULD | part_transaction, part_stock | M3 | Bổ sung ở BT3 |
| FR6 | Danh sách dưới ngưỡng | US6 | UC4 | SHOULD | part_stock | M1 (lọc dưới ngưỡng) | Bổ sung ở BT3 |
| FR7 | Lịch sử chi tiết nhập–xuất | US7 | UC5 | COULD | part_transaction, app_user | M3 | Bổ sung ở BT3 |
| FR8 | Tổng hợp nhập–xuất theo khoảng thời gian | US8 | UC5 (mở rộng) | COULD | part_transaction (tính SUM) | M3 | Bổ sung ở BT3 |


## Use Case Diagram

Actor: Kỹ thuật viên, Quản lý trung tâm.
Sơ đồ gốc ở docs/usecase.drawio.

UC6 (Kiểm tra ngưỡng tồn kho) và UC7 (Sinh cảnh báo tồn kho thấp) là hai use case xử lý nội bộ,
được kích hoạt gián tiếp từ UC2 (xuất linh kiện). Hai use case này không gắn actor vì không có hệ thống/
người dùng bên ngoài trực tiếp kích hoạt. Quan hệ: UC2 `<<include>>` UC6 (luôn kiểm tra sau mỗi
lần xuất, không điều kiện); UC7 `<<extend>>` UC6 (chỉ chạy khi tồn dưới ngưỡng).

### Đặc tả chi tiết UC2: Xuất linh kiện cho phiếu bảo hành

**Actor chính:** Kỹ thuật viên
**Mục tiêu:** Ghi nhận linh kiện đã dùng để sửa chữa, giảm đúng tồn kho.
**Điều kiện trước:** Kỹ thuật viên đã đăng nhập; phiếu bảo hành đang ở trạng thái Đang xử lý.
**Điều kiện sau:** Giao dịch xuất được lưu; tồn kho trung tâm giảm đúng số lượng; phiếu được
gắn linh kiện đã dùng.
**Liên quan:** US2, US3 | Mức ưu tiên: MUST

**LUỒNG CHÍNH:**
1. Kỹ thuật viên mở phiếu bảo hành đang xử lý, chọn "Xuất linh kiện".
2. Hệ thống hiển thị danh sách linh kiện và số lượng tồn hiện tại của trung tâm để kỹ thuật
   viên lựa chọn.
3. Kỹ thuật viên chọn linh kiện và nhập số lượng cần xuất.
4. Hệ thống kiểm tra số lượng xuất so với tồn kho.
5. Kỹ thuật viên xác nhận xuất.
6. Hệ thống ghi nhận giao dịch xuất, giảm tồn kho, gắn linh kiện vào phiếu.
7. Hệ thống kiểm tra tồn kho sau xuất có dưới ngưỡng cảnh báo hay không. `[include UC6]`

**LUỒNG NGOẠI LỆ:**
- **4a.** Số lượng xuất vượt quá tồn kho hiện tại → Hệ thống từ chối giao dịch, hiển thị "vượt
  quá tồn kho", không trừ tồn, giữ lại dữ liệu đã nhập để kỹ thuật viên sửa lại.
- **7a.** Nếu tồn kho sau xuất thấp hơn ngưỡng cảnh báo, UC7 – Sinh cảnh báo tồn kho thấp được
  kích hoạt (`<<extend>>` từ UC6) và hệ thống tạo cảnh báo gửi tới quản lý trung tâm.
