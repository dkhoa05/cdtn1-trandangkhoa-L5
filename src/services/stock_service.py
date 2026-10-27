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
        with self.uow() as r:
            user = r.users.get(user_id)
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
    def tim_linh_kien(self, user, center_id, q, page, size, chi_duoi_nguong=False):
        trung_tam = self._trung_tam(user, center_id)
        with self.uow() as r:
            rows, total = r.parts.tim(trung_tam, q, chi_duoi_nguong, size, (page - 1) * size)
        return self._trang(rows, total, page, size)

    # ---- FR2, FR3, FR4: xuất linh kiện cho phiếu (QT-09) ----
    def xuat_linh_kien(self, user, ticket_id, part_id, quantity):
        with self.uow() as r:
            phieu = r.tickets.get(ticket_id)
            if not phieu:
                raise AppError('TICKET_NOT_FOUND', f'Không tìm thấy phiếu {ticket_id}')
            self._trung_tam(user, phieu['center_id'])
            if phieu['status'] != TRANG_THAI_DANG_XU_LY:
                raise AppError('TICKET_NOT_PROCESSING',
                               f"Phiếu {phieu['ticket_code']} không ở trạng thái đang xử lý")
            # Khóa dòng tồn kho: hai lần xuất đồng thời không cùng đọc một số tồn (NFR2).
            ton = r.stock.khoa(user['center_id'], part_id)
            if not ton:
                raise AppError('PART_NOT_FOUND', 'Không tìm thấy linh kiện tại trung tâm này')
            if quantity > ton['quantity']:
                raise AppError('INSUFFICIENT_STOCK',
                               f"Vượt quá tồn kho: còn {ton['quantity']}, yêu cầu xuất {quantity}")
            con_lai = ton['quantity'] - quantity
            r.stock.dat_ton(user['center_id'], part_id, con_lai)
            gd = r.txns.them(user['center_id'], part_id, 'XUAT', quantity,
                             ticket_id, user['user_id'])
        return {
            'transaction_id': gd['transaction_id'], 'ticket_id': ticket_id, 'part_id': part_id,
            'quantity': quantity, 'remaining_stock': con_lai,
            'low_stock_alert': con_lai < ton['min_threshold'],   # UC6, UC7
            'created_at': gd['created_at'],
        }

    # ---- FR5: nhập kho, chỉ quản lý trung tâm ----
    def nhap_kho(self, user, part_id, center_id, quantity):
        self._chi_quan_ly(user, 'ghi nhận nhập kho')
        trung_tam = self._trung_tam(user, center_id)
        with self.uow() as r:
            ton = r.stock.khoa(trung_tam, part_id)
            if not ton:
                raise AppError('PART_NOT_FOUND', 'Không tìm thấy linh kiện tại trung tâm này')
            moi = ton['quantity'] + quantity
            r.stock.dat_ton(trung_tam, part_id, moi)
            gd = r.txns.them(trung_tam, part_id, 'NHAP', quantity, None, user['user_id'])
        return {'transaction_id': gd['transaction_id'], 'part_id': part_id,
                'center_id': trung_tam, 'quantity': quantity, 'new_stock': moi,
                'created_at': gd['created_at']}

    # ---- FR7 ----
    def lich_su(self, user, part_id, center_id, page, size):
        self._chi_quan_ly(user, 'xem lịch sử nhập–xuất')
        trung_tam = self._trung_tam(user, center_id)
        with self.uow() as r:
            rows, total = r.txns.lich_su(trung_tam, part_id, size, (page - 1) * size)
        return self._trang(rows, total, page, size)

    def tong_hop(self, user, part_id, center_id, tu_ngay, den_ngay):
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
        with self.uow() as r:
            rows, total = r.tickets.ds(user['center_id'], trang_thai, size, (page - 1) * size)
        return self._trang(rows, total, page, size)

    def linh_kien_cua_phieu(self, user, ticket_id):
        with self.uow() as r:
            phieu = r.tickets.get(ticket_id)
            if not phieu:
                raise AppError('TICKET_NOT_FOUND', f'Không tìm thấy phiếu {ticket_id}')
            self._trung_tam(user, phieu['center_id'])
            return {'ticket': phieu, 'data': r.txns.cua_phieu(ticket_id)}

    # ---- CRUD danh mục linh kiện (xóa mềm, QT-13) ----
    def lay_linh_kien(self, user, part_id):
        with self.uow() as r:
            part = r.parts.lay_theo_id(part_id)
            if not part:
                raise AppError('PART_NOT_FOUND', f'Không tìm thấy linh kiện {part_id}')
            ton = r.stock.lay_ton(user['center_id'], part_id)
        return {**part, 'stock': ton if ton and ton['is_active'] else None}

    def tao_linh_kien(self, user, part_code, part_name, unit_price):
        self._chi_quan_ly(user, 'thêm linh kiện')
        with self.uow() as r:
            if r.parts.tim_theo_ma(part_code):
                raise AppError('PART_CODE_EXISTS', f'Mã linh kiện {part_code} đã tồn tại')
            return r.parts.tao(part_code, part_name, unit_price)

    def sua_linh_kien(self, user, part_id, part_name, unit_price):
        self._chi_quan_ly(user, 'sửa linh kiện')
        with self.uow() as r:
            if not r.parts.lay_theo_id(part_id):
                raise AppError('PART_NOT_FOUND', f'Không tìm thấy linh kiện {part_id}')
            return r.parts.cap_nhat(part_id, part_name, unit_price)

    def ngung_linh_kien(self, user, part_id):
        """Xóa mềm. Không cho ngừng khi còn trung tâm giữ tồn, tránh mất dấu hàng thật."""
        self._chi_quan_ly(user, 'ngừng linh kiện')
        with self.uow() as r:
            if not r.parts.lay_theo_id(part_id):
                raise AppError('PART_NOT_FOUND', f'Không tìm thấy linh kiện {part_id}')
            if r.parts.con_ton(part_id):
                raise AppError('PART_HAS_STOCK',
                               'Linh kiện vẫn còn tồn kho ở trung tâm, chưa thể ngừng sử dụng')
            r.parts.ngung(part_id)
        return {'part_id': part_id, 'is_active': False}

    # ---- CRUD tồn kho của trung tâm ----
    def them_vao_kho(self, user, part_id, min_threshold):
        self._chi_quan_ly(user, 'thêm linh kiện vào kho')
        with self.uow() as r:
            if not r.parts.lay_theo_id(part_id):
                raise AppError('PART_NOT_FOUND', f'Không tìm thấy linh kiện {part_id}')
            ton = r.stock.lay_ton(user['center_id'], part_id)
            if ton and ton['is_active']:
                raise AppError('STOCK_EXISTS', 'Linh kiện đã có trong kho trung tâm này')
            r.stock.them(user['center_id'], part_id, min_threshold)
            ton = r.stock.lay_ton(user['center_id'], part_id)
        return {'part_id': part_id, 'center_id': user['center_id'],
                'quantity': ton['quantity'], 'min_threshold': min_threshold}

    def doi_nguong(self, user, part_id, min_threshold):
        self._chi_quan_ly(user, 'đổi ngưỡng cảnh báo')
        with self.uow() as r:
            ton = r.stock.khoa(user['center_id'], part_id)
            if not ton:
                raise AppError('PART_NOT_FOUND', 'Không tìm thấy linh kiện tại trung tâm này')
            r.stock.dat_nguong(user['center_id'], part_id, min_threshold)
        return {'part_id': part_id, 'center_id': user['center_id'],
                'quantity': ton['quantity'], 'min_threshold': min_threshold}

    def ngung_ton_kho(self, user, part_id):
        """Gỡ linh kiện khỏi kho trung tâm (xóa mềm), chỉ khi tồn đã về 0."""
        self._chi_quan_ly(user, 'gỡ linh kiện khỏi kho')
        with self.uow() as r:
            ton = r.stock.khoa(user['center_id'], part_id)
            if not ton:
                raise AppError('PART_NOT_FOUND', 'Không tìm thấy linh kiện tại trung tâm này')
            if ton['quantity'] > 0:
                raise AppError('STOCK_NOT_EMPTY',
                               f"Kho còn {ton['quantity']} linh kiện, chưa thể gỡ")
            r.stock.ngung(user['center_id'], part_id)
        return {'part_id': part_id, 'center_id': user['center_id'], 'is_active': False}
