"""Tầng 3: chỉ đọc/ghi PostgreSQL, không chứa quy tắc nghiệp vụ."""
from contextlib import contextmanager

from src import db


def _escape_like(q):
    return q.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')


def _tach_total(rows):
    total = rows[0]['total'] if rows else 0
    for r in rows:
        del r['total']
    return rows, total


class UserRepository:
    def __init__(self, conn):
        self.conn = conn

    def get(self, user_id):
        return self.conn.execute(
            """SELECT u.user_id, u.full_name, u.role, u.center_id, u.is_active, c.center_name
               FROM app_user u JOIN service_center c USING (center_id)
               WHERE u.user_id = %s""", (user_id,)).fetchone()


class PartRepository:
    def __init__(self, conn):
        self.conn = conn

    def tim(self, center_id, q, chi_duoi_nguong, limit, offset):
        mau = f'%{_escape_like(q)}%' if q else None
        rows = self.conn.execute(
            """SELECT p.part_id, p.part_code, p.part_name, p.unit_price, s.quantity, s.min_threshold,
                      COUNT(*) OVER () AS total
               FROM part_stock s JOIN part p USING (part_id)
               WHERE s.center_id = %(c)s AND s.is_active AND p.is_active
                 AND (%(mau)s::text IS NULL
                      OR p.part_code ILIKE %(mau)s OR p.part_name ILIKE %(mau)s)
                 AND (NOT %(low)s OR s.quantity < s.min_threshold)
               ORDER BY p.part_code
               LIMIT %(limit)s OFFSET %(offset)s""",
            {'c': center_id, 'mau': mau, 'low': chi_duoi_nguong,
             'limit': limit, 'offset': offset}).fetchall()
        return _tach_total(rows)

    def lay_theo_id(self, part_id):
        return self.conn.execute(
            'SELECT part_id, part_code, part_name, unit_price FROM part WHERE part_id = %s AND is_active',
            (part_id,)).fetchone()

    def tim_theo_ma(self, part_code):
        return self.conn.execute(
            'SELECT part_id FROM part WHERE part_code = %s', (part_code,)).fetchone()

    def tao(self, part_code, part_name, unit_price):
        return self.conn.execute(
            """INSERT INTO part (part_code, part_name, unit_price) VALUES (%s, %s, %s)
               RETURNING part_id, part_code, part_name, unit_price""",
            (part_code, part_name, unit_price)).fetchone()

    def cap_nhat(self, part_id, part_name, unit_price):
        return self.conn.execute(
            """UPDATE part SET part_name = %s, unit_price = %s WHERE part_id = %s
               RETURNING part_id, part_code, part_name, unit_price""",
            (part_name, unit_price, part_id)).fetchone()

    def con_ton(self, part_id):
        """True nếu còn trung tâm nào đang giữ tồn > 0 của linh kiện này."""
        return self.conn.execute(
            """SELECT EXISTS (SELECT 1 FROM part_stock
                               WHERE part_id = %s AND is_active AND quantity > 0) AS co""",
            (part_id,)).fetchone()['co']

    def ngung(self, part_id):
        self.conn.execute('UPDATE part SET is_active = false WHERE part_id = %s', (part_id,))
        self.conn.execute('UPDATE part_stock SET is_active = false WHERE part_id = %s', (part_id,))


class StockRepository:
    def __init__(self, conn):
        self.conn = conn

    def khoa(self, center_id, part_id):
        """Đọc tồn kho và khóa dòng đến hết transaction (NFR2)."""
        return self.conn.execute(
            """SELECT quantity, min_threshold FROM part_stock
               WHERE center_id = %s AND part_id = %s AND is_active FOR UPDATE""",
            (center_id, part_id)).fetchone()

    def lay_ton(self, center_id, part_id):
        """Đọc dòng tồn kho kể cả đã ngừng dùng (để biết có thể kích hoạt lại)."""
        return self.conn.execute(
            """SELECT quantity, min_threshold, is_active FROM part_stock
               WHERE center_id = %s AND part_id = %s""", (center_id, part_id)).fetchone()

    def them(self, center_id, part_id, min_threshold):
        """Đưa linh kiện vào kho trung tâm với tồn 0; kích hoạt lại nếu từng ngừng dùng."""
        self.conn.execute(
            """INSERT INTO part_stock (center_id, part_id, quantity, min_threshold)
               VALUES (%s, %s, 0, %s)
               ON CONFLICT (center_id, part_id)
               DO UPDATE SET is_active = true, min_threshold = EXCLUDED.min_threshold""",
            (center_id, part_id, min_threshold))

    def dat_nguong(self, center_id, part_id, min_threshold):
        self.conn.execute(
            'UPDATE part_stock SET min_threshold = %s WHERE center_id = %s AND part_id = %s',
            (min_threshold, center_id, part_id))

    def ngung(self, center_id, part_id):
        self.conn.execute(
            'UPDATE part_stock SET is_active = false WHERE center_id = %s AND part_id = %s',
            (center_id, part_id))

    def dat_ton(self, center_id, part_id, quantity):
        self.conn.execute(
            'UPDATE part_stock SET quantity = %s WHERE center_id = %s AND part_id = %s',
            (quantity, center_id, part_id))


class TransactionRepository:
    def __init__(self, conn):
        self.conn = conn

    def them(self, center_id, part_id, loai, quantity, ticket_id, user_id):
        return self.conn.execute(
            """INSERT INTO part_transaction
                   (center_id, part_id, txn_type, quantity, ticket_id, created_by)
               VALUES (%s, %s, %s, %s, %s, %s)
               RETURNING transaction_id, created_at""",
            (center_id, part_id, loai, quantity, ticket_id, user_id)).fetchone()

    def lich_su(self, center_id, part_id, limit, offset):
        rows = self.conn.execute(
            """SELECT t.transaction_id, t.created_at, t.txn_type, t.quantity, t.ticket_id,
                      u.full_name AS created_by_name, COUNT(*) OVER () AS total
               FROM part_transaction t JOIN app_user u ON u.user_id = t.created_by
               WHERE t.center_id = %s AND t.part_id = %s
               ORDER BY t.created_at DESC, t.transaction_id DESC
               LIMIT %s OFFSET %s""", (center_id, part_id, limit, offset)).fetchall()
        return _tach_total(rows)

    def tong_hop(self, center_id, part_id, tu_ngay, den_ngay):
        r = self.conn.execute(
            """SELECT COALESCE(SUM(quantity) FILTER (WHERE txn_type = 'NHAP'), 0)::int AS tong_nhap,
                      COALESCE(SUM(quantity) FILTER (WHERE txn_type = 'XUAT'), 0)::int AS tong_xuat
               FROM part_transaction
               WHERE center_id = %s AND part_id = %s
                 AND created_at >= %s AND created_at < %s::date + 1""",
            (center_id, part_id, tu_ngay, den_ngay)).fetchone()
        return r['tong_nhap'], r['tong_xuat']

    def cua_phieu(self, ticket_id):
        return self.conn.execute(
            """SELECT t.transaction_id, t.part_id, p.part_code, p.part_name, t.quantity, t.created_at
               FROM part_transaction t JOIN part p USING (part_id)
               WHERE t.ticket_id = %s AND t.txn_type = 'XUAT'
               ORDER BY t.created_at DESC, t.transaction_id DESC""", (ticket_id,)).fetchall()


class TicketRepository:
    def __init__(self, conn):
        self.conn = conn

    def get(self, ticket_id):
        return self.conn.execute(
            'SELECT ticket_id, ticket_code, center_id, status FROM ticket WHERE ticket_id = %s',
            (ticket_id,)).fetchone()

    def ds(self, center_id, trang_thai, limit, offset):
        rows = self.conn.execute(
            """SELECT ticket_id, ticket_code, center_id, status, COUNT(*) OVER () AS total
               FROM ticket
               WHERE center_id = %s AND (%s::text IS NULL OR status = %s)
               ORDER BY ticket_id DESC LIMIT %s OFFSET %s""",
            (center_id, trang_thai, trang_thai, limit, offset)).fetchall()
        return _tach_total(rows)


class Repos:
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
