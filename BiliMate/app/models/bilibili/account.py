from datetime import datetime
from app.services import db
from config import Config
import logging

# 获取日志记录器
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class BiliAccount(db.Model):
    """
    B站账号模型 - 仅用于存储扫码登录后的账号基本信息
    """
    __tablename__ = 'bili_accounts'
    
    mid = db.Column(db.String(20), primary_key=True, nullable=False)  # B站账号ID (主键)
    uname = db.Column(db.String(50), nullable=False)                 # B站账号名
    cookies = db.Column(db.Text, nullable=True)                     # B站登录cookies
    autoreply_enabled = db.Column(db.Boolean, default=True)        # 自动回复是否启用
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # 关联系统用户
    user = db.relationship('User', backref='bili_accounts', lazy=True)
    reply_config_id = db.Column(db.Integer, db.ForeignKey('reply_configs.id'), nullable=True)  # 关联的自动回复配置
    reply_config = db.relationship('ReplyConfig', backref='bili_accounts', lazy=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(Config.TIMEZONE))  # 创建时间
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(Config.TIMEZONE), 
                           onupdate=lambda: datetime.now(Config.TIMEZONE))  # 更新时间
                           
    def __repr__(self):
        return f'<BiliAccount {self.uname} ({self.mid})>'
