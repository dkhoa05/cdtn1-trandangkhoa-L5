// M1: Tồn kho linh kiện (UC1, UC4)
import { timLinhKien } from '../api/parts.api.js';
import { DataState } from '../components/DataState.js';
import { bangCuon, h } from '../components/dom.js';

// Giá trị bên trái gửi lên máy chủ (tham số status và sort của GET /api/parts), chữ bên phải hiện cho người dùng
const TINH_TRANG = [['all', 'Tất cả'], ['low', 'Dưới ngưỡng'], ['out', 'Hết hàng'], ['ok', 'Còn đủ']];
const SAP_XEP = [['code', 'Mã A đến Z'], ['name', 'Tên A đến Z'], ['qty_asc', 'Tồn thấp trước'], ['qty_desc', 'Tồn cao trước']];
const SO_DONG = [10, 20, 50];

/** Chữ và kiểu nhãn cho một dòng tồn kho. Nhãn luôn có chữ, không chỉ dựa vào màu. */
function nhanTinhTrang(p) {
  if (p.quantity === 0) return ['Hết hàng', 'nhan nhan-het'];
  // Dùng "<" chứ không phải "<=": tồn đúng bằng ngưỡng vẫn còn đủ, chỉ thấp hơn mới cảnh báo
  if (p.quantity < p.min_threshold) return ['Dưới ngưỡng', 'nhan nhan-canhbao'];
  return ['Đủ', 'nhan nhan-ok'];
}

const truong = (nhan, id, control, rong = false) =>
  h('div', { class: rong ? 'truong rong' : 'truong' }, h('label', { for: id }, nhan), control);

/** M1: bảng tồn kho của trung tâm người dùng, tìm theo mã hoặc tên, lọc theo tình trạng tồn, sắp xếp và phân trang. */
export function StockPage(goc, { nguoiDung }) {
  let q = '';
  let trangThai = 'all';
  let sapXep = 'code';
  let size = 20;
  let page = 1;

  const tomTat = h('p', { class: 'tom-tat', 'aria-live': 'polite' });   // vùng đọc kết quả cho trình đọc màn hình
  const dangLoc = () => q !== '' || trangThai !== 'all';
  // Nút xóa bộ lọc nằm cạnh dòng tóm tắt và chỉ hiện khi đang có bộ lọc để xóa
  const nutXoa = h('button', { type: 'button', class: 'phu', hidden: true, onclick: () => xoaBoLoc() }, 'Xóa bộ lọc');

  const cho = h('div');
  const ds = DataState(cho, {
    tai: async () => {
      tomTat.textContent = '';
      const d = await timLinhKien({ q, page, size, trangThai, sapXep });
      tomTat.textContent = d.total === 0 ? 'Không có linh kiện nào khớp.'
        : dangLoc() ? `Có ${d.total} linh kiện khớp bộ lọc.` : `Kho có ${d.total} linh kiện.`;
      nutXoa.hidden = !dangLoc();
      return d;
    },
    rong: (d) => d.data.length === 0,
    noiDungRong: () => (dangLoc()                          // AC1.2
      ? 'Không tìm thấy linh kiện nào khớp bộ lọc.'
      : 'Kho trung tâm chưa có linh kiện nào. Quản lý có thể thêm ở mục Danh mục.'),
    // Không cần nút xóa bộ lọc trong khung rỗng: nút ở hàng tóm tắt phía trên đã có sẵn và hiện đúng lúc đang lọc
    veKhiCoDuLieu: (d) => {
      const tongTrang = Math.max(1, Math.ceil(d.total / d.size));
      return h('div', {},
        bangCuon('Bảng tồn kho linh kiện', h('table', {},
          h('caption', { class: 'chi-doc' }, 'Tồn kho linh kiện của trung tâm'),
          h('thead', {}, h('tr', {}, ['Mã', 'Tên linh kiện', 'Tồn', 'Ngưỡng', 'Tình trạng']
            .map((t, i) => h('th', { scope: 'col', class: i === 2 || i === 3 ? 'so' : null }, t)))),
          h('tbody', {}, d.data.map((p) => {
            const [chu, kieu] = nhanTinhTrang(p);
            return h('tr', {},
              h('td', {}, p.part_code), h('td', {}, p.part_name),
              h('td', { class: 'so' }, p.quantity), h('td', { class: 'so' }, p.min_threshold),
              h('td', {}, h('span', { class: kieu }, chu)));
          })))),
        h('div', { class: 'phan-trang' },
          h('button', { type: 'button', class: 'phu', disabled: page <= 1, onclick: () => { page--; ds.taiLai(); } }, 'Trang trước'),
          h('span', {}, `Trang ${d.page}/${tongTrang}`),
          h('button', { type: 'button', class: 'phu', disabled: page >= tongTrang, onclick: () => { page++; ds.taiLai(); } }, 'Trang sau')));
    },
  });

  // Đọc lại các ô lọc rồi tải từ trang 1: mọi thay đổi bộ lọc đều quay về đầu danh sách
  function ap() {
    q = loc.q.value.trim();
    trangThai = loc.status.value;
    sapXep = loc.sort.value;
    size = Number(loc.size.value);
    page = 1;
    ds.taiLai();
  }

  function xoaBoLoc() {
    loc.q.value = '';
    loc.status.value = 'all';          // nhóm radio: gán value chọn đúng nút có giá trị đó
    ap();
  }

  let hen;
  const loc = h('form', {
    class: 'thanh-loc', role: 'search', 'aria-label': 'Lọc tồn kho',
    onsubmit: (e) => { e.preventDefault(); clearTimeout(hen); ap(); },
    // Chọn tình trạng, cách sắp xếp hay số dòng thì áp dụng ngay, không cần bấm Tìm
    onchange: (e) => { if (e.target.name !== 'q') ap(); },
    // Gõ từ khóa: chờ 300 ms sau lần gõ cuối mới gọi API, để gõ nhiều ký tự chỉ tốn một lần gọi
    oninput: (e) => { if (e.target.name === 'q') { clearTimeout(hen); hen = setTimeout(ap, 300); } },
  },
  truong('Tìm theo mã hoặc tên', 'loc-q',
    h('input', { id: 'loc-q', name: 'q', type: 'search', placeholder: 'Ví dụ: camera hoặc MH-IP13', autocomplete: 'off' }), true),
  h('fieldset', { class: 'phan-doan' },
    h('legend', {}, 'Tình trạng tồn'),
    h('div', { class: 'nhom' }, TINH_TRANG.map(([gia, chu], i) =>
      h('label', {}, h('input', { type: 'radio', name: 'status', value: gia, checked: i === 0 }), h('span', {}, chu))))),
  truong('Sắp xếp', 'loc-sort',
    h('select', { id: 'loc-sort', name: 'sort' }, SAP_XEP.map(([gia, chu]) => h('option', { value: gia }, chu)))),
  truong('Số dòng', 'loc-size',
    h('select', { id: 'loc-size', name: 'size' }, SO_DONG.map((n) => h('option', { value: n, selected: n === size }, n)))),
  h('button', { type: 'submit' }, 'Tìm'));

  goc.replaceChildren(h('section', { class: 'khung' },
    h('div', { class: 'trang-dau' },
      h('h1', {}, 'Tồn kho linh kiện'),
      h('p', { class: 'ghi-chu' }, `Trung tâm: ${nguoiDung.center_name}`)),
    loc, h('div', { class: 'tom-tat-hang' }, tomTat, nutXoa), cho));
}
