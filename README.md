# 智慧图书馆管理系统

Python Flask + SQLite + 原生前端，部署在阿里云 ECS。

## 在线访问

🌐 **http://121.40.116.75**

手机扫码也能打开（响应式布局）。

---

## 项目结构

```
图书馆管理系统/
├── app.py              # Flask 主程序（34个API接口）
├── requirements.txt    # Python 依赖
├── library.db          # SQLite 数据库文件
├── init_db.sql         # 数据库建表 SQL
├── templates/          # 前端 HTML 页面（10个）
│   ├── base.html           # 基础模板（暗色主题）
│   ├── index.html          # 首页（双入口）
│   ├── login.html          # 管理员登录
│   ├── dashboard.html      # 管理后台仪表盘
│   ├── books.html          # 图书管理
│   ├── readers.html        # 读者管理
│   ├── borrow.html         # 借阅管理
│   ├── announcements.html  # 公告管理
│   ├── reader_login.html   # 读者登录/注册
│   ├── reader_books.html   # 读者浏览图书
│   └── reader_dashboard.html # 读者个人中心
├── static/
│   ├── css/style.css       # 暗色主题样式
│   └── js/main.js          # 原生 JS 交互
├── deploy.sh           # 一键部署脚本
├── nginx.conf          # Nginx 配置
├── Procfile            # Gunicorn 启动配置
├── .env.example        # 环境变量示例
└── .gitignore
```

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python Flask |
| 数据库 | SQLite（WAL 模式） |
| 前端 | 原生 HTML + CSS + JS |
| 服务器 | 阿里云 ECS + Ubuntu |
| 部署 | Nginx + Gunicorn + Systemd |

---

## 本地运行

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 初始化数据库
python -c "from app import init_db; init_db()"

# 3. 启动服务
python app.py

# 4. 打开浏览器
# http://127.0.0.1:5000
```

---

## 查看数据库

### 方法一：用 SQLite 命令行（推荐）

```bash
# 进入项目目录
cd 图书馆管理系统

# 打开数据库
sqlite3 library.db

# 查看所有表
.tables

# 查看表结构（以 books 为例）
.schema books

# 查看图书数据
SELECT * FROM books LIMIT 10;

# 查看借阅记录（带书名和读者名）
SELECT b.title, r.name, br.borrow_date, br.due_date
FROM borrowing_records br
JOIN books b ON br.book_id = b.id
JOIN readers r ON br.reader_id = r.id
ORDER BY br.borrow_date DESC
LIMIT 20;

# 查看操作日志
SELECT * FROM operation_logs ORDER BY created_at DESC LIMIT 20;

# 查看读者列表
SELECT id, name, phone, created_at FROM readers;

# 查看书评
SELECT b.title, r.name, rev.rating, rev.content
FROM reviews rev
JOIN books b ON rev.book_id = b.id
JOIN readers r ON rev.reader_id = r.id
LIMIT 10;

# 统计借阅排行
SELECT b.title, COUNT(*) as borrow_count
FROM borrowing_records br
JOIN books b ON br.book_id = b.id
GROUP BY br.book_id
ORDER BY borrow_count DESC
LIMIT 10;

# 退出
.quit
```

### 方法二：用 VS Code 插件

1. 安装插件 **SQLite Viewer**（搜索 `alexcvzz.vscode-sqlite`）
2. 在 VS Code 中右键 `library.db` → **Open Database**
3. 左侧会出现数据库面板，点表名就能看数据

### 方法三：用 DB Browser for SQLite（图形界面）

1. 下载 [DB Browser for SQLite](https://sqlitebrowser.org/)
2. 打开 `library.db` 文件
3. 在"浏览数据"标签页切换表查看

---

## 数据库表说明（9张表）

### 核心表

| 表名 | 说明 | 主要字段 |
|------|------|---------|
| users | 用户和角色 | username, password_hash, role(admin/reader) |
| books | 图书信息 | title, author, isbn, category, status, cover_url |
| readers | 读者资料 | name, phone, email, reader_card |
| borrowing_records | 借阅记录 | book_id, reader_id, borrow_date, due_date, return_date |
| operation_logs | 操作日志 | user_id, action, detail, created_at |

### 功能表

| 表名 | 说明 |
|------|------|
| announcements | 公告通知 |
| reviews | 书评和评分 |
| favorites | 收藏 |
| recommendations | 读者荐购 |

---

## API 接口（34个）

| 模块 | 接口数 | 说明 |
|------|:------:|------|
| 用户认证 | 4 | 注册、登录、退出、状态检查 |
| 图书管理 | 6 | 增删改查、搜索、分类筛选 |
| 读者管理 | 3 | 列表、详情、信息更新 |
| 借阅管理 | 5 | 借阅、归还、续借、记录查询 |
| 公告系统 | 3 | 发布、列表、删除 |
| 书评模块 | 4 | 提交、查看、编辑、删除 |
| 收藏&荐购 | 5 | 收藏、取消收藏、荐购、查看 |
| 统计&日志 | 4 | 排行榜、概览、日志查询 |

---

## 部署到阿里云

```bash
# 在服务器上
bash deploy.sh
```

详见 `deploy.sh` 脚本，自动完成：安装依赖 → 配置 Nginx → 启动 Gunicorn → 设置 Systemd 开机自启。

---

## 小组成员

- **刘智** — 组长、需求、答辩
- **刘显鸿福** — Flask 后端、API、数据库
- **李青隆** — 阿里云部署、Nginx、运维
- **曾诗蕊** — 测试、Bug 跟踪、文档
- **程阳** — 前端页面、JS 交互、暗色主题

---

## 项目亮点

- 全栈自研（后端 Flask + 前端原生 JS，零框架依赖）
- 34 个 API + 9 张数据表
- SQLite WAL 模式优化并发
- 响应式暗色主题，手机扫码即用
- 78 条测试用例，96.2% 通过率
- 阿里云 ECS 部署，7×24 在线
