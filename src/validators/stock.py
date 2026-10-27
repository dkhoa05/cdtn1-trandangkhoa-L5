"""Kiểm tra định dạng dữ liệu vào (tầng 1 của ba tầng kiểm tra). Không đụng CSDL."""
import re
from datetime import date

from src.errors import AppError

MAX_SIZE = 100          # chặn size quá lớn để một lần gọi không kéo cả bảng về


def _loi(fields):
    return AppError('VALIDATION_FAILED', 'Dữ liệu không hợp lệ', fields)


def _so_nguyen_duong(v):
    # bool là con của int trong Python (True == 1), nên phải loại riêng, nếu không true được coi là số 1
    return isinstance(v, int) and not isinstance(v, bool) and v > 0


def _so_nguyen_khong_am(v):
    return isinstance(v, int) and not isinstance(v, bool) and v >= 0


def _chuoi(v, toi_da):
    return isinstance(v, str) and 1 <= len(v.strip()) <= toi_da


# Mã linh kiện: bắt đầu bằng chữ hoặc số, sau đó thêm chữ, số hoặc dấu gạch ngang, tối đa 30 ký tự
MA_LINH_KIEN = re.compile(r'^[A-Za-z0-9][A-Za-z0-9-]{0,29}$')


def _doc_body(body, bat_buoc):
    """Kiểm body JSON có đủ các trường số nguyên dương trong bat_buoc ({tên trường: thông báo lỗi}).
    Trả dict chỉ gồm các trường đó, nên trường thừa do người dùng gửi lên bị bỏ đi."""
    if not isinstance(body, dict):
        raise _loi({'body': 'Phải là một đối tượng JSON'})
    fields = {ten: tb for ten, tb in bat_buoc.items() if not _so_nguyen_duong(body.get(ten))}
    if fields:
        raise _loi(fields)
    return {ten: body[ten] for ten in bat_buoc}


def dang_nhap(body):
    """Nhận body đăng nhập. Trả {user_id}. Lỗi: VALIDATION_FAILED nếu thiếu hoặc sai kiểu."""
    return _doc_body(body, {'user_id': 'Phải là số nguyên dương'})


def xuat_kho(body):
    """Nhận body xuất kho. Trả {part_id, quantity}. Lỗi: VALIDATION_FAILED, kèm tên trường sai.
    Chỉ kiểm dạng dữ liệu; có đủ hàng để xuất hay không là việc của service."""
    return _doc_body(body, {'part_id': 'Phải là số nguyên dương',
                            'quantity': 'Phải là số nguyên dương'})


def nhap_kho(body):
    """Nhận body nhập kho. Trả {center_id, quantity}. Lỗi: VALIDATION_FAILED, kèm tên trường sai."""
    return _doc_body(body, {'center_id': 'Trung tâm không hợp lệ',
                            'quantity': 'Số lượng nhập phải lớn hơn 0'})


def phan_trang(args):
    """Làm gì: đọc page và size từ query string.
    Nhận: request.args. Trả: (page, size), mặc định (1, 20).
    Lỗi: VALIDATION_FAILED nếu page < 1 hoặc size ngoài khoảng 1 đến MAX_SIZE."""
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
    """Đọc một tham số số nguyên dương không bắt buộc. Trả None nếu vắng mặt hoặc rỗng; VALIDATION_FAILED nếu có mà sai."""
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
    """Làm gì: đọc khoảng ngày from và to (YYYY-MM-DD) từ query string.
    Trả: (from, to) kiểu date. Lỗi: VALIDATION_FAILED nếu sai định dạng hoặc from sau to."""
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
    """quy_tac: {tên trường: (hàm kiểm, thông báo lỗi)}. Gom MỌI lỗi theo trường rồi ném một lần,
    để giao diện tô đỏ hết các ô sai thay vì bắt người dùng sửa từng lỗi một."""
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
    """Nhận body tạo linh kiện. Trả {part_code, part_name, unit_price} đã cắt khoảng trắng đầu cuối của tên.
    Lỗi: VALIDATION_FAILED."""
    d = _kiem(body, {
        'part_code': (lambda v: isinstance(v, str) and MA_LINH_KIEN.match(v) is not None,
                      'Mã gồm chữ, số, dấu gạch ngang, tối đa 30 ký tự'),
        'part_name': _TEN, 'unit_price': _GIA})
    d['part_name'] = d['part_name'].strip()
    return d


def sua_linh_kien(body):
    """Nhận body sửa linh kiện. Trả {part_name, unit_price}; mã linh kiện cố ý không cho sửa. Lỗi: VALIDATION_FAILED."""
    d = _kiem(body, {'part_name': _TEN, 'unit_price': _GIA})
    d['part_name'] = d['part_name'].strip()
    return d


def them_vao_kho(body):
    """Nhận body đưa linh kiện vào kho. Trả {part_id, min_threshold}. Lỗi: VALIDATION_FAILED."""
    return _kiem(body, {'part_id': (_so_nguyen_duong, 'Phải là số nguyên dương'),
                        'min_threshold': _NGUONG})


def doi_nguong(body):
    """Nhận body đổi ngưỡng cảnh báo. Trả {min_threshold}. Lỗi: VALIDATION_FAILED."""
    return _kiem(body, {'min_threshold': _NGUONG})
