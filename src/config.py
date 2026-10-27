"""Đọc cấu hình từ biến môi trường (.env khi chạy cục bộ)."""
import os

from dotenv import load_dotenv

load_dotenv()


def db_name():
    return os.getenv('DB_NAME', 'cdtn1_l5_dev')


def database_url(dbname=None):
    return (
        f"host={os.getenv('DB_HOST', 'localhost')} "
        f"port={os.getenv('DB_PORT', '5432')} "
        f"dbname={dbname or db_name()} "
        f"user={os.getenv('DB_USER', 'postgres')} "
        f"password={os.getenv('DB_PASSWORD', '')}"
    )


SECRET_KEY = os.getenv('SECRET_KEY', 'dev-only-secret')
PORT = int(os.getenv('PORT', '5000'))
