// Dựng DOM bằng textContent, không dùng innerHTML để dữ liệu từ API không chèn được mã HTML.
/**
 * Tạo một phần tử HTML.
 * thuocTinh: thuộc tính thường; khóa bắt đầu bằng 'on' là sự kiện (onclick -> click); true bật thuộc tính, false hoặc null thì bỏ.
 * con: phần tử con, có thể lồng mảng; chuỗi và số được thêm như văn bản thuần nên không chèn được HTML.
 */
export function h(tag, thuocTinh = {}, ...con) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(thuocTinh)) {
    if (k.startsWith('on')) el.addEventListener(k.slice(2), v);
    else if (v === true) el.setAttribute(k, '');
    else if (v !== false && v !== null && v !== undefined) el.setAttribute(k, v);
  }
  for (const c of con.flat()) {
    if (c === null || c === undefined || c === false) continue;
    el.append(c instanceof Node ? c : document.createTextNode(String(c)));
  }
  return el;
}

/** Đổi chuỗi thời điểm ISO của máy chủ sang giờ địa phương dạng ngắn kiểu Việt Nam. */
export const gio = (iso) =>
  new Date(iso).toLocaleString('vi-VN', { dateStyle: 'short', timeStyle: 'short' });

/** Khung thông báo. loai: 'ok', 'canhbao' hoặc 'loi'. Lỗi dùng role alert để trình đọc màn hình đọc ngay, loại khác dùng role status. */
export function thongBao(loai, noiDung) {
  return h('div', { class: `tb tb-${loai}`, role: loai === 'loi' ? 'alert' : 'status' }, noiDung);
}
