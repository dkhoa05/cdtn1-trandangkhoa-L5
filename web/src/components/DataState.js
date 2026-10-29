import { h } from './dom.js';

/**
 * Bọc một lần tải dữ liệu với ba trạng thái: đang tải, rỗng, lỗi (có nút thử lại).
 *   tai()            -> Promise<dữ liệu>
 *   veKhiCoDuLieu(d) -> Node, chỉ gọi khi có dữ liệu
 *   rong(d)          -> true nếu dữ liệu coi là rỗng
 *   noiDungRong      -> chuỗi, hoặc hàm trả chuỗi (phân biệt "chưa có dữ liệu" với "bộ lọc không ra kết quả")
 *   hanhDongRong(d)  -> (tùy chọn) Node đặt dưới câu giải thích, ví dụ nút "Xóa bộ lọc"; trả null nếu không cần
 * Trả về { taiLai } để trang gọi lại khi dữ liệu đổi.
 */
export function DataState(goc, { tai, veKhiCoDuLieu, rong, noiDungRong = 'Không có dữ liệu.', hanhDongRong }) {
  let lanTai = 0;

  async function taiLai() {
    const lan = ++lanTai;           // bỏ kết quả của lần tải cũ nếu đã có lần mới hơn
    // Khung xương cho thấy chỗ sẽ có dữ liệu; chữ "Đang tải…" vẫn có để trình đọc màn hình đọc được
    goc.replaceChildren(h('div', { class: 'ds ds-tai', role: 'status', 'aria-busy': 'true' },
      h('p', {}, 'Đang tải…'),
      h('div', { class: 'xuong' }), h('div', { class: 'xuong' }), h('div', { class: 'xuong ngan' })));
    try {
      const d = await tai();
      if (lan !== lanTai) return;
      goc.replaceChildren(rong && rong(d)
        ? h('div', { class: 'ds ds-rong' },
          h('p', {}, typeof noiDungRong === 'function' ? noiDungRong(d) : noiDungRong),
          hanhDongRong ? hanhDongRong(d) : null)
        : veKhiCoDuLieu(d));
    } catch (e) {
      if (lan !== lanTai) return;
      goc.replaceChildren(h('div', { class: 'ds ds-loi', role: 'alert' },
        h('p', {}, e.message || 'Đã xảy ra lỗi.'),
        h('button', { type: 'button', class: 'phu', onclick: taiLai }, 'Thử lại')));
    }
  }

  taiLai();
  return { taiLai };
}
