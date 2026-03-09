from flask import Blueprint, jsonify
from functools import wraps
import logging

# 获取日志记录器
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# 创建主路由蓝图
main_bp = Blueprint('main', __name__)

# 统一响应装饰器
def api_response(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            # 确保返回格式一致
            if not isinstance(result, dict) or "success" not in result:
                result = {
                    "success": True,
                    "data": result if result is not None else {},
                    "message": "请求成功"
                }
            # 根据success字段设置HTTP状态码
            status_code = 200 if result["success"] else 400
            return jsonify(result), status_code
        except Exception as e:
            # 统一处理异常
            return jsonify({
                "success": False,
                "data": {},
                "message": str(e)
            }), 500
    return decorated_function

# 导入视图函数和路由
from . import views
from .bilibili import bilibili_bp
from .api_wrapper import api_wrapper_bp
from .api import api_bp

# 统一路由注册函数
def register_routes(app):
    """
    统一注册所有路由
    """
    app.register_blueprint(main_bp)
    app.register_blueprint(bilibili_bp, url_prefix='/bilibili')
    app.register_blueprint(api_wrapper_bp, url_prefix='/api_wrapper')
    app.register_blueprint(api_bp, url_prefix='/api')
