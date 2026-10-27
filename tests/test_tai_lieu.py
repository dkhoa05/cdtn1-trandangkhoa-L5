"""README là thứ giảng viên làm theo từng dòng: không được có ký tự hỏng và phải đúng quy ước bốn bước."""
import re
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent


def doc(duong_dan):
    return (GOC / duong_dan).read_text(encoding='utf-8')


def ky_tu_dieu_khien(noi_dung):
    return sorted({hex(ord(c)) for c in noi_dung if ord(c) < 32 and c not in '\n\r\t'})


def cac_buoc_muc_3(readme):
    muc = re.search(r'## 3\. Hướng dẫn chạy\n(.*?)\n## 4\.', readme, re.S).group(1)
    return re.findall(r'^\d+\. ', muc, re.M)


def test_tai_lieu_khong_co_ky_tu_dieu_khien_an():
    # Lỗi thật đã gặp (BUG-005): "\a" trong "venv\Scripts\activate" bị đổi thành ký tự BEL khi ghi tệp.
    for tep in ['README.md', *sorted(str(p.relative_to(GOC)) for p in (GOC / 'docs').glob('*.md'))]:
        assert ky_tu_dieu_khien(doc(tep)) == [], tep


def test_readme_muc_3_toi_da_bon_buoc():
    assert 1 <= len(cac_buoc_muc_3(doc('README.md'))) <= 4


def test_cac_lenh_trong_readme_tro_den_tep_co_that():
    readme = doc('README.md')
    for lenh, tep in (('pip install -r requirements.txt', 'requirements.txt'),
                      ('python -m src.db_init', 'src/db_init.py'),
                      ('python -m src.app', 'src/app.py'),
                      ('copy .env.example .env', '.env.example')):
        assert lenh in readme and (GOC / tep).exists(), lenh
