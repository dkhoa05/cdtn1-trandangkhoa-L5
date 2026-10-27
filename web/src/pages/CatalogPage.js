// M4: Danh mục linh kiện và tồn kho của trung tâm (thêm, sửa, ngừng sử dụng). Chỉ quản lý trung tâm.
import {
  doiNguong, ngungLinhKien, ngungTonKho, suaLinhKien, taoLinhKien, themVaoKho, timLinhKien,
} from '../api/parts.api.js';
import { DataState } from '../components/DataState.js';
import { h, thongBao } from '../components/dom.js';

const dinhDangGia = (v) => Number(v).toLocaleString('vi-VN') + ' đ';

export function CatalogPage(goc, { nguoiDung }) {
  if (nguoiDung.role !== 'QUAN_LY_TT') {
    goc.replaceChildren(h('section', { class: 'khung' }, h('h1', {}, 'Danh mục linh kiện'),
      thongBao('canhbao', 'Chỉ quản lý trung tâm được thêm, sửa hoặc ngừng sử dụng linh kiện.')));
    return;
  }

  let q = '';
  let page = 1;
  let dangSua = null;                       // linh kiện đang mở form sửa
  const khungKetQua = h('div', { 'aria-live': 'polite' });
  const choForm = h('div');
  const cho = h('div');

  const bao = (loai, noiDung) => khungKetQua.replaceChildren(thongBao(loai, noiDung));
  const loiApi = (er) => {
    const chiTiet = er.fields && Object.values(er.fields).join(' ');
    bao('loi', chiTiet ? `${er.message}: ${chiTiet}` : er.message);
  };
  // Chạy một thao tác ghi, báo kết quả rồi tải lại bảng; lỗi nghiệp vụ hiện nguyên văn từ máy chủ.
  async function thucHien(viec, thongDiepOk) {
    khungKetQua.replaceChildren();
    try {
      await viec();
      bao('ok', thongDiepOk);
      dangSua = null;
      veForm();
      ds.taiLai();
    } catch (er) { loiApi(er); }
  }

  const ds = DataState(cho, {
    tai: () => timLinhKien({ q, page, size: 20 }),
    rong: (d) => d.data.length === 0,
    noiDungRong: () => (q
      ? 'Không tìm thấy linh kiện nào khớp từ khóa.'
      : 'Kho trung tâm chưa có linh kiện nào. Hãy thêm linh kiện đầu tiên ở biểu mẫu phía trên.'),
    hanhDongRong: () => (q
      ? h('button', { type: 'button', class: 'phu', onclick: xoaTuKhoa }, 'Xóa từ khóa')
      : null),
    veKhiCoDuLieu: (d) => {
      const tongTrang = Math.max(1, Math.ceil(d.total / d.size));
      return h('div', {},
        h('table', {},
          h('thead', {}, h('tr', {}, ['Mã', 'Tên linh kiện', 'Đơn giá', 'Tồn', 'Ngưỡng', 'Thao tác']
            .map((t) => h('th', { scope: 'col' }, t)))),
          h('tbody', {}, d.data.map((p) => h('tr', {},
            h('td', {}, p.part_code), h('td', {}, p.part_name),
            h('td', { class: 'so' }, dinhDangGia(p.unit_price)),
            h('td', { class: 'so' }, p.quantity), h('td', { class: 'so' }, p.min_threshold),
            h('td', { class: 'thao-tac' },
              h('button', { type: 'button', class: 'phu', onclick: () => { dangSua = p; veForm(); } }, 'Sửa'),
              h('button', {
                type: 'button', class: 'phu',
                onclick: () => confirm(`Gỡ ${p.part_code} khỏi kho trung tâm?`)
                  && thucHien(() => ngungTonKho(p.part_id), `Đã gỡ ${p.part_code} khỏi kho.`),
              }, 'Gỡ khỏi kho'),
              h('button', {
                type: 'button', class: 'phu',
                onclick: () => confirm(`Ngừng sử dụng ${p.part_code} trong toàn hệ thống?`)
                  && thucHien(() => ngungLinhKien(p.part_id), `Đã ngừng sử dụng ${p.part_code}.`),
              }, 'Ngừng sử dụng')))))),
        h('div', { class: 'phan-trang' },
          h('button', { type: 'button', disabled: page <= 1, onclick: () => { page--; ds.taiLai(); } }, 'Trước'),
          h('span', {}, `Trang ${d.page}/${tongTrang} · ${d.total} linh kiện`),
          h('button', { type: 'button', disabled: page >= tongTrang, onclick: () => { page++; ds.taiLai(); } }, 'Sau')));
    },
  });

  function veForm() {
    const sua = dangSua;
    const ma = h('input', { id: 'ma', value: sua ? sua.part_code : '', disabled: !!sua, required: true, maxlength: 30 });
    const ten = h('input', { id: 'ten', value: sua ? sua.part_name : '', required: true, maxlength: 120 });
    const gia = h('input', { id: 'gia', type: 'number', min: 0, step: 1, value: sua ? sua.unit_price : 0, required: true });
    const nguong = h('input', { id: 'nguong', type: 'number', min: 0, step: 1, value: sua ? sua.min_threshold : 0, required: true });
    choForm.replaceChildren(h('form', {
      class: 'luoi-form',
      onsubmit: (e) => {
        e.preventDefault();
        if (sua) {
          thucHien(async () => {
            await suaLinhKien(sua.part_id, ten.value.trim(), Number(gia.value));
            await doiNguong(sua.part_id, Number(nguong.value));
          }, `Đã cập nhật ${sua.part_code}.`);
        } else {
          thucHien(async () => {
            const moi = await taoLinhKien(ma.value.trim(), ten.value.trim(), Number(gia.value));
            await themVaoKho(moi.part_id, Number(nguong.value));
          }, `Đã thêm ${ma.value.trim()} vào kho với tồn 0. Dùng "Nhập kho" để ghi nhận số lượng.`);
        }
      },
    },
    h('h2', {}, sua ? `Sửa linh kiện ${sua.part_code}` : 'Thêm linh kiện mới'),
    h('label', { for: 'ma' }, 'Mã linh kiện'), ma,
    h('label', { for: 'ten' }, 'Tên linh kiện'), ten,
    h('label', { for: 'gia' }, 'Đơn giá (đ)'), gia,
    h('label', { for: 'nguong' }, 'Ngưỡng cảnh báo'), nguong,
    h('div', { class: 'hang-nut' },
      h('button', { type: 'submit' }, sua ? 'Lưu thay đổi' : 'Thêm linh kiện'),
      sua && h('button', { type: 'button', class: 'phu', onclick: () => { dangSua = null; veForm(); } }, 'Hủy'))));
  }
  veForm();

  function xoaTuKhoa() {
    q = '';
    page = 1;
    loc.reset();
    ds.taiLai();
  }

  const loc = h('form', {
    class: 'thanh-loc',
    onsubmit: (e) => { e.preventDefault(); q = e.target.q.value.trim(); page = 1; ds.taiLai(); },
  },
  h('input', { name: 'q', type: 'search', placeholder: 'Mã hoặc tên linh kiện', 'aria-label': 'Tìm linh kiện' }),
  h('button', { type: 'submit' }, 'Tìm'));

  goc.replaceChildren(h('section', { class: 'khung' },
    h('h1', {}, 'Danh mục linh kiện và kho'),
    h('p', { class: 'ghi-chu' }, `Trung tâm: ${nguoiDung.center_name}. Linh kiện còn tồn không thể ngừng sử dụng; xóa chỉ là xóa mềm.`),
    choForm, khungKetQua, loc, cho));
}
