from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, Response
from flask_login import login_required, current_user, login_user, logout_user
from app import current_process, physical_cores
from . import main_bp
from ..models import User, AppConfig, BiliAccount
from ..models.config import ReplyConfig
from ..services import db
from ..services.bilibili.auth_service import AuthService
from ..services.license.license_manager import license_manager
import logging
import json
import os
from importlib import resources


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@main_bp.route('/')
def index():
    """
    首页
    """
    # 检查是否为首次运行
    is_first_run = User.query.count() == 0
    if is_first_run:
        return redirect(url_for('main.init'))
    
    # 如果用户未登录，跳转到登录页面
    if not current_user.is_authenticated:
        return redirect(url_for('main.login'))
    
    # 获取当前登录用户信息
    user = current_user

    if user.role == 'admin':
        return redirect(url_for('main.admin_users'))
    
    # 获取当前用户的B站账号信息
    bili_accounts = BiliAccount.query.filter_by(user_id=current_user.id).all()
    
    # 为每个账号添加头像信息（不修改数据库，仅在当前请求中使用）
    accounts_with_avatar = []
    auth_service = AuthService()
    for bili_account in bili_accounts:
        # 获取用户信息，包括头像
        user_info = auth_service.get_user_info(bili_account.mid, bili_account.mid)
        avatar = ''
        if user_info and user_info.get('success'):
            user_data = user_info.get('data', {})
            card = user_data.get('card', {})
            if card:
                avatar = card.get('face', '')
        
        # 将账号对象转换为字典，仅包含基本信息
        account_dict = {
            'mid': bili_account.mid,
            'uname': bili_account.uname,
            'cookies': bili_account.cookies,
            'autoreply_enabled': bili_account.autoreply_enabled,
            'created_at': bili_account.created_at.strftime('%Y-%m-%d'),
            'updated_at': bili_account.updated_at.strftime('%Y-%m-%d'),
            'avatar': avatar,  # 头像
            'account_status': "正常"  # 默认状态
        }
        accounts_with_avatar.append(account_dict)
    
    return render_template('core/index.html', user=user, bilibili_users=accounts_with_avatar)


@main_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """
    设置页面
    """
    from ..models import AppConfig
    
    # 获取应用配置
    app_config = AppConfig.get_config()
    
    if request.method == 'POST':
        setting_type = request.form.get('setting_type')
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        try:
            if setting_type == 'account':
                # 处理用户设置
                username = request.form.get('username')
                password = request.form.get('password')
                confirm_password = request.form.get('confirm_password')
                
                # 标志位：是否有实际修改
                has_changes = False
                
                # 验证用户名
                if username != current_user.username:
                    # 检查用户名是否已存在
                    existing_user = User.query.filter_by(username=username).first()
                    if existing_user:
                        if is_ajax:
                            return jsonify({'success': False, 'message': '用户名已存在'}), 400
                        flash('用户名已存在', 'danger')
                        return redirect(url_for('main.settings'))
                    current_user.username = username
                    has_changes = True
                
                # 验证密码
                if password:
                    if password != confirm_password:
                        if is_ajax:
                            return jsonify({'success': False, 'message': '两次输入的密码不一致'}), 400
                        flash('两次输入的密码不一致', 'danger')
                        return redirect(url_for('main.settings'))
                    current_user.set_password(password)
                    has_changes = True
                
                # 只有当有实际修改时才提交并返回成功消息
                if has_changes:
                    if is_ajax:
                        db.session.commit()
                        return jsonify({'success': True, 'message': '用户设置更新成功'})
                    db.session.commit()
                    flash('用户设置更新成功', 'success')
                else:
                    if is_ajax:
                        return jsonify({'success': True, 'message': '用户设置未修改'})
                    flash('用户设置未修改', 'info')
                
            elif setting_type == 'security':
                # 处理登录设置
                trust_login = request.form.get('enable_trust_login') == 'on'
                current_user.trust_login = trust_login
                db.session.commit()
                
                if is_ajax:
                    return jsonify({'success': True, 'message': '登录设置更新成功'})
                flash('登录设置更新成功', 'success')
                
            elif setting_type == 'appearance':
                # 处理主题设置
                theme = request.form.get('theme')
                current_user.theme = theme
                db.session.commit()
                
                if is_ajax:
                    return jsonify({'success': True, 'message': '主题设置更新成功'})
                flash('主题已更换', 'success')
            
            # 保存到数据库
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            if is_ajax:
                return jsonify({'success': False, 'message': f'设置保存失败: {str(e)}'}), 500
            flash(f'设置保存失败: {str(e)}', 'danger')
        
        return redirect(url_for('main.settings'))
    
    return render_template('core/settings.html', app_config=app_config)


@main_bp.route('/advanced')
@login_required
def advanced():
    """
    高级功能页面
    """
    from ..models import AppConfig
    
    # 获取应用配置
    app_config = AppConfig.get_config()
    
    return render_template('core/advanced.html', app_config=app_config)


@main_bp.route('/init')
def init():
    """
    首次运行初始化页面
    """
    # 检查是否已有用户，如果有则重定向到首页
    if User.query.count() > 0:
        return redirect(url_for('main.index'))
    
    return render_template('core/init.html')


@main_bp.route('/inituser', methods=['POST'])
def inituser():
    """
    创建初始用户
    """
    # 从表单中获取用户选择的模式
    app_mode = request.form.get('app_mode')
    
    # 构建用户数据
    user_data = {}
    if app_mode == 'personal':
        user_data['username'] = request.form.get('username')
        user_data['password'] = request.form.get('password')
        user_data['confirm_password'] = request.form.get('confirm_password')
    else:  # team模式
        user_data['admin_username'] = request.form.get('admin_username')
        user_data['admin_password'] = request.form.get('admin_password')
        user_data['admin_confirm_password'] = request.form.get('admin_confirm_password')
        user_data['license_code'] = request.form.get('license_code')
    
    # 调用用户服务创建初始用户
    from ..services.advanced.user_service import user_service
    result = user_service.create_initial_user(app_mode, user_data)
    
    if result['success']:
        flash(result['message'], 'success')
        return redirect(url_for('main.index'))
    else:
        flash(result['message'], 'danger')
        # 如果是团队版且授权码验证失败，跳转到步骤3
        if app_mode == 'team' and '授权码验证失败' in result['message']:
            return redirect(url_for('main.init', step=3))
        return redirect(url_for('main.init'))


@main_bp.route('/logout')
def logout():
    """
    用户退出登录
    """
    # 使用logout_user函数真正退出登录
    from flask_login import logout_user
    logout_user()
    flash('退出登录成功', 'success')
    return redirect(url_for('main.login'))


@main_bp.route('/admin/users')
@login_required
def admin_users():
    """
    管理员查看用户列表
    """
    from ..models import AppConfig
    
    # 检查应用模式，只有团队模式可以访问
    app_config = AppConfig.get_config()
    if app_config.app_mode != 'team':
        flash('当前版本不支持此功能', 'warning')
        return redirect(url_for('main.index'))
    
    # 检查是否为管理员
    if current_user.role != 'admin':
        flash('您没有权限访问此页面', 'danger')
        return redirect(url_for('main.index'))
    
    # 获取所有用户
    users = User.query.all()
    
    return render_template('admin/users.html', users=users)


@main_bp.route('/admin/register')
@login_required
def registration_management():
    """
    注册管理整合页面
    """
    from ..models import AppConfig
    from ..services.advanced.registration_service import registration_service
    
    # 检查应用模式，只有团队模式可以访问
    app_config = AppConfig.get_config()
    if app_config.app_mode != 'team':
        flash('当前版本不支持此功能', 'warning')
        return redirect(url_for('main.index'))
    
    # 检查是否为管理员
    if current_user.role != 'admin':
        flash('您没有权限访问此页面', 'danger')
        return redirect(url_for('main.index'))
    
    # 获取邀请码
    invitation_codes = registration_service.get_invitation_codes(current_user.id)
    
    return render_template('admin/register.html', invitation_codes=invitation_codes, app_config=app_config)


@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    用户注册页面
    """
    from ..models import AppConfig
    from ..services.advanced.registration_service import registration_service
    
    # 检查是否为首次运行
    is_first_run = User.query.count() == 0
    if is_first_run:
        # 如果是首次运行，跳转到初始化页面
        return redirect(url_for('main.init'))
    
    # 检查应用模式，只有团队模式可以注册
    app_config = AppConfig.get_config()
    if app_config.app_mode != 'team':
        flash('当前版本不支持注册功能', 'warning')
        return redirect(url_for('main.login'))
    
    # 检查是否允许直接注册
    if not app_config.allow_registration:
        flash('当前系统已关闭注册功能', 'warning')
        return redirect(url_for('main.login'))
    
    if request.method == 'POST':
        # 获取表单数据
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        invitation_code = request.form.get('invitation_code')
        
        # 验证输入
        if not username or not password:
            flash('用户名和密码不能为空', 'danger')
            return redirect(url_for('main.register'))
        
        # 验证密码一致性
        if password != confirm_password:
            flash('两次输入的密码不一致', 'danger')
            return redirect(url_for('main.register'))
        
        # 检查用户名是否已存在
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('用户名已存在', 'danger')
            return redirect(url_for('main.register'))
        
        # 验证邀请码
        user_level = 'normal'
        expiry_date = None
        
        if app_config.require_invitation:
            if not invitation_code:
                flash('请输入邀请码', 'danger')
                return redirect(url_for('main.register'))
            
            # 获取邀请码信息
            invite_code_obj = registration_service.get_invitation_code_by_code(invitation_code)
            if not invite_code_obj or not invite_code_obj.is_valid():
                flash('无效的邀请码', 'danger')
                return redirect(url_for('main.register'))
            
            # 使用邀请码
            if not registration_service.validate_invitation_code(invitation_code):
                flash('无效的邀请码', 'danger')
                return redirect(url_for('main.register'))
            
            # 获取邀请码设置的用户等级
            user_level = invite_code_obj.user_level
            # 如果是VIP，计算到期时间
            if user_level == 'vip' and invite_code_obj.vip_expiry_days:
                from datetime import datetime, timedelta
                from config import Config
                expiry_date = datetime.now(Config.TIMEZONE) + timedelta(days=invite_code_obj.vip_expiry_days)
        
        # 创建注册用户
        user = User(
            username=username,
            role='registered',  # 注册用户角色
            user_level=user_level,
            expiry_date=expiry_date,
            registration_code=invitation_code  # 保存邀请码
        )
        user.set_password(password)
        
        # 保存到数据库
        db.session.add(user)
        db.session.commit()
        
        flash('注册成功，请登录', 'success')
        return redirect(url_for('main.login'))
    
    return render_template('auth/register.html', app_config=app_config)


@main_bp.route('/register/invite/<code>', methods=['GET', 'POST'])
def register_by_invite(code):
    """
    通过邀请码注册
    """
    from ..models import AppConfig
    from ..services.advanced.registration_service import registration_service
    
    # 检查是否为首次运行
    is_first_run = User.query.count() == 0
    if is_first_run:
        # 如果是首次运行，跳转到初始化页面
        return redirect(url_for('main.init'))
    
    # 检查应用模式，只有团队模式可以注册
    app_config = AppConfig.get_config()
    if app_config.app_mode != 'team':
        flash('当前版本不支持注册功能', 'warning')
        return redirect(url_for('main.login'))
    
    # 验证邀请码
    invitation_code = registration_service.get_invitation_code_by_code(code)
    if not invitation_code or not invitation_code.is_valid():
        flash('无效的邀请码或邀请码已过期', 'danger')
        return redirect(url_for('main.login'))
    
    # 获取邀请码设置的用户等级
    user_level = invitation_code.user_level
    # 如果是VIP，计算到期时间
    expiry_date = None
    if user_level == 'vip' and invitation_code.vip_expiry_days:
        from datetime import datetime, timedelta
        from config import Config
        expiry_date = datetime.now(Config.TIMEZONE) + timedelta(days=invitation_code.vip_expiry_days)
    
    if request.method == 'POST':
        # 获取表单数据
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # 验证输入
        if not username or not password:
            flash('用户名和密码不能为空', 'danger')
            return redirect(url_for('main.register_by_invite', code=code))
        
        # 验证密码一致性
        if password != confirm_password:
            flash('两次输入的密码不一致', 'danger')
            return redirect(url_for('main.register_by_invite', code=code))
        
        # 检查用户名是否已存在
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('用户名已存在', 'danger')
            return redirect(url_for('main.register_by_invite', code=code))
        
        # 使用邀请码
        if not registration_service.validate_invitation_code(code):
            flash('邀请码已失效', 'danger')
            return redirect(url_for('main.login'))
        
        # 创建注册用户
        user = User(
            username=username,
            role='registered',  # 注册用户角色
            user_level=user_level,
            expiry_date=expiry_date,
            registration_code=code  # 保存邀请码
        )
        user.set_password(password)
        
        # 保存到数据库
        db.session.add(user)
        db.session.commit()
        
        flash('注册成功，请登录', 'success')
        return redirect(url_for('main.login'))
    
    return render_template('auth/register.html', invitation_code=code, app_config=app_config)


@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    用户登录页面
    """
    # 检查是否为首次运行
    is_first_run = User.query.count() == 0
    if is_first_run:
        # 如果是首次运行，跳转到初始化页面
        return redirect(url_for('main.init'))
    
    # 已登录用户不应该访问登录页面，直接跳转到首页
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        # 获取表单数据
        username = request.form.get('username')
        password = request.form.get('password')
        
        # 查找用户
        user = User.query.filter_by(username=username).first()
        
        # 检查是否满足内网免密登录条件
        allow_passwordless = False
        
        if user:
            # 1. 检查是否为个人版本
            app_config = AppConfig.get_config()
            is_personal = app_config.app_mode == 'personal'
            
            if is_personal:
                # 2. 检查是否启用了内网免密登录
                if user.trust_login:
                    # 3. 判断是否为内网访问
                    # 获取真实IP
                    real_ip = request.remote_addr
                    if request.headers.get('X-Forwarded-For'):
                        real_ip = request.headers.get('X-Forwarded-For').split(',')[0].strip()
                    
                    # 检查真实IP是否为内网网段
                    is_intranet_ip = False
                    if real_ip in ['127.0.0.1', '::1', 'localhost']:
                        is_intranet_ip = True
                    elif real_ip.startswith('10.') or (real_ip.startswith('172.') and 16 <= int(real_ip.split('.')[1]) <= 31) or real_ip.startswith('192.168.'):
                        is_intranet_ip = True
                    
                    # 检查Host是否为内网网段
                    host = request.host.split(':')[0]
                    is_intranet_host = False
                    if host in ['127.0.0.1', '::1', 'localhost'] or host.startswith('10.') or (host.startswith('172.') and 16 <= int(host.split('.')[1]) <= 31) or host.startswith('192.168.') or host in ['intranet.app', 'internal.company.local']:
                        is_intranet_host = True
                    
                    # 双条件同时满足
                    allow_passwordless = is_intranet_ip and is_intranet_host
        
        # 登录验证逻辑
        login_success = False
        
        if user:
            # 条件1：满足内网免密登录条件
            if allow_passwordless:
                login_success = True
            # 条件2：密码正确（避免password为None时调用check_password）
            elif password and user.check_password(password):
                login_success = True
        
        if login_success:
            # 登录成功，使用login_user函数实际登录用户
            login_user(user)
            
            # 检查并更新过期的VIP用户
            from ..services.advanced.user_service import user_service
            user_service.check_expired_vip_users()
            
            flash('登录成功', 'success')
            return redirect(url_for('main.index'))
        else:
            # 登录失败，显示错误信息
            flash('用户名或密码错误', 'danger')
            return redirect(url_for('main.login'))
    
    # GET请求，判断是否满足内网免密登录条件
    
    # 1. 获取应用配置，判断是否为个人版本
    app_config = AppConfig.get_config()
    is_personal = app_config.app_mode == 'personal'
    
    # 2. 只有个人版本才执行免密登录检查
    show_passwordless_login = False
    default_username = ''
    
    if is_personal:
        # 获取系统用户
        user = User.query.first()
        trust_login_enabled = False
        
        if user:
            # 3. 检查是否启用了内网免密登录
            trust_login_enabled = user.trust_login
            default_username = user.username
        
        # 4. 判断是否为内网访问
        is_intranet_access = False
        
        if user and trust_login_enabled:
            # 获取真实IP
            real_ip = request.remote_addr
            if request.headers.get('X-Forwarded-For'):
                real_ip = request.headers.get('X-Forwarded-For').split(',')[0].strip()
            
            # 检查真实IP是否为内网网段
            is_intranet_ip = False
            if real_ip in ['127.0.0.1', '::1', 'localhost']:
                is_intranet_ip = True
            elif real_ip.startswith('10.') or (real_ip.startswith('172.') and 16 <= int(real_ip.split('.')[1]) <= 31) or real_ip.startswith('192.168.'):
                is_intranet_ip = True
            
            # 检查Host是否为内网网段
            host = request.host.split(':')[0]
            is_intranet_host = False
            if host in ['127.0.0.1', '::1', 'localhost'] or host.startswith('10.') or (host.startswith('172.') and 16 <= int(host.split('.')[1]) <= 31) or host.startswith('192.168.') or host in ['intranet.app', 'internal.company.local']:
                is_intranet_host = True
            
            # 双条件同时满足
            is_intranet_access = is_intranet_ip and is_intranet_host
        
        # 5. 综合判断是否显示免密登录提示
        show_passwordless_login = not current_user.is_authenticated and is_intranet_access and trust_login_enabled
    
    return render_template('auth/login.html', 
                         show_passwordless_login=show_passwordless_login,
                         default_username=default_username,
                         app_config=app_config)


@main_bp.route('/template')
@login_required
def template():
    """
    模板管理页面
    """
    # 获取所有模板
    templates = ReplyConfig.query.filter_by(is_template=True).order_by(ReplyConfig.created_at.desc()).all()
    
    return render_template('core/template.html', templates=templates)


@main_bp.route('/replyconfig', methods=['GET'])
@login_required
def replyconfig():
    """
    自动回复配置页面
    支持多种平台，目前主要支持B站
    """
    # 获取参数
    platform = request.args.get('platform', 'bilibili')
    mid = request.args.get('mid')
    template_id = request.args.get('template_id')
    
    # 编辑模板时不需要mid参数
    if not mid and not template_id:
        from flask import flash, redirect, url_for
        flash('缺少必要参数', 'warning')
        return redirect(url_for('main.index'))

    
    current_account = None
    current_time = None
    account_status = "正常"
    is_editing_template = False
    template_name = None
    setting = None
    
    # 从数据库中获取账号信息
    from app.models import BiliAccount
    from datetime import datetime
    from config import Config
    from flask import redirect, url_for
    from app.services import db
    
    # 获取当前时间，显示完整日期时间
    current_time = datetime.now(Config.TIMEZONE).strftime('%Y-%m-%d %H:%M:%S')
    
    # 情况1：编辑模板（优先处理template_id）
    if template_id:
        is_editing_template = True
        setting = ReplyConfig.query.filter_by(id=template_id, is_template=True).first()
        if not setting:
            from flask import flash
            flash('模板不存在', 'warning')
            return redirect(url_for('main.index'))
        
        template_name = setting.name
        
        # 创建一个虚拟账号，用于模板编辑页面
        current_account = type('VirtualAccount', (), {
            'id': 0,
            'mid': 0,
            'uname': template_name,
            'face': '',
            'stat': {},
            'created_at': setting.created_at,
            'updated_at': setting.updated_at
        })()
    
    # 情况2：编辑账号设置
    else:
        # 根据平台类型获取账号信息
        if platform == 'bilibili':
            # 查询数据库获取账号信息
            current_account = BiliAccount.query.filter_by(mid=mid, user_id=current_user.id).first()
            
            if current_account:
                # 使用已经导入的AuthService
                auth_service = AuthService()
                
                # 获取最新的用户信息
                user_info = auth_service.get_user_info(mid, mid)  # 两个参数：当前账号ID和要查询的用户ID相同
                if user_info and user_info.get('success'):
                    user_data = user_info.get('data', {})
                    card = user_data.get('card', {})
                    if card:
                        # 更新账号信息，确保显示最新数据
                        current_account.face = card.get('face', '')
                        current_account.uname = card.get('name', current_account.uname)
                    else:
                        account_status = "异常"
                else:
                    account_status = "异常"
                
                # 获取或创建ReplyConfig对象（仅用于账号设置）
                setting = current_account.reply_config
                
                # 如果没有setting对象，创建一个新的
                if not setting:
                    setting = ReplyConfig()
                    db.session.add(setting)
                    db.session.flush()  # 获取新的ID
                    current_account.reply_config_id = setting.id
                    db.session.commit()
                    
                    # 刷新对象，确保获取到最新的属性
                    db.session.refresh(setting)
            else:
                # 账号不存在，提示并跳转到首页
                from flask import flash
                flash('账号不存在', 'warning')
                return redirect(url_for('main.index'))
        else:
            # 暂不支持其他平台
            from flask import flash
            flash('暂不支持该平台', 'warning')
            return redirect(url_for('main.index'))
    
    # 获取当前用户的所有模板，用于设置页面的模板切换
    templates = ReplyConfig.query.filter_by(is_template=True).order_by(ReplyConfig.created_at.desc()).all()
    
    # 创建一个临时的ReplyConfig实例，用于获取默认值
    default_setting = ReplyConfig()
    
    return render_template(
        'core/replyconfig.html', 
        current_account=current_account, 
        mid=mid,
        platform=platform,
        template_id=template_id,
        current_time=current_time, 
        account_status=account_status, 
        setting=setting, 
        default_setting=default_setting,
        templates=templates,
        is_editing_template=is_editing_template,
        template_name=template_name
    )


@main_bp.route('/about')
def about():
    """
    关于页面
    """
    return render_template('core/about.html')





@main_bp.route('/static/<path:filename>', endpoint='static')
def serve_static(filename):
    """
    使用importlib.resources提供静态文件服务，支持zipapp环境
    """
    try:
        # 使用importlib.resources获取静态文件内容
        resource_path = f'static/{filename}'
        content = resources.files('app').joinpath(resource_path).read_bytes()
        
        # 确定MIME类型
        mime_types = {
            '.css': 'text/css',
            '.js': 'application/javascript',
            '.ico': 'image/x-icon',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.woff2': 'font/woff2',
            '.woff': 'font/woff',
            '.ttf': 'font/ttf',
            '.otf': 'font/otf'
        }
        
        ext = os.path.splitext(filename)[1].lower()
        mime_type = mime_types.get(ext, 'application/octet-stream')
        
        # 返回静态文件内容
        from flask import current_app
        return current_app.response_class(content, mimetype=mime_type)
    except Exception as e:
        from flask import current_app
        current_app.logger.error(f'静态文件服务错误: {filename}, 错误: {str(e)}')
        return '静态文件未找到', 404
