import sys, subprocess, signal, atexit, os
import threading
import streamlit.web.cli as stcli

server_proc = None

def start_server():
    global server_proc
    server_proc = subprocess.Popen([sys.executable, "./BiliMate/server.py"])

def cleanup():
    """主进程退出时杀掉 server.py"""
    if server_proc and server_proc.poll() is None:
        # Windows 用 terminate；Linux/macOS 可以 terminate -> wait -> kill
        server_proc.terminate()
        try:
            server_proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server_proc.kill()

if __name__ == "__main__":
    # 注册钩子：当主进程收到 SIGINT/SIGTERM/SIGHUP 时杀子进程
    atexit.register(cleanup)
    signal.signal(signal.SIGINT,  lambda *_: sys.exit(0))
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
    # Linux/macOS 额外捕获 SIGHUP（终端关闭）
    if os.name != "nt":
        signal.signal(signal.SIGHUP, lambda *_: sys.exit(0))

    # 启动 server
    start_server()

    # 启动 webui
    sys.argv = ["streamlit", "run", "./BiliMate/webui.py", "--server.port=8181"]
    stcli.main()