"""Lỗi nghiệp vụ. Service ném AppError kèm mã lỗi, route đổi mã lỗi thành mã HTTP."""


class AppError(Exception):
    """Lỗi nghiệp vụ mà người dùng có thể hiểu và sửa (hết hàng, sai quyền, dữ liệu sai...).

    code là mã cố định để chương trình so sánh (ví dụ INSUFFICIENT_STOCK), message là câu hiển thị cho người dùng,
    fields (nếu có) chỉ ra trường nào sai. Service chỉ ném lỗi này, không biết mã HTTP; routes/api.py mới đổi sang HTTP.
    """

    def __init__(self, code, message, fields=None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.fields = fields or {}
