import { h } from './dom.js';

/**
 * Bọc một lần tải dữ liệu với ba trạng thái: đang tải, rỗng, lỗi (có nút thử lại).
 *   tai()            -> Promise<dữ liệu>
 *   veKhiCoDuLieu(d) -> Node, chỉ gọi khi có dữ liệu
 *   rong(d)          -> true nếu dữ liệu coi là rỗng
 *   noiDungRong      -> chuỗi, hoặc hàm trả chuỗi (phân biệt "chưa có dữ liệu" với "bộ lọc không ra kết quả")
 * Trả về { taiLai } để trang gọi lại khi dữ liệu đổi.
 */
export function DataState(goc, { tai, veKhiCoDuLieu, rong, noiDungRong = 'Không có dữ liệu.' }) {
  let lanTai = 0;

  async function taiLai() {
    const lan = ++lanTai;           // bỏ kết quả của lần tải cũ nếu đã có lần mới hơn
    goc.replaceChildren(h('p', { class: 'ds ds-tai', role: 'status' }, 'Đang tải…'));
    try {
      const d = await tai();
      if (lan !== lanTai) return;
      goc.replaceChildren(rong && rong(d)
        ? h('p', { class: 'ds ds-rong' }, typeof noiDungRong === 'function' ? noiDungRong(d) : noiDungRong)
        : veKhiCoDuLieu(d));
    } catch (e) {
      if (lan !== lanTai) return;
      goc.replaceChildren(h('div', { class: 'ds ds-loi', role: 'alert' },
        h('p', {}, e.message || 'Đã xảy ra lỗi.'),
        h('button', { type: 'button', onclick: taiLai }, 'Thử lại')));
    }
  }

  taiLai();
  return { taiLai };
}
