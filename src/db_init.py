"""Dựng CSDL: chạy toàn bộ migrations/*.sql rồi seeds/*.sql theo thứ tự tên tệp.

Chạy bằng: python -m src.db_init
Chạy lại lần hai không lỗi và không nhân đôi dữ liệu (IF NOT EXISTS, ON CONFLICT DO NOTHING).
"""
from pathlib import Path

from src import db

GOC = Path(__file__).resolve().parent.parent


def main():
    with db.connect() as conn:
        for thu_muc in ('migrations', 'seeds'):
            for tep in sorted((GOC / thu_muc).glob('*.sql')):
                conn.execute(tep.read_text(encoding='utf-8'))
                print(f'da chay {thu_muc}/{tep.name}')
        for bang in ('service_center', 'app_user', 'part', 'part_stock', 'ticket', 'part_transaction'):
            so = conn.execute(f'SELECT COUNT(*) AS n FROM {bang}').fetchone()['n']
            print(f'  {bang}: {so} dong')


if __name__ == '__main__':
    main()
