"""Kiểm thử tích hợp trên PostgreSQL thật (NFR2, TD-02): ngắt lỗi giữa chừng và hai giao dịch xuất đồng thời.

Mặc định BỎ QUA để bộ kiểm thử chính không phụ thuộc cơ sở dữ liệu có sẵn. Chạy bằng:
    PowerShell:  $env:RUN_PG_TESTS="1"; pytest tests/test_tich_hop_pg.py
Cần CSDL đã chạy `python -m src.db_init`; mỗi test tự tạo linh kiện riêng và ngừng sử dụng khi xong.
"""
import os
import threading
import uuid

import pytest

from src import db
from src.errors import AppError
from src.repositories import stock_repo
from src.services.stock_service import StockService

pytestmark = pytest.mark.skipif(not os.getenv('RUN_PG_TESTS'),
                                reason='đặt RUN_PG_TESTS=1 để chạy test cần PostgreSQL thật')


@pytest.fixture
def ctx():
    service = StockService(stock_repo.unit_of_work)
    quan_ly = service.lay_nguoi_dung(101)                 # quản lý trung tâm 1 trong dữ liệu mẫu
    with db.connect() as conn:
        phieu = conn.execute("SELECT ticket_id FROM ticket WHERE center_id = %s AND status = 'DANG_XU_LY' LIMIT 1",
                             (quan_ly['center_id'],)).fetchone()['ticket_id']
    part = service.tao_linh_kien(quan_ly, 'IT-' + uuid.uuid4().hex[:10], 'Linh kiện kiểm thử tích hợp', 1000)
    service.them_vao_kho(quan_ly, part['part_id'], 0)
    yield service, quan_ly, phieu, part['part_id']
    # Dọn: đưa tồn về 0 rồi ngừng sử dụng (xóa mềm, giữ nguyên lịch sử giao dịch, QT-13).
    with db.connect() as conn:
        ton = conn.execute('SELECT quantity FROM part_stock WHERE center_id = %s AND part_id = %s',
                           (quan_ly['center_id'], part['part_id'])).fetchone()
    if ton and ton['quantity'] > 0:
        service.xuat_linh_kien(quan_ly, phieu, part['part_id'], ton['quantity'])
    service.ngung_ton_kho(quan_ly, part['part_id'])
    service.ngung_linh_kien(quan_ly, part['part_id'])


def _ton(quan_ly, part_id):
    with db.connect() as conn:
        return conn.execute('SELECT quantity FROM part_stock WHERE center_id = %s AND part_id = %s',
                            (quan_ly['center_id'], part_id)).fetchone()['quantity']


def _so_giao_dich(part_id, loai):
    with db.connect() as conn:
        return conn.execute('SELECT COUNT(*) AS n FROM part_transaction WHERE part_id = %s AND txn_type = %s',
                            (part_id, loai)).fetchone()['n']


def test_ngat_loi_giua_chung_khong_de_ton_kho_lech_voi_log(ctx, monkeypatch):
    service, quan_ly, phieu, part_id = ctx
    service.nhap_kho(quan_ly, part_id, quan_ly['center_id'], 5)
    for _ in range(50):                                   # lặp: lỗi xảy ra sau khi đã trừ tồn nhưng trước khi ghi log
        monkeypatch.setattr(stock_repo.TransactionRepository, 'them',
                            lambda *a, **k: (_ for _ in ()).throw(RuntimeError('ngắt giữa chừng')))
        with pytest.raises(RuntimeError):
            service.xuat_linh_kien(quan_ly, phieu, part_id, 1)
    monkeypatch.undo()
    assert _ton(quan_ly, part_id) == 5                    # transaction rollback: tồn không đổi
    assert _so_giao_dich(part_id, 'XUAT') == 0            # và không có dòng log nào


def test_nhieu_giao_dich_xuat_dong_thoi_chi_mot_thanh_cong(ctx):
    service, quan_ly, phieu, part_id = ctx
    service.nhap_kho(quan_ly, part_id, quan_ly['center_id'], 1)       # chỉ còn 1, tám luồng cùng xuất 1
    ket_qua = []
    SO_LUONG = 8
    rao = threading.Barrier(SO_LUONG)

    def xuat():
        rao.wait()
        try:
            service.xuat_linh_kien(quan_ly, phieu, part_id, 1)
            ket_qua.append('ok')
        except AppError as e:
            ket_qua.append(e.code)
        except Exception as e:                            # lỗi lạ (ví dụ vi phạm CHECK) cũng tính là thất bại
            ket_qua.append(type(e).__name__)

    luong = [threading.Thread(target=xuat) for _ in range(SO_LUONG)]
    for t in luong:
        t.start()
    for t in luong:
        t.join()
    assert sorted(ket_qua) == ['INSUFFICIENT_STOCK'] * (SO_LUONG - 1) + ['ok']
    assert _ton(quan_ly, part_id) == 0                    # không âm, không xuất đôi
    assert _so_giao_dich(part_id, 'XUAT') == 1
