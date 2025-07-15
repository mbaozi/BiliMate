import os
import time
import json

import sys
sys.path.append("app")

from bilibili_api import BiliApi
import reply_config


# 获取当前工作目录
current_dir = os.getcwd()
# 日志目录
log_dir = os.path.join(current_dir, "logs")
# 确保日志文件夹存在
os.makedirs(log_dir, exist_ok=True)
# 构造日志文件名，包含时间戳
timestamp = time.strftime('%Y-%m-%d_%H-%M-%S', time.localtime(time.time()))
log_file = os.path.join(log_dir, f"BiliMsgBot_{timestamp}.txt")


# 日志打印
def log_print(*args, **kwargs):
    # 获取当前时间
    current_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
    # 构造日志字符串
    log_txt = f"[{current_time}] " + " ".join(map(str, args))
    # 打印到控制台
    print(log_txt, **kwargs)
    # 打开日志文件并写入日志内容
    with open(log_file, 'a', encoding='utf-8') as file:
        file.write(log_txt + "\n")


# 获取粉丝回复消息
def get_fans_reply_message(message):
    # 将输入消息转换为小写
    message_lower = message.lower()
    # 完全匹配（忽略大小写）
    for key in reply_config.fans_complete_dict.keys():
        if message_lower == key.lower():
            reply_message = reply_config.fans_complete_dict[key]
            return reply_message
    # 关键字匹配（忽略大小写）
    for key, value in reply_config.fans_keyword_dict.items():
        if key.lower() in message_lower:
            return value
    # 其他情况
    return reply_config.fans_other_dict["default"]


# 获取非粉丝回复消息
def get_non_fans_reply_message(message):
    # 将输入消息转换为小写
    message_lower = message.lower()
    # 完全匹配（忽略大小写）
    for key in reply_config.non_fans_complete_dict.keys():
        if message_lower == key.lower():
            reply_message = reply_config.non_fans_complete_dict[key]
            return reply_message
    # 关键字匹配（忽略大小写）
    for key, value in reply_config.non_fans_keyword_dict.items():
        if key.lower() in message_lower:
            return value
    # 其他情况
    return reply_config.non_fans_other_dict["default"]




if __name__ == "__main__":
    os.system('cls' if os.name == 'nt' else 'clear')
    bot = BiliApi()
    log_print("请扫描二维码登录")
    if bot.login():
        log_print("登录成功")
        log_print(f"欢迎您：{bot.my_uname}")
        # 初始更新粉丝列表
        bot.update_fans_list()
        no_msg_status = False
        while True:
            time.sleep(2)
            # 读取会话信息
            sessions = bot.get_sessions()
            # 逐个会话处理
            for each_session in sessions:
                if each_session['unread_count'] > 0:
                    no_msg_status = False
                    # 更新粉丝列表
                    bot.update_fans_list()
                    # 未读会话
                    log_print("================")
                    log_print("检测到未读消息")
                    unread_mid = each_session['last_msg']['sender_uid']
                    unread_msg = json.loads(each_session['last_msg']['content'])['content']
                    log_print(f"消息用户：{unread_mid}")
                    log_print(f"消息内容：{unread_msg}")
                    if bot.is_fan(user_mid=unread_mid):
                        reply_msg = get_fans_reply_message(unread_msg)
                        log_print(f"用户身份：粉丝")
                    else:
                        reply_msg = get_non_fans_reply_message(unread_msg)
                        log_print(f"用户身份：非粉丝")
                    log_print(f"消息回复：{reply_msg}")
                    # 回复消息
                    if bot.send_message(user_mid=unread_mid, msg=reply_msg):
                        log_print("消息自动回复成功")
                    else:
                        log_print("消息自动回复失败")
                    log_print("================")
            if not no_msg_status:
                log_print("当前无新消息，持续监测中...")
                no_msg_status = True

