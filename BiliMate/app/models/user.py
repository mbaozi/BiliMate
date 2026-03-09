from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from ..services import db
from config import Config
import logging

# 获取日志记录器
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class User(db.Model, UserMixin):
    """
    用户模型
    """
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='personal')  # 角色：'personal'（个人用户）、'admin'（管理员）、'registered'（注册用户）
    user_level = db.Column(db.String(20), nullable=True)  # 用户等级：'normal'（普通）、'vip'（高级），仅注册用户需要
    expiry_date = db.Column(db.DateTime, nullable=True)  # VIP用户到期时间
    theme = db.Column(db.String(20), default='light')  # 主题：'light' 或 'dark'
    trust_login = db.Column(db.Boolean, default=False)  # 启用内网免密登录
    registration_code = db.Column(db.String(50), nullable=True)  # 注册码（仅团队注册用户需要）
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(Config.TIMEZONE))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(Config.TIMEZONE), onupdate=lambda: datetime.now(Config.TIMEZONE))  # 更新时间
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def set_password(self, password):
        """
        设置用户密码
        """
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """
        验证用户密码
        """
        return check_password_hash(self.password_hash, password)
