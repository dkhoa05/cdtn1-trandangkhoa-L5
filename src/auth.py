"""Token đăng nhập ký bằng SECRET_KEY (itsdangerous đã đi kèm Flask)."""
from itsdangerous import BadSignature, URLSafeTimedSerializer
from werkzeug.security import check_password_hash, generate_password_hash

from src import config
from src.errors import AppError

# Token sống 8 giờ, đủ cho một ca làm việc; hết hạn thì người dùng phải đăng nhập lại.
HAN_TOKEN_GIAY = 8 * 3600


def bam_mat_khau(mat_khau):
    """Làm gì: băm mật khẩu bằng scrypt kèm salt ngẫu nhiên (werkzeug, đi kèm Flask).
    Nhận: mật khẩu dạng chuỗi. Trả: chuỗi băm để lưu vào app_user.password_hash. Lỗi: không có."""
    return generate_password_hash(mat_khau)


# Băm giả để đăng nhập với mã không tồn tại vẫn tốn thời gian như khi có mã, người ngoài không dò được mã nào có thật.
_BAM_GIA = generate_password_hash('chuoi-gia-khong-ai-dung')


def kiem_tra_mat_khau(mat_khau, bam):
    """Làm gì: so mật khẩu người dùng nhập với chuỗi băm đã lưu.
    Nhận: mat_khau (chuỗi), bam (chuỗi băm, hoặc None khi tài khoản chưa có mật khẩu hay không tồn tại).
    Trả: True nếu khớp. Lỗi: không có."""
    khop = check_password_hash(bam or _BAM_GIA, mat_khau)
    return bool(bam) and khop


def _ky():
    # salt tách token đăng nhập khỏi mọi thứ khác cũng ký bằng SECRET_KEY
    return URLSafeTimedSerializer(config.SECRET_KEY, salt='cdtn1-l5-login')


def tao_token(user_id):
    """Làm gì: tạo token đăng nhập.
    Nhận: user_id (số nguyên). Trả: chuỗi token đã ký, không mã hóa nên không được đặt dữ liệu bí mật vào.
    Lỗi: không có."""
    return _ky().dumps({'uid': user_id})


def doc_token(token):
    """Làm gì: đọc lại token do tao_token tạo.
    Nhận: chuỗi token từ header Authorization. Trả: user_id.
    Lỗi: UNAUTHORIZED khi token sai chữ ký, hết hạn hoặc thiếu."""
    try:
        return _ky().loads(token, max_age=HAN_TOKEN_GIAY)['uid']
    except (BadSignature, KeyError, TypeError):
        raise AppError('UNAUTHORIZED', 'Phiên đăng nhập không hợp lệ hoặc đã hết hạn')
