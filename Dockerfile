FROM python:3.10-slim

WORKDIR /app

# Cài thư viện trước để Docker dùng lại lớp này khi chỉ sửa mã nguồn
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src
COPY web ./web
COPY migrations ./migrations
COPY seeds ./seeds

# Chạy bằng người dùng thường, không chạy bằng root
RUN useradd --create-home app
USER app

EXPOSE 5000

# /health trả 503 khi mất CSDL thì urlopen báo lỗi, container chuyển sang unhealthy
HEALTHCHECK --interval=10s --timeout=5s --start-period=30s --retries=6 \
  CMD python -c "import urllib.request as u; u.urlopen('http://127.0.0.1:5000/health', timeout=3)"

# Lắng nghe 0.0.0.0 để cổng được mở ra ngoài container (127.0.0.1 chỉ truy cập được từ bên trong)
CMD ["flask", "--app", "src.app:create_app", "run", "--host", "0.0.0.0", "--port", "5000"]
