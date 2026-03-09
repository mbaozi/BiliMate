import os
import logging
from datetime import timezone, timedelta


class Config:
    """基础配置类
    
    所有环境配置的基础类，包含通用配置项
    """
    # 程序版本号
    APP_VERSION = '1.0.0'
    
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard-to-guess-string'
    
    # 数据库配置
    # 将data目录创建在当前工作目录
    DATABASE_DIR = os.path.join(os.getcwd(), 'data')
    os.makedirs(DATABASE_DIR, exist_ok=True)
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(DATABASE_DIR, 'bilimate.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 日志配置
    # 支持的日志级别: DEBUG, INFO, WARNING, ERROR, CRITICAL
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO').upper()
    
    # 日志级别映射，将字符串转换为logging模块的常量
    LOG_LEVEL_MAPPING = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    
    # 获取实际的日志级别常量
    LOG_LEVEL_VALUE = LOG_LEVEL_MAPPING.get(LOG_LEVEL, logging.INFO)

    # 应用运行环境 (development/production/testing)
    FLASK_ENV = os.environ.get('FLASK_ENV', 'development').lower()
    
    # 时区配置
    # 可以通过修改TIMEZONE_OFFSET来更改全局时区
    # 例如：UTC+8（北京时间）为8，UTC-5（纽约时间）为-5
    TIMEZONE_OFFSET = 8  # 默认设置为UTC+8（北京时间）
    # 创建时区对象
    TIMEZONE = timezone(timedelta(hours=TIMEZONE_OFFSET))


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    SQLALCHEMY_ECHO = False 


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    SQLALCHEMY_POOL_RECYCLE = 299
    SQLALCHEMY_POOL_TIMEOUT = 20


class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


# 配置映射
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}



