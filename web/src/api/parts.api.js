// Mỗi hàm dưới đây ứng với một endpoint trong docs/api-contract.md và trả đúng JSON của endpoint đó.
// Mọi hàm ném ApiError khi máy chủ trả lỗi (xem client.js). Dòng tồn kho trả về luôn thuộc trung tâm của người đang đăng nhập.
import { goi } from './client.js';

/**
 * Tìm linh kiện trong kho trung tâm theo mã hoặc tên (q), có phân trang.
 * duoiNguong = true chỉ lấy linh kiện có tồn thấp hơn ngưỡng cảnh báo.
 * Trả: { data: [{ part_id, part_code, part_name, quantity, min_threshold }], total, page, size }; total là tổng số dòng khớp, không phải số dòng của trang.
 */
export const timLinhKien = ({ q, page = 1, size = 20, duoiNguong = false } = {}) =>
  goi('GET', duoiNguong ? '/parts/low-stock' : '/parts', { query: { q, page, size } });

/** Ghi nhận nhập kho (chỉ quản lý). Trả: { quantity, new_stock }. Lỗi 400 nếu số lượng không phải số nguyên dương. */
export const nhapKho = (partId, centerId, quantity) =>
  goi('POST', `/parts/${partId}/stock-in`, { body: { center_id: centerId, quantity } });

/** Lịch sử nhập xuất của một linh kiện, mới nhất trước (chỉ quản lý). Trả danh sách phân trang, mỗi dòng có txn_type là 'NHAP' hoặc 'XUAT'; ticket_id là null với giao dịch nhập. */
export const lichSu = (partId, { page = 1, size = 20 } = {}) =>
  goi('GET', `/parts/${partId}/transactions`, { query: { page, size } });

/** Tổng nhập, tổng xuất trong khoảng ngày tu đến den (YYYY-MM-DD). Trả: { from, to, total_in, total_out, net_change }; không có giao dịch thì các số là 0 chứ không phải null. */
export const tongHop = (partId, tu, den) =>
  goi('GET', `/parts/${partId}/transactions/summary`, { query: { from: tu, to: den } });

/** Tạo linh kiện mới trong danh mục (chỉ quản lý). Lỗi 409 PART_CODE_EXISTS nếu mã đã có, kể cả mã của linh kiện đã ngừng. */
export const taoLinhKien = (partCode, partName, unitPrice) =>
  goi('POST', '/parts', { body: { part_code: partCode, part_name: partName, unit_price: unitPrice } });

/** Sửa tên và đơn giá; mã linh kiện không đổi được. */
export const suaLinhKien = (partId, partName, unitPrice) =>
  goi('PUT', `/parts/${partId}`, { body: { part_name: partName, unit_price: unitPrice } });

/** Ngừng sử dụng linh kiện (xóa mềm). Lỗi 409 PART_HAS_STOCK nếu còn kho giữ tồn lớn hơn 0. */
export const ngungLinhKien = (partId) => goi('DELETE', `/parts/${partId}`);

/** Đưa linh kiện vào kho trung tâm với tồn 0 và ngưỡng cảnh báo minThreshold. Lỗi 409 STOCK_EXISTS nếu đã có trong kho. */
export const themVaoKho = (partId, minThreshold) =>
  goi('POST', '/stock', { body: { part_id: partId, min_threshold: minThreshold } });

/** Đổi ngưỡng cảnh báo của linh kiện trong kho trung tâm. */
export const doiNguong = (partId, minThreshold) =>
  goi('PATCH', `/stock/${partId}`, { body: { min_threshold: minThreshold } });

/** Gỡ linh kiện khỏi kho trung tâm (xóa mềm). Lỗi 409 STOCK_NOT_EMPTY nếu tồn còn lớn hơn 0. */
export const ngungTonKho = (partId) => goi('DELETE', `/stock/${partId}`);
