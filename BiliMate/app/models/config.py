from datetime import datetime
from ..services import db
from config import Config
import logging
import hmac
import hashlib
import json

# 获取当前配置的SECRET_KEY
SECRET_KEY = "BiliMate by mbaozi"

# 获取日志记录器
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class AppConfig(db.Model):
    """
    应用配置模型（单例）
    用于存储应用级别的配置信息
    """
    id = db.Column(db.Integer, primary_key=True)
    app_mode = db.Column(db.String(20), nullable=False, default='personal')  # 应用模式：'personal'或'team'
    version = db.Column(db.String(20), nullable=False, default='1.0.0')  # 应用版本
    allow_registration = db.Column(db.Boolean, nullable=False, default=True)  # 是否允许用户直接注册
    require_invitation = db.Column(db.Boolean, nullable=False, default=False)  # 是否需要邀请码
    activation_history = db.Column(db.JSON, default=list)  # 激活历史列表
    activation_info = db.Column(db.JSON, default={
        "is_activated": False,
        "activation_type": "NULL",
        "activation_date": None,
        "expiry_date": None,
        "last_check_time": None
    })  # 统一的激活信息字段
    activation_hash = db.Column(db.String(64), nullable=True)  # 激活信息的哈希值，用于防篡改
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(Config.TIMEZONE))  # 创建时间
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(Config.TIMEZONE), onupdate=lambda: datetime.now(Config.TIMEZONE))  # 更新时间

    def __repr__(self):
        return f'<AppConfig {self.app_mode}>'

    @staticmethod
    def _generate_hash(data):
        """
        生成数据的HMAC-SHA256哈希值
        
        Args:
            data: 要哈希的数据
            
        Returns:
            str: 64位十六进制哈希值
        """
        # 将数据转换为JSON字符串，确保顺序一致
        data_str = json.dumps(data, sort_keys=True, default=str).encode('utf-8')
        # 使用SECRET_KEY生成HMAC-SHA256哈希
        h = hmac.new(SECRET_KEY.encode('utf-8'), data_str, hashlib.sha256)
        return h.hexdigest()
    
    def verify_hash(self):
        """
        验证activation_info的哈希值是否正确
        
        Returns:
            bool: 哈希值是否正确
        """
        if not self.activation_hash:
            # 没有哈希值，认为验证失败
            logger.warning("激活信息哈希值不存在，验证失败")
            return False
        
        # 生成当前activation_info的哈希值
        current_hash = self._generate_hash(self.activation_info)
        
        # 比较哈希值
        if hmac.compare_digest(current_hash, self.activation_hash):
            return True
        else:
            logger.warning(f"激活信息哈希验证失败！当前哈希: {current_hash}, 存储哈希: {self.activation_hash}")
            return False
    
    def update_activation_info(self, activation_info):
        """
        更新激活信息并生成新的哈希值
        
        Args:
            activation_info: 新的激活信息
        """
        self.activation_info = activation_info
        # 生成新的哈希值
        self.activation_hash = self._generate_hash(activation_info)
    
    @classmethod
    def get_config(cls):
        """
        获取应用配置（单例）
        如果不存在，则返回None
        如果存在但版本号不同，则更新为最新版本
        验证激活信息的哈希值
        """
        config = cls.query.first()
        if not config:
            # 配置不存在，返回None
            return None
        
        if config.version != Config.APP_VERSION:
            # 更新版本号为最新版本
            config.version = Config.APP_VERSION
            db.session.commit()
        
        # 验证哈希值
        if not config.verify_hash():
            # 哈希验证失败，重置为默认配置
            logger.error("激活信息被篡改，重置为默认配置")
            config.activation_info = {
                "is_activated": False,
                "activation_type": "NULL",
                "activation_date": None,
                "expiry_date": None,
                "last_check_time": None
            }
            config.activation_hash = config._generate_hash(config.activation_info)
            db.session.commit()
        
        return config


class ReplyConfig(db.Model):
    """
    自动回复配置模型
    存储账号的自动回复相关设置，支持作为模板被多个账号使用
    """
    __tablename__ = 'reply_configs'
    
    # 主键
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # 模板相关字段
    is_template = db.Column(db.Boolean, default=False)  # 是否为模板
    name = db.Column(db.String(100), nullable=True)  # 模板名称
    
    # 新粉丝回复设置
    enable_new_fans_reply = db.Column(db.Boolean, default=True)  # 是否启用新粉丝回复
    new_fans_reply = db.Column(db.Text, default="感谢关注，眼光不错哟")  # 新粉丝回复内容
    
    # 粉丝回复配置
    enable_fans_reply = db.Column(db.Boolean, default=True)  # 是否启用粉丝回复
    fans_complete_dict = db.Column(db.JSON, default={'hello': 'Hi，感谢您的支持'})  # 粉丝完全匹配字典
    fans_keyword_dict = db.Column(db.JSON, default={'你好': '你好吖，感谢您的支持'})  # 粉丝关键词匹配字典
    fans_other_reply = db.Column(db.Text, default="你好，不知道说啥，但不能啥都不回吖\n [doge] ")  # 粉丝其他回复内容
    
    # 非粉丝回复设置
    enable_non_fans_reply = db.Column(db.Boolean, default=True)  # 是否启用非粉丝回复
    non_fans_complete_dict = db.Column(db.JSON, default={'hello': 'Hi，给个关注呗'})  # 非粉丝完全匹配字典
    non_fans_keyword_dict = db.Column(db.JSON, default={'你好': '你好吖，给个关注呗'})  # 非粉丝关键词匹配字典
    non_fans_other_reply = db.Column(db.Text, default="给个关注呗")  # 非粉丝其他回复内容
    
    # 其他设置
    repet_protect_times = db.Column(db.Integer, default=5)  # 重复回复保护次数
    reply_interval_seconds = db.Column(db.Integer, default=3)  # 回复间隔秒数
    personality_identifier = db.Column(db.Text, nullable=True, default="_ʙɪʟɪᴍᴀᴛᴇ_")  # 个性标识
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(Config.TIMEZONE))  # 创建时间
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(Config.TIMEZONE), 
                           onupdate=lambda: datetime.now(Config.TIMEZONE))  # 更新时间
    
    def __repr__(self):
        if self.is_template:
            return f'<ReplyConfig Template {self.name}>'
        else:
            return f'<ReplyConfig {self.id}>'
