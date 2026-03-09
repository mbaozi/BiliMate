from flask import Blueprint, request, jsonify, Response
from flask_login import login_required, current_user
from ..services import db
from ..models import ReplyConfig, BiliAccount
from ..services.bilibili.auth_service import AuthService
from app.services.license import license_service
from app.services.advanced.registration_service import registration_service
from app.services.advanced.user_service import user_service
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# 创建API蓝图
api_bp = Blueprint('api', __name__)


@api_bp.route('/create_template', methods=['POST'])
@login_required
def create_template():
    """
    创建新模板
    """
    # 获取请求数据
    data = request.get_json()
    template_name = data.get('template_name')
    template_id = data.get('template_id')
    
    # 验证参数
    if not template_name:
        return jsonify({'success': False, 'message': '参数错误'}), 400
    
    # 检查注册用户的模板数量限制
    from app.services.license import license_service
    from flask_login import current_user
    
    # 检查注册用户的VIP状态
    if current_user.role == 'registered':
        # 普通注册用户只能创建一个模板，VIP注册用户无限制
        if current_user.user_level != 'vip':
            template_count = ReplyConfig.query.filter_by(is_template=True).count()
            if template_count >= 1:
                return jsonify({'success': False, 'message': '普通注册用户只能创建一个模板，请升级为VIP后创建更多模板'}), 400
    
    # 检查未激活用户的模板数量限制
    if not license_service.is_activated():
        template_count = ReplyConfig.query.filter_by(is_template=True).count()
        if template_count >= 1:
            return jsonify({'success': False, 'message': '应用未激活，只能创建一个模板，请激活应用后创建'}), 400
    
    # 检查模板名称是否已存在
    existing_template = ReplyConfig.query.filter_by(is_template=True, name=template_name).first()
    if existing_template:
        return jsonify({'success': False, 'message': '模板名称已存在'}), 400
    
    # 创建新模板
    if template_id and template_id != 'default':
        # 基于现有模板创建新模板
        existing_template = ReplyConfig.query.filter_by(id=template_id, is_template=True).first()
        if not existing_template:
            return jsonify({'success': False, 'message': '模板不存在'}), 404
        
        # 复制现有模板创建新模板
        template = ReplyConfig(
            enable_new_fans_reply=existing_template.enable_new_fans_reply,
            new_fans_reply=existing_template.new_fans_reply,
            enable_fans_reply=existing_template.enable_fans_reply,
            fans_complete_dict=existing_template.fans_complete_dict.copy() if existing_template.fans_complete_dict else {},
            fans_keyword_dict=existing_template.fans_keyword_dict.copy() if existing_template.fans_keyword_dict else {},
            fans_other_reply=existing_template.fans_other_reply,
            enable_non_fans_reply=existing_template.enable_non_fans_reply,
            non_fans_complete_dict=existing_template.non_fans_complete_dict.copy() if existing_template.non_fans_complete_dict else {},
            non_fans_keyword_dict=existing_template.non_fans_keyword_dict.copy() if existing_template.non_fans_keyword_dict else {},
            non_fans_other_reply=existing_template.non_fans_other_reply,
            repet_protect_times=existing_template.repet_protect_times,
            reply_interval_seconds=existing_template.reply_interval_seconds,
            is_template=True,
            name=template_name
        )
    else:
        # 基于默认设置创建新模板
        template = ReplyConfig(
            is_template=True,
            name=template_name
        )
    
    # 保存模板
    db.session.add(template)
    db.session.commit()
    
    # 添加flash消息，在页面刷新后显示
    from flask import flash
    flash('模板创建成功', 'success')
    
    return jsonify({'success': True, 'message': '模板创建成功'})


@api_bp.route('/delete_template', methods=['POST'])
@login_required
def delete_template():
    """
    删除模板
    """
    # 获取请求数据
    data = request.get_json()
    template_id = data.get('template_id')
    
    # 验证参数
    if not template_id:
        return jsonify({'success': False, 'message': '参数错误'}), 400
    
    # 获取模板
    template = ReplyConfig.query.filter_by(id=template_id, is_template=True).first()
    if not template:
        return jsonify({'success': False, 'message': '模板不存在'}), 404
    
    # 检查是否有账号正在使用该模板
    from app.models import BiliAccount
    # 查找所有使用该模板的账号
    accounts_using_template = BiliAccount.query.filter_by(reply_config_id=template_id).all()
    
    if accounts_using_template:
        # 获取使用该模板的账号名称列表
        account_names = [account.uname for account in accounts_using_template]
        return jsonify({'success': False, 'message': f'该模板已被账号 {account_names} 使用，无法删除'}), 400
    
    # 删除模板
    db.session.delete(template)
    db.session.commit()
    
    # 添加flash消息，在页面刷新后显示
    from flask import flash
    flash('模板删除成功', 'success')
    
    return jsonify({'success': True, 'message': '模板删除成功'})


@api_bp.route('/system_usage')
def get_system_usage():
    """
    获取系统资源占用API（CPU和内存）
    """
    try:
        from app import current_process, physical_cores
        process_cpu_percent = current_process.cpu_percent()
        process_memory_percent = current_process.memory_percent()
        process_memory_bytes = current_process.memory_info().rss  # 内存使用量（字节）

        return jsonify({
            'success': True,
            'data': {
                'process_cpu_percentage': round(process_cpu_percent, 2),
                'physical_cores': physical_cores,
                'process_memory_percentage': round(process_memory_percent, 2),
                'process_memory_bytes': process_memory_bytes
            },
            'message': '获取系统资源占用成功'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'data': {
                'process_cpu_percentage': 0,
                'physical_cores': 1,
                'process_memory_percentage': 0,
                'process_memory_bytes': 0
            },
            'message': f'获取系统资源占用失败: {str(e)}'
        })


@api_bp.route('/activate', methods=['POST'])
def activate():
    """
    处理激活请求
    """
    try:
        data = request.get_json()
        # 验证请求参数
        if not data or 'activation_code' not in data:
            return jsonify({
                'success': False,
                'message': '缺少激活码参数',
                'data': {}
            })
        activation_code = data['activation_code']
        remark = data.get('remark', '')
        
        # 调用激活服务
        result = license_service.activate(activation_code, remark)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': '激活失败',
            'data': {}
        })


@api_bp.route('/check_activation_status', methods=['GET'])
def check_activation_status():
    """查询激活状态"""
    try:
        # 调用激活服务查询状态
        result = license_service.get_activation_status()
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'查询激活状态失败: {str(e)}',
            'data': {
                'is_activated': False,
                'activation_status': '未激活',
                'activation_type': 'NULL',
                'expiry_date': 'NULL',
                'activation_date': 'NULL'
            }
        })


@api_bp.route('/user_info', methods=['GET'])
@login_required
def user_info():
    """获取用户信息"""
    try:
        return jsonify({
            'success': True,
            'message': '获取用户信息成功',
            'data': {
                'username': current_user.username,
                'role': current_user.role,
                'user_level': current_user.user_level,
                'expiry_date': current_user.expiry_date.isoformat() if current_user.expiry_date else None
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取用户信息失败: {str(e)}',
            'data': {}
        })


@api_bp.route('/refresh_activation_status', methods=['GET'])
def refresh_activation_status():
    """手动刷新激活状态"""
    try:
        # 调用激活服务刷新状态（从服务器查询并更新数据库）
        result = license_service.refresh_activation_status()
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'刷新激活状态失败: {str(e)}',
            'data': {
                'is_activated': False,
                'activation_status': '未激活',
                'activation_type': 'NULL',
                'expiry_date': 'NULL',
                'activation_date': 'NULL'
            }
        })


@api_bp.route('/activation_history', methods=['GET'])
def get_activation_history():
    """查询激活历史"""
    try:
        # 调用激活服务获取历史
        result = license_service.get_activation_history()
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'查询激活历史失败: {str(e)}',
            'data': []
        })


@api_bp.route('/check_update', methods=['GET'])
def check_update():
    """检查升级"""
    try:
        from app.services import upgrade_service
        # 调用升级服务检查升级
        result = upgrade_service.get_latest_version()
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'检查升级失败: {str(e)}',
            'data': {}
        })


@api_bp.route('/download_update', methods=['POST'])
def download_update():
    """下载升级包"""
    try:
        from app.services import upgrade_service
        # 获取请求数据
        data = request.get_json()
        download_url = data.get('download_url')
        
        # 验证参数
        if not download_url:
            return jsonify({'success': False, 'message': '缺少下载URL参数'}), 400
        
        # 调用升级服务下载升级包
        result = upgrade_service.download_upgrade_package(download_url)
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'下载升级包失败: {str(e)}',
            'data': {}
        })


@api_bp.route('/download_update_stream', methods=['POST'])
def download_update_stream():
    """下载升级包（流式传输进度）"""
    try:
        import json
        import queue
        import threading
        from flask import Response
        from app.services import upgrade_service
        # 获取请求数据
        data = request.get_json()
        download_url = data.get('download_url')
        
        # 验证参数
        if not download_url:
            return jsonify({'success': False, 'message': '缺少下载URL参数'}), 400
        
        # 创建队列来传递进度信息
        progress_queue = queue.Queue()
        download_result = None
        download_error = None
        
        # 下载线程函数
        def download_thread():
            nonlocal download_result, download_error
            
            # 进度回调函数
            def progress_callback(progress, downloaded, total):
                # 将进度信息添加到队列
                progress_queue.put({"type": "progress", "progress": progress, "downloaded": downloaded, "total": total})
            
            try:
                # 调用升级服务下载升级包，传递进度回调
                download_result = upgrade_service.download_upgrade_package(download_url, progress_callback=progress_callback)
                # 下载完成，添加完成信息到队列
                progress_queue.put({"type": "complete", "result": download_result})
            except Exception as e:
                download_error = str(e)
                # 下载失败，添加错误信息到队列
                progress_queue.put({"type": "error", "message": download_error})
        
        # 启动下载线程
        thread = threading.Thread(target=download_thread)
        thread.daemon = True
        thread.start()
        
        # SSE生成器函数
        def generate():
            while True:
                try:
                    # 从队列获取进度信息，超时1秒
                    item = progress_queue.get(timeout=1)
                    # 发送进度信息
                    yield f'data: {json.dumps(item)}\n\n'
                    # 标记任务完成
                    progress_queue.task_done()
                    # 如果是完成或错误，退出循环
                    if item["type"] in ["complete", "error"]:
                        break
                except queue.Empty:
                    # 队列为空，继续等待
                    continue
        
        # 返回SSE响应
        return Response(generate(), mimetype='text/event-stream', headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'下载升级包失败: {str(e)}',
            'data': {}
        })


@api_bp.route('/update_application', methods=['POST'])
def update_application():
    """升级应用"""
    try:
        from app.services import upgrade_service
        # 获取请求数据
        data = request.get_json()
        upgrade_package_path = data.get('upgrade_package_path')
        
        # 验证参数
        if not upgrade_package_path:
            return jsonify({'success': False, 'message': '缺少升级包路径参数'}), 400
        
        # 调用升级服务升级应用
        result = upgrade_service.upgrade_application(upgrade_package_path)
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'升级应用失败: {str(e)}',
            'data': {}
        })


@api_bp.route('/restart_application', methods=['POST'])
def restart_application():
    """重启应用"""
    try:
        import os, sys
        logger.info('开始重启应用...')
        # 执行重启
        try:
            os.execv(sys.executable, [sys.executable] + sys.argv)
            # 如果成功，这行代码永远不会返回
        except OSError as e:
            # 只有出错时才执行这里
            logger.error(f"重启失败: {e}")
            return jsonify({
                'success': False,
                'message': f'重启失败: {e}',
                'data': {}
            })
            sys.exit(1)
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'重启应用失败: {str(e)}',
            'data': {}
        })


@api_bp.route('/check_upgrade_preconditions', methods=['GET'])
def check_upgrade_preconditions():
    """检查升级前的条件"""
    try:
        from app.services import upgrade_service
        # 调用升级服务检查升级前条件
        result = upgrade_service.check_upgrade_preconditions()
        return jsonify({
            'success': True,
            'message': '检查升级前条件成功',
            'data': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'检查升级前条件失败: {str(e)}',
            'data': {}
        })


@api_bp.route('/delete_invitation_code', methods=['POST'])
@login_required
def delete_invitation_code():
    """删除邀请码"""
    try:
        # 获取请求数据
        data = request.get_json()
        code_id = data.get('code_id')
        
        # 验证参数
        if not code_id:
            return jsonify({'success': False, 'message': '缺少邀请码ID参数'}), 400
        
        # 检查权限
        from app.models import AppConfig
        app_config = AppConfig.get_config()
        if app_config.app_mode != 'team':
            return jsonify({'success': False, 'message': '当前版本不支持此功能'}), 403
        
        if current_user.role != 'admin':
            return jsonify({'success': False, 'message': '您没有权限执行此操作'}), 403
        
        # 删除邀请码
        success = registration_service.delete_invitation_code(code_id, current_user.id)
        
        if success:
            return jsonify({'success': True, 'message': '邀请码删除成功'})
        else:
            return jsonify({'success': False, 'message': '邀请码删除失败'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': f'删除邀请码失败: {str(e)}'}), 500


@api_bp.route('/delete_user', methods=['POST'])
@login_required
def delete_user():
    """删除用户"""
    try:
        # 获取请求数据
        data = request.get_json()
        user_id = data.get('user_id')
        
        # 验证参数
        if not user_id:
            return jsonify({'success': False, 'message': '缺少用户ID参数'}), 400
        
        # 检查权限
        from app.models import AppConfig
        app_config = AppConfig.get_config()
        if app_config.app_mode != 'team':
            return jsonify({'success': False, 'message': '当前版本不支持此功能'}), 403
        
        if current_user.role != 'admin':
            return jsonify({'success': False, 'message': '您没有权限执行此操作'}), 403
        
        # 删除用户
        result = user_service.delete_user(int(user_id))
        
        if result['success']:
            return jsonify({'success': True, 'message': result['message']})
        else:
            return jsonify({'success': False, 'message': result['message']}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': f'删除用户失败: {str(e)}'}), 500


@api_bp.route('/admin/registration-settings', methods=['POST'])
@login_required
def registration_settings():
    """
    管理员配置注册设置
    """
    from ..models import AppConfig
    from flask import jsonify
    
    # 检查应用模式，只有团队模式可以访问
    app_config = AppConfig.get_config()
    if app_config.app_mode != 'team':
        return jsonify({'success': False, 'message': '当前版本不支持此功能'})
    
    # 检查是否为管理员
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': '您没有权限访问此页面'})
    
    try:
        # 获取JSON数据
        data = request.get_json()
        
        # 更新配置
        if 'allow_registration' in data:
            app_config.allow_registration = data['allow_registration']
        if 'require_invitation' in data:
            app_config.require_invitation = data['require_invitation']
        
        # 保存到数据库
        from ..services import db
        db.session.commit()
        
        return jsonify({'success': True, 'message': '注册设置更新成功'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'保存设置失败: {str(e)}'})


@api_bp.route('/admin/invitation-codes', methods=['POST'])
@login_required
def invitation_codes():
    """
    管理员管理邀请码
    """
    from ..models import AppConfig
    from ..services.advanced.registration_service import registration_service
    from flask import jsonify
    
    # 检查应用模式，只有团队模式可以访问
    app_config = AppConfig.get_config()
    if app_config.app_mode != 'team':
        return jsonify({'success': False, 'message': '当前版本不支持此功能'})
    
    # 检查是否为管理员
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': '您没有权限访问此页面'})
    
    try:
        # 获取JSON数据
        data = request.get_json()
        
        # 获取参数
        max_uses = int(data.get('max_uses', 10))
        expire_days = int(data.get('expire_days', 7))
        code_count = int(data.get('code_count', 5))
        user_level = data.get('user_level', 'normal')
        vip_expiry_days = data.get('vip_expiry_days')
        vip_expiry_days = int(vip_expiry_days) if vip_expiry_days else None
        
        # 生成邀请码
        result = registration_service.generate_invitation_codes(
            user_id=current_user.id,
            max_uses=max_uses,
            expire_days=expire_days,
            count=code_count,
            user_level=user_level,
            vip_expiry_days=vip_expiry_days
        )
        
        return jsonify({'success': True, 'message': f'成功生成 {code_count} 个邀请码'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'生成邀请码失败: {str(e)}'})


@api_bp.route('/admin/users/edit', methods=['POST'])
@login_required
def edit_user():
    """
    管理员修改用户
    """
    from ..models import AppConfig
    from ..services.advanced.user_service import user_service
    from flask import jsonify
    
    # 检查应用模式，只有团队模式可以访问
    app_config = AppConfig.get_config()
    if app_config.app_mode != 'team':
        return jsonify({'success': False, 'message': '当前版本不支持此功能'})
    
    # 检查是否为管理员
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': '您没有权限访问此页面'})
    
    try:
        # 获取JSON数据
        data = request.get_json()
        
        # 获取参数
        user_id = int(data.get('user_id'))
        password = data.get('password')
        confirm_password = data.get('confirm_password')
        user_level = data.get('user_level')
        expiry_date_str = data.get('expiry_date')
        
        # 处理到期时间
        from datetime import datetime
        expiry_date = None
        if expiry_date_str:
            expiry_date = datetime.fromisoformat(expiry_date_str)
        
        # 调用用户服务更新用户信息
        result = user_service.update_user(user_id, password, confirm_password, user_level, expiry_date)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': f'更新用户失败: {str(e)}'})


@api_bp.route('/admin/users/create', methods=['POST'])
@login_required
def create_user():
    """
    管理员创建用户
    """
    from ..models import AppConfig
    from ..services.advanced.user_service import user_service
    from flask import jsonify
    
    # 检查应用模式，只有团队模式可以访问
    app_config = AppConfig.get_config()
    if app_config.app_mode != 'team':
        return jsonify({'success': False, 'message': '当前版本不支持此功能'})
    
    # 检查是否为管理员
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': '您没有权限访问此页面'})
    
    try:
        # 获取JSON数据
        data = request.get_json()
        
        # 获取参数
        username = data.get('username')
        password = data.get('password')
        confirm_password = data.get('confirm_password')
        user_level = data.get('user_level', 'normal')
        expiry_date_str = data.get('expiry_date')
        
        # 处理到期时间
        from datetime import datetime
        expiry_date = None
        if expiry_date_str:
            expiry_date = datetime.fromisoformat(expiry_date_str)
        
        # 调用用户服务创建用户
        result = user_service.create_user_by_admin(username, password, confirm_password, user_level, expiry_date)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': f'创建用户失败: {str(e)}'})


@api_bp.route('/save_settings', methods=['POST'])
@login_required
def save_settings():
    """
    保存设置
    """
    import json
    from ..models import ReplyConfig, BiliAccount
    from ..services import db
    
    try:
        # 获取表单数据
        form_data = request.form
        
        # 获取必要参数
        mid = form_data.get('mid')
        template_id = form_data.get('template_id')
        form_type = form_data.get('form_type')
        reset_default = form_data.get('reset_default') == 'true'
        
        # 确定要保存的设置对象
        setting = None
        if template_id:
            # 模板设置
            setting = ReplyConfig.query.filter_by(id=template_id, is_template=True).first()
            if not setting:
                return jsonify({'success': False, 'message': '模板不存在'})
        elif mid:
            # 账号设置
            account = BiliAccount.query.filter_by(mid=mid, user_id=current_user.id).first()
            if not account:
                return jsonify({'success': False, 'message': '账号不存在'})
            setting = account.reply_config
            if not setting:
                setting = ReplyConfig()
                db.session.add(setting)
                db.session.flush()
                account.reply_config_id = setting.id
        else:
            return jsonify({'success': False, 'message': '缺少必要参数'})
        
        # 保存设置
        if reset_default:
            # 恢复默认值
            default_setting = ReplyConfig()
            
            if form_type == 'new-fans-form':
                setting.enable_new_fans_reply = default_setting.enable_new_fans_reply
                setting.new_fans_reply = default_setting.new_fans_reply
            elif form_type == 'fans-form':
                setting.enable_fans_reply = default_setting.enable_fans_reply
                setting.fans_complete_dict = default_setting.fans_complete_dict
                setting.fans_keyword_dict = default_setting.fans_keyword_dict
                setting.fans_other_reply = default_setting.fans_other_reply
            elif form_type == 'non-fans-form':
                setting.enable_non_fans_reply = default_setting.enable_non_fans_reply
                setting.non_fans_complete_dict = default_setting.non_fans_complete_dict
                setting.non_fans_keyword_dict = default_setting.non_fans_keyword_dict
                setting.non_fans_other_reply = default_setting.non_fans_other_reply
            elif form_type == 'general-form':
                setting.repet_protect_times = default_setting.repet_protect_times
                setting.reply_interval_seconds = default_setting.reply_interval_seconds
            elif form_type == 'personality-form':
                setting.personality_identifier = default_setting.personality_identifier
        else:
            # 保存表单数据
            if form_type == 'new-fans-form':
                setting.enable_new_fans_reply = 'enable_new_fans_reply' in form_data
                if 'new_fans_reply' in form_data:
                    setting.new_fans_reply = form_data.get('new_fans_reply', '')
            elif form_type == 'fans-form':
                setting.enable_fans_reply = 'enable_fans_reply' in form_data
                if 'fans_complete_dict' in form_data:
                    try:
                        setting.fans_complete_dict = json.loads(form_data.get('fans_complete_dict', '{}'))
                    except json.JSONDecodeError:
                        setting.fans_complete_dict = {}
                if 'fans_keyword_dict' in form_data:
                    try:
                        setting.fans_keyword_dict = json.loads(form_data.get('fans_keyword_dict', '{}'))
                    except json.JSONDecodeError:
                        setting.fans_keyword_dict = {}
                if 'fans_other_reply' in form_data:
                    setting.fans_other_reply = form_data.get('fans_other_reply', '')
            elif form_type == 'non-fans-form':
                setting.enable_non_fans_reply = 'enable_non_fans_reply' in form_data
                if 'non_fans_complete_dict' in form_data:
                    try:
                        setting.non_fans_complete_dict = json.loads(form_data.get('non_fans_complete_dict', '{}'))
                    except json.JSONDecodeError:
                        setting.non_fans_complete_dict = {}
                if 'non_fans_keyword_dict' in form_data:
                    try:
                        setting.non_fans_keyword_dict = json.loads(form_data.get('non_fans_keyword_dict', '{}'))
                    except json.JSONDecodeError:
                        setting.non_fans_keyword_dict = {}
                if 'non_fans_other_reply' in form_data:
                    setting.non_fans_other_reply = form_data.get('non_fans_other_reply', '')
            elif form_type == 'general-form':
                if 'repet_protect_times' in form_data:
                    setting.repet_protect_times = int(form_data.get('repet_protect_times', 5))
                if 'reply_interval_seconds' in form_data:
                    setting.reply_interval_seconds = int(form_data.get('reply_interval_seconds', 5))
            elif form_type == 'personality-form':
                if 'personality_identifier' in form_data:
                    setting.personality_identifier = form_data.get('personality_identifier', '')
        
        # 保存到数据库
        db.session.commit()
        
        return jsonify({'success': True, 'message': '保存成功！'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'保存失败: {str(e)}'})



