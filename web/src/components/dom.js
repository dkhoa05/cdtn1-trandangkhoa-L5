// Dựng DOM bằng textContent, không dùng innerHTML để dữ liệu từ API không chèn được mã HTML.
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

export const gio = (iso) =>
  new Date(iso).toLocaleString('vi-VN', { dateStyle: 'short', timeStyle: 'short' });

export function thongBao(loai, noiDung) {
  return h('div', { class: `tb tb-${loai}`, role: loai === 'loi' ? 'alert' : 'status' }, noiDung);
}
