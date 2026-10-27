// M1: Tồn kho linh kiện (UC1, UC4)
import { timLinhKien } from '../api/parts.api.js';
import { DataState } from '../components/DataState.js';
import { h } from '../components/dom.js';

export function StockPage(goc, { nguoiDung }) {
  let q = '';
  let duoiNguong = false;
  let page = 1;

  const cho = h('div');
  const ds = DataState(cho, {
    tai: () => timLinhKien({ q, page, duoiNguong }),
    rong: (d) => d.data.length === 0,
    noiDungRong: () => (q || duoiNguong                  // AC1.2
      ? 'Không tìm thấy linh kiện nào khớp bộ lọc.'
      : 'Kho trung tâm chưa có linh kiện nào. Quản lý có thể thêm ở mục Danh mục.'),
    hanhDongRong: () => (q || duoiNguong
      ? h('button', { type: 'button', class: 'phu', onclick: xoaBoLoc }, 'Xóa bộ lọc')
      : null),
    veKhiCoDuLieu: (d) => {
      const tongTrang = Math.max(1, Math.ceil(d.total / d.size));
      return h('div', {},
        h('table', {},
          h('thead', {}, h('tr', {}, ['Mã', 'Tên linh kiện', 'Tồn', 'Ngưỡng', 'Trạng thái']
            .map((t) => h('th', { scope: 'col' }, t)))),
          h('tbody', {}, d.data.map((p) => {
            const thap = p.quantity < p.min_threshold;
            return h('tr', {},
              h('td', {}, p.part_code), h('td', {}, p.part_name),
              h('td', { class: 'so' }, p.quantity), h('td', { class: 'so' }, p.min_threshold),
              h('td', {}, h('span', { class: thap ? 'nhan nhan-canhbao' : 'nhan nhan-ok' },
                thap ? 'Dưới ngưỡng' : 'Đủ')));
          }))),
        h('div', { class: 'phan-trang' },
          h('button', { type: 'button', disabled: page <= 1, onclick: () => { page--; ds.taiLai(); } }, 'Trước'),
          h('span', {}, `Trang ${d.page}/${tongTrang} · ${d.total} linh kiện`),
          h('button', { type: 'button', disabled: page >= tongTrang, onclick: () => { page++; ds.taiLai(); } }, 'Sau')));
    },
  });

  function xoaBoLoc() {
    q = '';
    duoiNguong = false;
    page = 1;
    loc.reset();
    ds.taiLai();
  }

  const loc = h('form', {
    class: 'thanh-loc',
    onsubmit: (e) => {
      e.preventDefault();
      q = e.target.q.value.trim();
      duoiNguong = e.target.low.checked;
      page = 1;
      ds.taiLai();
    },
  },
  h('input', { name: 'q', type: 'search', placeholder: 'Mã hoặc tên linh kiện', 'aria-label': 'Tìm linh kiện' }),
  h('label', { class: 'dong' }, h('input', { name: 'low', type: 'checkbox' }), 'Chỉ hiện dưới ngưỡng cảnh báo'),
  h('button', { type: 'submit' }, 'Tìm'));

  goc.replaceChildren(h('section', { class: 'khung' },
    h('h1', {}, 'Tồn kho linh kiện'),
    h('p', { class: 'ghi-chu' }, `Trung tâm: ${nguoiDung.center_name}`),
    loc, cho));
}
