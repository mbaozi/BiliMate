import os
import sys
import threading
import subprocess
import streamlit.web.cli as stcli

# 修改系统路径
sys.path.append("BiliMate")

# 启动server.py的函数
def start_server():
    # 使用当前Python解释器运行server.py，非阻塞方式
    subprocess.Popen([sys.executable, "./BiliMate/server.py"])

if __name__ == "__main__":
    # 创建一个线程来启动server.py
    server_thread = threading.Thread(target=start_server)
    server_thread.start()

    # 修改命令行参数
    sys.argv = ["streamlit", "run", "./BiliMate/webui.py", "--server.port=8181"]
    
    # 启动Streamlit应用
    stcli.main()