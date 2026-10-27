// Các endpoint về phiếu bảo hành; xem docs/api-contract.md. Mọi hàm ném ApiError khi máy chủ trả lỗi.
import { goi } from './client.js';

/** Phiếu đang xử lý của trung tâm (chỉ phiếu loại này mới được xuất linh kiện). size 100 để một lần lấy đủ cho ô chọn. Trả danh sách phân trang. */
export const danhSachPhieuDangXuLy = () =>
  goi('GET', '/tickets', { query: { status: 'DANG_XU_LY', size: 100 } });

/** Linh kiện đã xuất cho một phiếu. Trả: { ticket, data: [{ part_code, part_name, quantity, created_at }] }. Lỗi: 404 nếu không có phiếu, 403 nếu phiếu thuộc trung tâm khác. */
export const linhKienCuaPhieu = (ticketId) => goi('GET', `/tickets/${ticketId}/parts`);

/**
 * Xuất linh kiện cho phiếu. Trả: { quantity, remaining_stock, low_stock_alert }.
 * low_stock_alert = true nghĩa là tồn sau khi xuất đã dưới ngưỡng (việc vẫn thành công, đây chỉ là cảnh báo).
 * Lỗi: 409 INSUFFICIENT_STOCK khi xuất vượt tồn, 422 TICKET_NOT_PROCESSING khi phiếu đã đóng, 400 khi dữ liệu sai.
 */
export const xuatLinhKien = (ticketId, partId, quantity) =>
  goi('POST', `/tickets/${ticketId}/parts`, { body: { part_id: partId, quantity } });
