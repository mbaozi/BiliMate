from flask import Flask
from jinja2.loaders import PackageLoader
from config import config
from config import Config

import logging
from logging.handlers import TimedRotatingFileHandler
import os
import psutil
from datetime import time
import re

# 创建当前进程实例，用于CPU使用率监控
current_process = psutil.Process()
physical_cores = psutil.cpu_count(logical=True)


def setup_logging(app):
    """
    配置应用日志
    """
    # 获取配置的日志级别
    log_level = app.config.get('LOG_LEVEL_VALUE', logging.INFO)
    # 创建日志目录
    # 将logs目录创建在当前工作目录
    LOG_DIR = os.path.join(os.getcwd(), 'logs')
    os.makedirs(LOG_DIR, exist_ok=True)
    
    # 设置日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    )

    # 文件处理器 - 每天滚动
    file_handler = TimedRotatingFileHandler(
        filename=os.path.join(LOG_DIR, 'bilimate.log'),
        when='midnight',
        interval=1,                # 滚动间隔为1天
        backupCount=30,            # 保留30天日志
        encoding='utf-8',          # 日志编码
        atTime=time(0, 0)          # 滚动时间为每天0点0分
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    file_handler.suffix = "%Y%m%d.log"  # 日志文件名格式
    file_handler.extMatch = re.compile(r"^\d{8}\.log$")  # 确保只有匹配格式的文件才会被清理
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    
    # 清空根日志记录器的现有处理器，避免重复
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(log_level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # 配置应用日志记录器，使用根日志记录器的配置
    app.logger.handlers.clear()
    app.logger.setLevel(logging.INFO)

    # 为第三方库设置日志级别，过滤不必要的日志
    if app.config.get('FLASK_ENV') == 'development':
        logging.getLogger('urllib3').setLevel(logging.INFO)
        logging.getLogger('werkzeug').setLevel(logging.INFO)
        logging.getLogger('apscheduler').setLevel(logging.INFO)
        logging.getLogger('tzlocal').setLevel(logging.INFO)
    else:
        logging.getLogger('urllib3').setLevel(logging.INFO)
        logging.getLogger('werkzeug').setLevel(logging.WARNING)
        logging.getLogger('apscheduler').setLevel(logging.WARNING)
        logging.getLogger('tzlocal').setLevel(logging.INFO)

    
    # 测试日志输出
    app.logger.info('BiliMate 日志系统初始化完成')


def create_app(config_name=None):
    """应用工厂函数"""
    # 禁用默认静态文件处理，使用自定义路由
    app = Flask(__name__, static_folder=None)
    
    # 配置模板加载器使用PackageLoader
    app.jinja_loader = PackageLoader('app', 'templates')
    
    # 加载配置
    app.config.from_object(config[config_name or 'default'])
    
    # 添加版本号到模板全局变量
    app.jinja_env.globals['APP_VERSION'] = Config.APP_VERSION
    
    # 配置日志系统
    setup_logging(app)
    
    # 初始化数据库扩展
    from .services import db, login_manager
    db.init_app(app)
    login_manager.init_app(app)
    
    # 配置Flask-Login的提示信息
    login_manager.login_message = '请先登录以访问此页面'
    login_manager.login_message_category = 'warning'
    
    # 配置用户加载函数
    from .models.user import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # 创建数据库表和初始化应用配置
    with app.app_context():
        # 导入模型
        from .models import User, AppConfig, BiliAccount, Conversation, MessagePair, ApiWrapper
        from .models.config import ReplyConfig
        from .models.registration import InvitationCode
        
        # 创建所有表
        db.create_all()
        app.logger.info('数据库表创建完成')
        
        # 初始化应用配置
        AppConfig.get_config()
        app.logger.info('应用配置初始化完成')
        
        # 检查是否为首次运行
        is_first_run = User.query.count() == 0
        if is_first_run:
            app.logger.info("首次运行，等待用户选择应用模式...")
    
    # 注册路由
    from .routes import register_routes
    register_routes(app)
    
    # 初始化任务管理器
    with app.app_context():
        from app.services.bilibili.task_manager import task_manager
        # 初始化任务管理器，创建活跃账号的客户端实例
        task_manager.initialize()
    
    # 无论是否为开发服务器，都初始化任务调度器
    app.logger.info("设置并启动任务调度器")
    from app.services.bilibili.task_scheduler import task_scheduler
    task_scheduler.set_app(app)
    task_scheduler.start()
    # 将任务调度器实例绑定到app对象上，方便API调用时获取正确实例
    app.task_scheduler = task_scheduler
    
    # 初始化激活状态调度器
    app.logger.info("初始化激活状态调度器")
    from app.services.license import license_service
    app.activation_scheduler = license_service
    # 设置应用实例
    app.activation_scheduler.set_app(app)
    
    # 启动激活状态调度器（无论是否已激活）
    with app.app_context():
        app.logger.info("启动激活状态调度器")
        app.activation_scheduler.start()
    
    app.logger.info(f'BiliMate 应用启动完成 - 配置: {config_name or "default"}')
    return app
