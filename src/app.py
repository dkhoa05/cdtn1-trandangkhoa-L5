"""Khởi tạo ứng dụng Flask. Chạy bằng: python -m src.app

Flask cũng phục vụ thư mục web/ (frontend JS thuần) cùng một origin với API,
nên trình duyệt không gặp lỗi CORS và chỉ cần một lệnh để chạy cả hệ thống.
"""
import logging
import time
import uuid
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import psycopg
from flask import Flask, g, jsonify, request, send_from_directory
from werkzeug.exceptions import HTTPException

from src import config, db
from src.errors import AppError
from src.log_config import cau_hinh_log
from src.repositories.stock_repo import unit_of_work
from src.routes.api import build_api, loi_json
from src.services.stock_service import StockService

WEB = Path(__file__).resolve().parent.parent / 'web'
cau_hinh_log()
log = logging.getLogger('l5')


def create_app(service=None):
    app = Flask(__name__, static_folder=None)
    app.config['SECRET_KEY'] = config.SECRET_KEY
    # datetime ra dạng ISO 8601 (mặc định là RFC 822); NUMERIC ra số thay vì chuỗi.
    app.json.default = lambda o: (
        o.isoformat() if isinstance(o, datetime)
        else int(o) if isinstance(o, Decimal) and o == o.to_integral_value()
        else float(o) if isinstance(o, Decimal) else str(o))
    app.json.ensure_ascii = False

    @app.get('/health')
    def health():
        try:
            with db.connect() as conn:
                conn.execute('SELECT 1')
            return jsonify(status='ok', db='ok')
        except Exception:
            # Không trả chi tiết lỗi kết nối để tránh lộ cấu hình.
            return jsonify(status='degraded', db='unreachable'), 503

    app.register_blueprint(build_api(service or StockService(unit_of_work)))

    @app.before_request
    def bat_dau_request():
        # Mã tương quan: dùng X-Request-Id của bên gọi nếu có, để lần theo một yêu cầu qua nhiều dòng log.
        g.request_id = request.headers.get('X-Request-Id') or uuid.uuid4().hex[:8]
        g.bat_dau = time.perf_counter()

    @app.after_request
    def ghi_log_request(res):
        res.headers['X-Request-Id'] = g.get('request_id', '-')
        log.info('yeu cau hoan tat', extra={'ngu_canh': {
            'requestId': g.get('request_id'), 'phuong_thuc': request.method, 'duong_dan': request.path,
            'ma_trang_thai': res.status_code,
            'thoi_gian_ms': round((time.perf_counter() - g.get('bat_dau', time.perf_counter())) * 1000, 1)}})
        return res

    @app.errorhandler(AppError)
    def loi_nghiep_vu(e):
        # Lỗi nghiệp vụ là việc bình thường, chỉ ghi INFO kèm mã lỗi và requestId, không kèm dữ liệu cá nhân.
        log.info('vi pham quy tac', extra={'ngu_canh': {
            'requestId': g.get('request_id'), 'ma_loi': e.code,
            'user_id': (g.get('user') or {}).get('user_id')}})
        return loi_json(e)

    @app.errorhandler(psycopg.OperationalError)
    def loi_mat_ket_noi_csdl(e):
        # Lỗi hạ tầng: ghi ERROR một lần ở đây (kèm ngăn xếp), người dùng chỉ nhận mã tra cứu.
        log.exception('mat ket noi CSDL', extra={'ngu_canh': {'requestId': g.get('request_id')}})
        return jsonify(error={'code': 'DB_UNAVAILABLE',
                              'message': 'Hệ thống đang gặp sự cố kết nối dữ liệu. Vui lòng thử lại sau.',
                              'requestId': g.get('request_id')}), 503

    @app.errorhandler(HTTPException)
    def loi_http(e):
        return jsonify(error={'code': e.name.upper().replace(' ', '_'),
                              'message': e.description}), e.code

    @app.errorhandler(Exception)
    def loi_khong_luong_truoc(e):
        # Chi tiết chỉ vào nhật ký; người gọi chỉ nhận requestId để đối chiếu.
        log.exception('loi khong luong truoc', extra={'ngu_canh': {
            'requestId': g.get('request_id'), 'phuong_thuc': request.method, 'duong_dan': request.path}})
        return jsonify(error={'code': 'INTERNAL_ERROR',
                              'message': 'Đã xảy ra lỗi không mong đợi. Vui lòng thử lại sau.',
                              'requestId': g.get('request_id')}), 500

    @app.get('/')
    def trang_chu():
        return send_from_directory(WEB, 'index.html')

    @app.get('/<path:duong_dan>')
    def tep_tinh(duong_dan):
        if duong_dan.startswith('api/'):
            return jsonify(error={'code': 'NOT_FOUND', 'message': 'Không có đường dẫn này'}), 404
        return send_from_directory(WEB, duong_dan)

    return app


if __name__ == '__main__':
    create_app().run(port=config.PORT, debug=True)
