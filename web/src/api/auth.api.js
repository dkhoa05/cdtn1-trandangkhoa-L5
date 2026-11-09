import { goi, phien } from './client.js';

/**
 * Hợp đồng: đăng nhập bằng mã người dùng và mật khẩu.
 * Trả: { user_id, full_name, role, center_id, center_name }, đồng thời lưu token vào phiên.
 * role là 'KY_THUAT_VIEN' hoặc 'QUAN_LY_TT'; giao diện dựa vào đó để ẩn chức năng không được dùng.
 * Lỗi: ApiError 401 khi mã hoặc mật khẩu không đúng hay tài khoản đã ngừng; 400 khi mã không phải số nguyên dương
 * hoặc thiếu mật khẩu. Mật khẩu chỉ đi trong thân request, không lưu ở đâu trong trình duyệt.
 */
export async function dangNhap(userId, matKhau) {
  const kq = await goi('POST', '/auth/login', { body: { user_id: userId, password: matKhau } });
  phien.luu(kq);
  return kq.user;
}

/** Xóa phiên ở trình duyệt. Token cũ vẫn dùng được đến khi hết hạn vì máy chủ không giữ danh sách đăng nhập. */
export function dangXuat() { phien.xoa(); }
