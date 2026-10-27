// M3: Nhập kho và lịch sử nhập–xuất (UC3, UC5). Chỉ quản lý trung tâm.
import { lichSu, nhapKho, tongHop } from '../api/parts.api.js';
import { DataState } from '../components/DataState.js';
import { PartPicker } from '../components/PartPicker.js';
import { gio, h, thongBao } from '../components/dom.js';

const homNay = () => new Date().toISOString().slice(0, 10);
const dauThang = () => homNay().slice(0, 8) + '01';

export function ReceiptPage(goc, { nguoiDung }) {
  if (nguoiDung.role !== 'QUAN_LY_TT') {
    goc.replaceChildren(h('section', { class: 'khung' }, h('h1', {}, 'Nhập kho và lịch sử'),
      thongBao('canhbao', 'Chỉ quản lý trung tâm được nhập kho và xem lịch sử nhập–xuất.')));
    return;
  }

  let linhKien = null;
  let tu = dauThang();
  let den = homNay();

  const khungKetQua = h('div', { 'aria-live': 'polite' });
  const choLichSu = h('div');
  const choTong = h('div');

  const dsLichSu = DataState(choLichSu, {
    tai: () => (linhKien ? lichSu(linhKien.part_id) : Promise.resolve({ data: [] })),
    rong: (d) => d.data.length === 0,
    noiDungRong: 'Chọn một linh kiện để xem lịch sử, hoặc linh kiện này chưa có giao dịch.',
    veKhiCoDuLieu: (d) => h('table', {},
      h('thead', {}, h('tr', {}, ['Thời điểm', 'Loại', 'Số lượng', 'Phiếu', 'Người thực hiện']
        .map((t) => h('th', { scope: 'col' }, t)))),
      h('tbody', {}, d.data.map((g) => h('tr', {},
        h('td', {}, gio(g.created_at)),
        h('td', {}, g.txn_type === 'NHAP' ? 'Nhập' : 'Xuất'),
        h('td', { class: 'so' }, g.quantity),
        h('td', {}, g.ticket_id ?? '—'),
        h('td', {}, g.created_by_name))))),
  });

  const dsTong = DataState(choTong, {
    tai: () => (linhKien ? tongHop(linhKien.part_id, tu, den) : Promise.resolve(null)),
    rong: (d) => d === null,
    noiDungRong: '',
    veKhiCoDuLieu: (d) => h('p', { class: 'tong' },
      `Từ ${d.from} đến ${d.to}: nhập ${d.total_in}, xuất ${d.total_out}, chênh lệch ${d.net_change >= 0 ? '+' : ''}${d.net_change}.`),
  });

  const lamMoi = () => { dsLichSu.taiLai(); dsTong.taiLai(); };
  const picker = PartPicker((p) => { linhKien = p; lamMoi(); });

  const soLuong = h('input', { id: 'so_luong', type: 'number', min: 1, step: 1, value: 1, required: true });
  const nut = h('button', { type: 'submit' }, 'Ghi nhận nhập kho');
  const formNhap = h('form', {
    onsubmit: async (e) => {
      e.preventDefault();
      khungKetQua.replaceChildren();
      if (!linhKien) {
        khungKetQua.append(thongBao('loi', 'Hãy chọn linh kiện cần nhập.'));
        return;
      }
      nut.disabled = true;
      try {
        const kq = await nhapKho(linhKien.part_id, nguoiDung.center_id, Number(soLuong.value));
        khungKetQua.append(thongBao('ok', `Đã nhập ${kq.quantity} × ${linhKien.part_code}. Tồn mới: ${kq.new_stock}.`));
        picker.taiLai();
        lamMoi();
      } catch (er) {
        const chiTiet = er.fields && Object.values(er.fields).join(' ');
        khungKetQua.append(thongBao('loi', chiTiet || er.message));
      } finally {
        nut.disabled = false;
      }
    },
  },
  h('label', {}, 'Linh kiện'), picker.phanTu,
  h('label', { for: 'so_luong' }, 'Số lượng nhập'), soLuong,
  khungKetQua, nut);

  const formKhoang = h('form', {
    class: 'thanh-loc',
    onsubmit: (e) => { e.preventDefault(); tu = e.target.tu.value; den = e.target.den.value; dsTong.taiLai(); },
  },
  h('label', {}, 'Từ ngày ', h('input', { name: 'tu', type: 'date', value: tu, required: true })),
  h('label', {}, 'Đến ngày ', h('input', { name: 'den', type: 'date', value: den, required: true })),
  h('button', { type: 'submit' }, 'Tính tổng'));

  goc.replaceChildren(h('section', { class: 'khung' },
    h('h1', {}, 'Nhập kho và lịch sử nhập–xuất'), formNhap,
    h('h2', {}, 'Tổng nhập, tổng xuất'), formKhoang, choTong,
    h('h2', {}, 'Lịch sử giao dịch'), choLichSu));
}
