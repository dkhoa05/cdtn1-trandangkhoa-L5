import { dangNhap } from '../api/auth.api.js';
import { h, thongBao } from '../components/dom.js';

/** Màn hình đăng nhập. goc: phần tử để vẽ vào; vaoTrangChinh: hàm được gọi sau khi đăng nhập thành công. */
export function LoginPage(goc, { vaoTrangChinh }) {
  const khungLoi = h('div');
  const nut = h('button', { type: 'submit' }, 'Đăng nhập');
  const o = h('input', { id: 'user_id', name: 'user_id', type: 'number', min: 1, required: true, autofocus: true });

  const form = h('form', {
    onsubmit: async (e) => {
      e.preventDefault();
      nut.disabled = true;
      khungLoi.replaceChildren();
      try {
        await dangNhap(Number(o.value));
        vaoTrangChinh();
      } catch (er) {
        const chiTiet = er.fields && er.fields.user_id;
        khungLoi.replaceChildren(thongBao('loi',
          // 401 dùng một câu chung cho cả "sai mã" và "tài khoản bị khóa", để không lộ mã nào có tồn tại
          er.status === 401 ? 'Mã người dùng không đúng hoặc tài khoản đã ngừng hoạt động.'
            : chiTiet || er.message));
      } finally {
        nut.disabled = false;
      }
    },
  },
  h('label', { for: 'user_id' }, 'Mã người dùng'), o,
  h('p', { class: 'ghi-chu' }, 'Dữ liệu mẫu: 2 là kỹ thuật viên trung tâm Ninh Kiều, 101 là quản lý trung tâm Quận 10.'),
  khungLoi, nut);

  goc.replaceChildren(h('section', { class: 'khung nho' }, h('h1', {}, 'Đăng nhập'), form));
}
