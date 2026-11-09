"""Chạy các test case API trong docs/test-plan.md trên hệ thống đang chạy, in request và kết quả thật.

Chạy bằng: python tests/tc_api.py TC-07 (bỏ mã thì chạy cả ba). Chỉ dùng thư viện chuẩn, không cần venv.
"""
import json
import os
import sys
import urllib.error
import urllib.request

GOC = 'http://localhost:5000'
TO = 100000000000                     # vượt giới hạn cột INT của PostgreSQL (2147483647)


def goi(method, duong_dan, user=None, body=None):
    tieu_de = {'Content-Type': 'application/json'}
    if user:
        tieu_de['Authorization'] = 'Bearer ' + dang_nhap(user)
    req = urllib.request.Request(GOC + duong_dan, method=method, headers=tieu_de,
                                 data=None if body is None else json.dumps(body).encode())
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def dang_nhap(user):
    # Mật khẩu mẫu lấy từ biến DEMO_PASSWORD (giá trị trong .env); không ghi cứng trong mã
    if 'DEMO_PASSWORD' not in os.environ:
        sys.exit('Hay dat bien moi truong DEMO_PASSWORD (gia tri trong .env) truoc khi chay.')
    return goi('POST', '/api/auth/login', body={'user_id': user, 'password': os.environ['DEMO_PASSWORD']})[1]['token']


def ton(user, part_code):
    return goi('GET', f'/api/parts?q={part_code}', user)[1]['data'][0]['quantity']


def in_kq(ma, mong_doi, status, than, *them):
    print(f'{ma} | mong doi: {mong_doi}\n     thuc te: HTTP {status}')
    print('     than phan hoi:', json.dumps(than, ensure_ascii=False)[:300])
    for dong in them:
        print('    ', dong)


def tc_02():
    s, d = goi('GET', '/api/parts?size=1', 2)
    in_kq('TC-02 GET /api/parts (user 2)', '200, co du lieu', s, d, f'tong so linh kien: {d.get("total")}')


def tc_07():
    s, d = goi('POST', '/api/tickets/51/parts', 2, {'part_id': 64, 'quantity': 0})
    in_kq('TC-07 POST /api/tickets/51/parts quantity=0', '400, VALIDATION_FAILED, neu truong quantity', s, d)


def tc_08():
    truoc = ton(101, 'MH-SS-01')
    s, d = goi('POST', '/api/parts/1/stock-in', 101, {'center_id': 1, 'quantity': TO})
    in_kq(f'TC-08 POST /api/parts/1/stock-in quantity={TO}', '400, neu truong quantity, ton khong doi', s, d,
          f'ton truoc/sau: {truoc} -> {ton(101, "MH-SS-01")}')


CAC_CA = {'TC-02': tc_02, 'TC-07': tc_07, 'TC-08': tc_08}

if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    for ma in sys.argv[1:] or CAC_CA:
        CAC_CA[ma]()
