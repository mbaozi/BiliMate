from flask import Blueprint, request, jsonify
from . import api_response
from flask_login import login_required, current_user
from app.services import api_wrapper_service
import logging

# 获取日志记录器
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# 创建API路由蓝图
api_wrapper_bp = Blueprint('api_wrapper', __name__)

@api_wrapper_bp.route('/api_test', methods=['POST'])
@login_required
@api_response
def api_test():
    """
    API测试路由
    转发用户的API测试请求并返回结果
    """
    data = request.get_json()
    # 服务层已经返回标准格式，直接返回
    return api_wrapper_service.execute_api(
        data.get('method', 'GET'),
        data.get('url'),
        data.get('headers', {}),
        data.get('body'),
        data.get('context'),
        data.get('system_prompt')
    )

@api_wrapper_bp.route('/api_wrappers', methods=['POST'])
@login_required
@api_response
def create_api_wrapper():
    """
    创建API封装
    """
    data = request.get_json()
    return api_wrapper_service.create_api_wrapper(data, current_user.id)

@api_wrapper_bp.route('/api_wrappers', methods=['GET'])
@login_required
@api_response
def list_api_wrappers():
    """
    获取API封装列表
    """
    response = api_wrapper_service.list_api_wrappers(current_user.id)
    return response

@api_wrapper_bp.route('/api_wrappers/<int:wrapper_id>', methods=['GET'])
@login_required
@api_response
def get_api_wrapper(wrapper_id):
    """
    获取单个API封装
    """
    return api_wrapper_service.get_api_wrapper(wrapper_id, current_user.id)

@api_wrapper_bp.route('/api_wrappers/<int:wrapper_id>', methods=['PUT'])
@login_required
@api_response
def update_api_wrapper(wrapper_id):
    """
    更新API封装
    """
    data = request.get_json()
    return api_wrapper_service.update_api_wrapper(wrapper_id, data, current_user.id)

@api_wrapper_bp.route('/api_wrappers/<int:wrapper_id>', methods=['DELETE'])
@login_required
@api_response
def delete_api_wrapper(wrapper_id):
    """
    删除API封装
    """
    return api_wrapper_service.delete_api_wrapper(wrapper_id, current_user.id)

@api_wrapper_bp.route('/api_wrappers/<int:wrapper_id>/test', methods=['POST'])
@login_required
@api_response
def test_api_wrapper(wrapper_id):
    """
    测试API封装
    """
    data = request.get_json()
    return api_wrapper_service.test_api_wrapper(wrapper_id, current_user.id, data.get('context'))
