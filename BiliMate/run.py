#!/usr/bin/env python3
"""
BiliMate
"""

import os, sys

# 检查是否是pyz文件
if '.pyz' in sys.argv[0]:
    pyz_path = sys.argv[0]
    runtime_dir = os.path.join(os.getcwd(), 'runtime')
    # 创建runtime目录（如果不存在）
    os.makedirs(runtime_dir, exist_ok=True)
    # 打开pyz文件并提取runtime目录
    try:
        import zipfile
        with zipfile.ZipFile(pyz_path, 'r') as zf:
            # 遍历pyz文件中的所有文件
            extracted_count = 0
            for member in zf.namelist():
                # 只提取runtime目录下的文件
                if member.startswith('runtime/') and not member.endswith('/'):
                    # 计算目标文件路径
                    target_path = os.path.join(os.getcwd(), member)
                    # 创建目标目录
                    os.makedirs(os.path.dirname(target_path), exist_ok=True)
                    # 检查目标文件是否存在，以及文件信息是否相同
                    need_extract = True
                    if os.path.exists(target_path):
                        # 获取pyz文件中文件的信息
                        pyz_file_info = zf.getinfo(member)
                        pyz_file_size = pyz_file_info.file_size
                        pyz_file_mtime = pyz_file_info.date_time
                        
                        # 获取目标文件的信息
                        target_file_stat = os.stat(target_path)
                        target_file_size = target_file_stat.st_size
                        target_file_mtime = target_file_stat.st_mtime
                        
                        # 转换为相同的格式进行比较
                        import datetime
                        pyz_mtime = datetime.datetime(*pyz_file_mtime).timestamp()
                        
                        # 比较文件大小和修改时间
                        if pyz_file_size == target_file_size and abs(pyz_mtime - target_file_mtime) < 1:
                            need_extract = False
                    
                    # 如果需要提取，覆盖现有文件
                    if need_extract:
                        with open(target_path, 'wb') as f:
                            f.write(zf.read(member))
                        extracted_count += 1
                        
                        # 更新目标文件的修改时间为pyz文件中文件的修改时间
                        pyz_file_info = zf.getinfo(member)
                        import time
                        mtime = time.mktime(pyz_file_info.date_time + (0, 0, -1))
                        os.utime(target_path, (mtime, mtime))
    except Exception as e:
        print(f"提取runtime目录时出错: {str(e)}")

# 添加runtime目录到sys.path
sys.path.insert(0, os.path.join(os.getcwd(), 'runtime'))

try:
    env_path = os.path.join(os.getcwd(), '.env')
    if os.path.exists(env_path):
        from dotenv import load_dotenv
        load_dotenv(dotenv_path=env_path)
        print("已加载 .env")
    else:
        print(f"未找到 .env 文件: {env_path}")
except AssertionError:
    pass


from app import create_app

# 获取环境配置
config_name = os.environ.get('FLASK_ENV', 'production')
app = create_app(config_name)

def main():
    """应用程序主入口函数"""
    # 从环境变量获取端口，默认8181
    port = int(os.environ.get('FLASK_PORT', 8181))
    
    # 记录应用启动信息
    app.logger.info('='*60)
    app.logger.info('BiliMate 应用启动中...')
    app.logger.info(f'运行配置: {config_name}')
    app.logger.info(f'调试模式: {app.config.get("DEBUG", False)}')
    app.logger.info(f'监听端口: {port}')
    app.logger.info('='*60)
    
    # 开发模式下运行
    try:
        app.run(
            host='0.0.0.0',
            port=port,
            debug=app.config['DEBUG'],
            threaded=True
        )
    except KeyboardInterrupt:
        app.logger.info('BiliMate 应用被用户中断，正在关闭...')
    except Exception as e:
        app.logger.error(f'BiliMate 应用运行出错: {str(e)}')
        raise

if __name__ == '__main__':
    main()
