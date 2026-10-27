"""Quy tắc nghiệp vụ kho (tầng service). Ba loại: luồng đúng, giá trị biên, dữ liệu sai."""
import pytest

from src.errors import AppError
from tests.conftest import KHAC_TT, KY_THUAT, QUAN_LY


# ---- Loại 1: luồng đúng ----
def test_xuat_du_ton_thi_giam_ton_va_ghi_giao_dich(service, kho):
    ra = service.xuat_linh_kien(KY_THUAT, 231, 45, 2)
    assert ra['remaining_stock'] == 3
    assert kho.ton[(1, 45)]['quantity'] == 3
    assert [(g['loai'], g['quantity'], g['ticket_id']) for g in kho.giao_dich] == [('XUAT', 2, 231)]


def test_quan_ly_nhap_kho_thi_tang_ton(service, kho):
    ra = service.nhap_kho(QUAN_LY, 45, 1, 10)
    assert ra['new_stock'] == 15
    assert kho.giao_dich[0]['loai'] == 'NHAP'


# ---- Loại 2: giá trị biên (AC3.2, QT-09) ----
def test_xuat_dung_bang_ton_thi_cho_xuat_ton_ve_0_va_canh_bao(service, kho):
    ra = service.xuat_linh_kien(KY_THUAT, 231, 45, 5)
    assert ra['remaining_stock'] == 0
    assert ra['low_stock_alert'] is True


def test_xuat_vuot_ton_dung_1_don_vi_thi_bi_tu_choi_va_khong_tru_ton(service, kho):
    with pytest.raises(AppError) as e:
        service.xuat_linh_kien(KY_THUAT, 231, 45, 6)
    assert e.value.code == 'INSUFFICIENT_STOCK'
    assert kho.ton[(1, 45)]['quantity'] == 5
    assert kho.giao_dich == []


def test_ton_con_dung_bang_nguong_thi_chua_canh_bao(service):
    # Tồn 5, ngưỡng 3: xuất 2 còn 3, không dưới ngưỡng. Xuất 3 còn 2, dưới ngưỡng.
    assert service.xuat_linh_kien(KY_THUAT, 231, 45, 2)['low_stock_alert'] is False
    assert service.xuat_linh_kien(KY_THUAT, 231, 45, 1)['low_stock_alert'] is True


# ---- Loại 3: dữ liệu sai và kiểm soát truy cập (QT-14) ----
def test_ky_thuat_vien_khong_duoc_nhap_kho(service):
    with pytest.raises(AppError) as e:
        service.nhap_kho(KY_THUAT, 45, 1, 10)
    assert e.value.code == 'FORBIDDEN'


def test_xuat_cho_phieu_cua_trung_tam_khac_bi_chan(service, kho):
    with pytest.raises(AppError) as e:
        service.xuat_linh_kien(KHAC_TT, 231, 45, 1)
    assert e.value.code == 'FORBIDDEN'
    assert kho.ton[(1, 45)]['quantity'] == 5


def test_xuat_cho_phieu_da_dong_bi_tu_choi(service):
    with pytest.raises(AppError) as e:
        service.xuat_linh_kien(KY_THUAT, 232, 45, 1)
    assert e.value.code == 'TICKET_NOT_PROCESSING'


def test_xuat_linh_kien_khong_co_trong_kho_thi_404(service):
    with pytest.raises(AppError) as e:
        service.xuat_linh_kien(KY_THUAT, 231, 999, 1)
    assert e.value.code == 'PART_NOT_FOUND'


def test_tra_cuu_trung_tam_khac_bi_chan(service):
    with pytest.raises(AppError) as e:
        service.tim_linh_kien(KY_THUAT, 2, None, 1, 20)
    assert e.value.code == 'FORBIDDEN'


def test_ky_thuat_vien_khong_xem_duoc_lich_su_nhap_xuat(service):
    with pytest.raises(AppError) as e:
        service.lich_su(KY_THUAT, 45, None, 1, 20)
    assert e.value.code == 'FORBIDDEN'
