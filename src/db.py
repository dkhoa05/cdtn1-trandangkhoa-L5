"""Kết nối PostgreSQL. Chỉ lớp repositories dùng module này."""
import psycopg
from psycopg.rows import dict_row

from src import config


def connect():
    """Làm gì: mở một kết nối PostgreSQL mới theo cấu hình trong .env.
    Nhận: không có. Trả: kết nối, mỗi dòng đọc ra là dict (tên cột -> giá trị).
    Lỗi: psycopg.OperationalError khi không nối được; app.py đổi lỗi này thành 503."""
    # connect_timeout=3: CSDL tắt thì báo lỗi sau 3 giây, không để người dùng chờ treo
    return psycopg.connect(config.database_url(), row_factory=dict_row, connect_timeout=3)
