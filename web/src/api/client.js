// Điểm duy nhất trong frontend được phép gọi fetch(). Các trang chỉ gọi *.api.js.
// Gom về một chỗ để việc gắn token, xử lý hết phiên (401) và đổi lỗi mạng thành thông báo tiếng Việt chỉ viết một lần.

// Phiên đăng nhập lưu trong sessionStorage: đóng tab là mất, khác localStorage nên đỡ nguy hiểm hơn nếu máy dùng chung.
// Hạn chế đã biết: mã JavaScript chạy trong trang (XSS) vẫn đọc được token; trang không chèn HTML thô nên rủi ro này thấp.
const KHOA_PHIEN = 'l5_phien';

/** Phiên hiện tại { token, user } trong sessionStorage. */
export const phien = {
  /** Trả phiên đã lưu, hoặc null nếu chưa đăng nhập hay dữ liệu lưu bị hỏng. */
  doc() {
    try { return JSON.parse(sessionStorage.getItem(KHOA_PHIEN)); } catch { return null; }
  },
  luu(p) { sessionStorage.setItem(KHOA_PHIEN, JSON.stringify(p)); },
  xoa() { sessionStorage.removeItem(KHOA_PHIEN); },
};

/**
 * Lỗi từ máy chủ, đã đổi sang một dạng duy nhất để trang chỉ cần catch một kiểu.
 * status: mã HTTP (0 nếu không kết nối được). code: mã lỗi nghiệp vụ như INSUFFICIENT_STOCK.
 * message: câu có thể hiển thị cho người dùng. fields: { tên trường: lý do sai } nếu có.
 */
export class ApiError extends Error {
  constructor(status, code, message, fields = {}) {
    super(message);
    this.status = status;
    this.code = code;
    this.fields = fields;
  }
}

/**
 * Hợp đồng: gọi một endpoint của máy chủ.
 * Nhận: method (GET, POST...), duongDan bắt đầu bằng '/' (không kèm '/api'), tùy chọn query và body.
 *   Tham số query bị bỏ nếu là undefined, null hoặc chuỗi rỗng.
 * Trả: dữ liệu JSON đã giải mã khi máy chủ trả 2xx.
 * Lỗi: ném ApiError. Mất mạng thì status = 0 và code = 'NETWORK'.
 *   Nhận 401 khi đang đăng nhập thì xóa phiên và đưa về trang đăng nhập trước khi ném lỗi.
 */
export async function goi(method, duongDan, { query, body } = {}) {
  // Chỉ dùng địa chỉ cùng nguồn (location.origin) vì Flask phục vụ cả giao diện lẫn API, nên không cần cấu hình địa chỉ API riêng.
  const url = new URL('/api' + duongDan, location.origin);
  for (const [k, v] of Object.entries(query || {})) {
    if (v !== undefined && v !== null && v !== '') url.searchParams.set(k, v);
  }
  const p = phien.doc();
  const headers = { Accept: 'application/json' };
  if (body !== undefined) headers['Content-Type'] = 'application/json';
  if (p) headers.Authorization = 'Bearer ' + p.token;

  let res;
  try {
    res = await fetch(url, { method, headers, body: body === undefined ? undefined : JSON.stringify(body) });
  } catch {
    throw new ApiError(0, 'NETWORK', 'Không kết nối được máy chủ. Kiểm tra backend đã chạy chưa.');
  }

  // Phản hồi lỗi có thể không phải JSON (ví dụ trang lỗi của proxy), nên không để việc giải mã làm vỡ luồng xử lý lỗi
  const data = await res.json().catch(() => null);
  if (res.ok) return data;

  // 401: phiên hết hạn hoặc không hợp lệ -> xóa token, về trang đăng nhập.
  if (res.status === 401 && p) {
    phien.xoa();
    location.hash = '#/login';
  }
  const e = (data && data.error) || {};
  throw new ApiError(res.status, e.code || 'UNKNOWN',
    e.message || `Máy chủ trả về lỗi ${res.status}`, e.fields);
}
