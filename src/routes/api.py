"""Tầng 1: nhận HTTP, gọi service, đổi mã lỗi nghiệp vụ thành mã HTTP.

Không có quy tắc nghiệp vụ ở đây; bảng HTTP_BY_CODE là toàn bộ phần "biết về HTTP".
"""
from functools import wraps

from flask import Blueprint, g, jsonify, request

from src import auth
from src.errors import AppError
from src.routes import views as hd
from src.validators import stock as v

HTTP_BY_CODE = {
    'VALIDATION_FAILED': 400,
    'UNAUTHORIZED': 401,
    'FORBIDDEN': 403,
    'TICKET_NOT_FOUND': 404,
    'PART_NOT_FOUND': 404,
    'INSUFFICIENT_STOCK': 409,        # QT-09
    'PART_CODE_EXISTS': 409,
    'PART_HAS_STOCK': 409,
    'STOCK_EXISTS': 409,
    'STOCK_NOT_EMPTY': 409,
    'TICKET_NOT_PROCESSING': 422,
}


def loi_json(e):
    """Đổi AppError thành phản hồi JSON theo MỘT khuôn chung {"error": {"code", "message", "fields"}},
    để giao diện chỉ cần một chỗ xử lý lỗi. Mã HTTP lấy từ HTTP_BY_CODE; mã lạ mặc định 400."""
    than = {'code': e.code, 'message': e.message}
    if e.fields:
        than['fields'] = e.fields
    return jsonify(error=than), HTTP_BY_CODE.get(e.code, 400)


def build_api(service):
    bp = Blueprint('api', __name__, url_prefix='/api')

    def can_dang_nhap(ham):
        """Decorator: chặn request thiếu hoặc sai token, rồi gắn người dùng hiện tại vào g.user cho hàm bên dưới dùng."""
        @wraps(ham)
        def boc(*a, **kw):
            tieu_de = request.headers.get('Authorization', '')
            # Quy ước chuẩn: Authorization: Bearer <token>; cắt 7 ký tự đầu ("Bearer ") để lấy token
            if not tieu_de.startswith('Bearer '):
                raise AppError('UNAUTHORIZED', 'Thiếu thông tin đăng nhập')
            g.user = service.lay_nguoi_dung(auth.doc_token(tieu_de[7:]))
            return ham(*a, **kw)
        return boc

    @bp.post('/auth/login')
    def dang_nhap():
        # Chưa có mật khẩu (xem thay-doi-thiet-ke TD-05): đăng nhập chỉ bằng mã người dùng, chỉ phù hợp bản thử nghiệm
        user_id = v.dang_nhap(request.get_json(silent=True))['user_id']
        user = service.lay_nguoi_dung(user_id)
        return jsonify(token=auth.tao_token(user_id), user={
            k: user[k] for k in ('user_id', 'full_name', 'role', 'center_id', 'center_name')})

    @bp.get('/parts')
    @can_dang_nhap
    def tim_linh_kien():
        page, size = v.phan_trang(request.args)
        trang_thai, sap_xep = v.loc_ton_kho(request.args)
        return jsonify(hd.to_page_view(service.tim_linh_kien(
            g.user, v.so_nguyen_tuy_chon(request.args, 'center_id'),
            (request.args.get('q') or '').strip() or None, page, size, trang_thai, sap_xep),
            hd.to_part_stock_view))

    @bp.get('/parts/low-stock')
    @can_dang_nhap
    def duoi_nguong():
        page, size = v.phan_trang(request.args)
        _, sap_xep = v.loc_ton_kho(request.args)          # endpoint này luôn là trạng thái low; chỉ nhận thêm sort
        return jsonify(hd.to_page_view(service.tim_linh_kien(
            g.user, v.so_nguyen_tuy_chon(request.args, 'center_id'),
            (request.args.get('q') or '').strip() or None, page, size, 'low', sap_xep),
            hd.to_part_stock_view))

    @bp.post('/parts')
    @can_dang_nhap
    def tao_linh_kien():
        d = v.tao_linh_kien(request.get_json(silent=True))
        part = service.tao_linh_kien(g.user, d['part_code'], d['part_name'], d['unit_price'])
        return jsonify(hd.to_part_view(part)), 201

    @bp.get('/parts/<int:part_id>')
    @can_dang_nhap
    def lay_linh_kien(part_id):
        return jsonify(hd.to_part_detail_view(service.lay_linh_kien(g.user, part_id)))

    @bp.put('/parts/<int:part_id>')
    @can_dang_nhap
    def sua_linh_kien(part_id):
        d = v.sua_linh_kien(request.get_json(silent=True))
        return jsonify(hd.to_part_view(
            service.sua_linh_kien(g.user, part_id, d['part_name'], d['unit_price'])))

    @bp.delete('/parts/<int:part_id>')
    @can_dang_nhap
    def ngung_linh_kien(part_id):
        return jsonify(hd.to_deactivated_view(service.ngung_linh_kien(g.user, part_id)))

    @bp.post('/stock')
    @can_dang_nhap
    def them_vao_kho():
        d = v.them_vao_kho(request.get_json(silent=True))
        return jsonify(hd.to_stock_view(
            service.them_vao_kho(g.user, d['part_id'], d['min_threshold']))), 201

    @bp.patch('/stock/<int:part_id>')
    @can_dang_nhap
    def doi_nguong(part_id):
        d = v.doi_nguong(request.get_json(silent=True))
        return jsonify(hd.to_stock_view(service.doi_nguong(g.user, part_id, d['min_threshold'])))

    @bp.delete('/stock/<int:part_id>')
    @can_dang_nhap
    def ngung_ton_kho(part_id):
        return jsonify(hd.to_deactivated_view(service.ngung_ton_kho(g.user, part_id)))

    @bp.post('/parts/<int:part_id>/stock-in')
    @can_dang_nhap
    def nhap_kho(part_id):
        d = v.nhap_kho(request.get_json(silent=True))
        return jsonify(hd.to_stock_in_view(
            service.nhap_kho(g.user, part_id, d['center_id'], d['quantity']))), 201

    @bp.get('/parts/<int:part_id>/transactions')
    @can_dang_nhap
    def lich_su(part_id):
        page, size = v.phan_trang(request.args)
        return jsonify(hd.to_page_view(service.lich_su(
            g.user, part_id, v.so_nguyen_tuy_chon(request.args, 'center_id'), page, size),
            hd.to_transaction_view))

    @bp.get('/parts/<int:part_id>/transactions/summary')
    @can_dang_nhap
    def tong_hop(part_id):
        tu, den = v.khoang_ngay(request.args)
        return jsonify(hd.to_summary_view(service.tong_hop(
            g.user, part_id, v.so_nguyen_tuy_chon(request.args, 'center_id'), tu, den)))

    @bp.get('/tickets')
    @can_dang_nhap
    def ds_phieu():
        page, size = v.phan_trang(request.args)
        return jsonify(hd.to_page_view(service.ds_phieu(
            g.user, request.args.get('status') or None, page, size), hd.to_ticket_view))

    @bp.get('/tickets/<int:ticket_id>/parts')
    @can_dang_nhap
    def linh_kien_cua_phieu(ticket_id):
        kq = service.linh_kien_cua_phieu(g.user, ticket_id)
        return jsonify(ticket=hd.to_ticket_view(kq['ticket']),
                       data=[hd.to_used_part_view(x) for x in kq['data']])

    @bp.post('/tickets/<int:ticket_id>/parts')
    @can_dang_nhap
    def xuat_kho(ticket_id):
        d = v.xuat_kho(request.get_json(silent=True))
        return jsonify(hd.to_issue_view(service.xuat_linh_kien(
            g.user, ticket_id, d['part_id'], d['quantity']))), 201

    return bp
