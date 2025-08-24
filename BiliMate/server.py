#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BiliMate – B站小助手 服务端

作者信息
--------
Author : 是萌包子吖
Site   : https://mbaozi.cn
GitHub : https://github.com/mbaozi

版本记录
--------
Version : 0.1.0
Date    : 2025-08-18
Change  : 初版发布
"""

import json, struct, qrcode, time, threading
from pathlib import Path
from bilibili_api import BiliApi
import multiprocessing.shared_memory as shm
from collections import deque

# 共享内存大小
SHARED_SIZE = 128 * 1024

# 文件
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)
COOKIE_FILE = DATA_DIR / "cookies.json"
SETTINGS_FILE = DATA_DIR / "settings.json"
LOG_FILE = DATA_DIR / f"log_BiliMate.txt"
# 默认设置
DEFAULT_SETTINGS = {
    "new_fans_reply": "感谢关注，眼光不错哟",
    "non_fans_complete_dict": {
        "hello": "Hi，给个关注呗",
    },
    "non_fans_keyword_dict": {
        "你好": "你好吖，给个关注呗",
    },
    "non_fans_other_reply": "给个关注呗",
    "fans_complete_dict": {
        "hello": "Hi，感谢您的支持",
    },
    "fans_keyword_dict": {
        "你好": "你好吖，感谢您的支持",
    },
    "fans_other_reply": "你好，不知道说啥，但不能啥都不回吖\n [doge] ",
    "token_key": "BiliMate",
    "login_remember": True,
    "repet_protect_times": 3,
    "interval_seconds": 5,
}




# BiliMate服务端
class BiliMateServer:
    def __init__(self):
        # 创建共享内存
        try:
            self.mem = shm.SharedMemory(name="BiliMate_shm", create=True, size=SHARED_SIZE)
        except FileExistsError:
            self.mem = shm.SharedMemory(name="BiliMate_shm", create=False, size=SHARED_SIZE)
        # 初始化
        self.bili_api = BiliApi()
        self.login_status = "未登录"
        self.login_url = ""
        self.total_fans = 0
        self.inc_fans = 0
        self.total_click = 0
        self.inc_click = 0
        self.total_like = 0
        self.inc_like = 0
        self.total_fav = 0
        self.inc_fav = 0
        self.fans_list = []
        self.timestamp_ns = 0
        self.message_list: dict[int, list[str]] = {}
        self.thread_update_video_data_status = False
        self.thread_auto_reply_msg_status = False


    # 打印日志
    def log_print(self, *args, **kwargs):
        MAX_LOG_SIZE = 100 * 1024 * 1024   # 100 MB
        CUT_SIZE     = 10 * 1024 * 1024    # 每次砍掉前 10 MB
        # 获取当前时间
        current_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        # 构造日志字符串
        print_str = " ".join(map(str, args))
        if print_str and print_str[0] == "\n":
            log_txt = f"\n[{current_time}] " + print_str[1:]
        else:
            log_txt = f"[{current_time}] " + print_str
        # 打印到控制台
        print(log_txt, **kwargs)
        # 日志裁剪
        if LOG_FILE.exists() and LOG_FILE.stat().st_size >= MAX_LOG_SIZE:
            try:
                data = LOG_FILE.read_bytes()
                new_data = data[CUT_SIZE:]
                LOG_FILE.write_bytes(new_data)
            except Exception:
                pass
        # 打开日志文件并写入日志内容
        with open(LOG_FILE, 'a', encoding='utf-8') as file:
            file.write(log_txt + "\n")


    # 加载设置参数
    def load_settings(self):
        try:
            settings = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        except Exception as e:
            settings = DEFAULT_SETTINGS.copy()
            self.save_settings(settings)
            print(f"加载设置参数失败，恢复默认参数: {e}")
        self.login_remember = settings.get("login_remember", DEFAULT_SETTINGS["login_remember"])
        self.interval_seconds = settings.get("interval_seconds", DEFAULT_SETTINGS["interval_seconds"])
        self.repet_protect_times = settings.get("repet_protect_times", DEFAULT_SETTINGS["repet_protect_times"])
        self.new_fans_reply = settings.get("new_fans_reply")
        self.non_fans_complete_dict = settings.get("non_fans_complete_dict")
        self.non_fans_keyword_dict = settings.get("non_fans_keyword_dict")
        self.non_fans_other_reply = settings.get("non_fans_other_reply")
        self.fans_complete_dict = settings.get("fans_complete_dict")
        self.fans_keyword_dict = settings.get("fans_keyword_dict")
        self.fans_other_reply = settings.get("fans_other_reply")
        return True


    # 保存设置参数
    def save_settings(self, settings):
        SETTINGS_FILE.write_text(
            json.dumps(settings, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


    # 更新共享内存
    def update_shared_mem(self):
        data = {
            "login_status": self.login_status,
            "login_url": self.bili_api.login_url,
            "login_time_cnt": self.login_time_cnt,
            "my_uname": self.bili_api.my_uname,
            "my_mid": self.bili_api.my_mid,
            "total_fans": self.total_fans,
            "inc_fans": self.inc_fans,
            "total_click": self.total_click,
            "inc_click": self.inc_click,
            "total_like": self.total_like,
            "inc_like": self.inc_like,
            "total_fav": self.total_fav,
            "inc_fav": self.inc_fav,
            "fans_list": self.fans_list,
            "state_info_status": self.thread_update_video_data_status,
            "reply_info_status": self.thread_auto_reply_msg_status,
        }
        # print(data)
        payload = json.dumps(data).encode()
        length = len(payload)
        self.mem.buf[:4] = struct.pack('<I', length)
        self.mem.buf[4:4+length] = payload


    # 等待登录结果
    def wait_login_status(self, time_out: int = 120):
        # 等待扫描登录
        self.login_time_cnt = time_out
        time_step = 1
        while self.login_time_cnt > 0:
            self.update_shared_mem()
            time.sleep(time_step)
            self.login_time_cnt = self.login_time_cnt - time_step
            login_status = self.bili_api.get_login_status()
            login_status_code = login_status.get("code", -1)
            if login_status_code == 0:
                self.bili_api.get_account_info()
                if self.bili_api.my_mid != None:
                    self.login_status = "已登录"
                    self.log_print("登录成功")
                    self.load_settings()
                    if self.login_remember:
                        #保存参数
                        self.save_login()
                    return True
            elif login_status_code == 86090 and self.login_status != "已扫码，请尽快确认":
                self.login_status = "已扫码，请尽快确认"
                self.log_print("已扫码，请尽快确认")
            elif login_status_code == 86038 and self.login_status != "二维码已失效":
                self.login_status = "二维码已失效"
                self.log_print("二维码已失效")
            elif login_status_code == 86101 and self.login_status != "未登录":
                self.login_status = "未登录"
                self.log_print("未扫码")
            else:
                pass
        self.log_print("超时未登录成功")
        return False
    

    # 登录
    def login(self):
        # 自动加载历史 cookies
        if COOKIE_FILE.exists():
            try:
                cookies = json.loads(COOKIE_FILE.read_text(encoding="utf-8"))
                self.bili_api.session.cookies.update(cookies)
                self.bili_api.get_account_info()
                if self.bili_api.my_mid != None:
                    self.login_status = "已登录"
                    return True
            except:
                pass
        # 使用二维码登录
        self.log_print("当前未登录")
        self.bili_api.get_login_info()
        if self.bili_api.login_url != None:
            # 显示登录二维码
            qr = qrcode.QRCode(
                version=1,
                box_size=1,
                border=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L
            )
            qr.add_data(self.bili_api.login_url)
            qr.make()
            self.log_print("请扫描下方二维码登录\n")
            qr.print_tty()
            # 获取登录结果
            return self.wait_login_status()
        else:
            return False


    # 保存登录
    def save_login(self):
        cookies = self.bili_api.session.cookies.get_dict()
        if cookies:
            COOKIE_FILE.parent.mkdir(parents=True, exist_ok=True)
            COOKIE_FILE.write_text(json.dumps(cookies, indent=2, ensure_ascii=False))


    # 获取粉丝数
    def get_fans_num(self):
        # 更新关系状态(会同步更新粉丝状态)
        relation_state = self.bili_api.get_relation_state()
        self.fans_num = relation_state.get("follower", 0)
        return self.fans_num


    # 更新粉丝列表
    def reload_fans_list(self):
        total = self.get_fans_num()
        if not total:
            return []
        if total > 1000:
            self.log_print("您的粉丝数超过1000，目前仅加载前1000个粉丝")
            total = 1000
        self.fans_list = []
        pages = (total - 1) // 50 + 1
        for page in range(1, pages+1):
            fans_detail = self.bili_api.get_fans_detail(page=page, num=50)
            if not fans_detail or 'list' not in fans_detail:
                return []
            self.fans_list.extend({'uname': f['uname'], 'mid': f['mid']} for f in fans_detail['list'])
        return self.fans_list


    # 更新粉丝列表
    def update_fans_list(self):
        # 如果有粉丝解除关注，需重新遍历一遍粉丝列表
        if len(self.fans_list) != self.get_fans_num():
            self.reload_fans_list()


    # 获取新关注用户
    def get_new_fans(self):
        fans_list_status = self.bili_api.get_fans_list_status()
        new_fans_count = fans_list_status.get("count", 0)
        last_access_ts = fans_list_status.get("time", 0)
        self.new_fans_list = []
        if new_fans_count:
            new_fans_detail = self.bili_api.get_fans_detail(num=new_fans_count, last_access_ts=last_access_ts)
            if not new_fans_detail or 'list' not in new_fans_detail:
                return []
            self.new_fans_list.extend({'uname': f['uname'], 'mid': f['mid']} for f in new_fans_detail['list'])
        # 合并到总列表
        self.fans_list[:0] = self.new_fans_list
        return self.new_fans_list


    # 粉丝判断
    def is_fan(self, user_mid: int = 0):
        for fan in self.fans_list:
            if fan.get('mid') == user_mid:
                return True
        return False


    # 新粉丝判断
    def is_new_fan(self, user_mid: int = 0):
        for idx, fan in enumerate(self.new_fans_list):
            if fan.get('mid') == user_mid:
                del self.new_fans_list[idx]     # 仅生效一次，立即移除
                return True
        return False


    # 检查重复消息
    def check_repet_message(self, user_mid: int = 0, msg: str = "无消息内容"):
        if self.repet_protect_times == 0:
            return False
        need = self.repet_protect_times + 1
        if (user_mid not in self.message_list or
                self.message_list[user_mid].maxlen != need):
            self.message_list[user_mid] = deque(maxlen=need)
        dq = self.message_list[user_mid]
        dq.append(msg)
        if len(dq) < need:
            return False
        return len(set(dq)) == 1


    # 发送消息
    def send_message(self, user_mid: int = 0, msg: str = "无消息内容"):
        message_lower = msg.lower()
        if self.is_new_fan(user_mid):
            msg_replay = self.new_fans_reply
            self.log_print(f"用户身份：新粉丝")
        elif self.is_fan(user_mid):
            if message_lower in self.fans_complete_dict:
                msg_replay = self.fans_complete_dict[message_lower]
            else:
                hit_key = next((k for k in self.fans_keyword_dict
                    if k in message_lower), None)
                if hit_key is not None:
                    msg_replay = self.fans_keyword_dict[hit_key]
                else:
                    msg_replay = self.fans_other_reply
            self.log_print(f"用户身份：粉丝")
            self.log_print(f"消息内容：\n{msg}")
        else:
            if message_lower in self.non_fans_complete_dict:
                msg_replay = self.non_fans_complete_dict[message_lower]
            else:
                hit_key = next((k for k in self.non_fans_keyword_dict
                    if k in message_lower), None)
                if hit_key is not None:
                    msg_replay = self.non_fans_keyword_dict[hit_key]
                else:
                    msg_replay = self.non_fans_other_reply
            self.log_print(f"用户身份：非粉丝")
            self.log_print(f"消息内容：\n{msg}")

        
        if msg_replay and not self.check_repet_message(user_mid, msg_replay):
            self.log_print(f"消息回复：\n{msg_replay}")
            self.bili_api.send_message(user_mid=user_mid, msg=msg_replay)
        else:
            self.log_print(f"无匹配消息回复")


    # 获取新会话
    def get_new_sessions(self):
        # 记住当前时间戳
        temp_timestamp_ns = self.timestamp_ns
        # 更新当前时间戳
        self.timestamp_ns = int(time.time_ns() / 1_000)
        # 读取最近会话列表
        sessions = self.bili_api.get_sessions(begin_ts=temp_timestamp_ns, end_ts=self.timestamp_ns)
        # 此处可添加has_more判断优化
        session_list = sessions.get("session_list")
        return session_list


    # 获取用户昵称
    def get_user_name(self, user_mid: int = 0):
        user_info = self.bili_api.get_user_info(user_mid)
        return user_info['card']['name']


    # 更新视频数据
    def update_video_data(self):
        # 获取视频数据
        video_data = self.bili_api.get_video_data()
        self.total_fans = video_data.get("total_fans", 0)
        self.inc_fans = video_data.get("incr_fans", 0)
        self.total_click = video_data.get("total_click", 0)
        self.inc_click = video_data.get("incr_click", 0)
        self.total_like = video_data.get("total_like", 0)
        self.inc_like = video_data.get("inc_like", 0)
        self.total_fav = video_data.get("total_fav", 0)
        self.inc_fav = video_data.get("inc_fav", 0)


    # 自动回复消息
    def auto_reply_msg(self):
        # 获取新粉丝
        self.get_new_fans()
        # 新粉丝打招呼
        while self.new_fans_list:
            self.notice_status = True
            self.log_print(f"\n检测到新粉丝【{self.new_fans_list[0]['uname']}】关注")
            self.send_message(user_mid=self.new_fans_list[0]['mid'])
        # 获取新消息
        new_sessions = self.get_new_sessions()
        # 消息回复
        if new_sessions:
            for each_session in new_sessions:
                if each_session.get("unread_count", 0) > 0:
                    self.notice_status = True
                    self.log_print(f"\n检测到新消息")
                    unread_mid = each_session['last_msg']['sender_uid']
                    unread_name = self.get_user_name(unread_mid)
                    unread_msg = json.loads(each_session['last_msg']['content'])['content']
                    self.log_print(f"消息用户：{unread_name}")
                    self.send_message(user_mid=unread_mid, msg=unread_msg)
        if self.notice_status:
            self.log_print("\n当前无新消息，持续监测中...")
            self.notice_status = False
        

    # 线程-更新视频数据
    def thread_update_video_data(self):
        while not self._thread_update_video_data_stop_evt.is_set():
            try:
                if self.thread_update_video_data_status:
                    self.update_video_data()
            except Exception as e:
                self.log_print("\n[暂停线程]-更新视频数据")
                self.log_print(f"更新视频数据异常：{e}")
                self.log_print("将在10分钟后自动重启运行")
                self.thread_update_video_data_status = False
                time.sleep(10*60)
                self.log_print("\n[恢复线程]-更新视频数据")
                self.thread_update_video_data_status = True
            self._thread_update_video_data_stop_evt.wait(3600)


    # 线程-自动回复消息
    def thread_auto_reply_msg(self):
        while not self._thread_auto_reply_msg_stop_evt.is_set():
            try:
                # 重新加载设置参数
                self.load_settings()
                if self.thread_auto_reply_msg_status:
                    self.auto_reply_msg()
                time.sleep(self.interval_seconds)
            except Exception as e:
                self.log_print("\n[暂停线程]-自动回复消息")
                self.log_print(f"自动回复消息异常：{e}")
                self.log_print("将在10分钟后自动重启运行")
                self.thread_auto_reply_msg_status = False
                time.sleep(10*60)
                self.log_print("\n[恢复线程]-自动回复消息")
                self.thread_auto_reply_msg_status = True
            self._thread_auto_reply_msg_stop_evt.wait(self.interval_seconds)


    # 线程-共享内存
    def thread_update_shared_mem(self):
        while True:
            try:
                # 更新共享内存
                self.update_shared_mem()
            except Exception as e:
                pass
            time.sleep(1)


    # 主引擎
    def engine(self):
        # 先登录
        self.log_print("检查登录状态")
        if self.login():
            self.log_print("登录已完成")
        else:
            self.log_print("登录未完成")
            self.log_print("程序终止")
        # 初始更新粉丝列表
        self.log_print("初始加载粉丝列表")
        self.reload_fans_list()
        self.log_print("加载粉丝列表完成")
        self.log_print(f"粉丝总数：{self.fans_num}，已加载粉丝数：{len(self.fans_list)}")

        # 启动线程-共享内存
        self._thread_update_shared_mem = threading.Thread(target=self.thread_update_shared_mem, daemon=True)
        self._thread_update_shared_mem.start()

        # 启动线程-更新视频数据
        self.thread_update_video_data_status = True
        self._thread_update_video_data_stop_evt = threading.Event()
        self._thread_update_video_data = threading.Thread(target=self.thread_update_video_data, daemon=True)
        self._thread_update_video_data.start()
        self.log_print("\n[启动线程]-更新视频数据")

        # 登录成功执行自动消息
        self.notice_status = True
        # 启动线程-自动回复消息
        self.thread_auto_reply_msg_status = True
        self._thread_auto_reply_msg_stop_evt = threading.Event()
        self._thread_auto_reply_msg_data = threading.Thread(target=self.thread_auto_reply_msg, daemon=True)
        self._thread_auto_reply_msg_data.start()
        self.log_print("\n[启动线程]-自动回复消息")

        while True:
            pass




if __name__ == "__main__":
    bilimate = BiliMateServer()
    bilimate.engine()