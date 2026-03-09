# BiliMate

## 项目介绍

BiliMate是基于Python Flask开发的B站助手工具，旨在帮助UP主更高效地管理账号互动。目前核心功能为自动回复消息，更多实用功能正在持续开发中。

## 功能特性

### 账号管理与授权
- 用户登录系统
- B站账号授权与管理
- 支持多账号管理

### B站私信自动回复
- 支持自动回复B站私信
- 可区分粉丝和非粉丝设置不同回复内容
- 支持完全匹配和关键词匹配回复

### 新粉丝自动回复
- 支持对新关注的粉丝自动发送欢迎消息
- 可自定义欢迎消息内容

### 回复模板管理
- 支持创建、编辑和管理回复模板
- 支持在回复中使用变量

### 重复回复保护
- 防止对同一用户频繁发送回复消息
- 可配置保护规则

### 消息统计和管理
- 支持查看和管理历史消息记录
- 支持查看回复成功率

## 技术栈

### 后端
- Python 3.13+
- Flask
- SQLAlchemy
- APScheduler
- Requests

### 前端
- HTML5
- CSS3
- JavaScript

## 安装步骤

### 1. 克隆仓库

```bash
git clone https://github.com/mbaozi/BiliMate.git
cd BiliMate
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

复制 `.env.example` 文件为 `.env` 并根据需要修改配置。

### 4. 启动应用

```bash
cd BiliMate
python run.py
```

默认情况下，应用会在 `http://localhost:8181` 启动。

## 使用方法

### 首次登录设置
1. 启动应用后，访问 `http://localhost:8181`
2. 按照提示完成首次登录设置

### 授权B站账号
1. 登录系统后，进入B站账号管理页面
2. 点击"添加账号"按钮
3. 使用B站手机APP扫描二维码进行授权
4. 授权成功后，账号会自动添加到系统中

### 配置自动回复
1. 进入回复配置页面
2. 选择要配置的B站账号
3. 启用自动回复功能
4. 配置粉丝和非粉丝的回复规则
5. 保存配置

### 管理回复模板
1. 进入模板管理页面
2. 创建新模板或编辑现有模板
3. 保存模板后，可在回复配置中使用

## 项目结构

```
BiliMate/
├── BiliMate/
│   ├── app/
│   │   ├── models/          # 数据模型
│   │   ├── routes/           # 路由
│   │   ├── services/         # 业务逻辑
│   │   ├── static/           # 静态文件
│   │   ├── templates/        # 模板文件
│   │   └── __init__.py       # 应用初始化
│   ├── config.py             # 配置文件
│   ├── run.py                # 应用入口
│   └── build_pyz.py          # 打包脚本
├── .env.example              # 环境变量示例
├── .gitignore                # Git忽略文件
├── Dockerfile                # Docker配置
├── LICENSE                   # 许可证文件
├── README.md                 # 项目说明
├── docker-compose.yml        # Docker Compose配置
└── requirements.txt          # 依赖文件
```

## 许可证

本项目采用 GNU Affero General Public License v3.0 许可证。详见 [LICENSE](LICENSE) 文件。

## 联系方式

- GitHub: [https://github.com/mbaozi/BiliMate](https://github.com/mbaozi/BiliMate)
- B站UP主: [是萌包子吖](https://space.bilibili.com/3546855325567315)

## 版本信息

当前版本: v1.0.0
