# 图书馆管理系统 - Library Management System

一个完整的图书馆管理系统，支持管理员后台和读者自助服务。

## 功能

### 管理员后台 (/login)
- 仪表盘：馆藏统计、借阅概览、操作日志
- 图书管理：100本预置图书，支持增删改查、分类筛选
- 读者管理：读者信息管理、借阅状态跟踪
- 借阅管理：在借/逾期/归还历史三个Tab，操作日志完整记录

### 读者自助 (/reader)
- 自助注册：任何人均可注册读者账户
- 图书浏览：卡片式浏览全部可借图书，搜索和分类筛选
- 自助借阅：一键借阅（默认30天）
- 自助归还：查看当前借阅，一键归还
- 借阅历史：查看全部个人借阅记录

## 快速启动

```bash
# 安装依赖
pip install -r requirements.txt

# 启动（默认SQLite，无需安装数据库）
python app.py

# 访问
# 首页:     http://localhost:5000
# 管理员:   http://localhost:5000/login    (root / 1234)
# 读者入口: http://localhost:5000/reader   (自助注册)
```

## 使用 MySQL

```bash
# 1. 创建数据库
mysql -u root -p < init_db.sql

# 2. 启动应用
set USE_MYSQL=1
python app.py
```

## 部署到 Render.com（免费）

1. 将代码推送到 GitHub 仓库
2. 在 [Render.com](https://render.com) 创建 Web Service
3. 连接 GitHub 仓库
4. 设置：
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app --bind 0.0.0.0:$PORT`
5. 部署完成后访问 Render 提供的 URL

## 默认账号

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 管理员 | root | 1234 |
| 示例读者 | R20240001 ~ R20240008 | 123456 |

## 技术栈

- 后端：Python Flask
- 数据库：SQLite（默认）/ MySQL（可选）
- 前端：原生 HTML/CSS/JS，无框架依赖
- 部署：支持 Render / Railway / 任意 VPS
