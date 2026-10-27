// Điểm duy nhất trong frontend được phép gọi fetch(). Các trang chỉ gọi *.api.js.
const KHOA_PHIEN = 'l5_phien';

export const phien = {
  doc() {
    try { return JSON.parse(sessionStorage.getItem(KHOA_PHIEN)); } catch { return null; }
  },
  luu(p) { sessionStorage.setItem(KHOA_PHIEN, JSON.stringify(p)); },
  xoa() { sessionStorage.removeItem(KHOA_PHIEN); },
};

export class ApiError extends Error {
  constructor(status, code, message, fields = {}) {
    super(message);
    this.status = status;
    this.code = code;
    this.fields = fields;
  }
}

export async function goi(method, duongDan, { query, body } = {}) {
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
