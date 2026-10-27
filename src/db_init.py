"""Dựng CSDL: chạy toàn bộ migrations/*.sql rồi seeds/*.sql theo thứ tự tên tệp.

Chạy bằng: python -m src.db_init
Chạy lại lần hai không lỗi và không nhân đôi dữ liệu (IF NOT EXISTS, ON CONFLICT DO NOTHING).
Nếu CSDL đích (biến DB_NAME) chưa có thì tự tạo, nên README không cần bước tạo CSDL bằng tay.
"""
import sys
from pathlib import Path

import psycopg
from psycopg import sql

from src import config, db

# Thư mục gốc của repo, để tìm migrations/ và seeds/ dù lệnh được chạy từ thư mục nào
GOC = Path(__file__).resolve().parent.parent


def tao_csdl_neu_chua_co():
    """Tạo CSDL đích nếu chưa có, bằng cách nối tạm vào CSDL 'postgres' của cùng máy chủ.

    Hỏi bảng pg_database thay vì đọc thông báo lỗi, vì thông báo lỗi đổi theo ngôn ngữ của máy chủ.
    """
    ten = config.db_name()
    try:
        conn = psycopg.connect(config.database_url('postgres'), autocommit=True, connect_timeout=3)
    except psycopg.OperationalError:
        return                    # không nối được CSDL 'postgres': để lần nối chính báo đúng lỗi thật
    with conn:
        if conn.execute('SELECT 1 FROM pg_database WHERE datname = %s', (ten,)).fetchone():
            return
        try:
            conn.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(ten)))
        except psycopg.errors.InsufficientPrivilege:
            sys.exit(f'Người dùng PostgreSQL hiện tại không có quyền tạo CSDL. '
                     f'Hãy tạo CSDL {ten} bằng pgAdmin rồi chạy lại.')
    print(f'da tao co so du lieu {ten}')


def main():
    tao_csdl_neu_chua_co()
    with db.connect() as conn:
        # Thứ tự quan trọng: migrations tạo bảng trước, seeds mới có bảng để nạp dữ liệu
        for thu_muc in ('migrations', 'seeds'):
            for tep in sorted((GOC / thu_muc).glob('*.sql')):
                conn.execute(tep.read_text(encoding='utf-8'))
                print(f'da chay {thu_muc}/{tep.name}')
        # Đếm lại để người chạy tự thấy dữ liệu đã có; chạy lần hai các con số này không đổi
        for bang in ('service_center', 'app_user', 'part', 'part_stock', 'ticket', 'part_transaction'):
            so = conn.execute(f'SELECT COUNT(*) AS n FROM {bang}').fetchone()['n']
            print(f'  {bang}: {so} dong')


if __name__ == '__main__':
    main()
