import { goi, phien } from './client.js';

export async function dangNhap(userId) {
  const kq = await goi('POST', '/auth/login', { body: { user_id: userId } });
  phien.luu(kq);
  return kq.user;
}

export function dangXuat() { phien.xoa(); }
