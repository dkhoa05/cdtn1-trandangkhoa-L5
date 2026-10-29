"""Tầng 2: toàn bộ quy tắc nghiệp vụ kho. Không biết gì về HTTP hay SQL.

Nhận `unit_of_work` (hàm trả về context manager cấp bộ repository trong MỘT
transaction) qua constructor, nên test được bằng đối tượng giả, không cần CSDL.
"""
from src.errors import AppError

VAI_TRO_QUAN_LY = 'QUAN_LY_TT'
TRANG_THAI_DANG_XU_LY = 'DANG_XU_LY'


class StockService:
    def __init__(self, unit_of_work):
        self.uow = unit_of_work

    # ---- đăng nhập ----
    def lay_nguoi_dung(self, user_id):
        """Đọc người dùng đang đăng nhập và xác nhận còn hoạt động.

        Nhận: user_id: số nguyên dương lấy từ token.
        Trả: dict người dùng: user_id, full_name, role, center_id, center_name, is_active.
        Lỗi: UNAUTHORIZED khi không có người dùng hoặc đã ngừng hoạt động.
        """
        with self.uow() as r:
            user = r.users.lay_nguoi_dung(user_id)
        if not user or not user['is_active']:
            raise AppError('UNAUTHORIZED', 'Phiên đăng nhập không hợp lệ hoặc đã hết hạn')
        return user

    @staticmethod
    def _chi_quan_ly(user, viec):
        if user['role'] != VAI_TRO_QUAN_LY:
            raise AppError('FORBIDDEN', f'Chỉ quản lý trung tâm được {viec}')

    # ---- QT-14: mọi truy cập bị giới hạn trong trung tâm của người dùng ----
    @staticmethod
    def _trung_tam(user, center_id):
        if center_id is not None and center_id != user['center_id']:
            raise AppError('FORBIDDEN', 'Bạn chỉ thao tác được trên dữ liệu của trung tâm mình')
        return user['center_id']

    @staticmethod
    def _trang(rows, total, page, size):
        return {'data': rows, 'page': page, 'size': size, 'total': total}

    # ---- FR1, FR6 ----
    def tim_linh_kien(self, user, center_id, q, page, size, trang_thai='all', sap_xep='code'):
        """Tra cứu tồn kho linh kiện của trung tâm, theo mã hoặc tên, có thể chỉ lấy dưới ngưỡng (FR1, FR6, QT-14).

        Nhận: user; center_id: None hoặc trung tâm của user; q: từ khóa hoặc None; page, size: phân trang; trang_thai: all, low, out hoặc ok; sap_xep: code, name, qty_asc hoặc qty_desc.
        Trả: dict {data, page, size, total}; data rỗng khi không có linh kiện khớp (không phải lỗi).
        Lỗi: FORBIDDEN khi center_id khác trung tâm của user.
        """
        trung_tam = self._trung_tam(user, center_id)
        with self.uow() as r:
            rows, total = r.parts.tim_linh_kien_trong_kho(
                trung_tam, q, trang_thai, sap_xep, size, (page - 1) * size)
        return self._trang(rows, total, page, size)

    # ---- FR2, FR3, FR4: xuất linh kiện cho phiếu (QT-09) ----
    def xuat_linh_kien(self, user, ticket_id, part_id, quantity):
        """Xuất linh kiện cho một phiếu đang xử lý, trừ tồn và ghi giao dịch trong một transaction (QT-09, QT-14).

        Nhận: user; ticket_id, part_id: số nguyên dương; quantity: số nguyên dương.
        Trả: dict kết quả xuất: remaining_stock là tồn còn lại, low_stock_alert là True khi tồn thấp hơn ngưỡng.
        Lỗi: TICKET_NOT_FOUND, FORBIDDEN (phiếu của trung tâm khác), TICKET_NOT_PROCESSING, PART_NOT_FOUND, INSUFFICIENT_STOCK khi quantity lớn hơn tồn (không trừ tồn).
        """
        with self.uow() as r:
            phieu = r.tickets.lay_phieu(ticket_id)
            if not phieu:
                raise AppError('TICKET_NOT_FOUND', f'Không tìm thấy phiếu {ticket_id}')
            self._trung_tam(user, phieu['center_id'])
            if phieu['status'] != TRANG_THAI_DANG_XU_LY:
                raise AppError('TICKET_NOT_PROCESSING',
                               f"Phiếu {phieu['ticket_code']} không ở trạng thái đang xử lý")
            # Khóa dòng tồn kho: hai lần xuất đồng thời không cùng đọc một số tồn (NFR2).
            ton = r.stock.khoa_dong_ton_kho(user['center_id'], part_id)
            if not ton:
                raise AppError('PART_NOT_FOUND', 'Không tìm thấy linh kiện tại trung tâm này')
            if quantity > ton['quantity']:
                raise AppError('INSUFFICIENT_STOCK',
                               f"Vượt quá tồn kho: còn {ton['quantity']}, yêu cầu xuất {quantity}")
            con_lai = ton['quantity'] - quantity
            r.stock.ghi_ton_moi(user['center_id'], part_id, con_lai)
            gd = r.txns.ghi_giao_dich(user['center_id'], part_id, 'XUAT', quantity,
                             ticket_id, user['user_id'])
        return {
            'transaction_id': gd['transaction_id'], 'ticket_id': ticket_id, 'part_id': part_id,
            'quantity': quantity, 'remaining_stock': con_lai,
            'low_stock_alert': con_lai < ton['min_threshold'],   # UC6, UC7
            'created_at': gd['created_at'],
        }

    # ---- FR5: nhập kho, chỉ quản lý trung tâm ----
    def nhap_kho(self, user, part_id, center_id, quantity):
        """Ghi nhận nhập kho cho một linh kiện, cộng tồn và ghi giao dịch NHAP (FR5, chỉ quản lý trung tâm).

        Nhận: user; part_id; center_id: trung tâm của user; quantity: số nguyên dương.
        Trả: dict kết quả nhập: new_stock là tồn mới.
        Lỗi: FORBIDDEN khi không phải quản lý hoặc khác trung tâm; PART_NOT_FOUND khi linh kiện không có trong kho.
        """
        self._chi_quan_ly(user, 'ghi nhận nhập kho')
        trung_tam = self._trung_tam(user, center_id)
        with self.uow() as r:
            ton = r.stock.khoa_dong_ton_kho(trung_tam, part_id)
            if not ton:
                raise AppError('PART_NOT_FOUND', 'Không tìm thấy linh kiện tại trung tâm này')
            moi = ton['quantity'] + quantity
            r.stock.ghi_ton_moi(trung_tam, part_id, moi)
            gd = r.txns.ghi_giao_dich(trung_tam, part_id, 'NHAP', quantity, None, user['user_id'])
        return {'transaction_id': gd['transaction_id'], 'part_id': part_id,
                'center_id': trung_tam, 'quantity': quantity, 'new_stock': moi,
                'created_at': gd['created_at']}

    # ---- FR7 ----
    def lich_su(self, user, part_id, center_id, page, size):
        """Liệt kê giao dịch nhập xuất của một linh kiện, mới nhất trước (FR7, chỉ quản lý trung tâm).

        Nhận: user; part_id; center_id: None hoặc trung tâm của user; page, size.
        Trả: dict {data, page, size, total}; data rỗng khi linh kiện chưa có giao dịch.
        Lỗi: FORBIDDEN khi không phải quản lý hoặc khác trung tâm.
        """
        self._chi_quan_ly(user, 'xem lịch sử nhập–xuất')
        trung_tam = self._trung_tam(user, center_id)
        with self.uow() as r:
            rows, total = r.txns.lich_su(trung_tam, part_id, size, (page - 1) * size)
        return self._trang(rows, total, page, size)

    def tong_hop(self, user, part_id, center_id, tu_ngay, den_ngay):
        """Tính tổng nhập, tổng xuất của một linh kiện trong khoảng ngày, gồm cả hai đầu mút (FR7).

        Nhận: user; part_id; center_id; tu_ngay, den_ngay: date với tu_ngay <= den_ngay.
        Trả: dict: total_in, total_out, net_change = total_in - total_out (có thể âm); 0 khi không có giao dịch.
        Lỗi: FORBIDDEN khi không phải quản lý hoặc khác trung tâm.
        """
        self._chi_quan_ly(user, 'xem lịch sử nhập–xuất')
        trung_tam = self._trung_tam(user, center_id)
        with self.uow() as r:
            tong_nhap, tong_xuat = r.txns.tong_hop(trung_tam, part_id, tu_ngay, den_ngay)
        return {'part_id': part_id, 'center_id': trung_tam,
                'from': tu_ngay.isoformat(), 'to': den_ngay.isoformat(),
                'total_in': tong_nhap, 'total_out': tong_xuat,
                'net_change': tong_nhap - tong_xuat}

    # ---- phục vụ màn hình M2 ----
    def ds_phieu(self, user, trang_thai, page, size):
        """Liệt kê phiếu bảo hành của trung tâm người dùng, lọc theo trạng thái (phục vụ chọn phiếu ở M2).

        Nhận: user; trang_thai: chuỗi trạng thái hoặc None; page, size.
        Trả: dict {data, page, size, total}; data rỗng khi không có phiếu khớp.
        Lỗi: Không ném lỗi nghiệp vụ; chỉ lỗi hạ tầng (mất kết nối CSDL) nổi lên để route xử lý.
        """
        with self.uow() as r:
            rows, total = r.tickets.danh_sach_phieu(user['center_id'], trang_thai, size, (page - 1) * size)
        return self._trang(rows, total, page, size)

    def linh_kien_cua_phieu(self, user, ticket_id):
        """Liệt kê linh kiện đã xuất cho một phiếu (AC2.2, QT-14).

        Nhận: user; ticket_id: số nguyên dương.
        Trả: dict {ticket, data}; data rỗng khi phiếu chưa xuất linh kiện nào.
        Lỗi: TICKET_NOT_FOUND; FORBIDDEN khi phiếu của trung tâm khác.
        """
        with self.uow() as r:
            phieu = r.tickets.lay_phieu(ticket_id)
            if not phieu:
                raise AppError('TICKET_NOT_FOUND', f'Không tìm thấy phiếu {ticket_id}')
            self._trung_tam(user, phieu['center_id'])
            return {'ticket': phieu, 'data': r.txns.giao_dich_cua_phieu(ticket_id)}

    # ---- CRUD danh mục linh kiện (xóa mềm, QT-13) ----
    def lay_linh_kien(self, user, part_id):
        """Đọc một linh kiện còn hoạt động kèm tồn kho tại trung tâm của người dùng.

        Nhận: user; part_id: số nguyên dương.
        Trả: dict linh kiện; khóa stock là None khi chưa có trong kho trung tâm (khác với tồn bằng 0).
        Lỗi: PART_NOT_FOUND khi linh kiện không tồn tại hoặc đã ngừng sử dụng.
        """
        with self.uow() as r:
            part = r.parts.lay_linh_kien(part_id)
            if not part:
                raise AppError('PART_NOT_FOUND', f'Không tìm thấy linh kiện {part_id}')
            ton = r.stock.lay_ton(user['center_id'], part_id)
        return {**part, 'stock': ton if ton and ton['is_active'] else None}

    def tao_linh_kien(self, user, part_code, part_name, unit_price):
        """Tạo linh kiện mới trong danh mục (chỉ quản lý trung tâm).

        Nhận: user; part_code: mã duy nhất; part_name; unit_price: đồng Việt Nam, số nguyên >= 0.
        Trả: dict linh kiện vừa tạo, chưa có trong kho của trung tâm nào.
        Lỗi: FORBIDDEN khi không phải quản lý; PART_CODE_EXISTS khi trùng mã.
        """
        self._chi_quan_ly(user, 'thêm linh kiện')
        with self.uow() as r:
            if r.parts.tim_theo_ma(part_code):
                raise AppError('PART_CODE_EXISTS', f'Mã linh kiện {part_code} đã tồn tại')
            return r.parts.tao_linh_kien(part_code, part_name, unit_price)

    def sua_linh_kien(self, user, part_id, part_name, unit_price):
        """Sửa tên và đơn giá của linh kiện, không đổi mã (chỉ quản lý trung tâm).

        Nhận: user; part_id; part_name; unit_price.
        Trả: dict linh kiện sau khi sửa.
        Lỗi: FORBIDDEN khi không phải quản lý; PART_NOT_FOUND.
        """
        self._chi_quan_ly(user, 'sửa linh kiện')
        with self.uow() as r:
            if not r.parts.lay_linh_kien(part_id):
                raise AppError('PART_NOT_FOUND', f'Không tìm thấy linh kiện {part_id}')
            return r.parts.cap_nhat_linh_kien(part_id, part_name, unit_price)

    def ngung_linh_kien(self, user, part_id):
        """Ngừng sử dụng linh kiện bằng xóa mềm, giữ nguyên lịch sử giao dịch (QT-13).

        Nhận: user (quản lý trung tâm); part_id.
        Trả: dict {part_id, is_active: False}.
        Lỗi: FORBIDDEN; PART_NOT_FOUND; PART_HAS_STOCK khi còn trung tâm giữ tồn lớn hơn 0.
        """
        self._chi_quan_ly(user, 'ngừng linh kiện')
        with self.uow() as r:
            if not r.parts.lay_linh_kien(part_id):
                raise AppError('PART_NOT_FOUND', f'Không tìm thấy linh kiện {part_id}')
            if r.parts.co_ton_kho(part_id):
                raise AppError('PART_HAS_STOCK',
                               'Linh kiện vẫn còn tồn kho ở trung tâm, chưa thể ngừng sử dụng')
            r.parts.ngung_su_dung_linh_kien(part_id)
        return {'part_id': part_id, 'is_active': False}

    # ---- CRUD tồn kho của trung tâm ----
    def them_vao_kho(self, user, part_id, min_threshold):
        """Đưa linh kiện vào kho trung tâm với tồn bắt đầu bằng 0; tồn chỉ đổi qua giao dịch nhập, xuất.

        Nhận: user (quản lý trung tâm); part_id; min_threshold: số nguyên >= 0.
        Trả: dict dòng tồn kho: quantity = 0 (hoặc tồn cũ khi kích hoạt lại).
        Lỗi: FORBIDDEN; PART_NOT_FOUND; STOCK_EXISTS khi linh kiện đã có trong kho.
        """
        self._chi_quan_ly(user, 'thêm linh kiện vào kho')
        with self.uow() as r:
            if not r.parts.lay_linh_kien(part_id):
                raise AppError('PART_NOT_FOUND', f'Không tìm thấy linh kiện {part_id}')
            ton = r.stock.lay_ton(user['center_id'], part_id)
            if ton and ton['is_active']:
                raise AppError('STOCK_EXISTS', 'Linh kiện đã có trong kho trung tâm này')
            r.stock.them_vao_kho(user['center_id'], part_id, min_threshold)
            ton = r.stock.lay_ton(user['center_id'], part_id)
        return {'part_id': part_id, 'center_id': user['center_id'],
                'quantity': ton['quantity'], 'min_threshold': min_threshold}

    def doi_nguong(self, user, part_id, min_threshold):
        """Đổi ngưỡng cảnh báo của linh kiện trong kho trung tâm.

        Nhận: user (quản lý trung tâm); part_id; min_threshold: số nguyên >= 0.
        Trả: dict dòng tồn kho với ngưỡng mới.
        Lỗi: FORBIDDEN; PART_NOT_FOUND khi linh kiện không có trong kho.
        """
        self._chi_quan_ly(user, 'đổi ngưỡng cảnh báo')
        with self.uow() as r:
            ton = r.stock.khoa_dong_ton_kho(user['center_id'], part_id)
            if not ton:
                raise AppError('PART_NOT_FOUND', 'Không tìm thấy linh kiện tại trung tâm này')
            r.stock.dat_nguong(user['center_id'], part_id, min_threshold)
        return {'part_id': part_id, 'center_id': user['center_id'],
                'quantity': ton['quantity'], 'min_threshold': min_threshold}

    def ngung_ton_kho(self, user, part_id):
        """Gỡ linh kiện khỏi kho trung tâm bằng xóa mềm, chỉ khi tồn đã về 0 (QT-13).

        Nhận: user (quản lý trung tâm); part_id.
        Trả: dict {part_id, center_id, is_active: False}.
        Lỗi: FORBIDDEN; PART_NOT_FOUND; STOCK_NOT_EMPTY khi tồn lớn hơn 0.
        """
        self._chi_quan_ly(user, 'gỡ linh kiện khỏi kho')
        with self.uow() as r:
            ton = r.stock.khoa_dong_ton_kho(user['center_id'], part_id)
            if not ton:
                raise AppError('PART_NOT_FOUND', 'Không tìm thấy linh kiện tại trung tâm này')
            if ton['quantity'] > 0:
                raise AppError('STOCK_NOT_EMPTY',
                               f"Kho còn {ton['quantity']} linh kiện, chưa thể gỡ")
            r.stock.ngung_su_dung_ton_kho(user['center_id'], part_id)
        return {'part_id': part_id, 'center_id': user['center_id'], 'is_active': False}
