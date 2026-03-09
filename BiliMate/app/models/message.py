from datetime import datetime
from app.services import db
from config import Config
import logging

# 获取日志记录器
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class Conversation(db.Model):
    """
    对话会话模型
    用于管理完整的对话记录
    """
    __tablename__ = 'conversations'
    
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.String(50), unique=True, nullable=False)  # 对话ID
    platform = db.Column(db.String(20), nullable=False, default='bilibili')  # 平台类型
    account_id = db.Column(db.String(20), nullable=False)  # 账号ID
    talker_id = db.Column(db.String(20), nullable=False)  # 对话者ID
    last_msg_time = db.Column(db.DateTime)  # 最后消息时间
    msg_count = db.Column(db.Integer, default=0)  # 消息对数
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(Config.TIMEZONE))  # 创建时间
    
    # 关联消息对记录
    message_pairs = db.relationship('MessagePair', backref='conversation', lazy=True, cascade='all, delete-orphan')
    
    # 添加索引，优化查询效率
    __table_args__ = (
        # 优化对话者列表查询
        db.Index('idx_conversation_account_talker', 'account_id', 'talker_id'),
        # 优化时间排序查询
        db.Index('idx_conversation_created_at', 'created_at'),
        # 优化最后消息时间查询
        db.Index('idx_conversation_last_msg_time', 'last_msg_time'),
    )
    
    def __repr__(self):
        return f'<Conversation {self.conversation_id} between {self.account_id} and {self.talker_id}>'


class MessagePair(db.Model):
    """
    消息对模型
    用于存储用户消息和系统回复的对应关系
    """
    __tablename__ = 'message_pairs'
    
    id = db.Column(db.Integer, primary_key=True)
    pair_id = db.Column(db.String(50), unique=True, nullable=False)  # 消息对ID
    conversation_id = db.Column(db.String(50), db.ForeignKey('conversations.conversation_id'), nullable=False)  # 关联对话ID
    receive_msg = db.Column(db.Text, nullable=False)  # 用户发送的消息
    reply_msg = db.Column(db.Text, nullable=False)  # 系统回复的消息
    reply_status = db.Column(db.Boolean, default=True)  # 回复状态
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(Config.TIMEZONE))  # 处理时间
    sequence_num = db.Column(db.Integer, nullable=False)  # 消息对在对话中的序号
    msg_type = db.Column(db.String(20), nullable=False, default='normal')  # 消息类型：normal（正常）、notice（提示）、welcome（欢迎）
    
    # 添加索引，优化查询效率
    __table_args__ = (
        # 优化对话详情查询
        db.Index('idx_message_pair_conversation', 'conversation_id', 'sequence_num'),
        # 优化时间排序查询
        db.Index('idx_message_pair_created_at', 'created_at'),
    )
    
    def __repr__(self):
        return f'<MessagePair {self.pair_id} in conversation {self.conversation_id}>'
