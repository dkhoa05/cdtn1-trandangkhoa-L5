// M2: Xuất linh kiện cho phiếu bảo hành (UC2, QT-09)
import { danhSachPhieuDangXuLy, linhKienCuaPhieu, xuatLinhKien } from '../api/tickets.api.js';
import { DataState } from '../components/DataState.js';
import { PartPicker } from '../components/PartPicker.js';
import { gio, h, thongBao } from '../components/dom.js';

/** M2: chọn phiếu đang xử lý, chọn linh kiện, nhập số lượng rồi xuất; bên dưới là danh sách linh kiện đã xuất cho phiếu đó. */
export function IssuePage(goc) {
  let phieuId = null;
  let linhKien = null;

  const khungKetQua = h('div', { 'aria-live': 'polite' });
  const choDaDung = h('div');
  const dsDaDung = DataState(choDaDung, {
    tai: () => (phieuId ? linhKienCuaPhieu(phieuId) : Promise.resolve({ data: [] })),
    rong: (d) => d.data.length === 0,
    noiDungRong: 'Phiếu này chưa xuất linh kiện nào.',
    veKhiCoDuLieu: (d) => h('table', {},
      h('thead', {}, h('tr', {}, ['Mã', 'Tên linh kiện', 'Số lượng', 'Thời điểm']
        .map((t) => h('th', { scope: 'col' }, t)))),
      h('tbody', {}, d.data.map((g) => h('tr', {},
        h('td', {}, g.part_code), h('td', {}, g.part_name),
        h('td', { class: 'so' }, g.quantity), h('td', {}, gio(g.created_at)))))),
  });

  const chonPhieu = h('div');
  DataState(chonPhieu, {
    tai: danhSachPhieuDangXuLy,
    rong: (d) => d.data.length === 0,
    noiDungRong: 'Trung tâm chưa có phiếu nào đang xử lý.',
    veKhiCoDuLieu: (d) => h('select', {
      id: 'phieu', 'aria-label': 'Phiếu bảo hành',
      onchange: (e) => { phieuId = Number(e.target.value) || null; khungKetQua.replaceChildren(); dsDaDung.taiLai(); },
    }, h('option', { value: '' }, '— Chọn phiếu —'),
    d.data.map((t) => h('option', { value: t.ticket_id }, t.ticket_code))),
  });

  const picker = PartPicker((p) => { linhKien = p; });
  const soLuong = h('input', { id: 'so_luong', type: 'number', min: 1, step: 1, value: 1, required: true });
  const nut = h('button', { type: 'submit' }, 'Xác nhận xuất');

  const form = h('form', {
    onsubmit: async (e) => {
      e.preventDefault();
      khungKetQua.replaceChildren();
      if (!phieuId || !linhKien) {
        khungKetQua.append(thongBao('loi', 'Hãy chọn phiếu và linh kiện trước khi xuất.'));
        return;
      }
      nut.disabled = true;     // khóa nút trong lúc chờ máy chủ, tránh bấm hai lần làm xuất trùng
      try {
        const kq = await xuatLinhKien(phieuId, linhKien.part_id, Number(soLuong.value));
        khungKetQua.append(thongBao('ok', `Đã xuất ${kq.quantity} × ${linhKien.part_code}. Tồn còn lại: ${kq.remaining_stock}.`));
        if (kq.low_stock_alert) {
          khungKetQua.append(thongBao('canhbao', 'Tồn kho đã xuống dưới ngưỡng cảnh báo. Cần báo quản lý trung tâm đặt bổ sung.'));
        }
        picker.taiLai();        // làm mới số tồn hiển thị
        linhKien = null;
        dsDaDung.taiLai();
      } catch (er) {
        // Lỗi nghiệp vụ (409 vượt tồn, 422 phiếu đã đóng, 400 sai dữ liệu): giữ nguyên dữ liệu đã nhập.
        const chiTiet = er.fields && Object.values(er.fields).join(' ');
        khungKetQua.append(thongBao('loi', chiTiet ? `${er.message}: ${chiTiet}` : er.message));
      } finally {
        nut.disabled = false;
      }
    },
  },
  h('label', { for: 'phieu' }, 'Phiếu bảo hành đang xử lý'), chonPhieu,
  h('label', {}, 'Linh kiện'), picker.phanTu,
  h('label', { for: 'so_luong' }, 'Số lượng'), soLuong,
  khungKetQua, nut);

  goc.replaceChildren(h('section', { class: 'khung' },
    h('h1', {}, 'Xuất linh kiện cho phiếu'), form,
    h('h2', {}, 'Linh kiện đã dùng cho phiếu'), choDaDung));
}
