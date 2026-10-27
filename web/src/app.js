import { dangXuat } from './api/auth.api.js';
import { phien } from './api/client.js';
import { h } from './components/dom.js';
import { CatalogPage } from './pages/CatalogPage.js';
import { IssuePage } from './pages/IssuePage.js';
import { LoginPage } from './pages/LoginPage.js';
import { ReceiptPage } from './pages/ReceiptPage.js';
import { StockPage } from './pages/StockPage.js';

const goc = document.getElementById('app');
const TRANG = {
  '#/stock': ['Tồn kho', StockPage],
  '#/issue': ['Xuất linh kiện', IssuePage],
  '#/receipt': ['Nhập kho & lịch sử', ReceiptPage],
  '#/catalog': ['Danh mục', CatalogPage],
};

function ve() {
  const p = phien.doc();
  const hash = location.hash || '#/stock';
  if (!p) {
    if (hash !== '#/login') { location.hash = '#/login'; return; }
    document.body.classList.remove('da-dang-nhap');
    LoginPage(goc, { vaoTrangChinh: () => { location.hash = '#/stock'; } });
    return;
  }
  if (!TRANG[hash]) { location.hash = '#/stock'; return; }

  document.body.classList.add('da-dang-nhap');
  const nguoiDung = p.user;
  const thanhDieuHuong = h('header', { class: 'thanh' },
    h('nav', { 'aria-label': 'Chức năng' }, Object.entries(TRANG).map(([duong, [ten]]) =>
      h('a', { href: duong, 'aria-current': duong === hash ? 'page' : false }, ten))),
    h('div', { class: 'nguoi-dung' },
      h('span', {}, `${nguoiDung.full_name} · ${nguoiDung.center_name}`),
      h('button', { type: 'button', onclick: () => { dangXuat(); location.hash = '#/login'; } }, 'Đăng xuất')));
  const noiDung = h('main');
  document.body.querySelector('header.thanh')?.remove();
  document.body.prepend(thanhDieuHuong);
  goc.replaceChildren(noiDung);
  TRANG[hash][1](noiDung, { nguoiDung });
}

window.addEventListener('hashchange', ve);
ve();
