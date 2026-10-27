"""Kiểm tra định dạng dữ liệu vào (tầng 1 của ba tầng kiểm tra). Không đụng CSDL."""
import re
from datetime import date

from src.errors import AppError

MAX_SIZE = 100


def _loi(fields):
    return AppError('VALIDATION_FAILED', 'Dữ liệu không hợp lệ', fields)


def _so_nguyen_duong(v):
    return isinstance(v, int) and not isinstance(v, bool) and v > 0


def _so_nguyen_khong_am(v):
    return isinstance(v, int) and not isinstance(v, bool) and v >= 0


def _chuoi(v, toi_da):
    return isinstance(v, str) and 1 <= len(v.strip()) <= toi_da


MA_LINH_KIEN = re.compile(r'^[A-Za-z0-9][A-Za-z0-9-]{0,29}$')


def _doc_body(body, bat_buoc):
    if not isinstance(body, dict):
        raise _loi({'body': 'Phải là một đối tượng JSON'})
    fields = {ten: tb for ten, tb in bat_buoc.items() if not _so_nguyen_duong(body.get(ten))}
    if fields:
        raise _loi(fields)
    return {ten: body[ten] for ten in bat_buoc}


def dang_nhap(body):
    return _doc_body(body, {'user_id': 'Phải là số nguyên dương'})


def xuat_kho(body):
    return _doc_body(body, {'part_id': 'Phải là số nguyên dương',
                            'quantity': 'Phải là số nguyên dương'})


def nhap_kho(body):
    return _doc_body(body, {'center_id': 'Trung tâm không hợp lệ',
                            'quantity': 'Số lượng nhập phải lớn hơn 0'})


def phan_trang(args):
    fields, kq = {}, {}
    for ten, mac_dinh, tran in (('page', 1, None), ('size', 20, MAX_SIZE)):
        tho = args.get(ten)
        if tho is None:
            kq[ten] = mac_dinh
            continue
        try:
            v = int(tho)
        except ValueError:
            v = 0
        if v < 1 or (tran and v > tran):
            fields[ten] = 'Phải là số nguyên từ 1' + (f' đến {tran}' if tran else '')
        kq[ten] = v
    if fields:
        raise _loi(fields)
    return kq['page'], kq['size']


def so_nguyen_tuy_chon(args, ten):
    tho = args.get(ten)
    if tho is None or tho == '':
        return None
    try:
        v = int(tho)
    except ValueError:
        v = 0
    if v < 1:
        raise _loi({ten: 'Phải là số nguyên dương'})
    return v


def khoang_ngay(args):
    fields, ngay = {}, {}
    for ten in ('from', 'to'):
        try:
            ngay[ten] = date.fromisoformat(args.get(ten, ''))
        except ValueError:
            fields[ten] = 'Phải là ngày dạng YYYY-MM-DD'
    if not fields and ngay['from'] > ngay['to']:
        fields['from'] = 'Khoảng thời gian không hợp lệ: from phải nhỏ hơn hoặc bằng to'
    if fields:
        raise _loi(fields)
    return ngay['from'], ngay['to']


def _kiem(body, quy_tac):
    """quy_tac: {ten: (ham_kiem, thong_bao)}; gom mọi lỗi theo trường."""
    if not isinstance(body, dict):
        raise _loi({'body': 'Phải là một đối tượng JSON'})
    fields = {ten: tb for ten, (kiem, tb) in quy_tac.items() if not kiem(body.get(ten))}
    if fields:
        raise _loi(fields)
    return {ten: body[ten] for ten in quy_tac}


_TEN = (lambda v: _chuoi(v, 120), 'Tên từ 1 đến 120 ký tự')
_GIA = (_so_nguyen_khong_am, 'Đơn giá phải là số nguyên từ 0')
_NGUONG = (_so_nguyen_khong_am, 'Ngưỡng phải là số nguyên từ 0')


def tao_linh_kien(body):
    d = _kiem(body, {
        'part_code': (lambda v: isinstance(v, str) and MA_LINH_KIEN.match(v) is not None,
                      'Mã gồm chữ, số, dấu gạch ngang, tối đa 30 ký tự'),
        'part_name': _TEN, 'unit_price': _GIA})
    d['part_name'] = d['part_name'].strip()
    return d


def sua_linh_kien(body):
    d = _kiem(body, {'part_name': _TEN, 'unit_price': _GIA})
    d['part_name'] = d['part_name'].strip()
    return d


def them_vao_kho(body):
    return _kiem(body, {'part_id': (_so_nguyen_duong, 'Phải là số nguyên dương'),
                        'min_threshold': _NGUONG})


def doi_nguong(body):
    return _kiem(body, {'min_threshold': _NGUONG})
