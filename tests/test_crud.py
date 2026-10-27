"""CRUD linh kiện và tồn kho: quy tắc xóa mềm (QT-13) và phân quyền (tầng service + HTTP)."""
import pytest

from src.errors import AppError
from tests.conftest import KY_THUAT, QUAN_LY


def test_tao_linh_kien_moi_roi_doc_lai_duoc(service):
    p = service.tao_linh_kien(QUAN_LY, 'LK-NEW-1', 'Loa ngoài', 120000)
    assert service.lay_linh_kien(QUAN_LY, p['part_id'])['part_name'] == 'Loa ngoài'


def test_sua_linh_kien_doi_ten_va_gia(service):
    ra = service.sua_linh_kien(QUAN_LY, 45, 'Màn hình iPhone 13 Pro', 2800000)
    assert (ra['part_name'], ra['unit_price']) == ('Màn hình iPhone 13 Pro', 2800000)


def test_ma_linh_kien_trung_bi_tu_choi(service):
    with pytest.raises(AppError) as e:
        service.tao_linh_kien(QUAN_LY, 'MH-IP13-001', 'Trùng mã', 1)
    assert e.value.code == 'PART_CODE_EXISTS'


def test_linh_kien_con_ton_thi_khong_ngung_duoc(service):
    with pytest.raises(AppError) as e:
        service.ngung_linh_kien(QUAN_LY, 45)          # kho trung tâm 1 còn 5
    assert e.value.code == 'PART_HAS_STOCK'


def test_linh_kien_khong_con_ton_thi_ngung_mem_va_khong_xoa_vat_ly(service, kho):
    p = service.tao_linh_kien(QUAN_LY, 'LK-NEW-2', 'Ốp lưng', 50000)
    service.ngung_linh_kien(QUAN_LY, p['part_id'])
    assert kho.danh_muc[p['part_id']]['is_active'] is False      # dòng vẫn còn, chỉ đánh dấu
    with pytest.raises(AppError) as e:
        service.lay_linh_kien(QUAN_LY, p['part_id'])
    assert e.value.code == 'PART_NOT_FOUND'


def test_them_vao_kho_voi_ton_bang_0_roi_doi_nguong(service, kho):
    ra = service.them_vao_kho(QUAN_LY, 46, 4)
    assert ra['quantity'] == 0
    service.doi_nguong(QUAN_LY, 46, 9)
    assert kho.ton[(1, 46)]['min_threshold'] == 9


def test_them_vao_kho_lan_hai_bi_tu_choi(service):
    with pytest.raises(AppError) as e:
        service.them_vao_kho(QUAN_LY, 45, 3)          # đã có trong kho
    assert e.value.code == 'STOCK_EXISTS'


def test_go_khoi_kho_chi_khi_ton_ve_0(service):
    with pytest.raises(AppError) as e:
        service.ngung_ton_kho(QUAN_LY, 45)
    assert e.value.code == 'STOCK_NOT_EMPTY'
    service.xuat_linh_kien(QUAN_LY, 231, 45, 5)       # xuất hết
    assert service.ngung_ton_kho(QUAN_LY, 45)['is_active'] is False


def test_ky_thuat_vien_khong_duoc_ghi_danh_muc_va_kho(service):
    for thao_tac in (lambda: service.tao_linh_kien(KY_THUAT, 'X1', 'x', 1),
                     lambda: service.sua_linh_kien(KY_THUAT, 45, 'x', 1),
                     lambda: service.ngung_linh_kien(KY_THUAT, 46),
                     lambda: service.them_vao_kho(KY_THUAT, 46, 1),
                     lambda: service.doi_nguong(KY_THUAT, 45, 1),
                     lambda: service.ngung_ton_kho(KY_THUAT, 45)):
        with pytest.raises(AppError) as e:
            thao_tac()
        assert e.value.code == 'FORBIDDEN'


def test_http_tao_linh_kien_thieu_truong_tra_400_kem_ten_truong(client, dang_nhap):
    r = client.post('/api/parts', json={'part_code': 'khong hop le!', 'unit_price': -5},
                    headers=dang_nhap(101))
    assert r.status_code == 400
    assert set(r.get_json()['error']['fields']) == {'part_code', 'part_name', 'unit_price'}


def test_http_vong_doi_linh_kien_201_200_200_404(client, dang_nhap):
    h = dang_nhap(101)
    tao = client.post('/api/parts', json={'part_code': 'LK-HTTP-1', 'part_name': 'Cáp sạc',
                                          'unit_price': 80000}, headers=h)
    assert tao.status_code == 201
    pid = tao.get_json()['part_id']
    assert client.put(f'/api/parts/{pid}', json={'part_name': 'Cáp sạc nhanh', 'unit_price': 90000},
                      headers=h).status_code == 200
    assert client.delete(f'/api/parts/{pid}', headers=h).status_code == 200
    assert client.get(f'/api/parts/{pid}', headers=h).status_code == 404
