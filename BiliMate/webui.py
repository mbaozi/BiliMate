#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BiliMate – B站小助手 WEBUI前端

作者信息
--------
Author : 是萌包子吖
Site   : https://mbaozi.cn
GitHub : https://github.com/mbaozi

版本记录
--------
Version : 0.1.0
Date    : 2025-08-26
Change  : 初版发布
"""

import json, struct, qrcode, time
from pathlib import Path
import multiprocessing.shared_memory as shm
from collections import deque
from PIL import Image
from io import BytesIO
import pandas as pd
import streamlit as st


# 共享内存大小
SHARED_SIZE = 128 * 1024

# 文件
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)
COOKIE_FILE = DATA_DIR / "cookies.json"
SETTINGS_FILE = DATA_DIR / "settings.json"
LOG_FILE = DATA_DIR / f"log_BiliMate.txt"
LOGO_FILE = Path(__file__).parent / "favicon.ico"
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

# 状态更新时间
STATUS_VIEW_REFRESH_INTERVAL = 1

# 局部更新时间
STATE_INFO_REFRESH_INTERVAL = 10
REPLY_INFO_REFRESH_INTERVAL = 2

# 显示回复行数
REPLY_INFO_DISPLAY_LINES = 50



# BiliMate客户端
class BiliMateWebUI:
    def __init__(self):
        # 样式 & 页面配置
        st.html("""
            <style>
            .stAppDeployButton {display: none !important;}
            .powered {
                position: fixed;
                right: 20px;
                bottom: 20px;
                font-size: 12px;
                color: #888;
                background: rgba(255,255,255,.7);
                padding: 2px 6px;
                border-radius: 4px;
                z-index: 9999;
            }
            </style>
            <div class="powered">
                Powered by <a href="https://space.bilibili.com/3546855325567315" target="_blank" style="color:#0366d6;text-decoration:none;">是萌包子吖</a>
            </div>
        """)
        st.set_page_config(
            page_title="BiliMate",
            page_icon=LOGO_FILE,
            layout="centered",
            initial_sidebar_state="collapsed",
            menu_items={}
        )
        st.logo(
            image=LOGO_FILE,
            size="large",
            link="https://github.com/mbaozi/BiliMate"
        )
        # 初始化共享内存
        self.timestamp_list = deque(maxlen=5)
        try:
            self.mem = shm.SharedMemory(name="BiliMate_shm", create=False, size=SHARED_SIZE)
        except FileNotFoundError:
            st.error("BiliMate 服务异常")
            st.stop()
        self.reload_shared_mem()
        
        # 访问口令
        self.verify_token()
        # 访问页面
        st.session_state.page = "dashboard" if self.login_status == "已登录" else "login"
        if st.session_state.page == "login":
            self.page_login()
        elif st.session_state.page == "dashboard":
            self.page_dashboard()


    # 加载设置参数
    def load_settings(self):
        try:
            settings = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        except Exception as e:
            settings = DEFAULT_SETTINGS.copy()
            self.save_settings(settings)
            print(f"加载设置参数失败，恢复默认参数: {e}")
        return settings


    # 保存设置参数
    def save_settings(self, settings):
        SETTINGS_FILE.write_text(
            json.dumps(settings, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    
    # 确认访问口令
    def verify_token(self):
        settings = self.load_settings()
        token_key = settings.get("token_key", "")
        if token_key and not st.session_state.get("unlocked"):
            st.markdown("### 🔐 请输入口令")
            st.caption("在设置中留空即可取消口令")
            token_key_input = st.text_input(
                "🔐 请输入口令",
                type="password",
                key="pwd",
                label_visibility="collapsed"
            )
            if st.button("进入"):
                if token_key_input == token_key:
                    st.session_state["unlocked"] = True
                    st.success("口令正确，加载中...")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("口令错误，默认口令：BiliMate")
            st.stop()


    # 定时：更新共享内存
    @st.fragment(run_every=STATUS_VIEW_REFRESH_INTERVAL)
    def reload_shared_mem(self):
        try:
            length = struct.unpack('<I', self.mem.buf[:4])[0]
            payload = bytes(self.mem.buf[4:4+length]).decode()
            data =  json.loads(payload)
            time_stamp = data.get("time_stamp", 0)
            self.timestamp_list.append(time_stamp)
            if len(self.timestamp_list) == 5 and len(set(self.timestamp_list)) == 1:
                # 时间戳不更新了，服务端可能挂了
                st.error("BiliMate 服务异常")
                # st.stop()
            self.login_status = data.get("login_status", "未登录")
            self.login_url = data.get("login_url", "")
            self.login_time_cnt = data.get("login_time_cnt", 120)
            self.my_uname = data.get("my_uname", "")
            self.my_mid = data.get("my_mid", 3546855325567315)
            self.total_fans = data.get("total_fans", 0)
            self.inc_fans = data.get("inc_fans", 0)
            self.total_click = data.get("total_click", 0)
            self.inc_click = data.get("inc_click", 0)
            self.total_like = data.get("total_like", 0)
            self.inc_like = data.get("inc_like", 0)
            self.total_fav = data.get("total_fav", 0)
            self.inc_fav = data.get("inc_fav", 0)
            self.fans_list = data.get("fans_list", "[]")
            self.state_info_status = data.get("state_info_status", False)
            self.reply_info_status = data.get("reply_info_status", False)
        except Exception as e:
            print(f"更新共享内存异常: {e}")


    # 弹窗：功能设置
    @st.dialog("功能设置", width="large")
    def dialog_settings(self):
        # st.subheader("功能设置")
        settings = self.load_settings()
        st.html('<hr style="border:none;margin:0.5em 0;height:1px;background:#f0f0f080;">')
        new_fans_reply = st.text_area("欢迎语内容（新关注自动回复）", value=settings["new_fans_reply"], height=80, key="new_fans_reply_input")
        st.html('<hr style="border:none;margin:0.5em 0;height:1px;background:#f0f0f080;">')
        role = st.radio("消息对象", ["fans", "non_fans"], horizontal=True,
                        format_func=lambda x: "粉丝" if x == "fans" else "非粉丝")
        match_type = st.selectbox("匹配方式（收到消息自动回复）", ["complete_dict", "keyword_dict", "other"],
                                format_func=lambda x: {"complete_dict": "完全匹配", "keyword_dict": "关键字匹配", "other": "兜底回复"}[x])
        key_map = {"complete_dict": f"{role}_complete_dict", "keyword_dict": f"{role}_keyword_dict", "other": f"{role}_other_reply"}
        dict_key = key_map[match_type]
        if match_type == "other":
            reply_text = st.text_area("兜底回复内容", value=settings[dict_key], height=120, key=dict_key)
        else:
            kv_df = st.data_editor(pd.DataFrame(list(settings[dict_key].items()), columns=["关键词", "回复内容"]),
                                use_container_width=True, num_rows="dynamic", key=f"{dict_key}_editor")
        st.html('<hr style="border:none;margin:0.5em 0;height:1px;background:#f0f0f080;">')
        token_key = st.text_input(
            label="登录口令（留空取消口令）", 
            value=settings["token_key"], 
            type="password", 
            key="pwd", 
            label_visibility="visible"
        )
        st.html('<hr style="border:none;margin:0.5em 0;height:1px;background:#f0f0f080;">')
        repet_protect_times_value = settings["repet_protect_times"]
        repet_protect_times = st.number_input(
            label="重复消息保护次数（连续重复消息不回复，为0则不保护）",
            min_value=0,
            max_value=10,
            value=repet_protect_times_value,
            step=1,
            format="%d"
        )
        st.html('<hr style="border:none;margin:0.5em 0;height:1px;background:#f0f0f080;">')
        interval_seconds_value = settings["interval_seconds"]
        max_value = 60 * 5
        min_value = 1
        if interval_seconds_value < min_value:
            interval_seconds_value = min_value
        elif interval_seconds_value > max_value:
            interval_seconds_value = max_value
        interval_seconds = st.number_input(
            label="循环间隔（秒）",
            min_value=min_value,
            max_value=max_value,
            value=interval_seconds_value,
            step=1,
            format="%d"
        )
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 保存", use_container_width=True):
                settings["new_fans_reply"] = new_fans_reply.strip()
                if match_type == "other":
                    settings[dict_key] = reply_text.strip()
                else:
                    settings[dict_key] = {k.strip(): v.strip() for k, v in kv_df.itertuples(index=False) if k and str(k).strip()}
                settings["token_key"] = token_key
                settings["repet_protect_times"] = repet_protect_times
                settings["interval_seconds"] = interval_seconds
                self.save_settings(settings)
                st.toast("已保存！", icon="✅")
        with col2:
            if st.button("↩️ 恢复默认", use_container_width=True):
                self.save_settings(DEFAULT_SETTINGS)
                st.toast("已恢复默认！", icon="↩️")
                time.sleep(3)
                st.rerun()


    # 弹窗：粉丝列表
    @st.dialog("粉丝列表", width="large")
    def dialog_fans(self):
        # st.subheader("粉丝列表")
        st.caption(f"共 **{len(self.fans_list)}** 位粉丝，此处最多显示100位")
        if len(self.fans_list) > 100:
            fans_list_dis = self.fans_list[0:100]
        else:
            fans_list_dis = self.fans_list
        st.html('<hr style="border:none;margin:0.5em 0;height:1px;background:#f0f0f080;">')
        cols = st.columns(5)
        for idx, f in enumerate(fans_list_dis):
            with cols[idx % 5]:
                st.link_button(label=f["uname"], url=f"https://space.bilibili.com/{f['mid']}")


    # 局部：状态显示运行状态
    @st.fragment(run_every=STATUS_VIEW_REFRESH_INTERVAL)
    def show_state_info_status(self):
        if self.state_info_status:
            st.markdown('<span style="color:green; font-weight:bold;">运行中 🟢</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span style="color:red; font-weight:bold;">已暂停 ⏸️</span>', unsafe_allow_html=True)


    # 局部：回复显示运行状态
    @st.fragment(run_every=STATUS_VIEW_REFRESH_INTERVAL)
    def show_reply_info_status(self):
        if self.reply_info_status:
            st.markdown('<span style="color:green; font-weight:bold;">运行中 🟢</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span style="color:red; font-weight:bold;">已暂停 ⏸️</span>', unsafe_allow_html=True)


    # 局部：状态显示
    @st.fragment(run_every=STATE_INFO_REFRESH_INTERVAL)
    def show_state_info(self):
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("👥 粉丝量", f"{self.total_fans:,}", delta=f"{self.inc_fans:+d}")
        col2.metric("▶️ 播放量", f"{self.total_click:,}", delta=f"{self.inc_click:+d}")
        col3.metric("❤️ 点赞量", f"{self.total_like:,}", delta=f"{self.inc_like:+d}")
        col4.metric("⭐ 收藏量", f"{self.total_fav:,}", delta=f"{self.inc_fav:+d}")


    # 局部：回复显示
    @st.fragment(run_every=REPLY_INFO_REFRESH_INTERVAL)
    def show_reply_info(self):
        if not LOG_FILE.exists():
            html = "<div>暂无日志文件</div>"
        else:
            try:
                lines = LOG_FILE.read_text(encoding="utf-8", errors="ignore").splitlines()
                lines = lines[-REPLY_INFO_DISPLAY_LINES:] if len(lines) > REPLY_INFO_DISPLAY_LINES else lines
                html = "<br>".join(lines)
            except Exception as e:
                html = f"读取日志失败：{e}"
        st.components.v1.html(
            f"""
            <div id="logBox">{html}</div>
            <style>
                #logBox{{
                    height:300px;overflow-y:auto;border:1px solid #d1d5da;border-radius:8px;
                    padding:8px 12px;font-family:Consolas,Monaco,monospace;font-size:14px;
                    line-height:1.5;background:#fafbfc;color:#374151;
                }}
            </style>
            <script>
                const b=document.getElementById('logBox');
                if(b)b.scrollTop=b.scrollHeight;
            </script>
            """,
            height=330,
        )


    # 局部：登录状态显示
    @st.fragment(run_every=1)
    def show_login_status(self):
        if self.login_status == "已登录":
            st.session_state["current_page"] = "dashboard"
            st.info(f"登录成功，即将自动跳转")
            st.rerun()
        elif self.login_status == "已扫码，请尽快确认":
            st.info(f"请在 {self.login_time_cnt} 秒内完成登录\n\n已扫码，请尽快确认")
        elif self.login_status == "二维码已失效":
            st.info(f"二维码已失效，即将自动刷新二维码")
            st.rerun()
        elif self.login_status == "超时未登录":
            # 登录超时    
            st.info(f"超时未登录，即将自动刷新二维码")
            st.rerun()
        else:
            st.info(f"请在 {self.login_time_cnt} 秒内完成登录")

    
    # 保存登录状态
    def on_remember_change(self):
        settings = self.load_settings()
        settings["login_remember"] = st.session_state.login_remember
        self.save_settings(settings)


    # 页面：登录
    def page_login(self):
        settings = self.load_settings()
        # 未登录
        st.header("请扫码登录")
        print(self.login_url)
        # 生成二维码
        qr = qrcode.make(self.login_url)
        buf = BytesIO()
        qr.save(buf, format="PNG")
        buf.seek(0)
        img = Image.open(buf)
        # 居中显示
        col1, col2, col3 = st.columns([1, 2, 1]) 
        with col2:
            login_img = st.empty()
            login_img.image(img, width=240)
            col2_1, col2_2, col2_3 = st.columns([1, 2, 1])
            with col2_2:
                login_remember = st.checkbox(
                    "保存登录状态",
                    value=settings["login_remember"],
                    key="login_remember",
                    on_change=self.on_remember_change
                )
        # 登录提示及检查
        self.show_login_status()
        
    
    # 页面：仪表盘
    def page_dashboard(self):
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown(f"### 你好，{self.my_uname}")
        with col2:
            col2_1, col2_2, col2_3, col2_4 = st.columns(4)
            with col2_1:
                st.link_button(
                    label="📺",
                    url=f"https://space.bilibili.com/{self.my_mid}",
                    help="我的主页",
                    use_container_width=True
                )
            with col2_2:
                if st.button("🔄", key="refresh_page", help="刷新页面", use_container_width=True):
                    st.toast("页面即将刷新！", icon="🔄")
                    time.sleep(1)
                    st.rerun()
                    # st.components.v1.html(
                    #     """
                    #     <script>
                    #         // 延迟 0 ms，确保按钮事件先完成
                    #         setTimeout(() => { window.parent.location.reload(); }, 0);
                    #     </script>
                    #     """,
                    #     height=0,
                    # )
            with col2_3:
                if st.button("👥", key="open_fans", help="粉丝列表", use_container_width=True):
                    self.dialog_fans()
            with col2_4:
                if st.button("⚙️", key="open_settings", help="功能设置", use_container_width=True):
                    self.dialog_settings()

        st.html('<hr style="border:none;margin:0.5em 0;height:1px;background:#f0f0f080;">')
        colb1, colb2 = st.columns([6, 1])
        with colb1:
            st.subheader("状态信息")
        with colb2:
            self.show_state_info_status()
        self.show_state_info()

        st.html('<hr style="border:none;margin:0.5em 0;height:1px;background:#f0f0f080;">')
        colc1, colc2 = st.columns([6, 1])
        with colc1:
            st.subheader("回复记录")
        with colc2:
            self.show_reply_info_status()
        self.show_reply_info()



if __name__ == "__main__":
    webui = BiliMateWebUI()

