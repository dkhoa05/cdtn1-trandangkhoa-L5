#!/bin/sh
# Khởi động trên Render: tạo bảng và nạp dữ liệu mẫu (chạy lại không nhân đôi), rồi mở máy chủ ở cổng Render cấp.
set -e
python -m src.db_init
exec flask --app src.app:create_app run --host 0.0.0.0 --port "${PORT:-5000}"
