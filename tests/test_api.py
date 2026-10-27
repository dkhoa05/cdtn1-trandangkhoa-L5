"""Tầng HTTP: mã trạng thái và hình dạng lỗi khớp docs/api-contract.md."""


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
    assert client.post('/api/auth/login', json={'user_id': 1}).status_code == 401


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
