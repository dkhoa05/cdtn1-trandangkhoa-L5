"""Lỗi nghiệp vụ. Service ném AppError kèm mã lỗi, route đổi mã lỗi thành mã HTTP."""


class AppError(Exception):
    def __init__(self, code, message, fields=None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.fields = fields or {}
