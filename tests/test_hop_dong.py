"""Test hợp đồng ở ranh giới giữa lớp nghiệp vụ và giao diện: kiểm HÌNH DẠNG và Ý NGHĨA của dữ liệu trả ra.

Không kiểm giá trị nghiệp vụ. Đổi tên một trường mà không sửa hợp đồng thì các test này vỡ ngay trên máy.
"""
import datetime
import re
from decimal import Decimal

from src.routes import views

ISO_8601 = re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(\+|-)\d{2}:\d{2}$')
GIO_VN = datetime.timezone(datetime.timedelta(hours=7))


def dong_csdl_gia():
    """Một dòng giống hệt psycopg trả về: Decimal cho NUMERIC, datetime có múi giờ, có cột nội bộ."""
    return {'part_id': 45, 'part_code': 'MH-IP13-001', 'part_name': 'Màn hình iPhone 13',
            'unit_price': Decimal('2500000'), 'quantity': 5, 'min_threshold': 3, 'is_active': True,
            'total': 123}


# ---- Luồng đúng: đúng bộ trường của hợp đồng, kiểu đúng ----
def test_to_part_stock_view_tra_dung_cac_truong_va_bo_cot_noi_bo():
    v = views.to_part_stock_view(dong_csdl_gia())
    assert set(v) == {'part_id', 'part_code', 'part_name', 'unit_price', 'quantity', 'min_threshold'}
    assert v['unit_price'] == 2500000 and type(v['unit_price']) is int     # đồng Việt Nam, số nguyên


def test_thoi_diem_la_chuoi_iso_8601_kem_mui_gio():
    t = {'transaction_id': 1, 'created_at': datetime.datetime(2026, 10, 28, 0, 37, 52, tzinfo=GIO_VN),
         'txn_type': 'NHAP', 'quantity': 3, 'ticket_id': None, 'created_by_name': 'Quản lý TT01'}
    v = views.to_transaction_view(t)
    assert set(v) == {'transaction_id', 'created_at', 'txn_type', 'quantity', 'ticket_id', 'created_by_name'}
    assert ISO_8601.match(v['created_at'])


# ---- Ý nghĩa đặc biệt của null ----
def test_nhap_kho_khong_gan_phieu_thi_ticket_id_la_null_khong_phai_0():
    t = {'transaction_id': 1, 'created_at': datetime.datetime(2026, 10, 28, tzinfo=GIO_VN),
         'txn_type': 'NHAP', 'quantity': 3, 'ticket_id': None, 'created_by_name': 'x'}
    assert views.to_transaction_view(t)['ticket_id'] is None


def test_linh_kien_chua_co_trong_kho_thi_stock_la_null_khong_phai_ton_0():
    v = views.to_part_detail_view({'part_id': 46, 'part_code': 'PIN-SS-01', 'part_name': 'Pin',
                                   'unit_price': Decimal('300000'), 'stock': None})
    assert v['stock'] is None
    co = views.to_part_detail_view({**dong_csdl_gia(), 'stock': {'quantity': 0, 'min_threshold': 3,
                                                                  'is_active': True}})
    assert co['stock'] == {'quantity': 0, 'min_threshold': 3}               # 0 là có trong kho nhưng hết hàng


# ---- Qua API: tên trường khớp hợp đồng ----
def test_api_danh_sach_phieu_dung_bo_truong(client, dang_nhap):
    r = client.get('/api/tickets?status=DANG_XU_LY', headers=dang_nhap(2))
    for phieu in r.get_json()['data']:
        assert set(phieu) == {'ticket_id', 'ticket_code', 'center_id', 'status'}


def test_api_chi_tiet_linh_kien_gia_la_so_va_stock_dung_hinh_dang(client, dang_nhap):
    h = dang_nhap(2)
    co = client.get('/api/parts/45', headers=h).get_json()
    assert set(co) == {'part_id', 'part_code', 'part_name', 'unit_price', 'stock'}
    assert set(co['stock']) == {'quantity', 'min_threshold'}               # không lộ cột is_active
    chua = client.get('/api/parts/46', headers=h).get_json()
    assert chua['stock'] is None
    assert chua['unit_price'] == 300000 and isinstance(chua['unit_price'], int)   # BUG-003: không trả chuỗi "300000"


def test_api_ket_qua_xuat_kho_dung_bo_truong_va_thoi_diem_iso(client, dang_nhap):
    r = client.post('/api/tickets/231/parts', json={'part_id': 45, 'quantity': 1}, headers=dang_nhap(2))
    d = r.get_json()
    assert set(d) == {'transaction_id', 'ticket_id', 'part_id', 'quantity', 'remaining_stock',
                      'low_stock_alert', 'created_at'}
    assert ISO_8601.match(d['created_at'])
