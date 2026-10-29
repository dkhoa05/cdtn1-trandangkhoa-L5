// M2: Xuất linh kiện cho phiếu bảo hành (UC2, QT-09)
import { danhSachPhieuDangXuLy, linhKienCuaPhieu, xuatLinhKien } from '../api/tickets.api.js';
import { DataState } from '../components/DataState.js';
import { PartPicker } from '../components/PartPicker.js';
import { bangCuon, gio, h, thongBao } from '../components/dom.js';

/** M2: chọn phiếu đang xử lý, chọn linh kiện, nhập số lượng rồi xuất; bên dưới là danh sách linh kiện đã xuất cho phiếu đó. */
export function IssuePage(goc) {
  let phieuId = null;
  let linhKien = null;

  const khungKetQua = h('div', { 'aria-live': 'polite' });
  const choDaDung = h('div');
  const dsDaDung = DataState(choDaDung, {
    tai: () => (phieuId ? linhKienCuaPhieu(phieuId) : Promise.resolve({ data: [] })),
    rong: (d) => d.data.length === 0,
    noiDungRong: () => (phieuId ? 'Phiếu này chưa xuất linh kiện nào.' : 'Chọn một phiếu ở trên để xem linh kiện đã dùng.'),
    veKhiCoDuLieu: (d) => bangCuon('Linh kiện đã xuất cho phiếu', h('table', {},
      h('caption', { class: 'chi-doc' }, 'Linh kiện đã xuất cho phiếu đang chọn'),
      h('thead', {}, h('tr', {}, ['Mã', 'Tên linh kiện', 'Số lượng', 'Thời điểm']
        .map((t, i) => h('th', { scope: 'col', class: i === 2 ? 'so' : null }, t)))),
      h('tbody', {}, d.data.map((g) => h('tr', {},
        h('td', {}, g.part_code), h('td', {}, g.part_name),
        h('td', { class: 'so' }, g.quantity), h('td', {}, gio(g.created_at))))))),
  });

  const chonPhieu = h('div');
  DataState(chonPhieu, {
    tai: danhSachPhieuDangXuLy,
    rong: (d) => d.data.length === 0,
    noiDungRong: 'Trung tâm chưa có phiếu nào đang xử lý.',
    veKhiCoDuLieu: (d) => h('select', {
      id: 'phieu',
      onchange: (e) => { phieuId = Number(e.target.value) || null; khungKetQua.replaceChildren(); dsDaDung.taiLai(); },
    }, h('option', { value: '' }, '— Chọn phiếu —'),
    d.data.map((t) => h('option', { value: t.ticket_id }, t.ticket_code))),
  });

  const soLuong = h('input', {
    id: 'so_luong', type: 'number', min: 1, step: 1, value: 1, required: true, inputmode: 'numeric',
    'aria-describedby': 'goi-y-ton', oninput: () => capNhatGoiY(),
  });
  // Gợi ý tồn hiện tại ngay cạnh ô số lượng. Chỉ nhắc, không chặn: máy chủ vẫn là nơi quyết định (QT-09) và
  // trả lỗi 409 nếu vượt tồn, nên người dùng vẫn thấy được thông báo lỗi thật khi cố xuất quá số có.
  const goiY = h('p', { id: 'goi-y-ton', class: 'ghi-chu', 'aria-live': 'polite' });
  function capNhatGoiY() {
    if (!linhKien) { goiY.textContent = ''; goiY.classList.remove('canh-bao-chu'); return; }
    const sl = Number(soLuong.value);
    const vuot = Number.isInteger(sl) && sl > linhKien.quantity;
    goiY.textContent = `Tồn hiện tại: ${linhKien.quantity}. Ngưỡng cảnh báo: ${linhKien.min_threshold}.`
      + (vuot ? ' Số lượng đang nhập lớn hơn tồn, máy chủ sẽ từ chối.' : '');
    goiY.classList.toggle('canh-bao-chu', vuot);
  }
  const picker = PartPicker((p) => { linhKien = p; capNhatGoiY(); });
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
        capNhatGoiY();
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
  h('label', { for: 'linh-kien' }, 'Linh kiện'), picker.phanTu,
  h('label', { for: 'so_luong' }, 'Số lượng'), soLuong, goiY,
  khungKetQua, nut);

  goc.replaceChildren(h('section', { class: 'khung' },
    h('div', { class: 'trang-dau' }, h('h1', {}, 'Xuất linh kiện cho phiếu'),
      h('p', { class: 'ghi-chu' }, 'Chọn phiếu đang xử lý, chọn linh kiện rồi nhập số lượng cần xuất.')),
    form,
    h('h2', {}, 'Linh kiện đã dùng cho phiếu'), choDaDung));
}
