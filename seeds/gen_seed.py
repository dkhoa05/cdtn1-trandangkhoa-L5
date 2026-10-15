"""Sinh seeds/001_demo.sql từ bộ dữ liệu case study Mekong Mobile.

Chạy một lần khi cần tạo lại dữ liệu mẫu:
    python seeds/gen_seed.py <thư mục chứa các tệp .csv của dataset>

Tệp SQL sinh ra đã được commit, người chạy hệ thống không cần dataset gốc.
"""
import csv
import sys
from pathlib import Path

MOC_GIAO_DICH = '2026-07-01'   # chỉ nạp giao dịch từ ngày này để tệp seed gọn
MA_QUAN_LY = 100               # user_id quản lý = 100 + center_id


def doc(thu_muc, ten):
    with open(Path(thu_muc) / ten, encoding='utf-8') as f:
        return list(csv.DictReader(f))


def q(v):
    """Giá trị SQL: chuỗi được bọc nháy đơn, rỗng thành NULL."""
    if v is None or v == '':
        return 'NULL'
    return "'" + str(v).replace("'", "''") + "'"


def insert(bang, cot, dong):
    gia_tri = ',\n'.join('(' + ', '.join(d) + ')' for d in dong)
    return f'INSERT INTO {bang} ({", ".join(cot)}) VALUES\n{gia_tri}\nON CONFLICT DO NOTHING;\n'


def main(thu_muc):
    centers = doc(thu_muc, 'service_centers.csv')
    parts = doc(thu_muc, 'parts.csv')
    stock = doc(thu_muc, 'part_stock.csv')
    techs = doc(thu_muc, 'technicians.csv')
    tickets = doc(thu_muc, 'tickets_history.csv')
    txns = [t for t in doc(thu_muc, 'part_transactions.csv') if t['ngay'] >= MOC_GIAO_DICH]

    # Phiếu cần nạp: phiếu đang xử lý (để demo xuất kho) và phiếu có giao dịch xuất được nạp.
    ma_phieu_can = {t['ticket_code'] for t in txns if t['ticket_code']}
    tickets = [t for t in tickets if t['status'] == 'DANG_XU_LY' or t['ticket_code'] in ma_phieu_can]
    phieu_theo_ma = {t['ticket_code']: t for t in tickets}

    ktv_theo_tt = {}
    for k in techs:
        if k['is_active'] == 'true':
            ktv_theo_tt.setdefault(k['center_id'], k['technician_id'])
    ma_ktv = {k['technician_id']: k['center_id'] for k in techs}

    def nguoi_xuat(phieu):
        # Ưu tiên kỹ thuật viên của phiếu nếu cùng trung tâm, không thì lấy KTV đầu tiên của trung tâm.
        k = phieu['technician_id']
        return k if ma_ktv.get(k) == phieu['center_id'] else ktv_theo_tt[phieu['center_id']]

    out = ['-- Dữ liệu mẫu sinh bởi seeds/gen_seed.py, KHÔNG sửa tay.',
           '-- ON CONFLICT DO NOTHING để nạp lại lần hai không nhân đôi dữ liệu.\n']
    out.append(insert('service_center', ['center_id', 'center_code', 'center_name', 'city'],
                      [[c['center_id'], q(c['center_code']), q(c['center_name']), q(c['thanh_pho'])]
                       for c in centers]))
    users = [[k['technician_id'], q(k['ho_ten']), q('KY_THUAT_VIEN'), k['center_id'], k['is_active']]
             for k in techs]
    users += [[str(MA_QUAN_LY + int(c['center_id'])), q('Quản lý ' + c['center_code']), q('QUAN_LY_TT'),
               c['center_id'], 'true'] for c in centers]
    out.append(insert('app_user', ['user_id', 'full_name', 'role', 'center_id', 'is_active'], users))
    out.append(insert('part', ['part_id', 'part_code', 'part_name', 'unit_price'],
                      [[p['part_id'], q(p['part_code']), q(p['part_name']), p['unit_price']] for p in parts]))
    out.append(insert('part_stock', ['center_id', 'part_id', 'quantity', 'min_threshold'],
                      [[s['center_id'], s['part_id'], s['quantity'], s['min_threshold']] for s in stock]))
    out.append(insert('ticket', ['ticket_id', 'ticket_code', 'center_id', 'status'],
                      [[t['ticket_id'], q(t['ticket_code']), t['center_id'], q(t['status'])] for t in tickets]))
    rows = []
    for t in txns:
        phieu = phieu_theo_ma.get(t['ticket_code'])
        nguoi = nguoi_xuat(phieu) if t['loai'] == 'XUAT' else str(MA_QUAN_LY + int(t['center_id']))
        rows.append([t['transaction_id'], t['center_id'], t['part_id'], q(t['loai']), t['so_luong'],
                     phieu['ticket_id'] if phieu else 'NULL', nguoi, q(t['ngay'] + ' 08:00+07')])
    out.append(insert('part_transaction', ['transaction_id', 'center_id', 'part_id', 'txn_type', 'quantity',
                                           'ticket_id', 'created_by', 'created_at'], rows))
    # Đẩy sequence lên sau khóa lớn nhất để bản ghi tạo mới không trùng khóa với dữ liệu mẫu.
    for bang, cot in [('service_center', 'center_id'), ('app_user', 'user_id'), ('part', 'part_id'),
                      ('ticket', 'ticket_id'), ('part_transaction', 'transaction_id')]:
        out.append(f"SELECT setval(pg_get_serial_sequence('{bang}', '{cot}'), "
                   f"(SELECT COALESCE(MAX({cot}), 1) FROM {bang}));")

    dich = Path(__file__).with_name('001_demo.sql')
    dich.write_text('\n'.join(out) + '\n', encoding='utf-8')
    print(f'{dich}: {len(centers)} trung tâm, {len(users)} người dùng, {len(parts)} linh kiện, '
          f'{len(stock)} dòng tồn kho, {len(tickets)} phiếu, {len(rows)} giao dịch')


if __name__ == '__main__':
    main(sys.argv[1])
