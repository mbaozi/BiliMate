from datetime import datetime
from app.services import db
import logging

# 获取日志记录器
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class ApiWrapper(db.Model):
    """
    API封装模型，用于存储可复用的API调用配置
    """
    __tablename__ = 'api_wrappers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)  # API封装名称，唯一
    method = db.Column(db.String(10), default='GET')  # 请求方法
    url = db.Column(db.String(500), nullable=False)  # API地址
    headers = db.Column(db.JSON, default=dict)  # 请求头
    body = db.Column(db.JSON, default=dict)  # 请求体
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # 所属用户ID
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # 创建时间
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # 更新时间
    # 调用限制字段
    limit_type = db.Column(db.String(20), default='unlimited', nullable=False)  # 限制类型
    limit_value = db.Column(db.Integer, default=0, nullable=False)  # 限制值
    limit_field = db.Column(db.String(200), default='', nullable=False)  # 超过限制时的替代值
    # API模板类型
    api_type = db.Column(db.String(50), default='custom', nullable=False)  # API提供商类型
    # 大模型预制角色
    system_prompt = db.Column(db.Text, default='', nullable=False)  # 大模型system角色提示词
    # 最大对话数
    max_conversations = db.Column(db.Integer, default=100, nullable=False)  # 单个对话的最大历史消息数
    
    # 关联关系
    user = db.relationship('User', backref=db.backref('api_wrappers', lazy=True))
    
    def to_dict(self):
        """
        转换为字典格式
        """
        return {
            'id': self.id,
            'name': self.name,
            'method': self.method,
            'url': self.url,
            'headers': self.headers,
            'body': self.body,
            'api_type': self.api_type,
            'system_prompt': self.system_prompt,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
            'limit_type': self.limit_type,
            'limit_value': self.limit_value,
            'limit_field': self.limit_field,
            'max_conversations': self.max_conversations
        }


class ApiCallRecord(db.Model):
    """
    API调用记录模型，用于存储每个talker_mid的API调用次数
    """
    __tablename__ = 'api_call_records'
    
    id = db.Column(db.Integer, primary_key=True)
    api_wrapper_id = db.Column(db.Integer, db.ForeignKey('api_wrappers.id'), nullable=False)  # API封装ID
    talker_mid = db.Column(db.String(50), nullable=False)  # 对话者ID
    call_count = db.Column(db.Integer, default=1, nullable=False)  # 调用次数
    period_start = db.Column(db.DateTime, nullable=False)  # 当前统计周期的开始时间
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # 最后更新时间
    
    # 关联关系
    api_wrapper = db.relationship('ApiWrapper', backref=db.backref('call_records', lazy=True))
    
    # 复合唯一索引：确保每个API封装、每个对话者在每个统计周期内只有一条记录
    __table_args__ = (
        db.UniqueConstraint('api_wrapper_id', 'talker_mid', 'period_start', name='_api_talker_period_uc'),
    )
