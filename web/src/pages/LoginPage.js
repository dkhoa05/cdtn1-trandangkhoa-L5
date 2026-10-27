import { dangNhap } from '../api/auth.api.js';
import { h, thongBao } from '../components/dom.js';

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
