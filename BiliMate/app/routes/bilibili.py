from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from app.services.bilibili import AuthService
from app.routes import api_response
import logging

# 获取日志记录器
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# 创建B站相关路由蓝图
bilibili_bp = Blueprint('bilibili', __name__)


@bilibili_bp.route('/login')
@login_required
def login():
    """
    B站登录页面
    """
    return render_template('bilibili/login.html')


@bilibili_bp.route('/login/generate_qrcode')
@login_required
@api_response
def generate_login_qrcode():
    """
    生成B站登录二维码
    """
    try:
        logger.info("开始生成B站登录二维码")
        # 动态创建认证服务实例
        auth_service = AuthService()
        # 调用认证服务生成二维码
        return auth_service.generate_login_qrcode()
    except Exception as e:
        logger.error(f"生成二维码失败: {str(e)}", exc_info=True)
        return {
            'success': False,
            'data': {},
            'message': f"生成二维码失败: {str(e)}"
        }


@bilibili_bp.route('/login/check_status', methods=['POST'])
@login_required
@api_response
def check_login_status():
    """
    检查B站登录状态
    """
    # 获取请求数据
    data = request.get_json()
    qrcode_key = data.get('qrcode_key')
    
    if not qrcode_key:
        return {
            'success': False,
            'message': '缺少qrcode_key参数',
            'data': {
                'status': 'error',
            }
        }
    
    # 动态创建认证服务实例
    auth_service = AuthService()
    # 调用认证服务检查登录状态
    status_data = auth_service.check_login_status(qrcode_key=qrcode_key)
    
    # 检查登录是否成功
    if status_data.get('success'):
        api_data = status_data.get('data', {})
        code = api_data.get('code', -1)
        
        # 定义状态映射
        status_map = {
            0: {'status': 'success', 'message': '登录成功'},
            86038: {'status': 'expired', 'message': '已失效，请点击刷新'},
            86090: {'status': 'scanned', 'message': '已扫码，请尽快确认'},
            86101: {'status': 'waiting', 'message': '未扫码，请及时扫码'}
        }
        
        # 获取状态信息，状态外都算error
        if code in status_map:
            status_info = status_map[code]
            status = status_info['status']
            message = status_info['message']
            logger.info(f"登录状态检查成功，状态码: {code}，状态: {status}，消息: {message}")
            
            # 登录成功时保存账号信息
            if status == 'success':
                logger.info("B站登录成功，开始保存账号信息")
                save_result = auth_service.save_login_account()
                if not save_result.get('success'):
                    logger.error("账号信息保存失败")
                    message = save_result['message'] or'账号信息保存失败'
                    status = 'error'
        else:
            # 状态外都算error
            message = '未知状态'
            status = 'error'

        return {
                'success': True if status != 'error' else False,
                'message': message,
                'data': {
                    'status': status,
                }
        }
    else:
        logger.error("登录状态检查失败")
        return {
            'success': False,
            'message': status_data.get('message', '登录状态检查失败'),
            'data': {
                'status': 'error',
            }
        }


@bilibili_bp.route('/account_info')
@login_required
@api_response
def get_account_info():
    """
    获取账号信息
    """
    # 动态创建认证服务实例
    auth_service = AuthService()
    
    # 调用认证服务获取账号信息
    return auth_service.get_account_info()


@bilibili_bp.route('/user_info')
@login_required
@api_response
def get_user_info():
    """
    获取指定B站账号信息
    
    Args:
        mid (str): B站账号ID
        
    Returns:
        JSON: 包含账号信息的响应
    """
    # 获取mid参数
    mid = request.args.get('mid')
    
    if not mid:
        return {
            'success': False,
            'message': '缺少mid参数',
            'data': {}
        }
    
    # 动态创建认证服务实例
    auth_service = AuthService()
    
    # 调用认证服务获取指定账号信息
    return auth_service.get_user_info(mid, mid)


@bilibili_bp.route('/update_video_data')
@login_required
@api_response
def update_video_data():
    """
    更新B站账号视频数据API
    
    Args:
        mid (str): B站账号ID
        
    Returns:
        JSON: 包含更新结果的响应
    """
    mid = request.args.get('mid')
    
    if not mid:
        return {
            'success': False,
            'message': '缺少mid参数',
            'data': {}
        }
    
    # 从数据库中获取账号信息
    from app.models import BiliAccount
    from flask_login import current_user
    from app.services import db
    
    # 获取当前系统用户的账号信息
    current_account = BiliAccount.query.filter_by(mid=mid, user_id=current_user.id).first()
    
    if not current_account:
        return {
            'success': False,
            'message': '未找到该账号',
            'data': {}
        }
    
    # 动态创建认证服务实例
    auth_service = AuthService()
    
    # 获取视频数据，包含播放量、收藏数等
    video_data = auth_service.get_video_data(mid)
    
    if video_data and video_data.get('success'):
        # 确保stat字段存在
        if not hasattr(current_account, 'stat') or not isinstance(current_account.stat, dict):
            current_account.stat = {}
        
        # 处理API返回的数据
        api_data = video_data.get('data', {})
        
        if isinstance(api_data, dict):
            # 总数据
            current_account.stat['total_fans'] = api_data.get('total_fans', 0)
            current_account.stat['total_click'] = api_data.get('total_click', 0)
            current_account.stat['total_like'] = api_data.get('total_like', 0)
            current_account.stat['total_fav'] = api_data.get('total_fav', 0)
            # 新增数据
            current_account.stat['incr_fans'] = api_data.get('incr_fans', 0)
            current_account.stat['incr_click'] = api_data.get('incr_click', 0)
            current_account.stat['inc_like'] = api_data.get('inc_like', 0)
            current_account.stat['inc_fav'] = api_data.get('inc_fav', 0)
            
            # 提交到数据库
            db.session.commit()

        logger.info(f"更新账号 {mid} 的统计数据完成: {current_account.stat}")
        
        return {
            'success': True,
            'message': '视频数据更新成功',
            'data': {
                'mid': mid,
                'stat': current_account.stat
            }
        }
    else:
        return {
            'success': False,
            'message': '获取视频数据失败',
            'data': {}
        }


@bilibili_bp.route('/toggle_autoreply', methods=['POST'])
@login_required
@api_response
def toggle_autoreply():
    """
    切换账号自动回复状态
    """
    from flask_login import current_user
    from app.models import BiliAccount
    from app.services import db
    
    # 获取请求数据
    data = request.get_json()
    mid = data.get('mid')
    
    if not mid:
        return {
            'success': False,
            'message': '缺少mid参数'
        }
    
    # 查询账号
    account = BiliAccount.query.filter_by(mid=mid, user_id=current_user.id).first()
    if not account:
        return {
            'success': False,
            'message': '未找到该账号'
        }
    
    # 切换自动回复状态
    account.autoreply_enabled = not account.autoreply_enabled
    
    # 保存到数据库
    db.session.commit()
    
    # 重载任务，确保自动回复状态变化能被任务调度器识别
    from flask import current_app
    task_scheduler = current_app.task_scheduler
    task_scheduler.reload_tasks()
    
    return {
        'success': True,
        'message': f'自动回复已{"启用" if account.autoreply_enabled else "停用"}成功',
        'data': {
            'autoreply_enabled': account.autoreply_enabled
        }
    }


@bilibili_bp.route('/remove_account', methods=['POST'])
@login_required
@api_response
def remove_account():
    """
    移除B站账号
    """
    from flask_login import current_user
    from app.models import BiliAccount
    from app.services import db
    
    # 获取请求数据
    data = request.get_json()
    mid = data.get('mid')
    
    if not mid:
        return {
            'success': False,
            'message': '缺少mid参数'
        }
    
    # 查询账号
    account = BiliAccount.query.filter_by(mid=mid, user_id=current_user.id).first()
    if not account:
        return {
            'success': False,
            'message': '未找到该账号'
        }
    
    # 删除账号
    db.session.delete(account)
    db.session.commit()
    
    # 重载任务，确保移除的账号不再被任务调度器处理
    from flask import current_app
    task_scheduler = current_app.task_scheduler
    task_scheduler.reload_tasks()
    
    return {
        'success': True,
        'message': '账号已移除成功',
        'data': {
            'mid': mid
        }
    }


@bilibili_bp.route('/dashboard')
@login_required
def dashboard():
    """
    B站账号仪表盘页面
    """
    # 获取账号mid参数
    mid = request.args.get('mid')
    
    # 如果没有提供mid，提示并跳转到首页
    if not mid:
        from flask import flash, redirect, url_for
        flash('B站账号不存在', 'warning')
        return redirect(url_for('main.index'))
    
    current_account = None
    
    account_status = "正常"
    # 从数据库中获取账号信息
    from app.models import BiliAccount
    from flask import redirect, url_for
    
    # 查询数据库获取账号信息
    current_account = BiliAccount.query.filter_by(mid=mid, user_id=current_user.id).first()
    
    if current_account:
        # 动态创建认证服务实例
        auth_service = AuthService()
        
        # 获取最新的用户信息
        user_info = auth_service.get_user_info(mid, mid)  # 两个参数：当前账号ID和要查询的用户ID相同
        if user_info and user_info.get('success'):
            user_data = user_info.get('data', {})
            card = user_data.get('card', {})
            if card:
                # 添加动态属性，从API响应中获取
                current_account.face = card.get('face', '')
                current_account.uname = card.get('name', current_account.uname)
                
                # 初始化视频数据相关字段，确保页面渲染时不会出错
                if not hasattr(current_account, 'stat'):
                    current_account.stat = {}
                
                current_account.stat = {
                    # 总数据字段
                    'total_click':0, 
                    'total_fans': 0, 
                    'total_fav': 0, 
                    'total_like': 0, 
                    # 新增数据字段
                    'incr_click': 0,
                    'incr_fans': 0,
                    'inc_fav': 0,
                    'inc_like': 0
                }
        else:
            account_status = "异常"
    else:
        # 账号不存在，提示并跳转到首页
        from flask import flash
        flash('B站账号不存在', 'warning')
        return redirect(url_for('main.index'))
    
    return render_template('bilibili/dashboard.html', mid=mid, current_account=current_account, account_status=account_status)


@bilibili_bp.route('/apply_template', methods=['POST'])
@login_required
@api_response
def apply_template():
    """
    应用模板到指定账号
    """
    from app.models import BiliAccount
    from app.models.config import ReplyConfig
    from app.services import db
    
    # 获取请求数据
    data = request.get_json()
    mid = data.get('mid')
    template_id = data.get('template_id')
    
    # 验证参数
    if not mid or not template_id:
        return {'success': False, 'message': '参数错误', 'data': {}}
    
    # 获取账号和模板
    account = BiliAccount.query.filter_by(mid=mid, user_id=current_user.id).first()
    template = ReplyConfig.query.filter_by(id=template_id, is_template=True).first()
    
    if not account:
        return {'success': False, 'message': '账号不存在', 'data': {}}
    
    if not template:
        return {'success': False, 'message': '模板不存在', 'data': {}}
    
    # 应用模板
    account.reply_config_id = template.id
    db.session.commit()
    
    return {'success': True, 'message': '模板应用成功', 'data': {
        'mid': mid,
        'template_id': template_id
    }}


@bilibili_bp.route('/switch_to_custom', methods=['POST'])
@login_required
@api_response
def switch_to_custom():
    """
    将账号切换为自定义设置
    """
    from app.models import BiliAccount
    from app.models.config import ReplyConfig
    from app.services import db
    
    # 获取请求数据
    data = request.get_json()
    mid = data.get('mid')
    
    # 验证参数
    if not mid:
        return {'success': False, 'message': '参数错误', 'data': {}}
    
    # 获取账号
    account = BiliAccount.query.filter_by(mid=mid, user_id=current_user.id).first()
    if not account:
        return {'success': False, 'message': '账号不存在', 'data': {}}
    
    # 获取当前设置
    current_setting = account.reply_config
    if not current_setting:
        return {'success': False, 'message': '当前设置不存在', 'data': {}}
    
    # 如果当前已经是自定义设置，直接返回
    if not current_setting.is_template:
        return {'success': True, 'message': '当前已是自定义设置', 'data': {
            'mid': mid,
            'is_template': False
        }}
    
    # 创建新的自定义设置记录（复制当前模板的配置）
    custom_setting = ReplyConfig(
        enable_new_fans_reply=current_setting.enable_new_fans_reply,
        new_fans_reply=current_setting.new_fans_reply,
        enable_fans_reply=current_setting.enable_fans_reply,
        fans_complete_dict=current_setting.fans_complete_dict.copy() if current_setting.fans_complete_dict else {},
        fans_keyword_dict=current_setting.fans_keyword_dict.copy() if current_setting.fans_keyword_dict else {},
        fans_other_reply=current_setting.fans_other_reply,
        enable_non_fans_reply=current_setting.enable_non_fans_reply,
        non_fans_complete_dict=current_setting.non_fans_complete_dict.copy() if current_setting.non_fans_complete_dict else {},
        non_fans_keyword_dict=current_setting.non_fans_keyword_dict.copy() if current_setting.non_fans_keyword_dict else {},
        non_fans_other_reply=current_setting.non_fans_other_reply,
        repet_protect_times=current_setting.repet_protect_times,
        reply_interval_seconds=current_setting.reply_interval_seconds,
        is_template=False,  # 自定义设置
        name=f"{account.uname}的设置"  # 固定名称格式
    )
    
    # 保存新的自定义设置
    db.session.add(custom_setting)
    db.session.flush()  # 获取新的ID
    
    # 将账号关联到新的自定义设置
    account.reply_config_id = custom_setting.id
    db.session.commit()
    
    return {'success': True, 'message': '已切换为自定义设置', 'data': {
        'mid': mid,
        'is_template': False,
        'reply_config_id': custom_setting.id
    }}



@bilibili_bp.route('/conversations', methods=['GET'])
@login_required
@api_response
def get_conversations():
    """
    获取对话列表
    """
    from app.services.bilibili.conversation_service import conversation_service
    
    # 获取参数
    mid = request.args.get('mid')
    
    # 验证参数
    if not mid:
        return {'success': False, 'message': '缺少mid参数', 'data': {}}
    
    # 调用对话服务获取对话列表
    return conversation_service.get_conversations(account_id=str(mid))


@bilibili_bp.route('/conversations/<talker_id>', methods=['GET'])
@login_required
@api_response
def get_conversation_detail(talker_id):
    """
    获取对话详情
    """
    from app.services.bilibili.conversation_service import conversation_service
    
    # 获取参数
    mid = request.args.get('mid')
    limit = request.args.get('limit', 20)
    offset = request.args.get('offset', 0)
    
    # 验证参数
    if not mid:
        return {'success': False, 'message': '缺少mid参数', 'data': {}}
    
    try:
        limit = int(limit)
        offset = int(offset)
    except ValueError:
        limit = 20
        offset = 0
    
    # 调用对话服务获取对话详情
    return conversation_service.get_conversation_detail(
        account_id=str(mid),
        talker_id=talker_id,
        limit=limit,
        offset=offset
    )


@bilibili_bp.route('/conversations/<talker_id>/clear', methods=['DELETE'])
@login_required
@api_response
def clear_conversation(talker_id):
    """
    清空对话
    """
    from app.services.bilibili.conversation_service import conversation_service
    
    # 获取参数
    mid = request.args.get('mid')
    
    # 验证参数
    if not mid:
        return {'success': False, 'message': '缺少mid参数', 'data': {}}
    
    # 调用对话服务清空对话
    return conversation_service.clear_conversation(
        account_id=str(mid),
        talker_id=talker_id
    )



