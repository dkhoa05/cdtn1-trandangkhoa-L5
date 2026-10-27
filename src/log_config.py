"""Cấu hình log MỘT lần cho cả ứng dụng: mỗi dòng là một JSON ghi ra stdout.

Mỗi dòng có thời điểm ISO 8601, mức, thông điệp và ngữ cảnh (requestId, mã người dùng, mã lỗi...).
Các trường nhạy cảm bị che; không bao giờ ghi mật khẩu, token, chuỗi kết nối hay thân request.
Mức log lấy từ biến môi trường LOG_LEVEL (INFO mặc định, DEBUG khi cần điều tra).
"""
import json
import logging
import os
import sys
from datetime import datetime

TRUONG_CHE = ('password', 'mat_khau', 'token', 'authorization', 'secret', 'so_dien_thoai')


def che(du_lieu):
    """Thay giá trị của mọi khóa có tên nhạy cảm bằng '***', đệ quy qua dict và list."""
    if isinstance(du_lieu, dict):
        return {k: '***' if any(t in str(k).lower() for t in TRUONG_CHE) else che(v)
                for k, v in du_lieu.items()}
    if isinstance(du_lieu, list):
        return [che(x) for x in du_lieu]
    return du_lieu


class JsonFormatter(logging.Formatter):
    def format(self, record):
        dong = {
            'thoi_diem': datetime.fromtimestamp(record.created).astimezone().isoformat(timespec='milliseconds'),
            'muc': record.levelname.lower(),
            'nguon': record.name,
            'thong_diep': record.getMessage(),
        }
        dong.update(che(getattr(record, 'ngu_canh', None) or {}))
        if record.exc_info:
            dong['ngan_xep'] = self.formatException(record.exc_info)   # chỉ vào log, không bao giờ vào phản hồi
        return json.dumps(dong, ensure_ascii=False)


class _GhiRaStdout(logging.Handler):
    """Luôn ghi vào sys.stdout hiện tại (khi chạy trong container, `docker compose logs` đọc được)."""

    def emit(self, record):
        sys.stdout.write(self.format(record) + '\n')
        sys.stdout.flush()


def cau_hinh_log():
    goc = logging.getLogger()
    if getattr(goc, '_l5_da_cau_hinh', False):
        return
    h = _GhiRaStdout()
    h.setFormatter(JsonFormatter())
    goc.handlers[:] = [h]
    goc.setLevel(os.getenv('LOG_LEVEL', 'INFO').upper())
    logging.getLogger('werkzeug').setLevel(logging.WARNING)       # dòng truy cập đã có log JSON riêng
    goc._l5_da_cau_hinh = True
