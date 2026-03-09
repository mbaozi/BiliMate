from datetime import datetime
from ..services import db
from config import Config
import logging

# 获取日志记录器
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class InvitationCode(db.Model):
    """
    邀请码模型
    用于管理团队模式下的邀请码注册和分享链接
    """
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(8), unique=True, nullable=False)  # 8位邀请码，同时作为分享链接的token
    created_by = db.Column(db.Integer, nullable=False)  # 创建者ID
    max_uses = db.Column(db.Integer, nullable=False, default=10)  # 最大使用次数
    current_uses = db.Column(db.Integer, nullable=False, default=0)  # 当前使用次数
    expires_at = db.Column(db.DateTime, nullable=False)  # 邀请码过期时间
    user_level = db.Column(db.String(20), nullable=False, default='normal')  # 注册用户等级：'normal'或'vip'
    vip_expiry_days = db.Column(db.Integer, nullable=True)  # VIP有效期（天数），仅当user_level为'vip'时有效
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(Config.TIMEZONE))  # 创建时间
    
    def __repr__(self):
        return f'<InvitationCode {self.code}>'
    
    def is_valid(self):
        """
        检查邀请码是否有效
        
        Returns:
            bool: 邀请码是否有效
        """
        # 检查是否达到最大使用次数
        if self.current_uses >= self.max_uses:
            return False
        
        # 检查是否过期
        if datetime.now(Config.TIMEZONE) > self.expires_at.replace(tzinfo=Config.TIMEZONE):
            return False
        
        return True
    
    def use_code(self):
        """
        使用邀请码
        
        Returns:
            bool: 是否成功使用
        """
        if self.is_valid():
            self.current_uses += 1
            db.session.commit()
            return True
        return False