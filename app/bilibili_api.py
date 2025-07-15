# bilibili api接口

import requests
import qrcode
import time
import json
import uuid


DEBUG = False

class BiliApi:
    def __init__(self):
        # 变量初始化
        self.fans_num = 0
        self.fans_page0_detail = None
        # 请求头
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        # 创建一个会话
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        pass


    # 请求登录二维码
    def get_login_url(self):
        login_url = ""
        # 获取登录二维码
        GET_LOGIN_URL = "https://passport.bilibili.com/x/passport-login/web/qrcode/generate"
        params = {
            # "source": "main-fe-header",
            # "go_url": "https://www.bilibili.com/"
        }
        response = self.session.get(GET_LOGIN_URL, params=params)
        if response.status_code == 200:
            response_data = response.json()
            if DEBUG:
                print(response_data)
            if response_data['code'] == 0:
                # 提取二维码网站
                login_url = response_data['data']['url']
                self.qrcode_key = response_data['data']['qrcode_key']
            else:
                if DEBUG:
                    print("获取登录二维码失败")
        else:
            if DEBUG:
                print("请求失败，状态码:", response.status_code)
        return login_url


    # 获取登录结果
    def get_login_status(self, time_out: int = 120):
        # 等待扫描登录
        time_cnt = time_out
        time_step = 1
        CHECK_LOGIN_URL = "https://passport.bilibili.com/x/passport-login/web/qrcode/poll"
        params = {
            "qrcode_key": self.qrcode_key,
        }
        while time_cnt > 0:
            time.sleep(time_step)
            time_cnt = time_cnt - time_step
            response = self.session.get(CHECK_LOGIN_URL, params=params)
            if response.status_code == 200:
                response_data = response.json()
                if DEBUG:
                    print(response_data)
                if response_data['code'] == 0:
                    if response_data['data']['code'] == 0:
                        if DEBUG:
                            print("登录成功")
                        return self.update_account_info()
                    elif response_data['data']['code'] == 86090:
                        if DEBUG:
                            print("已扫码，请尽快确认")
                    elif response_data['data']['code'] == 86038:
                        if DEBUG:
                            print("二维码已失效")
                    else:
                        pass
        if DEBUG:
            print("超时未登录成功")
        return False
    

    # 登录
    def login(self):
        login_url = self.get_login_url()
        if login_url != "":
            # 显示登录二维码
            qr = qrcode.QRCode(
                version=1,
                box_size=1,
                border=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L
            )
            qr.add_data(login_url)
            qr.make()
            if DEBUG:
                print("\n扫描下方二维码登录\n")
            qr.print_tty()
            # 获取登录结果
            return self.get_login_status()
        else:
            return False


    # 更新用户信息
    def update_account_info(self):
        GET_ACCOUNT_URL = "https://api.bilibili.com/x/member/web/account"
        response = self.session.get(GET_ACCOUNT_URL)
        if response.status_code == 200:
            response_data = response.json()
            if DEBUG:
                print(response_data)
            if response_data['code'] == 0:
                self.my_mid = response_data['data']['mid']
                self.my_uname = response_data['data']['uname']
                self.my_userid = response_data['data']['userid']
                if DEBUG:
                    print(f"mid：{self.my_mid}")
                    print(f"uname：{self.my_uname}")
                    print(f"userid：{self.my_userid}")
                return True
            else:
                if DEBUG:
                    print("获取用户信息失败")
                return False
        else:
            if DEBUG:
                print("请求失败，状态码:", response.status_code)
            return False


    # 获取粉丝情况
    def get_fans_detail(self, page: int = 0, num: int = 1):
        GET_FOLLOWER_URL = "https://api.bilibili.com/x/relation/followers"
        params = {
            "pn": page,
            "ps": num,
            "vmid": self.my_mid
        }
        response = self.session.get(GET_FOLLOWER_URL, params=params)
        if response.status_code == 200:
            response_data = response.json()
            # if DEBUG:
            #     print(response_data)
            if response_data['code'] == 0:
                return response_data['data']
            else:
                if DEBUG:
                    print("获取粉丝信息失败")
        else:
            if DEBUG:
                print("请求失败，状态码:", response.status_code)
        return None


    # 获取粉丝数量
    def get_fans_num(self):
        # 通过获取一页粉丝来得知粉丝数
        fans_num = -1
        fans_detail = self.get_fans_detail(page=0, num=1)
        if fans_detail != None:
            fans_num = fans_detail['total']
            if DEBUG:
                print(f"当前粉丝数：{fans_num}")
        else:
            if DEBUG:
                print("获取粉丝数失败")
        return fans_num
    

    # 获取粉丝列表
    def get_fans_list(self):
        # 按照粉丝个数，分多页获取粉丝列表
        fans_list = []
        fans_index = 0
        self.fans_num = self.get_fans_num()
        self.fans_page0_detail = self.get_fans_detail(page=0, num=50)
        page_num = self.fans_num // 50 + 1
        for page_i in range(1, page_num+1):
            fans_detail = self.get_fans_detail(page=page_i, num=50)
            if fans_detail != None:
                # 处理粉丝列表
                for each_fan in fans_detail['list']:
                    # 处理粉丝信息
                    fans_index += 1
                    fans_list.append({'uname': each_fan['uname'], 'mid': each_fan['mid']})
                    if DEBUG:
                        print(f"粉丝{fans_index}：{fans_list[fans_index-1]}")
            else:
                if DEBUG:
                    print("获取粉丝列表失败")
                return None
        return fans_list


    # 更新粉丝列表
    def update_fans_list(self):
        # 如果粉丝没有发生变更，则不需要更新
        # 检查粉丝第一页和总数是否发生变化
        fans_num_temp = self.get_fans_num()
        fans_page0_temp = self.get_fans_detail(page=0, num=50)
        if (fans_num_temp != self.fans_num) or (fans_page0_temp != self.fans_page0_detail):
            fans_list_temp = self.get_fans_list()
            if fans_list_temp != None:
                self.fans_list = fans_list_temp
                return True
            else:
                if DEBUG:
                    print("更新粉丝列表失败")
                return False
        else:
            if DEBUG:
                print("无需更新粉丝列表")
            return True


    # 粉丝判断
    def is_fan(self, user_mid: int = 0):
        for each_fan in self.fans_list:
            if user_mid == each_fan['mid']:
                return True
        return False


    # 获取会话列表
    def get_sessions(self, count: int = 20):
        GET_SESSIONS_URL = "https://api.vc.bilibili.com/session_svr/v1/session_svr/get_sessions"
        params = {
            "session_type": 4,
            "group_fold": 0,
            "unfollow_fold": 0,
            "sort_rule": 2,
            "build": 0,
            "size": count,
            "mobi_app": "web"
        }
        response = self.session.get(GET_SESSIONS_URL, params=params)
        if response.status_code == 200:
            response_data = response.json()
            # if DEBUG:
            #     print(response_data)
            if response_data['code'] == 0:
                return response_data['data']['session_list']
            else:
                print(f"获取会话列表失败，错误信息: {response_data['message']}")
        else:
            if DEBUG:
                print("请求失败，状态码:", response.status_code)
        return None


    # 获取会话消息
    def get_session_detail(self, user_mid: int = 0):
        GET_SESSION_DETAIL_URL = "https://api.vc.bilibili.com/session_svr/v1/session_svr/session_detail"
        params = {
            "talker_id": user_mid,
            "session_type": 1,
            "build": 0,
            "mobi_app": "web"
        }
        response = self.session.get(GET_SESSION_DETAIL_URL, params=params)
        if response.status_code == 200:
            response_data = response.json()
            if response_data['code'] == 0:
                return response_data['data']['session_list']
            else:
                print(f"获取会话列表失败，错误信息: {response_data['message']}")
        else:
            if DEBUG:
                print("请求失败，状态码:", response.status_code)
        return None


    # 发送消息
    def send_message(self, user_mid: int = 0, msg: str = "无消息内容"):
        SEND_MSG_URL = "https://api.vc.bilibili.com/web_im/v1/web_im/send_msg"
        tail = "\n"+"\u005f"*20+"\n\u300c\u0042\u0069\u006c\u0069\u004d\u0061\u0074\u0065\u300d\u81ea\u52a8\u56de\u590d"
        data = {
            "msg[sender_uid]": self.my_mid,
            "msg[receiver_id]": user_mid,
            "msg[receiver_type]": 1,
            "msg[msg_type]": 1,
            "msg[msg_status]": 0,
            "msg[content]": json.dumps({"content":msg+tail}),
            "msg[dev_id]": str(uuid.uuid4()),
            "msg[new_face_version]": 0,
            "msg[timestamp]": int(time.time()),
            "from_filework": 0,
            "build": 0,
            "mobi_app": "web",
            "csrf": self.session.cookies.get('bili_jct'),
        }
        response = self.session.post(SEND_MSG_URL, data=data)
        if response.status_code == 200:
            response_data = response.json()
            if DEBUG:
                print(response_data)
            if response_data['code'] == 0:
                if DEBUG:
                    print(f"成功回复")
                    print(f"用户：{user_mid}")
                    print(f"消息：{msg}")
                return True
            else:
                if DEBUG:
                    print("回复用户消息失败")
                return False
        else:
            if DEBUG:
                print("请求失败，状态码:", response.status_code)
            return False
