"""Token đăng nhập ký bằng SECRET_KEY (itsdangerous đã đi kèm Flask)."""
from itsdangerous import BadSignature, URLSafeTimedSerializer

from src import config
from src.errors import AppError

HAN_TOKEN_GIAY = 8 * 3600


def _ky():
    return URLSafeTimedSerializer(config.SECRET_KEY, salt='cdtn1-l5-login')


def tao_token(user_id):
    return _ky().dumps({'uid': user_id})


def doc_token(token):
    """Trả user_id, hoặc ném UNAUTHORIZED khi token sai, hết hạn hoặc thiếu."""
    try:
        return _ky().loads(token, max_age=HAN_TOKEN_GIAY)['uid']
    except (BadSignature, KeyError, TypeError):
        raise AppError('UNAUTHORIZED', 'Phiên đăng nhập không hợp lệ hoặc đã hết hạn')
