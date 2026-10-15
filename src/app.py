"""Khởi tạo ứng dụng Flask. Chạy bằng: python -m src.app"""
from flask import Flask, jsonify

from src import config, db


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = config.SECRET_KEY

    @app.get('/health')
    def health():
        try:
            with db.connect() as conn:
                conn.execute('SELECT 1')
            return jsonify(status='ok', db='ok')
        except Exception:
            # Không trả chi tiết lỗi kết nối để tránh lộ cấu hình.
            return jsonify(status='degraded', db='unreachable'), 503

    return app


if __name__ == '__main__':
    create_app().run(port=config.PORT, debug=True)
