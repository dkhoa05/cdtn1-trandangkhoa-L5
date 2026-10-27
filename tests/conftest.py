"""Repository giả lưu trong bộ nhớ: test nghiệp vụ và API không cần PostgreSQL."""
import datetime
from contextlib import contextmanager

import pytest

from src.app import create_app
from src.services.stock_service import StockService

QUAN_LY = {'user_id': 101, 'full_name': 'Quản lý TT01', 'role': 'QUAN_LY_TT',
           'center_id': 1, 'is_active': True, 'center_name': 'TTBH Quận 10'}
KY_THUAT = {'user_id': 2, 'full_name': 'Kỹ thuật viên TT01', 'role': 'KY_THUAT_VIEN',
            'center_id': 1, 'is_active': True, 'center_name': 'TTBH Quận 10'}
KHAC_TT = {'user_id': 7, 'full_name': 'Kỹ thuật viên TT05', 'role': 'KY_THUAT_VIEN',
           'center_id': 5, 'is_active': True, 'center_name': 'TTBH Cái Răng'}
DA_NGHI = {**KY_THUAT, 'user_id': 1, 'is_active': False}


class KhoGia:
    """Một 'CSDL' nhỏ: linh kiện 45 tại trung tâm 1 còn 5, ngưỡng 3."""

    def __init__(self):
        self.users = {u['user_id']: u for u in (QUAN_LY, KY_THUAT, KHAC_TT, DA_NGHI)}
        self.ton = {(1, 45): {'quantity': 5, 'min_threshold': 3}}
        self.phieu = {
            231: {'ticket_id': 231, 'ticket_code': 'BH-000231/2026', 'center_id': 1,
                  'status': 'DANG_XU_LY'},
            232: {'ticket_id': 232, 'ticket_code': 'BH-000232/2026', 'center_id': 1,
                  'status': 'DA_DONG'},
        }
        self.danh_muc = {45: {'part_id': 45, 'part_code': 'MH-IP13-001',
                              'part_name': 'Màn hình iPhone 13', 'unit_price': 2500000,
                              'is_active': True},
                         46: {'part_id': 46, 'part_code': 'PIN-SS-01', 'part_name': 'Pin Samsung',
                              'unit_price': 300000, 'is_active': True}}
        self.giao_dich = []
        self.da_commit = 0
        # Repository giả dùng chung một đối tượng cho tiện.
        self.users_repo = self.parts = self.stock = self.txns = self.tickets = self

    # users
    def get(self, key):
        if key in self.users:
            return self.users[key]
        return self.phieu.get(key)

    # stock
    def khoa(self, center_id, part_id):
        t = self.ton.get((center_id, part_id))
        return t if t and t.get('is_active', True) else None

    def dat_ton(self, center_id, part_id, quantity):
        self.ton[(center_id, part_id)]['quantity'] = quantity

    # txns
    def them(self, center_id, part_id, *con_lai):
        if len(con_lai) == 1:                    # StockRepository.them(center, part, ngưỡng)
            return self.them_ton(center_id, part_id, con_lai[0])
        loai, quantity, ticket_id, user_id = con_lai      # TransactionRepository.them
        gd = {'transaction_id': 9000 + len(self.giao_dich), 'created_at':
              datetime.datetime(2026, 10, 22, 9, 30, tzinfo=datetime.timezone.utc)}
        self.giao_dich.append({**gd, 'loai': loai, 'quantity': quantity,
                               'ticket_id': ticket_id, 'user_id': user_id})
        return gd

    def lich_su(self, *a):
        return [], 0

    def tong_hop(self, *a):
        return 15, 8

    def cua_phieu(self, ticket_id):
        return [g for g in self.giao_dich if g['ticket_id'] == ticket_id]

    # parts (danh mục) và các thao tác CRUD
    def lay_theo_id(self, part_id):
        p = self.danh_muc.get(part_id)
        return p if p and p['is_active'] else None

    def tim_theo_ma(self, part_code):
        return next((p for p in self.danh_muc.values() if p['part_code'] == part_code), None)

    def tao(self, part_code, part_name, unit_price):
        part_id = max(self.danh_muc) + 1
        self.danh_muc[part_id] = {'part_id': part_id, 'part_code': part_code,
                                  'part_name': part_name, 'unit_price': unit_price,
                                  'is_active': True}
        return self.danh_muc[part_id]

    def cap_nhat(self, part_id, part_name, unit_price):
        self.danh_muc[part_id].update(part_name=part_name, unit_price=unit_price)
        return self.danh_muc[part_id]

    def con_ton(self, part_id):
        return any(k[1] == part_id and v['quantity'] > 0 and v.get('is_active', True)
                   for k, v in self.ton.items())

    def ngung(self, *khoa):
        if len(khoa) == 1:                       # PartRepository.ngung(part_id)
            self.danh_muc[khoa[0]]['is_active'] = False
        else:                                    # StockRepository.ngung(center_id, part_id)
            self.ton[tuple(khoa)]['is_active'] = False

    def lay_ton(self, center_id, part_id):
        t = self.ton.get((center_id, part_id))
        return {'is_active': True, **t} if t else None

    def them_ton(self, center_id, part_id, min_threshold):
        self.ton[(center_id, part_id)] = {'quantity': 0, 'min_threshold': min_threshold,
                                          'is_active': True}

    def dat_nguong(self, center_id, part_id, min_threshold):
        self.ton[(center_id, part_id)]['min_threshold'] = min_threshold

    def tim(self, center_id, q, chi_duoi_nguong, limit, offset):
        return [], 0

    def ds(self, *a):
        return list(self.phieu.values()), len(self.phieu)


@pytest.fixture
def kho():
    return KhoGia()


@pytest.fixture
def service(kho):
    @contextmanager
    def uow():
        yield kho
        kho.da_commit += 1

    return StockService(uow)


@pytest.fixture
def client(service):
    return create_app(service).test_client()


@pytest.fixture
def dang_nhap(client):
    def _dang_nhap(user_id):
        r = client.post('/api/auth/login', json={'user_id': user_id})
        assert r.status_code == 200, r.get_json()
        return {'Authorization': 'Bearer ' + r.get_json()['token']}
    return _dang_nhap

