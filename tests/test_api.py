"""Tầng HTTP: mã trạng thái và hình dạng lỗi khớp docs/api-contract.md."""
from tests.conftest import MAT_KHAU_TEST


def test_xuat_thanh_cong_tra_201(client, dang_nhap):
    r = client.post('/api/tickets/231/parts', json={'part_id': 45, 'quantity': 2},
                    headers=dang_nhap(2))
    assert r.status_code == 201
    assert r.get_json()['remaining_stock'] == 3


def test_xuat_vuot_ton_tra_409_kem_ma_loi(client, dang_nhap):
    r = client.post('/api/tickets/231/parts', json={'part_id': 45, 'quantity': 6},
                    headers=dang_nhap(2))
    assert r.status_code == 409
    assert r.get_json()['error']['code'] == 'INSUFFICIENT_STOCK'


def test_so_luong_am_hoac_khong_phai_so_nguyen_tra_400_kem_ten_truong(client, dang_nhap):
    h = dang_nhap(2)
    for xau in (-1, 0, 1.5, '3', None):
        r = client.post('/api/tickets/231/parts', json={'part_id': 45, 'quantity': xau}, headers=h)
        assert r.status_code == 400, xau
        assert 'quantity' in r.get_json()['error']['fields']


def test_khong_co_token_hoac_token_gia_tra_401(client):
    assert client.get('/api/parts').status_code == 401
    r = client.get('/api/parts', headers={'Authorization': 'Bearer gia-mao'})
    assert r.status_code == 401


def test_nguoi_dung_da_nghi_khong_dang_nhap_duoc(client):
    r = client.post('/api/auth/login', json={'user_id': 1, 'password': MAT_KHAU_TEST})
    assert r.status_code == 401


def test_sai_mat_khau_hoac_sai_ma_cung_mot_cau_tra_loi_401(client):
    # TD-10: không lộ mã nào có thật, nên sai mật khẩu và sai mã phải giống hệt nhau
    sai_mk = client.post('/api/auth/login', json={'user_id': 2, 'password': 'sai-mat-khau'})
    sai_ma = client.post('/api/auth/login', json={'user_id': 999999, 'password': MAT_KHAU_TEST})
    assert sai_mk.status_code == sai_ma.status_code == 401
    assert sai_mk.get_json() == sai_ma.get_json()
    assert 'token' not in sai_mk.get_json()


def test_dang_nhap_thieu_hoac_sai_kieu_mat_khau_tra_400(client):
    for body in ({'user_id': 2}, {'user_id': 2, 'password': ''}, {'user_id': 2, 'password': 123},
                 {'user_id': 2, 'password': 'a' * 129}):
        r = client.post('/api/auth/login', json=body)
        assert r.status_code == 400, body
        assert 'password' in r.get_json()['error']['fields']


def test_dang_nhap_dung_khong_tra_chuoi_bam_hay_mat_khau(client):
    r = client.post('/api/auth/login', json={'user_id': 2, 'password': MAT_KHAU_TEST})
    assert r.status_code == 200
    assert MAT_KHAU_TEST not in r.get_data(as_text=True)
    assert 'hash' not in r.get_data(as_text=True)


def test_mat_khau_luu_dang_bam_co_salt_rieng():
    from src import auth
    a, b = auth.bam_mat_khau('cung-mot-mat-khau'), auth.bam_mat_khau('cung-mot-mat-khau')
    assert a != b and 'cung-mot-mat-khau' not in a          # salt khác nhau nên chuỗi băm khác nhau
    assert auth.kiem_tra_mat_khau('cung-mot-mat-khau', a)
    assert not auth.kiem_tra_mat_khau('khac', a)
    assert not auth.kiem_tra_mat_khau('cung-mot-mat-khau', None)   # tài khoản chưa có mật khẩu


def test_tra_cuu_trung_tam_khac_tra_403(client, dang_nhap):
    r = client.get('/api/parts?center_id=2', headers=dang_nhap(2))
    assert r.status_code == 403


def test_tong_hop_khoang_ngay_dao_nguoc_tra_400(client, dang_nhap):
    r = client.get('/api/parts/45/transactions/summary?from=2026-09-30&to=2026-09-01',
                   headers=dang_nhap(101))
    assert r.status_code == 400


def test_tong_hop_hop_le(client, dang_nhap):
    r = client.get('/api/parts/45/transactions/summary?from=2026-09-01&to=2026-09-30',
                   headers=dang_nhap(101))
    assert r.get_json()['net_change'] == 7


def test_loi_khong_luong_truoc_tra_500_khong_lo_chi_tiet(client, service, dang_nhap):
    h = dang_nhap(2)
    service.tim_linh_kien = lambda *a, **k: 1 / 0
    r = client.get('/api/parts', headers=h)
    assert r.status_code == 500
    assert 'division' not in r.get_data(as_text=True)
    assert r.get_json()['error']['requestId']


# ---- Dữ liệu vượt giới hạn cột phải bị từ chối 400 (BUG-006), không phải 500 ----
def test_nhap_kho_so_luong_vuot_gioi_han_cot_tra_400_kem_ten_truong(client, dang_nhap, kho):
    r = client.post('/api/parts/45/stock-in', json={'center_id': 1, 'quantity': 100000000000},
                    headers=dang_nhap(101))
    assert r.status_code == 400
    assert 'quantity' in r.get_json()['error']['fields']
    assert kho.ton[(1, 45)]['quantity'] == 5


def test_nhap_kho_dung_gioi_han_cot_van_qua_validator(client, dang_nhap):
    r = client.post('/api/parts/45/stock-in', json={'center_id': 1, 'quantity': 2147483647},
                    headers=dang_nhap(101))
    assert r.status_code == 201


def test_csdl_tu_choi_gia_tri_tra_400_khong_phai_500(client, service, dang_nhap):
    import psycopg

    def loi(*a, **k):
        raise psycopg.DataError('integer out of range')

    h = dang_nhap(2)
    service.tim_linh_kien = loi
    r = client.get('/api/parts', headers=h)
    assert r.status_code == 400
    assert r.get_json()['error']['code'] == 'VALIDATION_FAILED'
    assert 'integer out of range' not in r.get_data(as_text=True)


# ---- Mất kết nối CSDL: lỗi hạ tầng phải ra 503 kèm mã tra cứu, không phải 500 chung chung ----
def _service_mat_db():
    from contextlib import contextmanager

    import psycopg

    from src.services.stock_service import StockService

    @contextmanager
    def uow():
        raise psycopg.OperationalError('connection refused')
        yield  # pragma: no cover

    return StockService(uow)


def test_mat_ket_noi_csdl_tra_503_kem_ma_tra_cuu(dang_nhap_token):
    client = dang_nhap_token
    r = client.get('/api/parts', headers={'Authorization': 'Bearer ' + client.token})
    assert r.status_code == 503
    loi = r.get_json()['error']
    assert loi['code'] == 'DB_UNAVAILABLE'
    assert loi['requestId']
    assert 'refused' not in r.get_data(as_text=True)      # không lộ chi tiết kỹ thuật


def test_loc_tinh_trang_ton_va_sap_xep_duoc_chuyen_xuong_tang_du_lieu(client, dang_nhap, kho):
    r = client.get('/api/parts?q=man&status=out&sort=qty_asc&size=5', headers=dang_nhap(2))
    assert r.status_code == 200
    assert kho.lan_tim_cuoi == {'center_id': 1, 'q': 'man', 'trang_thai': 'out',
                                'sap_xep': 'qty_asc', 'limit': 5, 'offset': 0}


def test_khong_truyen_bo_loc_thi_dung_mac_dinh_tat_ca_sap_theo_ma(client, dang_nhap, kho):
    client.get('/api/parts', headers=dang_nhap(2))
    assert (kho.lan_tim_cuoi['trang_thai'], kho.lan_tim_cuoi['sap_xep']) == ('all', 'code')


def test_bo_loc_sai_gia_tri_tra_400_kem_ten_tham_so(client, dang_nhap):
    h = dang_nhap(2)
    for url, truong in (('/api/parts?status=het', 'status'), ('/api/parts?sort=gia', 'sort'),
                        ('/api/parts/low-stock?sort=1; DROP TABLE part', 'sort')):
        r = client.get(url, headers=h)
        assert r.status_code == 400, url
        assert truong in r.get_json()['error']['fields']


def test_low_stock_luon_la_trang_thai_low_va_van_loc_theo_tu_khoa(client, dang_nhap, kho):
    client.get('/api/parts/low-stock?q=pin&status=ok', headers=dang_nhap(2))
    assert kho.lan_tim_cuoi['trang_thai'] == 'low' and kho.lan_tim_cuoi['q'] == 'pin'
