import { goi } from './client.js';

export const timLinhKien = ({ q, page = 1, size = 20, duoiNguong = false } = {}) =>
  goi('GET', duoiNguong ? '/parts/low-stock' : '/parts', { query: { q, page, size } });

export const nhapKho = (partId, centerId, quantity) =>
  goi('POST', `/parts/${partId}/stock-in`, { body: { center_id: centerId, quantity } });

export const lichSu = (partId, { page = 1, size = 20 } = {}) =>
  goi('GET', `/parts/${partId}/transactions`, { query: { page, size } });

export const tongHop = (partId, tu, den) =>
  goi('GET', `/parts/${partId}/transactions/summary`, { query: { from: tu, to: den } });

export const taoLinhKien = (partCode, partName, unitPrice) =>
  goi('POST', '/parts', { body: { part_code: partCode, part_name: partName, unit_price: unitPrice } });

export const suaLinhKien = (partId, partName, unitPrice) =>
  goi('PUT', `/parts/${partId}`, { body: { part_name: partName, unit_price: unitPrice } });

export const ngungLinhKien = (partId) => goi('DELETE', `/parts/${partId}`);

export const themVaoKho = (partId, minThreshold) =>
  goi('POST', '/stock', { body: { part_id: partId, min_threshold: minThreshold } });

export const doiNguong = (partId, minThreshold) =>
  goi('PATCH', `/stock/${partId}`, { body: { min_threshold: minThreshold } });

export const ngungTonKho = (partId) => goi('DELETE', `/stock/${partId}`);
