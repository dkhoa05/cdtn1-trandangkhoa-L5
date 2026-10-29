import { dangNhap } from '../api/auth.api.js';
import { h, thongBao } from '../components/dom.js';

// Hai tài khoản trong dữ liệu mẫu (seeds/001_demo.sql, README mục 3). Bấm một lần là vào, không phải nhớ và gõ mã.
// Tên người dùng thật hiện ở thanh trên cùng sau khi đăng nhập, lấy từ máy chủ chứ không ghi cứng ở đây.
const TAI_KHOAN_MAU = [
  { id: 2, vaiTro: 'Kỹ thuật viên', noi: 'TTBH Ninh Kiều', moTa: 'Tra cứu tồn kho và xuất linh kiện cho phiếu bảo hành.' },
  { id: 101, vaiTro: 'Quản lý trung tâm', noi: 'TTBH Quận 10', moTa: 'Thêm nhập kho, lịch sử nhập–xuất và danh mục linh kiện.' },
];

/** Màn hình đăng nhập. goc: phần tử để vẽ vào; vaoTrangChinh: hàm được gọi sau khi đăng nhập thành công. */
export function LoginPage(goc, { vaoTrangChinh }) {
  const khungLoi = h('div', { 'aria-live': 'polite' });
  const cacNut = [];                              // khóa hết nút trong lúc chờ máy chủ, tránh bấm hai lần

  async function vao(userId) {
    cacNut.forEach((n) => { n.disabled = true; });
    khungLoi.replaceChildren();
    try {
      await dangNhap(userId);
      vaoTrangChinh();
    } catch (er) {
      const chiTiet = er.fields && er.fields.user_id;
      khungLoi.replaceChildren(thongBao('loi',
        // 401 dùng một câu chung cho cả "sai mã" và "tài khoản bị khóa", để không lộ mã nào có tồn tại
        er.status === 401 ? 'Mã người dùng không đúng hoặc tài khoản đã ngừng hoạt động.'
          : chiTiet || er.message));
    } finally {
      cacNut.forEach((n) => { n.disabled = false; });
    }
  }

  const nhanh = TAI_KHOAN_MAU.map((t, i) => {
    const nut = h('button', { type: 'button', class: 'the-dang-nhap', autofocus: i === 0, onclick: () => vao(t.id) },
      h('strong', {}, t.vaiTro), h('span', {}, t.noi), h('small', {}, t.moTa));
    cacNut.push(nut);
    return nut;
  });

  const o = h('input', { id: 'user_id', name: 'user_id', type: 'number', min: 1, required: true, inputmode: 'numeric' });
  const nutGui = h('button', { type: 'submit' }, 'Đăng nhập');
  cacNut.push(nutGui);
  const form = h('form', { onsubmit: (e) => { e.preventDefault(); vao(Number(o.value)); } },
    h('label', { for: 'user_id' }, 'Mã người dùng'), o, nutGui);

  goc.replaceChildren(h('main', { id: 'noi-dung' }, h('section', { class: 'khung nho' },
    h('h1', {}, 'Đăng nhập'),
    h('p', { class: 'ghi-chu' }, 'Chọn một tài khoản mẫu để vào ngay. Bản thử nghiệm chưa có mật khẩu.'),
    h('div', { class: 'dang-nhap-nhanh' }, nhanh),
    khungLoi,
    h('details', { class: 'khac' }, h('summary', {}, 'Đăng nhập bằng mã người dùng khác'), form))));
}
