FROM python:3.10-slim

WORKDIR /app

# Cài thư viện trước để Docker dùng lại lớp này khi chỉ sửa mã nguồn
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src
COPY web ./web
COPY migrations ./migrations
COPY seeds ./seeds

EXPOSE 5000

# Lắng nghe 0.0.0.0 để cổng được mở ra ngoài container (127.0.0.1 chỉ truy cập được từ bên trong)
CMD ["flask", "--app", "src.app:create_app", "run", "--host", "0.0.0.0", "--port", "5000"]
