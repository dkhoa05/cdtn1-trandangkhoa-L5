"""Tầng 3: chỉ đọc/ghi PostgreSQL, không chứa quy tắc nghiệp vụ."""
from contextlib import contextmanager

from src import db


def _escape_like(q):
    # Người dùng gõ % hoặc _ phải được hiểu là ký tự thường, không phải ký tự đại diện của LIKE
    return q.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')


def _tach_total(rows):
    # COUNT(*) OVER () trả tổng số dòng ở MỌI dòng kết quả, nên chỉ cần lấy từ dòng đầu;
    # tách ra để một câu SQL vừa phân trang vừa cho biết tổng, khỏi chạy thêm câu COUNT riêng.
    total = rows[0]['total'] if rows else 0
    for r in rows:
        del r['total']
    return rows, total


class UserRepository:
    def __init__(self, conn):
        self.conn = conn

    def lay_nguoi_dung(self, user_id):
        """Trả người dùng kèm tên trung tâm, hoặc None nếu không có."""
        return self.conn.execute(
            """SELECT u.user_id, u.full_name, u.role, u.center_id, u.is_active, c.center_name
               FROM app_user u JOIN service_center c USING (center_id)
               WHERE u.user_id = %s""", (user_id,)).fetchone()


# Điều kiện lọc và thứ tự sắp xếp là hằng số của repository: giá trị người dùng gửi lên chỉ để CHỌN khóa trong hai
# bảng này (validator đã giới hạn), không bao giờ được nối vào câu SQL.
_LOC_TON = {'all': 'TRUE', 'low': 's.quantity < s.min_threshold', 'out': 's.quantity = 0',
            'ok': 's.quantity >= s.min_threshold'}
_SAP_XEP = {'code': 'p.part_code', 'name': 'p.part_name, p.part_code',
            'qty_asc': 's.quantity, p.part_code', 'qty_desc': 's.quantity DESC, p.part_code'}


class PartRepository:
    def __init__(self, conn):
        self.conn = conn

    def tim_linh_kien_trong_kho(self, center_id, q, trang_thai, sap_xep, limit, offset):
        """Làm gì: tìm linh kiện đang dùng trong kho của một trung tâm, theo mã hoặc tên, sắp theo mã.
        Nhận: q rỗng nghĩa là không lọc theo từ khóa; trang_thai: all, low (tồn dưới ngưỡng; hết hàng cũng thuộc nhóm này
        khi ngưỡng lớn hơn 0), out (tồn bằng 0) hoặc ok (tồn không thấp hơn ngưỡng); sap_xep: code, name, qty_asc hoặc qty_desc.
        Trả: (danh sách dòng, tổng số dòng khớp). Lỗi: không có."""
        mau = f'%{_escape_like(q)}%' if q else None
        rows = self.conn.execute(
            f"""SELECT p.part_id, p.part_code, p.part_name, p.unit_price, s.quantity, s.min_threshold,
                      COUNT(*) OVER () AS total
               FROM part_stock s JOIN part p USING (part_id)
               WHERE s.center_id = %(c)s AND s.is_active AND p.is_active
                 AND (%(mau)s::text IS NULL
                      OR p.part_code ILIKE %(mau)s OR p.part_name ILIKE %(mau)s)
                 AND {_LOC_TON[trang_thai]}
               ORDER BY {_SAP_XEP[sap_xep]}
               LIMIT %(limit)s OFFSET %(offset)s""",
            {'c': center_id, 'mau': mau, 'limit': limit, 'offset': offset}).fetchall()
        return _tach_total(rows)

    def lay_linh_kien(self, part_id):
        """Trả linh kiện còn dùng theo id, hoặc None (linh kiện đã ngừng cũng coi như không có)."""
        return self.conn.execute(
            'SELECT part_id, part_code, part_name, unit_price FROM part WHERE part_id = %s AND is_active',
            (part_id,)).fetchone()

    def tim_theo_ma(self, part_code):
        """Tìm theo mã KỂ CẢ linh kiện đã ngừng, vì cột mã là duy nhất nên mã cũ vẫn chiếm chỗ."""
        return self.conn.execute(
            'SELECT part_id FROM part WHERE part_code = %s', (part_code,)).fetchone()

    def tao_linh_kien(self, part_code, part_name, unit_price):
        """Thêm linh kiện mới vào danh mục, trả dòng vừa tạo (RETURNING lấy luôn part_id do CSDL cấp)."""
        return self.conn.execute(
            """INSERT INTO part (part_code, part_name, unit_price) VALUES (%s, %s, %s)
               RETURNING part_id, part_code, part_name, unit_price""",
            (part_code, part_name, unit_price)).fetchone()

    def cap_nhat_linh_kien(self, part_id, part_name, unit_price):
        """Sửa tên và đơn giá; trả dòng sau khi sửa, hoặc None nếu không có linh kiện."""
        return self.conn.execute(
            """UPDATE part SET part_name = %s, unit_price = %s WHERE part_id = %s
               RETURNING part_id, part_code, part_name, unit_price""",
            (part_name, unit_price, part_id)).fetchone()

    def co_ton_kho(self, part_id):
        """True nếu còn trung tâm nào đang giữ tồn > 0 của linh kiện này."""
        return self.conn.execute(
            """SELECT EXISTS (SELECT 1 FROM part_stock
                               WHERE part_id = %s AND is_active AND quantity > 0) AS co""",
            (part_id,)).fetchone()['co']

    def ngung_su_dung_linh_kien(self, part_id):
        """Xóa mềm: đặt is_active = false ở danh mục và ở mọi kho, không xóa dòng để còn lịch sử xuất nhập."""
        self.conn.execute('UPDATE part SET is_active = false WHERE part_id = %s', (part_id,))
        self.conn.execute('UPDATE part_stock SET is_active = false WHERE part_id = %s', (part_id,))


class StockRepository:
    def __init__(self, conn):
        self.conn = conn

    def khoa_dong_ton_kho(self, center_id, part_id):
        """Đọc tồn kho và khóa dòng đến hết transaction (NFR2).

        FOR UPDATE làm hai người xuất cùng lúc phải xếp hàng: người thứ hai chờ đến khi người đầu xong
        rồi mới đọc tồn, nên không thể cùng thấy "còn 5" rồi cùng xuất 5.
        """
        return self.conn.execute(
            """SELECT quantity, min_threshold FROM part_stock
               WHERE center_id = %s AND part_id = %s AND is_active FOR UPDATE""",
            (center_id, part_id)).fetchone()

    def lay_ton(self, center_id, part_id):
        """Đọc dòng tồn kho kể cả đã ngừng dùng (để biết có thể kích hoạt lại)."""
        return self.conn.execute(
            """SELECT quantity, min_threshold, is_active FROM part_stock
               WHERE center_id = %s AND part_id = %s""", (center_id, part_id)).fetchone()

    def them_vao_kho(self, center_id, part_id, min_threshold):
        """Đưa linh kiện vào kho trung tâm với tồn 0; kích hoạt lại nếu từng ngừng dùng."""
        self.conn.execute(
            """INSERT INTO part_stock (center_id, part_id, quantity, min_threshold)
               VALUES (%s, %s, 0, %s)
               ON CONFLICT (center_id, part_id)
               DO UPDATE SET is_active = true, min_threshold = EXCLUDED.min_threshold""",
            (center_id, part_id, min_threshold))

    def dat_nguong(self, center_id, part_id, min_threshold):
        """Đổi ngưỡng cảnh báo tồn thấp của một linh kiện trong một kho."""
        self.conn.execute(
            'UPDATE part_stock SET min_threshold = %s WHERE center_id = %s AND part_id = %s',
            (min_threshold, center_id, part_id))

    def ngung_su_dung_ton_kho(self, center_id, part_id):
        """Gỡ linh kiện khỏi kho một trung tâm bằng xóa mềm; danh mục chung không đổi."""
        self.conn.execute(
            'UPDATE part_stock SET is_active = false WHERE center_id = %s AND part_id = %s',
            (center_id, part_id))

    def ghi_ton_moi(self, center_id, part_id, quantity):
        """Ghi số tồn mới. Chỉ gọi sau khi khoa_dong_ton_kho() đã giữ khóa dòng, nếu không hai lần ghi có thể đè nhau."""
        self.conn.execute(
            'UPDATE part_stock SET quantity = %s WHERE center_id = %s AND part_id = %s',
            (quantity, center_id, part_id))


class TransactionRepository:
    def __init__(self, conn):
        self.conn = conn

    def ghi_giao_dich(self, center_id, part_id, loai, quantity, ticket_id, user_id):
        """Ghi một dòng lịch sử nhập hoặc xuất (loai là NHAP hoặc XUAT). Trả mã giao dịch và thời điểm ghi."""
        return self.conn.execute(
            """INSERT INTO part_transaction
                   (center_id, part_id, txn_type, quantity, ticket_id, created_by)
               VALUES (%s, %s, %s, %s, %s, %s)
               RETURNING transaction_id, created_at""",
            (center_id, part_id, loai, quantity, ticket_id, user_id)).fetchone()

    def lich_su(self, center_id, part_id, limit, offset):
        """Lịch sử nhập xuất của một linh kiện, mới nhất trước. Trả (danh sách, tổng số dòng)."""
        rows = self.conn.execute(
            """SELECT t.transaction_id, t.created_at, t.txn_type, t.quantity, t.ticket_id,
                      u.full_name AS created_by_name, COUNT(*) OVER () AS total
               FROM part_transaction t JOIN app_user u ON u.user_id = t.created_by
               WHERE t.center_id = %s AND t.part_id = %s
               ORDER BY t.created_at DESC, t.transaction_id DESC
               LIMIT %s OFFSET %s""", (center_id, part_id, limit, offset)).fetchall()
        return _tach_total(rows)

    def tong_hop(self, center_id, part_id, tu_ngay, den_ngay):
        """Tổng nhập và tổng xuất trong khoảng ngày. Trả (tong_nhap, tong_xuat), không có giao dịch thì là (0, 0).

        Điều kiện "< den_ngay + 1 ngày" để bao gồm trọn ngày cuối, kể cả giao dịch lúc 23:59.
        """
        r = self.conn.execute(
            """SELECT COALESCE(SUM(quantity) FILTER (WHERE txn_type = 'NHAP'), 0)::int AS tong_nhap,
                      COALESCE(SUM(quantity) FILTER (WHERE txn_type = 'XUAT'), 0)::int AS tong_xuat
               FROM part_transaction
               WHERE center_id = %s AND part_id = %s
                 AND created_at >= %s AND created_at < %s::date + 1""",
            (center_id, part_id, tu_ngay, den_ngay)).fetchone()
        return r['tong_nhap'], r['tong_xuat']

    def giao_dich_cua_phieu(self, ticket_id):
        """Các lần xuất linh kiện của một phiếu, mới nhất trước, kèm mã và tên linh kiện."""
        return self.conn.execute(
            """SELECT t.transaction_id, t.part_id, p.part_code, p.part_name, t.quantity, t.created_at
               FROM part_transaction t JOIN part p USING (part_id)
               WHERE t.ticket_id = %s AND t.txn_type = 'XUAT'
               ORDER BY t.created_at DESC, t.transaction_id DESC""", (ticket_id,)).fetchall()


class TicketRepository:
    def __init__(self, conn):
        self.conn = conn

    def lay_phieu(self, ticket_id):
        """Trả phiếu theo id, hoặc None nếu không có."""
        return self.conn.execute(
            'SELECT ticket_id, ticket_code, center_id, status FROM ticket WHERE ticket_id = %s',
            (ticket_id,)).fetchone()

    def danh_sach_phieu(self, center_id, trang_thai, limit, offset):
        """Danh sách phiếu của một trung tâm; trang_thai None nghĩa là lấy mọi trạng thái. Trả (danh sách, tổng)."""
        rows = self.conn.execute(
            """SELECT ticket_id, ticket_code, center_id, status, COUNT(*) OVER () AS total
               FROM ticket
               WHERE center_id = %s AND (%s::text IS NULL OR status = %s)
               ORDER BY ticket_id DESC LIMIT %s OFFSET %s""",
            (center_id, trang_thai, trang_thai, limit, offset)).fetchall()
        return _tach_total(rows)


class Repos:
    """Gom các repository dùng chung MỘT kết nối, để chúng cùng nằm trong một transaction."""

    def __init__(self, conn):
        self.users = UserRepository(conn)
        self.parts = PartRepository(conn)
        self.stock = StockRepository(conn)
        self.txns = TransactionRepository(conn)
        self.tickets = TicketRepository(conn)


@contextmanager
def unit_of_work():
    """Một transaction cho cả lần gọi service: commit khi thành công, rollback khi lỗi."""
    with db.connect() as conn:
        yield Repos(conn)
