import { dangNhap } from '../api/auth.api.js';
import { h, thongBao } from '../components/dom.js';

// Hai tài khoản trong dữ liệu mẫu (seeds/001_demo.sql, README mục 3). Bấm vào thẻ để điền sẵn mã, chỉ còn nhập mật khẩu.
// Tên người dùng thật hiện ở thanh trên cùng sau khi đăng nhập, lấy từ máy chủ chứ không ghi cứng ở đây.
const TAI_KHOAN_MAU = [
  { id: 2, vaiTro: 'Kỹ thuật viên', noi: 'TTBH Ninh Kiều', moTa: 'Tra cứu tồn kho và xuất linh kiện cho phiếu bảo hành.' },
  { id: 101, vaiTro: 'Quản lý trung tâm', noi: 'TTBH Quận 10', moTa: 'Thêm nhập kho, lịch sử nhập–xuất và danh mục linh kiện.' },
];

/** Màn hình đăng nhập. goc: phần tử để vẽ vào; vaoTrangChinh: hàm được gọi sau khi đăng nhập thành công. */
export function LoginPage(goc, { vaoTrangChinh }) {
  const khungLoi = h('div', { 'aria-live': 'polite' });
  const cacNut = [];                              // khóa hết nút trong lúc chờ máy chủ, tránh bấm hai lần

  async function vao(userId, matKhau) {
    cacNut.forEach((n) => { n.disabled = true; });
    khungLoi.replaceChildren();
    try {
      await dangNhap(userId, matKhau);
      vaoTrangChinh();
    } catch (er) {
      const chiTiet = er.fields && er.fields.user_id;
      khungLoi.replaceChildren(thongBao('loi',
        // 401 dùng một câu chung cho "sai mã", "sai mật khẩu" và "tài khoản bị khóa", để không lộ mã nào có tồn tại
        er.status === 401 ? 'Mã người dùng hoặc mật khẩu không đúng, hoặc tài khoản đã ngừng hoạt động.'
          : chiTiet || er.message));
    } finally {
      cacNut.forEach((n) => { n.disabled = false; });
    }
  }

  const o = h('input', { id: 'user_id', name: 'user_id', type: 'number', min: 1, required: true, inputmode: 'numeric' });
  const mk = h('input', { id: 'password', name: 'password', type: 'password', required: true, maxlength: 128,
    autocomplete: 'current-password' });

  // Thẻ tài khoản mẫu chỉ điền sẵn mã và đưa con trỏ tới ô mật khẩu; việc đăng nhập vẫn qua form bên dưới
  const nhanh = TAI_KHOAN_MAU.map((t, i) => h('button', { type: 'button', class: 'the-dang-nhap', autofocus: i === 0,
    onclick: () => { o.value = t.id; mk.focus(); } },
    h('strong', {}, t.vaiTro), h('span', {}, t.noi), h('small', {}, t.moTa)));

  const nutGui = h('button', { type: 'submit' }, 'Đăng nhập');
  cacNut.push(nutGui);
  const form = h('form', { onsubmit: async (e) => {
    e.preventDefault();
    await vao(Number(o.value), mk.value);
    mk.value = '';                                  // không để mật khẩu nằm lại trên màn hình sau khi gửi
  } },
  h('label', { for: 'user_id' }, 'Mã người dùng'), o,
  h('label', { for: 'password' }, 'Mật khẩu'), mk, nutGui);

  goc.replaceChildren(h('main', { id: 'noi-dung' }, h('section', { class: 'khung nho' },
    h('h1', {}, 'Đăng nhập'),
    h('p', { class: 'ghi-chu' }, 'Chọn một tài khoản mẫu để điền sẵn mã, hoặc nhập mã người dùng khác. Mật khẩu của tài khoản mẫu ghi trong README.'),
    h('div', { class: 'dang-nhap-nhanh' }, nhanh),
    khungLoi,
    form)));
}
