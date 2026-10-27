"""Log JSON ra stdout: có thời điểm ISO, requestId khớp header, và KHÔNG chứa token hay chi tiết kỹ thuật."""
import json
import re

from src.log_config import che

ISO_8601 = re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}(\+|-)\d{2}:\d{2}$')


def doc_log(capsys):
    return [json.loads(d) for d in capsys.readouterr().out.splitlines() if d.strip().startswith('{')]


def test_moi_request_co_mot_dong_log_json_voi_request_id_khop_header(client, dang_nhap, capsys):
    h = dang_nhap(2)
    capsys.readouterr()                                   # bỏ log của lần đăng nhập
    r = client.get('/api/parts', headers={**h, 'X-Request-Id': 'abc-123'})
    dong = [d for d in doc_log(capsys) if d['thong_diep'] == 'yeu cau hoan tat'][-1]
    assert r.headers['X-Request-Id'] == 'abc-123' == dong['requestId']
    assert ISO_8601.match(dong['thoi_diem'])
    assert (dong['phuong_thuc'], dong['duong_dan'], dong['ma_trang_thai']) == ('GET', '/api/parts', 200)


def test_log_khong_chua_token_dang_nhap(client, dang_nhap, capsys):
    h = dang_nhap(2)
    token = h['Authorization'].split()[1]
    client.get('/api/parts', headers=h)
    assert token not in capsys.readouterr().out


def test_che_cac_truong_nhay_cam():
    ra = che({'user_id': 7, 'Authorization': 'Bearer x', 'ngoai': {'DB_PASSWORD': 'p', 'ok': 1}})
    assert ra == {'user_id': 7, 'Authorization': '***', 'ngoai': {'DB_PASSWORD': '***', 'ok': 1}}


def test_loi_nghiep_vu_ghi_muc_info_kem_ma_loi_khong_ghi_error(client, dang_nhap, capsys):
    h = dang_nhap(2)
    capsys.readouterr()
    client.post('/api/tickets/231/parts', json={'part_id': 45, 'quantity': 99}, headers=h)
    dong = doc_log(capsys)
    vp = [d for d in dong if d['thong_diep'] == 'vi pham quy tac'][0]
    assert vp['muc'] == 'info' and vp['ma_loi'] == 'INSUFFICIENT_STOCK' and vp['user_id'] == 2
    assert not [d for d in dong if d['muc'] == 'error']   # lỗi người dùng không phải sự cố


def test_mat_ket_noi_csdl_ghi_error_mot_lan_kem_ngan_xep_va_ma_tra_cuu(dang_nhap_token, capsys):
    client = dang_nhap_token
    capsys.readouterr()
    r = client.get('/api/parts', headers={'Authorization': 'Bearer ' + client.token})
    loi = [d for d in doc_log(capsys) if d['muc'] == 'error']
    assert len(loi) == 1                                  # ghi log đúng một lần, ở trình xử lý duy nhất
    assert loi[0]['requestId'] == r.get_json()['error']['requestId']
    assert 'ngan_xep' in loi[0] and 'refused' not in r.get_data(as_text=True)
