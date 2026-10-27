"""Hợp đồng dữ liệu giữa lớp nghiệp vụ và giao diện, thi hành bằng các hàm chuyển đổi ở ranh giới.

Giao diện KHÔNG đọc thẳng tên cột của cơ sở dữ liệu: mọi phản hồi đi qua một hàm to_*_view ở đây,
nên đổi tên cột chỉ phải sửa một chỗ, và hàm nào cũng liệt kê rõ từng trường trả ra.

Ba thứ mỗi hợp đồng nêu rõ: HÌNH DẠNG (trường, kiểu), Ý NGHĨA (đơn vị, giá trị đặc biệt) và
HÀNH VI KHI SAI (không có dữ liệu thì trả gì). Tên trường dùng snake_case khớp docs/api-contract.md.
"""
from datetime import datetime


def _iso(moc):
    """Thời điểm dạng ISO 8601 kèm múi giờ, ví dụ 2026-10-28T00:37:52+07:00; None giữ nguyên None."""
    return moc.isoformat() if isinstance(moc, datetime) else moc


def to_part_stock_view(r):
    """Một dòng tồn kho của linh kiện tại trung tâm của người dùng (danh sách tra cứu M1, M2, M3, M4).

    part_id, quantity, min_threshold : số nguyên; quantity và min_threshold luôn >= 0.
    part_code, part_name             : chuỗi, luôn có.
    unit_price                       : số nguyên, đơn vị đồng Việt Nam, luôn có, >= 0.
    Ý nghĩa: quantity < min_threshold nghĩa là dưới ngưỡng cảnh báo (QT-09).
    """
    return {
        'part_id': r['part_id'], 'part_code': r['part_code'], 'part_name': r['part_name'],
        'unit_price': int(r['unit_price']),
        'quantity': r['quantity'], 'min_threshold': r['min_threshold'],
    }


def to_part_view(r):
    """Một linh kiện trong danh mục, không kèm tồn kho (kết quả tạo và sửa linh kiện).

    part_id: số nguyên; part_code, part_name: chuỗi; unit_price: số nguyên đồng Việt Nam.
    """
    return {
        'part_id': r['part_id'], 'part_code': r['part_code'], 'part_name': r['part_name'],
        'unit_price': int(r['unit_price']),
    }


def to_part_detail_view(r):
    """Linh kiện kèm tồn kho tại trung tâm của người dùng (đọc một linh kiện).

    stock: {quantity, min_threshold} khi linh kiện đang có trong kho trung tâm này;
           None khi chưa có hoặc đã gỡ khỏi kho (KHÔNG phải tồn bằng 0).
    """
    ton = r.get('stock')
    chi_tiet = to_part_view(r)
    chi_tiet['stock'] = None if not ton else {
        'quantity': ton['quantity'], 'min_threshold': ton['min_threshold']}
    return chi_tiet


def to_ticket_view(t):
    """Một phiếu bảo hành (chỉ các cột luồng kho cần): ticket_id, center_id là số nguyên;
    ticket_code, status là chuỗi; status 'DANG_XU_LY' mới được xuất linh kiện."""
    return {
        'ticket_id': t['ticket_id'], 'ticket_code': t['ticket_code'],
        'center_id': t['center_id'], 'status': t['status'],
    }


def to_transaction_view(t):
    """Một giao dịch kho trong lịch sử của một linh kiện.

    txn_type   : 'NHAP' hoặc 'XUAT'.
    ticket_id  : số nguyên khi XUAT; None khi NHAP (nhập kho không gắn phiếu).
    created_at : chuỗi ISO 8601 kèm múi giờ.
    """
    return {
        'transaction_id': t['transaction_id'], 'created_at': _iso(t['created_at']),
        'txn_type': t['txn_type'], 'quantity': t['quantity'],
        'ticket_id': t['ticket_id'], 'created_by_name': t['created_by_name'],
    }


def to_used_part_view(g):
    """Một linh kiện đã xuất cho một phiếu (AC2.2): transaction_id, part_id, quantity là số nguyên;
    part_code, part_name là chuỗi; created_at là chuỗi ISO 8601 kèm múi giờ."""
    return {
        'transaction_id': g['transaction_id'], 'part_id': g['part_id'],
        'part_code': g['part_code'], 'part_name': g['part_name'],
        'quantity': g['quantity'], 'created_at': _iso(g['created_at']),
    }


def to_issue_view(d):
    """Kết quả xuất linh kiện cho phiếu (UC2).

    remaining_stock  : tồn còn lại sau khi xuất, số nguyên >= 0.
    low_stock_alert  : True khi remaining_stock thấp hơn ngưỡng cảnh báo (UC6, UC7).
    """
    return {
        'transaction_id': d['transaction_id'], 'ticket_id': d['ticket_id'], 'part_id': d['part_id'],
        'quantity': d['quantity'], 'remaining_stock': d['remaining_stock'],
        'low_stock_alert': d['low_stock_alert'], 'created_at': _iso(d['created_at']),
    }


def to_stock_in_view(d):
    """Kết quả nhập kho (UC3): new_stock là tồn mới sau khi nhập."""
    return {
        'transaction_id': d['transaction_id'], 'part_id': d['part_id'], 'center_id': d['center_id'],
        'quantity': d['quantity'], 'new_stock': d['new_stock'], 'created_at': _iso(d['created_at']),
    }


def to_stock_view(d):
    """Dòng tồn kho sau khi thêm vào kho hoặc đổi ngưỡng: part_id, center_id, quantity, min_threshold."""
    return {
        'part_id': d['part_id'], 'center_id': d['center_id'],
        'quantity': d['quantity'], 'min_threshold': d['min_threshold'],
    }


def to_deactivated_view(d):
    """Kết quả xóa mềm: is_active luôn False; có center_id khi gỡ khỏi kho một trung tâm."""
    kq = {'part_id': d['part_id'], 'is_active': d['is_active']}
    if 'center_id' in d:
        kq['center_id'] = d['center_id']
    return kq


def to_summary_view(d):
    """Tổng hợp nhập xuất trong khoảng ngày (FR7): from, to là chuỗi YYYY-MM-DD;
    total_in, total_out, net_change là số nguyên (net_change = total_in - total_out, có thể âm)."""
    return {
        'part_id': d['part_id'], 'center_id': d['center_id'], 'from': d['from'], 'to': d['to'],
        'total_in': d['total_in'], 'total_out': d['total_out'], 'net_change': d['net_change'],
    }


def to_page_view(kq, chuyen_doi):
    """Giữ nguyên thông tin phân trang (page, size, total), chuyển từng phần tử của data."""
    return {'data': [chuyen_doi(x) for x in kq['data']],
            'page': kq['page'], 'size': kq['size'], 'total': kq['total']}
