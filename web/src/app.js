import { dangXuat } from './api/auth.api.js';
import { phien } from './api/client.js';
import { h } from './components/dom.js';
import { CatalogPage } from './pages/CatalogPage.js';
import { IssuePage } from './pages/IssuePage.js';
import { LoginPage } from './pages/LoginPage.js';
import { ReceiptPage } from './pages/ReceiptPage.js';
import { StockPage } from './pages/StockPage.js';

const TEN_UNG_DUNG = 'Kho linh kiện thay thế';
const VAI_TRO = { KY_THUAT_VIEN: 'Kỹ thuật viên', QUAN_LY_TT: 'Quản lý trung tâm' };
const goc = document.getElementById('app');
// Mỗi trang: [tên trên menu, hàm vẽ trang, chỉ quản lý trung tâm được dùng]
const TRANG = {
  '#/stock': ['Tồn kho', StockPage, false],
  '#/issue': ['Xuất linh kiện', IssuePage, false],
  '#/receipt': ['Nhập kho & lịch sử', ReceiptPage, true],
  '#/catalog': ['Danh mục', CatalogPage, true],
};
// Kỹ thuật viên không có việc ở trang nhập kho và danh mục nên menu không hiện chúng. Đây chỉ là gọn giao diện:
// việc chặn thật vẫn nằm ở máy chủ (service trả 403), mỗi trang cũng tự báo nếu bị mở bằng địa chỉ gõ tay.
const duocDung = (hash, nguoiDung) => Boolean(TRANG[hash]) && (!TRANG[hash][2] || nguoiDung.role === 'QUAN_LY_TT');

let daVeLanDau = false;

// Vẽ lại màn hình theo địa chỉ sau dấu # (ví dụ #/stock). Chưa đăng nhập thì mọi địa chỉ đều đưa về trang đăng nhập.
function ve() {
  const p = phien.doc();
  const hash = location.hash || '#/stock';
  if (!p) {
    if (hash !== '#/login') { location.hash = '#/login'; return; }
    document.body.classList.remove('da-dang-nhap');
    document.body.querySelector('header.thanh')?.remove();
    document.title = `Đăng nhập · ${TEN_UNG_DUNG}`;
    LoginPage(goc, { vaoTrangChinh: () => { location.hash = '#/stock'; } });
    return;
  }
  const nguoiDung = p.user;
  if (!duocDung(hash, nguoiDung)) { location.hash = '#/stock'; return; }

  document.body.classList.add('da-dang-nhap');
  const noiDung = h('main', { id: 'noi-dung', tabindex: '-1' });
  const thanhDieuHuong = h('header', { class: 'thanh' }, h('div', { class: 'thanh-trong' },
    // Liên kết "#noi-dung" sẽ đổi hash và làm bộ định tuyến vẽ lại, nên dùng nút để chuyển focus vào nội dung
    h('button', { type: 'button', class: 'bo-qua', onclick: () => noiDung.focus() }, 'Bỏ qua điều hướng'),
    h('a', { class: 'thuong-hieu', href: '#/stock' }, 'Kho linh kiện'),
    h('nav', { 'aria-label': 'Chức năng' }, Object.entries(TRANG)
      .filter(([duong]) => duocDung(duong, nguoiDung))
      .map(([duong, [ten]]) => h('a', { href: duong, 'aria-current': duong === hash ? 'page' : false }, ten))),
    h('div', { class: 'nguoi-dung' },
      h('div', { class: 'thong-tin' },
        h('span', { class: 'ten' }, nguoiDung.full_name),
        h('span', { class: 'chuc' }, `${VAI_TRO[nguoiDung.role] || nguoiDung.role} · ${nguoiDung.center_name}`)),
      h('button', { type: 'button', onclick: () => { dangXuat(); location.hash = '#/login'; } }, 'Đăng xuất'))));
  document.body.querySelector('header.thanh')?.remove();
  document.body.prepend(thanhDieuHuong);
  goc.replaceChildren(noiDung);
  document.title = `${TRANG[hash][0]} · ${TEN_UNG_DUNG}`;
  TRANG[hash][1](noiDung, { nguoiDung });
  // Đổi trang thì đưa focus vào nội dung để trình đọc màn hình đọc từ đầu trang mới; lần vẽ đầu không cướp focus
  if (daVeLanDau) noiDung.focus({ preventScroll: true });
  daVeLanDau = true;
}

// Đổi tab hay bấm Back chỉ đổi phần sau dấu #, nên nghe hashchange là đủ, không cần tải lại trang
window.addEventListener('hashchange', ve);
ve();
