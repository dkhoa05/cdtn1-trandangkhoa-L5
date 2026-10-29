import { timLinhKien } from '../api/parts.api.js';
import { DataState } from './DataState.js';
import { h } from './dom.js';

/**
 * Ô lọc theo mã/tên + danh sách chọn linh kiện của trung tâm. Gọi onChange(part|null).
 * idChon là id của ô chọn: trang đặt <label for=idChon> để ô chọn có nhãn hiện sẵn cho người dùng và trình đọc màn hình.
 */
export function PartPicker(onChange, { idChon = 'linh-kien' } = {}) {
  let q = '';
  let hen;
  const cho = h('div');
  const o = h('input', {
    id: `${idChon}-loc`, type: 'search', placeholder: 'Gõ mã hoặc tên để thu hẹp danh sách', autocomplete: 'off',
    'aria-label': 'Lọc danh sách linh kiện',
    oninput: (e) => {
      // Chờ 250 ms sau lần gõ cuối mới gọi API, để gõ "ABC" chỉ tốn một lần gọi thay vì ba
      clearTimeout(hen);
      hen = setTimeout(() => { q = e.target.value.trim(); onChange(null); ds.taiLai(); }, 250);
    },
  });
  function xoaTuKhoa() {
    q = '';
    o.value = '';
    onChange(null);
    ds.taiLai();
  }
  const ds = DataState(cho, {
    tai: () => timLinhKien({ q, size: 100 }),
    rong: (d) => d.data.length === 0,
    noiDungRong: () => (q ? 'Không tìm thấy linh kiện nào khớp từ khóa.' : 'Kho trung tâm chưa có linh kiện nào.'),
    hanhDongRong: () => (q
      ? h('button', { type: 'button', class: 'phu', onclick: xoaTuKhoa }, 'Xóa từ khóa')
      : null),
    veKhiCoDuLieu: (d) => {
      const chon = h('select', {
        id: idChon,
        onchange: (e) => onChange(d.data.find((p) => String(p.part_id) === e.target.value) || null),
      }, h('option', { value: '' }, '— Chọn linh kiện —'),
      d.data.map((p) => h('option', { value: p.part_id },
        `${p.part_code} · ${p.part_name} (tồn ${p.quantity})`)));
      return h('div', {}, chon,
        d.total > d.data.length && h('p', { class: 'ghi-chu' },
          `Hiển thị ${d.data.length}/${d.total}. Gõ thêm để lọc.`));
    },
  });
  return { phanTu: h('div', { class: 'picker' }, o, cho), taiLai: ds.taiLai };
}
