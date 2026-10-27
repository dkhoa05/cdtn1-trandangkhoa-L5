import { goi } from './client.js';

export const danhSachPhieuDangXuLy = () =>
  goi('GET', '/tickets', { query: { status: 'DANG_XU_LY', size: 100 } });

export const linhKienCuaPhieu = (ticketId) => goi('GET', `/tickets/${ticketId}/parts`);

export const xuatLinhKien = (ticketId, partId, quantity) =>
  goi('POST', `/tickets/${ticketId}/parts`, { body: { part_id: partId, quantity } });
