"""Đọc cấu hình từ biến môi trường (.env khi chạy cục bộ)."""
import os

from dotenv import load_dotenv

load_dotenv()


def db_name():
    return os.getenv('DB_NAME', 'cdtn1_l5_dev')


def database_url(dbname=None):
    """Ghép chuỗi kết nối PostgreSQL từ biến môi trường; dbname cho phép nối tạm vào CSDL khác (db_init dùng)."""
    return (
        f"host={os.getenv('DB_HOST', 'localhost')} "
        f"port={os.getenv('DB_PORT', '5432')} "
        f"dbname={dbname or db_name()} "
        f"user={os.getenv('DB_USER', 'postgres')} "
        f"password={os.getenv('DB_PASSWORD', '')}"
    )


# Giá trị mặc định chỉ để chạy thử trên máy cá nhân; khi triển khai thật phải đặt SECRET_KEY riêng trong .env,
# vì ai biết khóa này đều tự tạo được token đăng nhập giả.
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-only-secret')
PORT = int(os.getenv('PORT', '5000'))
