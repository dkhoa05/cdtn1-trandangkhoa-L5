-- TD-10: mật khẩu đăng nhập, lưu dạng băm (scrypt kèm salt), không bao giờ lưu mật khẩu thật.
-- NULL nghĩa là chưa đặt mật khẩu; python -m src.db_init đặt mật khẩu mẫu cho các tài khoản dữ liệu mẫu.
ALTER TABLE app_user ADD COLUMN IF NOT EXISTS password_hash TEXT;
