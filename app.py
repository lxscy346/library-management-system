# -*- coding: utf-8 -*-
"""
图书馆管理系统 - Flask 后端
- 管理员后台: /login → 管理图书、读者、借阅
- 读者自助:   /reader → 注册、登录、浏览图书、借还书
默认使用 SQLite，设置 USE_MYSQL=1 切换 MySQL
"""
import os
import sqlite3
from datetime import datetime, timedelta
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'library-management-system-secret-2024')

# ---- 数据库配置 ----
USE_MYSQL = os.environ.get('USE_MYSQL', '0') == '1'
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'library.db')

if USE_MYSQL:
    import pymysql
    DB_CONFIG = {
        'host': os.environ.get('DB_HOST', 'localhost'),
        'user': os.environ.get('DB_USER', 'root'),
        'password': os.environ.get('DB_PASSWORD', '123456'),
        'database': os.environ.get('DB_NAME', 'library_management'),
        'charset': 'utf8mb4',
        'cursorclass': pymysql.cursors.DictCursor,
    }


class DB:
    def __init__(self):
        self._conn = None
        self._mysql = USE_MYSQL

    def connect(self):
        if self._mysql:
            self._conn = pymysql.connect(**DB_CONFIG)
        else:
            self._conn = sqlite3.connect(DB_PATH)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA foreign_keys=ON")
        return self._conn

    @property
    def conn(self):
        if self._conn is None:
            self.connect()
        return self._conn

    def cursor(self):
        return self.conn.cursor()

    def commit(self):
        self.conn.commit()

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None

    def placeholder(self):
        return '%s' if self._mysql else '?'

    def curdate(self):
        return 'CURDATE()' if self._mysql else "date('now')"

    def now(self):
        return 'NOW()' if self._mysql else "datetime('now','localtime')"


def get_db():
    return DB()


def fetch_all_dict(cursor):
    if USE_MYSQL:
        return cursor.fetchall()
    return [dict(r) for r in cursor.fetchall()]


def fetch_one_dict(cursor):
    if USE_MYSQL:
        return cursor.fetchone()
    row = cursor.fetchone()
    return dict(row) if row else None


# ---- 100 本样本书籍 ----

def get_sample_books():
    return [
        # 计算机科学 1-15
        ('978-7-111-00001-1', '深入理解计算机系统（原书第3版）', 'Randal E. Bryant', '机械工业出版社', '计算机科学', 139.00, 5, 'A区-01-01'),
        ('978-7-111-00002-8', '算法导论（原书第3版）', 'Thomas H. Cormen', '机械工业出版社', '计算机科学', 128.00, 4, 'A区-01-02'),
        ('978-7-111-00003-5', '计算机程序设计艺术 卷1', 'Donald E. Knuth', '人民邮电出版社', '计算机科学', 198.00, 3, 'A区-01-03'),
        ('978-7-111-00004-2', '计算机程序设计艺术 卷2', 'Donald E. Knuth', '人民邮电出版社', '计算机科学', 198.00, 3, 'A区-01-04'),
        ('978-7-111-00005-9', '计算机程序设计艺术 卷3', 'Donald E. Knuth', '人民邮电出版社', '计算机科学', 198.00, 3, 'A区-01-05'),
        ('978-7-111-00006-6', '计算机程序的构造和解释', 'Harold Abelson', '机械工业出版社', '计算机科学', 99.00, 4, 'A区-02-01'),
        ('978-7-111-00007-3', '编译原理（第2版）', 'Alfred V. Aho', '机械工业出版社', '计算机科学', 89.00, 4, 'A区-02-02'),
        ('978-7-111-00008-0', '操作系统概念（第9版）', 'Abraham Silberschatz', '机械工业出版社', '计算机科学', 99.00, 5, 'A区-02-03'),
        ('978-7-111-00009-7', '现代操作系统（第4版）', 'Andrew S. Tanenbaum', '机械工业出版社', '计算机科学', 109.00, 4, 'A区-02-04'),
        ('978-7-111-00010-3', '计算机网络：自顶向下方法（第8版）', 'James F. Kurose', '清华大学出版社', '计算机网络', 109.00, 5, 'A区-03-01'),
        ('978-7-111-00011-0', 'TCP/IP详解 卷1：协议', 'W. Richard Stevens', '机械工业出版社', '计算机网络', 129.00, 4, 'A区-03-02'),
        ('978-7-111-00012-7', '图解TCP/IP（第5版）', '竹下隆史', '人民邮电出版社', '计算机网络', 69.00, 6, 'A区-03-03'),
        ('978-7-111-00013-4', 'HTTP权威指南', 'David Gourley', '人民邮电出版社', '计算机网络', 109.00, 4, 'A区-03-04'),
        ('978-7-111-00014-1', '数据结构与算法分析：C语言描述', 'Mark Allen Weiss', '清华大学出版社', '计算机科学', 89.00, 5, 'A区-04-01'),
        ('978-7-111-00015-8', '数据结构（C++语言版）', '邓俊辉', '清华大学出版社', '计算机科学', 79.00, 5, 'A区-04-02'),
        ('978-7-111-00016-5', '算法（第4版）', 'Robert Sedgewick', '人民邮电出版社', '计算机科学', 99.00, 4, 'A区-04-03'),
        ('978-7-111-00017-2', '编程珠玑（第2版）', 'Jon Bentley', '人民邮电出版社', '计算机科学', 49.00, 5, 'A区-04-04'),
        ('978-7-111-00018-9', '程序设计实践', 'Brian W. Kernighan', '机械工业出版社', '计算机科学', 59.00, 5, 'A区-04-05'),
        ('978-7-111-00019-6', '代码大全（第2版）', 'Steve McConnell', '电子工业出版社', '软件工程', 128.00, 4, 'B区-01-01'),
        ('978-7-111-00020-2', '重构：改善既有代码的设计', 'Martin Fowler', '人民邮电出版社', '软件工程', 89.00, 5, 'B区-01-02'),
        ('978-7-111-00021-9', '设计模式：可复用面向对象软件的基础', 'Erich Gamma', '机械工业出版社', '软件工程', 79.00, 5, 'B区-01-03'),
        ('978-7-111-00022-6', '敏捷软件开发：原则、模式与实践', 'Robert C. Martin', '清华大学出版社', '软件工程', 99.00, 4, 'B区-01-04'),
        ('978-7-111-00023-3', '人月神话', 'Frederick P. Brooks', '清华大学出版社', '软件工程', 59.00, 6, 'B区-01-05'),
        ('978-7-111-00024-0', '程序员修炼之道', 'David Thomas', '电子工业出版社', '软件工程', 79.00, 5, 'B区-02-01'),
        ('978-7-111-00025-7', '黑客与画家', 'Paul Graham', '人民邮电出版社', '计算机科学', 69.00, 6, 'B区-02-02'),
        # 编程语言 26-45
        ('978-7-111-00026-4', 'C程序设计语言（第2版）', 'Brian W. Kernighan', '机械工业出版社', '编程语言', 49.00, 8, 'B区-02-03'),
        ('978-7-111-00027-1', 'C++ Primer（第5版）', 'Stanley B. Lippman', '电子工业出版社', '编程语言', 128.00, 5, 'B区-02-04'),
        ('978-7-111-00028-8', 'Effective C++（第3版）', 'Scott Meyers', '电子工业出版社', '编程语言', 69.00, 6, 'B区-02-05'),
        ('978-7-111-00029-5', 'Python编程：从入门到实践（第3版）', 'Eric Matthes', '人民邮电出版社', '编程语言', 99.00, 6, 'B区-03-01'),
        ('978-7-111-00030-1', '流畅的Python', 'Luciano Ramalho', '人民邮电出版社', '编程语言', 139.00, 4, 'B区-03-02'),
        ('978-7-111-00031-8', 'Python Cookbook（第3版）', 'David Beazley', '人民邮电出版社', '编程语言', 108.00, 4, 'B区-03-03'),
        ('978-7-111-00032-5', '利用Python进行数据分析', 'Wes McKinney', '机械工业出版社', '编程语言', 99.00, 5, 'B区-03-04'),
        ('978-7-111-00033-2', 'Java核心技术 卷I（第12版）', 'Cay S. Horstmann', '机械工业出版社', '编程语言', 149.00, 5, 'B区-03-05'),
        ('978-7-111-00034-9', 'Effective Java（第3版）', 'Joshua Bloch', '机械工业出版社', '编程语言', 99.00, 5, 'B区-04-01'),
        ('978-7-111-00035-6', 'Java并发编程实战', 'Brian Goetz', '机械工业出版社', '编程语言', 89.00, 5, 'B区-04-02'),
        ('978-7-111-00036-3', '深入理解Java虚拟机（第3版）', '周志明', '机械工业出版社', '编程语言', 99.00, 5, 'B区-04-03'),
        ('978-7-111-00037-0', 'JavaScript高级程序设计（第4版）', 'Matt Frisbie', '人民邮电出版社', 'Web开发', 129.00, 5, 'B区-04-04'),
        ('978-7-111-00038-7', 'JavaScript权威指南（第7版）', 'David Flanagan', '机械工业出版社', 'Web开发', 139.00, 4, 'B区-04-05'),
        ('978-7-111-00039-4', '你不知道的JavaScript（上卷）', 'Kyle Simpson', '人民邮电出版社', 'Web开发', 69.00, 6, 'C区-01-01'),
        ('978-7-111-00040-0', 'Go语言程序设计', 'Alan A. A. Donovan', '机械工业出版社', '编程语言', 79.00, 5, 'C区-01-02'),
        ('978-7-111-00041-7', 'Go语言实战', 'William Kennedy', '人民邮电出版社', '编程语言', 69.00, 5, 'C区-01-03'),
        ('978-7-111-00042-4', 'Rust权威指南', 'Steve Klabnik', '电子工业出版社', '编程语言', 129.00, 4, 'C区-01-04'),
        ('978-7-111-00043-1', 'C#高级编程（第11版）', 'Christian Nagel', '清华大学出版社', '编程语言', 148.00, 4, 'C区-01-05'),
        ('978-7-111-00044-8', 'TypeScript编程', 'Boris Cherny', '机械工业出版社', 'Web开发', 79.00, 5, 'C区-02-01'),
        ('978-7-111-00045-5', 'Swift编程权威指南（第3版）', 'Matthew Mathias', '人民邮电出版社', '编程语言', 119.00, 4, 'C区-02-02'),
        # 数据库 & 大数据 46-57
        ('978-7-111-00046-2', '数据库系统概念（第7版）', 'Abraham Silberschatz', '机械工业出版社', '数据库', 119.00, 4, 'C区-02-03'),
        ('978-7-111-00047-9', '高性能MySQL（第4版）', 'Silvia Botros', '电子工业出版社', '数据库', 128.00, 4, 'C区-02-04'),
        ('978-7-111-00048-6', 'MySQL技术内幕（第5版）', 'Paul DuBois', '人民邮电出版社', '数据库', 139.00, 4, 'C区-02-05'),
        ('978-7-111-00049-3', 'Redis设计与实现', '黄健宏', '机械工业出版社', '数据库', 79.00, 5, 'C区-03-01'),
        ('978-7-111-00050-9', 'MongoDB权威指南（第3版）', 'Shannon Bradshaw', '人民邮电出版社', '数据库', 99.00, 4, 'C区-03-02'),
        ('978-7-111-00051-6', '数据密集型应用系统设计', 'Martin Kleppmann', '中国电力出版社', '数据库', 139.00, 4, 'C区-03-03'),
        ('978-7-111-00052-3', 'Spark权威指南', 'Bill Chambers', '中国电力出版社', '大数据', 128.00, 4, 'C区-03-04'),
        ('978-7-111-00053-0', 'Hadoop权威指南（第4版）', 'Tom White', '清华大学出版社', '大数据', 148.00, 3, 'C区-03-05'),
        ('978-7-111-00054-7', 'Flink基础教程', 'Fabian Hueske', '人民邮电出版社', '大数据', 79.00, 5, 'C区-04-01'),
        ('978-7-111-00055-4', 'Kafka权威指南', 'Neha Narkhede', '人民邮电出版社', '大数据', 89.00, 5, 'C区-04-02'),
        ('978-7-111-00056-1', 'Elasticsearch权威指南', 'Clinton Gormley', '机械工业出版社', '大数据', 99.00, 4, 'C区-04-03'),
        ('978-7-111-00057-8', 'ClickHouse原理解析与应用实践', '朱凯', '机械工业出版社', '大数据', 99.00, 4, 'C区-04-04'),
        # 人工智能 58-70
        ('978-7-111-00058-5', '深度学习', 'Ian Goodfellow', '人民邮电出版社', '人工智能', 168.00, 3, 'D区-01-01'),
        ('978-7-111-00059-2', '机器学习', '周志华', '清华大学出版社', '人工智能', 88.00, 5, 'D区-01-02'),
        ('978-7-111-00060-8', '统计学习方法（第2版）', '李航', '清华大学出版社', '人工智能', 79.00, 5, 'D区-01-03'),
        ('978-7-111-00061-5', '模式识别与机器学习', 'Christopher M. Bishop', '机械工业出版社', '人工智能', 128.00, 3, 'D区-01-04'),
        ('978-7-111-00062-2', '动手学深度学习', 'Aston Zhang', '人民邮电出版社', '人工智能', 99.00, 5, 'D区-01-05'),
        ('978-7-111-00063-9', 'Python机器学习基础教程', 'Andreas C. Müller', '人民邮电出版社', '人工智能', 79.00, 5, 'D区-02-01'),
        ('978-7-111-00064-6', '自然语言处理综论', 'Daniel Jurafsky', '电子工业出版社', '人工智能', 128.00, 3, 'D区-02-02'),
        ('978-7-111-00065-3', '计算机视觉：算法与应用', 'Richard Szeliski', '清华大学出版社', '人工智能', 119.00, 3, 'D区-02-03'),
        ('978-7-111-00066-0', '强化学习（第2版）', 'Richard S. Sutton', '电子工业出版社', '人工智能', 139.00, 3, 'D区-02-04'),
        ('978-7-111-00067-7', '神经网络与深度学习', '邱锡鹏', '机械工业出版社', '人工智能', 99.00, 5, 'D区-02-05'),
        ('978-7-111-00068-4', 'PyTorch深度学习实战', 'Eli Stevens', '人民邮电出版社', '人工智能', 119.00, 4, 'D区-03-01'),
        ('978-7-111-00069-1', 'TensorFlow深度学习', 'Geron Aurelien', '机械工业出版社', '人工智能', 139.00, 4, 'D区-03-02'),
        ('978-7-111-00070-7', 'OpenCV计算机视觉编程攻略', 'Robert Laganiere', '人民邮电出版社', '人工智能', 89.00, 4, 'D区-03-03'),
        # 文学 71-82
        ('978-7-111-00071-4', '百年孤独', '加西亚·马尔克斯', '南海出版公司', '文学小说', 55.00, 6, 'E区-01-01'),
        ('978-7-111-00072-1', '三体', '刘慈欣', '重庆出版社', '文学小说', 45.00, 8, 'E区-01-02'),
        ('978-7-111-00073-8', '三体II：黑暗森林', '刘慈欣', '重庆出版社', '文学小说', 48.00, 8, 'E区-01-03'),
        ('978-7-111-00074-5', '三体III：死神永生', '刘慈欣', '重庆出版社', '文学小说', 58.00, 8, 'E区-01-04'),
        ('978-7-111-00075-2', '活着', '余华', '北京十月文艺出版社', '文学小说', 35.00, 10, 'E区-01-05'),
        ('978-7-111-00076-9', '围城', '钱钟书', '人民文学出版社', '文学小说', 39.00, 6, 'E区-02-01'),
        ('978-7-111-00077-6', '平凡的世界（全三册）', '路遥', '北京十月文艺出版社', '文学小说', 108.00, 5, 'E区-02-02'),
        ('978-7-111-00078-3', '红楼梦', '曹雪芹', '人民文学出版社', '文学小说', 68.00, 6, 'E区-02-03'),
        ('978-7-111-00079-0', '1984', 'George Orwell', '北京十月文艺出版社', '文学小说', 39.00, 6, 'E区-02-04'),
        ('978-7-111-00080-6', '动物农场', 'George Orwell', '上海译文出版社', '文学小说', 29.00, 8, 'E区-02-05'),
        ('978-7-111-00081-3', '挪威的森林', '村上春树', '上海译文出版社', '文学小说', 42.00, 6, 'E区-03-01'),
        ('978-7-111-00082-0', '小王子', '圣埃克苏佩里', '人民文学出版社', '文学小说', 28.00, 10, 'E区-03-02'),
        # 历史哲学 83-90
        ('978-7-111-00083-7', '人类简史', '尤瓦尔·赫拉利', '中信出版社', '历史文化', 68.00, 6, 'E区-03-03'),
        ('978-7-111-00084-4', '未来简史', '尤瓦尔·赫拉利', '中信出版社', '历史文化', 68.00, 6, 'E区-03-04'),
        ('978-7-111-00085-1', '万历十五年', '黄仁宇', '三联书店', '历史文化', 42.00, 6, 'E区-03-05'),
        ('978-7-111-00086-8', '全球通史', '斯塔夫里阿诺斯', '北京大学出版社', '历史文化', 88.00, 4, 'E区-04-01'),
        ('978-7-111-00087-5', '苏菲的世界', 'Jostein Gaarder', '作家出版社', '哲学', 45.00, 5, 'E区-04-02'),
        ('978-7-111-00088-2', '中国哲学简史', '冯友兰', '北京大学出版社', '哲学', 49.00, 5, 'E区-04-03'),
        ('978-7-111-00089-9', '理想国', '柏拉图', '商务印书馆', '哲学', 58.00, 5, 'E区-04-04'),
        ('978-7-111-00090-5', '论语译注', '杨伯峻', '中华书局', '哲学', 38.00, 5, 'E区-04-05'),
        # 经济管理 91-95
        ('978-7-111-00091-2', '经济学原理（第8版）', 'N. Gregory Mankiw', '北京大学出版社', '经济管理', 128.00, 4, 'F区-01-01'),
        ('978-7-111-00092-9', '思考，快与慢', 'Daniel Kahneman', '中信出版社', '经济管理', 69.00, 5, 'F区-01-02'),
        ('978-7-111-00093-6', '国富论', 'Adam Smith', '商务印书馆', '经济管理', 88.00, 4, 'F区-01-03'),
        ('978-7-111-00094-3', '从0到1', 'Peter Thiel', '中信出版社', '经济管理', 49.00, 6, 'F区-01-04'),
        ('978-7-111-00095-0', '创新者的窘境', 'Clayton M. Christensen', '中信出版社', '经济管理', 59.00, 5, 'F区-01-05'),
        # 数学科学 96-100
        ('978-7-111-00096-7', '高等数学（第七版）', '同济大学数学系', '高等教育出版社', '数学', 56.00, 8, 'F区-02-01'),
        ('978-7-111-00097-4', '线性代数及其应用', 'David C. Lay', '机械工业出版社', '数学', 79.00, 5, 'F区-02-02'),
        ('978-7-111-00098-1', '概率论与数理统计', '陈希孺', '中国科学技术大学出版社', '数学', 69.00, 5, 'F区-02-03'),
        ('978-7-111-00099-8', '时间简史', 'Stephen Hawking', '湖南科学技术出版社', '自然科学', 45.00, 6, 'F区-02-04'),
        ('978-7-111-00100-1', '上帝掷骰子吗：量子物理史话', '曹天元', '北京联合出版公司', '自然科学', 49.00, 6, 'F区-02-05'),
    ]


# ---- 数据库初始化 ----

def init_db():
    if USE_MYSQL:
        return

    db = get_db()
    cur = db.cursor()

    cur.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(50) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL,
            name VARCHAR(100) NOT NULL,
            role VARCHAR(20) NOT NULL DEFAULT 'librarian',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            isbn VARCHAR(20) NOT NULL UNIQUE,
            title VARCHAR(200) NOT NULL,
            author VARCHAR(100) NOT NULL,
            publisher VARCHAR(100),
            category VARCHAR(50),
            price REAL DEFAULT 0.00,
            total_copies INTEGER DEFAULT 1,
            available_copies INTEGER DEFAULT 1,
            location VARCHAR(50),
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS readers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reader_no VARCHAR(20) NOT NULL UNIQUE,
            name VARCHAR(100) NOT NULL,
            password VARCHAR(255) NOT NULL DEFAULT '',
            gender VARCHAR(10) DEFAULT '其他',
            phone VARCHAR(20),
            email VARCHAR(100),
            address VARCHAR(200),
            max_borrow INTEGER DEFAULT 5,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS borrow_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id INTEGER NOT NULL,
            reader_id INTEGER NOT NULL,
            borrow_date DATE NOT NULL,
            due_date DATE NOT NULL,
            return_date DATE,
            status VARCHAR(20) DEFAULT 'borrowed',
            operator_id INTEGER,
            FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE,
            FOREIGN KEY (reader_id) REFERENCES readers(id) ON DELETE CASCADE,
            FOREIGN KEY (operator_id) REFERENCES users(id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS operation_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username VARCHAR(50),
            action VARCHAR(20) NOT NULL,
            book_id INTEGER,
            book_title VARCHAR(200),
            reader_id INTEGER,
            reader_name VARCHAR(100),
            borrow_record_id INTEGER,
            detail TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
        );

        CREATE INDEX IF NOT EXISTS idx_logs_action ON operation_logs(action);
        CREATE INDEX IF NOT EXISTS idx_logs_created_at ON operation_logs(created_at);
        CREATE INDEX IF NOT EXISTS idx_logs_book_id ON operation_logs(book_id);
        CREATE INDEX IF NOT EXISTS idx_logs_reader_id ON operation_logs(reader_id);
    """)

    cur.execute("SELECT COUNT(*) as cnt FROM books")
    if cur.fetchone()[0] == 0:
        books = get_sample_books()
        cur.executemany(
            "INSERT INTO books (isbn, title, author, publisher, category, price, total_copies, available_copies, location) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [(b[0], b[1], b[2], b[3], b[4], b[5], b[6], b[6], b[7]) for b in books]
        )

        # 示例读者（有密码的为自助注册用户）
        sample_readers = [
            ('R20240001', '张三', generate_password_hash('123456'), '男', '13800138001', 'zhangsan@example.com', '北京市海淀区中关村大街1号', 5),
            ('R20240002', '李四', generate_password_hash('123456'), '女', '13800138002', 'lisi@example.com', '北京市朝阳区望京街道2号', 5),
            ('R20240003', '王五', generate_password_hash('123456'), '男', '13800138003', 'wangwu@example.com', '上海市浦东新区张江路3号', 5),
            ('R20240004', '赵六', generate_password_hash('123456'), '女', '13800138004', 'zhaoliu@example.com', '广州市天河区体育西路4号', 3),
            ('R20240005', '孙七', generate_password_hash('123456'), '男', '13800138005', 'sunqi@example.com', '深圳市南山区科技园5号', 5),
            ('R20240006', '周八', generate_password_hash('123456'), '女', '13800138006', 'zhouba@example.com', '杭州市西湖区文三路6号', 5),
            ('R20240007', '吴九', generate_password_hash('123456'), '男', '13800138007', 'wujiu@example.com', '成都市武侯区天府大道7号', 3),
            ('R20240008', '郑十', generate_password_hash('123456'), '女', '13800138008', 'zhengshi@example.com', '武汉市洪山区珞喻路8号', 5),
        ]
        cur.executemany(
            "INSERT INTO readers (reader_no, name, password, gender, phone, email, address, max_borrow) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)", sample_readers
        )

        # 示例借阅记录
        cur.execute("INSERT INTO borrow_records (book_id, reader_id, borrow_date, due_date, return_date, status) VALUES (?,?,?,?,?,?)",
                    (37, 1, '2024-11-01', '2024-12-01', '2024-11-28', 'returned'))
        cur.execute("INSERT INTO borrow_records (book_id, reader_id, borrow_date, due_date, return_date, status) VALUES (?,?,?,?,?,?)",
                    (29, 2, '2024-11-10', '2024-12-10', '2024-12-05', 'returned'))
        cur.execute("INSERT INTO borrow_records (book_id, reader_id, borrow_date, due_date, return_date, status) VALUES (?,?,?,?,?,?)",
                    (71, 1, '2024-10-15', '2024-11-15', '2024-11-14', 'returned'))
        cur.execute("INSERT INTO borrow_records (book_id, reader_id, borrow_date, due_date, status) VALUES (?,?,?,?,?)",
                    (1, 3, '2024-12-01', '2024-12-31', 'borrowed'))
        cur.execute("INSERT INTO borrow_records (book_id, reader_id, borrow_date, due_date, status) VALUES (?,?,?,?,?)",
                    (71, 1, '2024-12-15', '2025-01-14', 'borrowed'))
        cur.execute("UPDATE books SET available_copies = available_copies - 1 WHERE id = 1")
        cur.execute("UPDATE books SET available_copies = available_copies - 1 WHERE id = 71")

        # 示例操作日志
        cur.executemany(
            "INSERT INTO operation_logs (user_id, username, action, book_id, book_title, reader_id, reader_name, borrow_record_id, detail, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (None, 'root', 'borrow', 37, 'JavaScript高级程序设计（第4版）', 1, '张三', 1,
                 '借阅: 读者「张三」借阅《JavaScript高级程序设计（第4版）》，借期2024-11-01至2024-12-01', '2024-11-01 09:15:00'),
                (None, 'root', 'return', 37, 'JavaScript高级程序设计（第4版）', 1, '张三', 1,
                 '归还: 读者「张三」归还《JavaScript高级程序设计（第4版）》，按期归还', '2024-11-28 14:30:00'),
                (None, 'root', 'borrow', 29, 'Python编程：从入门到实践（第3版）', 2, '李四', 2,
                 '借阅: 读者「李四」借阅《Python编程：从入门到实践（第3版）》', '2024-11-10 10:00:00'),
                (None, 'root', 'return', 29, 'Python编程：从入门到实践（第3版）', 2, '李四', 2,
                 '归还: 读者「李四」归还《Python编程：从入门到实践（第3版）》，按期归还', '2024-12-05 16:20:00'),
                (None, 'root', 'borrow', 71, '百年孤独', 1, '张三', 3,
                 '借阅: 读者「张三」借阅《百年孤独》', '2024-10-15 08:45:00'),
                (None, 'root', 'return', 71, '百年孤独', 1, '张三', 3,
                 '归还: 读者「张三」归还《百年孤独》，按期归还', '2024-11-14 11:10:00'),
                (None, 'root', 'borrow', 1, '深入理解计算机系统（原书第3版）', 3, '王五', 4,
                 '借阅: 读者「王五」借阅《深入理解计算机系统（原书第3版）》', '2024-12-01 15:30:00'),
                (None, 'root', 'borrow', 71, '百年孤独', 1, '张三', 5,
                 '借阅: 读者「张三」借阅《百年孤独》，借期2024-12-15至2025-01-14', '2024-12-15 13:00:00'),
            ]
        )

    db.commit()
    db.close()


def init_admin_user():
    db = get_db()
    cur = db.cursor()
    ph = db.placeholder()
    cur.execute(f"SELECT COUNT(*) as cnt FROM users WHERE username = {ph}", ('root',))
    row = cur.fetchone()
    cnt = row[0] if not USE_MYSQL else row['cnt']
    if cnt == 0:
        cur.execute(
            f"INSERT INTO users (username, password, name, role) VALUES ({ph}, {ph}, {ph}, {ph})",
            ('root', generate_password_hash('1234'), '系统管理员', 'admin')
        )
        db.commit()
        print("管理员已创建 - 用户名: root  密码: 1234")
    db.close()


# ---- 装饰器 ----

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'admin':
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated


def reader_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'reader_id' not in session:
            return redirect(url_for('reader_login_page'))
        return f(*args, **kwargs)
    return decorated


# ---- 日志 ----

def write_log(action, book_id=None, book_title=None, reader_id=None, reader_name=None, record_id=None, detail=None):
    try:
        db = get_db()
        cur = db.cursor()
        ph = db.placeholder()
        nm = db.now()
        user_id = session.get('user_id') or session.get('reader_id')
        username = session.get('username') or session.get('reader_name', '读者')
        cur.execute(f"""
            INSERT INTO operation_logs (user_id, username, action, book_id, book_title,
                                         reader_id, reader_name, borrow_record_id, detail, created_at)
            VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {nm})
        """, (user_id, username, action, book_id, book_title, reader_id, reader_name, record_id, detail))
        db.commit()
        db.close()
    except Exception as e:
        print(f"日志写入失败: {e}")


# ==================== 首页 ====================

@app.route('/')
def index():
    return render_template('index.html')


# ==================== 管理员后台 ====================

@app.route('/login')
def login_page():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))


@app.route('/dashboard')
@admin_required
def dashboard():
    try:
        db = get_db()
        cur = db.cursor()
        cd = db.curdate()
        cur.execute("SELECT COUNT(*) as cnt FROM books")
        book_count = fetch_one_dict(cur)['cnt']
        cur.execute("SELECT COUNT(*) as cnt FROM readers")
        reader_count = fetch_one_dict(cur)['cnt']
        cur.execute("SELECT COUNT(*) as cnt FROM borrow_records WHERE status = 'borrowed'")
        borrowing_count = fetch_one_dict(cur)['cnt']
        cur.execute(f"SELECT COUNT(*) as cnt FROM borrow_records WHERE status = 'borrowed' AND due_date < {cd}")
        overdue_count = fetch_one_dict(cur)['cnt']
        cur.execute("""
            SELECT br.*, b.title as book_title, r.name as reader_name
            FROM borrow_records br JOIN books b ON br.book_id = b.id JOIN readers r ON br.reader_id = r.id
            ORDER BY br.id DESC LIMIT 10
        """)
        recent_records = fetch_all_dict(cur)
        cur.execute("SELECT * FROM operation_logs ORDER BY id DESC LIMIT 8")
        recent_logs = fetch_all_dict(cur)
        db.close()
        return render_template('dashboard.html',
                               book_count=book_count, reader_count=reader_count,
                               borrowing_count=borrowing_count, overdue_count=overdue_count,
                               recent_records=recent_records, recent_logs=recent_logs)
    except Exception as e:
        return f"数据库连接失败: {e}"


@app.route('/books')
@admin_required
def books_page():
    return render_template('books.html')


@app.route('/readers')
@admin_required
def readers_page():
    return render_template('readers.html')


@app.route('/borrow')
@admin_required
def borrow_page():
    return render_template('borrow.html')


# ==================== 管理员 API ====================

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')
    if not username or not password:
        return jsonify({'success': False, 'message': '用户名和密码不能为空'})
    try:
        db = get_db()
        cur = db.cursor()
        ph = db.placeholder()
        cur.execute(f"SELECT * FROM users WHERE username = {ph}", (username,))
        user = fetch_one_dict(cur)
        db.close()
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['name'] = user['name']
            session['role'] = user['role']
            return jsonify({'success': True, 'message': '登录成功', 'redirect': '/dashboard'})
        else:
            return jsonify({'success': False, 'message': '用户名或密码错误'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'登录失败: {e}'})


@app.route('/api/current_user')
@admin_required
def api_current_user():
    return jsonify({'username': session.get('username'), 'name': session.get('name'), 'role': session.get('role')})


# ---- 图书管理 API ----

@app.route('/api/books', methods=['GET'])
def api_get_books():
    if 'user_id' not in session and 'reader_id' not in session:
        return jsonify({'success': False, 'message': '未登录'}), 401
    keyword = request.args.get('keyword', '')
    category = request.args.get('category', '')
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 10))
    offset = (page - 1) * page_size
    try:
        db = get_db()
        cur = db.cursor()
        ph = db.placeholder()
        conditions, params = [], []
        if keyword:
            conditions.append(f"(title LIKE {ph} OR author LIKE {ph} OR isbn LIKE {ph} OR publisher LIKE {ph})")
            kw = f'%{keyword}%'
            params.extend([kw, kw, kw, kw])
        if category:
            conditions.append(f"category = {ph}")
            params.append(category)
        where = 'WHERE ' + ' AND '.join(conditions) if conditions else ''
        cur.execute(f"SELECT COUNT(*) as total FROM books {where}", params)
        total = fetch_one_dict(cur)['total']
        cur.execute(f"SELECT * FROM books {where} ORDER BY id ASC LIMIT {ph} OFFSET {ph}", params + [page_size, offset])
        books = fetch_all_dict(cur)
        db.close()
        return jsonify({'success': True, 'data': books, 'total': total})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/books', methods=['POST'])
@admin_required
def api_add_book():
    data = request.get_json()
    for f in ['isbn', 'title', 'author']:
        if not data.get(f): return jsonify({'success': False, 'message': f'{f} 不能为空'})
    try:
        db = get_db()
        cur = db.cursor()
        ph = db.placeholder()
        total = int(data.get('total_copies', 1))
        cur.execute(f"""INSERT INTO books (isbn, title, author, publisher, category, price,
                       total_copies, available_copies, location, description)
                       VALUES ({ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph})""",
                    (data['isbn'], data['title'], data['author'], data.get('publisher', ''),
                     data.get('category', ''), float(data.get('price', 0)), total, total,
                     data.get('location', ''), data.get('description', '')))
        db.commit()
        db.close()
        write_log('add_book', book_title=data['title'], detail=f"添加图书「{data['title']}」")
        return jsonify({'success': True, 'message': '添加成功'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/books/<int:book_id>', methods=['PUT'])
@admin_required
def api_update_book(book_id):
    data = request.get_json()
    try:
        db = get_db()
        cur = db.cursor()
        ph = db.placeholder()
        cur.execute(f"SELECT * FROM books WHERE id = {ph}", (book_id,))
        old = fetch_one_dict(cur)
        if not old: db.close(); return jsonify({'success': False, 'message': '图书不存在'})
        total = int(data.get('total_copies', 1))
        cur.execute(f"""UPDATE books SET isbn={ph}, title={ph}, author={ph}, publisher={ph},
                       category={ph}, price={ph}, total_copies={ph}, location={ph}, description={ph}
                       WHERE id={ph}""",
                    (data.get('isbn'), data.get('title'), data.get('author'), data.get('publisher', ''),
                     data.get('category', ''), float(data.get('price', 0)), total,
                     data.get('location', ''), data.get('description', ''), book_id))
        db.commit()
        db.close()
        write_log('edit_book', book_id=book_id, book_title=data.get('title', old['title']),
                  detail=f"编辑图书「{old['title']}」")
        return jsonify({'success': True, 'message': '更新成功'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/books/<int:book_id>', methods=['DELETE'])
@admin_required
def api_delete_book(book_id):
    try:
        db = get_db()
        cur = db.cursor()
        ph = db.placeholder()
        cur.execute(f"SELECT title FROM books WHERE id = {ph}", (book_id,))
        b = fetch_one_dict(cur)
        title = b['title'] if b else '未知'
        cur.execute(f"DELETE FROM books WHERE id = {ph}", (book_id,))
        db.commit()
        db.close()
        write_log('delete_book', book_id=book_id, book_title=title, detail=f"删除图书「{title}」")
        return jsonify({'success': True, 'message': '删除成功'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# ---- 读者管理 API（管理员用）----

@app.route('/api/readers', methods=['GET'])
@admin_required
def api_get_readers():
    keyword = request.args.get('keyword', '')
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 10))
    offset = (page - 1) * page_size
    try:
        db = get_db()
        cur = db.cursor()
        ph = db.placeholder()
        if keyword:
            kw = f'%{keyword}%'
            cur.execute(f"SELECT COUNT(*) as total FROM readers WHERE name LIKE {ph} OR reader_no LIKE {ph} OR phone LIKE {ph}", (kw, kw, kw))
            total = fetch_one_dict(cur)['total']
            cur.execute(f"SELECT * FROM readers WHERE name LIKE {ph} OR reader_no LIKE {ph} OR phone LIKE {ph} ORDER BY id DESC LIMIT {ph} OFFSET {ph}",
                        (kw, kw, kw, page_size, offset))
        else:
            cur.execute("SELECT COUNT(*) as total FROM readers"); total = fetch_one_dict(cur)['total']
            cur.execute(f"SELECT * FROM readers ORDER BY id DESC LIMIT {ph} OFFSET {ph}", (page_size, offset))
        readers = fetch_all_dict(cur)
        for r in readers:
            cur.execute(f"SELECT COUNT(*) as cnt FROM borrow_records WHERE reader_id = {ph} AND status = 'borrowed'", (r['id'],))
            r['borrowing_count'] = fetch_one_dict(cur)['cnt']
        db.close()
        return jsonify({'success': True, 'data': readers, 'total': total})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/readers', methods=['POST'])
@admin_required
def api_add_reader():
    data = request.get_json()
    if not data.get('name'): return jsonify({'success': False, 'message': '姓名不能为空'})
    try:
        db = get_db()
        cur = db.cursor()
        ph = db.placeholder()
        if not data.get('reader_no'):
            data['reader_no'] = f"R{datetime.now().strftime('%Y%m%d%H%M%S')}"
        cur.execute(f"SELECT COUNT(*) as cnt FROM readers WHERE reader_no = {ph}", (data['reader_no'],))
        if fetch_one_dict(cur)['cnt'] > 0: db.close(); return jsonify({'success': False, 'message': '编号已存在'})
        cur.execute(f"INSERT INTO readers (reader_no, name, password, gender, phone, email, address, max_borrow) VALUES ({ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph})",
                    (data['reader_no'], data['name'], generate_password_hash('123456'), data.get('gender', '其他'),
                     data.get('phone', ''), data.get('email', ''), data.get('address', ''), int(data.get('max_borrow', 5))))
        db.commit(); db.close()
        return jsonify({'success': True, 'message': '添加成功'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/readers/<int:reader_id>', methods=['PUT'])
@admin_required
def api_update_reader(reader_id):
    data = request.get_json()
    try:
        db = get_db()
        cur = db.cursor()
        ph = db.placeholder()
        cur.execute(f"SELECT * FROM readers WHERE id = {ph}", (reader_id,))
        if not fetch_one_dict(cur): db.close(); return jsonify({'success': False, 'message': '读者不存在'})
        cur.execute(f"SELECT COUNT(*) as cnt FROM readers WHERE reader_no = {ph} AND id != {ph}", (data['reader_no'], reader_id))
        if fetch_one_dict(cur)['cnt'] > 0: db.close(); return jsonify({'success': False, 'message': '编号已被使用'})
        cur.execute(f"UPDATE readers SET reader_no={ph}, name={ph}, gender={ph}, phone={ph}, email={ph}, address={ph}, max_borrow={ph} WHERE id={ph}",
                    (data['reader_no'], data['name'], data.get('gender', '其他'), data.get('phone', ''),
                     data.get('email', ''), data.get('address', ''), int(data.get('max_borrow', 5)), reader_id))
        db.commit(); db.close()
        return jsonify({'success': True, 'message': '更新成功'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/readers/<int:reader_id>', methods=['DELETE'])
@admin_required
def api_delete_reader(reader_id):
    try:
        db = get_db()
        cur = db.cursor()
        ph = db.placeholder()
        cur.execute(f"SELECT COUNT(*) as cnt FROM borrow_records WHERE reader_id = {ph} AND status = 'borrowed'", (reader_id,))
        if fetch_one_dict(cur)['cnt'] > 0: db.close(); return jsonify({'success': False, 'message': '还有未归还的图书'})
        cur.execute(f"DELETE FROM readers WHERE id = {ph}", (reader_id,))
        db.commit(); db.close()
        return jsonify({'success': True, 'message': '删除成功'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# ---- 借阅管理 API ----

@app.route('/api/borrow', methods=['GET'])
def api_get_borrow_records():
    if 'user_id' not in session and 'reader_id' not in session:
        return jsonify({'success': False, 'message': '未登录'}), 401
    status = request.args.get('status', '')
    keyword = request.args.get('keyword', '')
    reader_id_filter = request.args.get('reader_id', '')
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 10))
    offset = (page - 1) * page_size
    try:
        db = get_db()
        cur = db.cursor()
        ph = db.placeholder()
        cd = db.curdate()
        conditions, params = [], []
        if status:
            if status == 'overdue': conditions.append(f"(br.status = 'borrowed' AND br.due_date < {cd})")
            else: conditions.append(f"br.status = {ph}"); params.append(status)
        if keyword:
            conditions.append(f"(b.title LIKE {ph} OR b.isbn LIKE {ph} OR r.name LIKE {ph})")
            kw = f'%{keyword}%'; params.extend([kw, kw, kw])
        if reader_id_filter:
            conditions.append(f"br.reader_id = {ph}"); params.append(reader_id_filter)
        where = 'WHERE ' + ' AND '.join(conditions) if conditions else ''
        cur.execute(f"SELECT COUNT(*) as total FROM borrow_records br JOIN books b ON br.book_id=b.id JOIN readers r ON br.reader_id=r.id {where}", params)
        total = fetch_one_dict(cur)['total']
        cur.execute(f"""SELECT br.*, b.title as book_title, b.isbn as book_isbn, r.name as reader_name, r.reader_no
                       FROM borrow_records br JOIN books b ON br.book_id=b.id JOIN readers r ON br.reader_id=r.id
                       {where} ORDER BY br.id DESC LIMIT {ph} OFFSET {ph}""", params + [page_size, offset])
        records = fetch_all_dict(cur)
        for rec in records:
            if rec['status'] == 'borrowed' and rec['due_date']:
                due = rec['due_date']
                if isinstance(due, str): due = datetime.strptime(due, '%Y-%m-%d').date()
                if due < datetime.now().date(): rec['status'] = 'overdue'
        db.close()
        return jsonify({'success': True, 'data': records, 'total': total})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/borrow', methods=['POST'])
def api_borrow_book():
    if 'user_id' not in session and 'reader_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'}), 401
    data = request.get_json()
    reader_id = data.get('reader_id')
    book_id = data.get('book_id')
    borrow_days = int(data.get('borrow_days', 30))
    if not reader_id or not book_id: return jsonify({'success': False, 'message': '参数不完整'})
    try:
        db = get_db()
        cur = db.cursor()
        ph = db.placeholder()
        cur.execute(f"SELECT * FROM readers WHERE id = {ph}", (reader_id,))
        reader = fetch_one_dict(cur)
        if not reader: db.close(); return jsonify({'success': False, 'message': '读者不存在'})
        cur.execute(f"SELECT * FROM books WHERE id = {ph}", (book_id,))
        book = fetch_one_dict(cur)
        if not book: db.close(); return jsonify({'success': False, 'message': '图书不存在'})
        if book['available_copies'] <= 0: db.close(); return jsonify({'success': False, 'message': '该图书已全部借出'})
        cur.execute(f"SELECT COUNT(*) as cnt FROM borrow_records WHERE reader_id = {ph} AND status = 'borrowed'", (reader_id,))
        if fetch_one_dict(cur)['cnt'] >= reader['max_borrow']:
            db.close(); return jsonify({'success': False, 'message': f"已借满（上限{reader['max_borrow']}本）"})
        cur.execute(f"SELECT COUNT(*) as cnt FROM borrow_records WHERE reader_id = {ph} AND book_id = {ph} AND status = 'borrowed'", (reader_id, book_id))
        if fetch_one_dict(cur)['cnt'] > 0: db.close(); return jsonify({'success': False, 'message': '已借过此书尚未归还'})
        today = datetime.now().date()
        due_date = today + timedelta(days=borrow_days)
        operator_id = session.get('user_id') or session.get('reader_id')
        cur.execute(f"INSERT INTO borrow_records (book_id, reader_id, borrow_date, due_date, status, operator_id) VALUES ({ph},{ph},{ph},{ph},'borrowed',{ph})",
                    (book_id, reader_id, today.strftime('%Y-%m-%d'), due_date.strftime('%Y-%m-%d'), operator_id))
        record_id = cur.lastrowid
        cur.execute(f"UPDATE books SET available_copies = available_copies - 1 WHERE id = {ph}", (book_id,))
        db.commit(); db.close()
        detail = f"借阅: 读者「{reader['name']}」借阅《{book['title']}》，{today}至{due_date}，共{borrow_days}天"
        write_log('borrow', book_id=book_id, book_title=book['title'], reader_id=reader_id, reader_name=reader['name'], record_id=record_id, detail=detail)
        return jsonify({'success': True, 'message': '借阅成功'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/return/<int:record_id>', methods=['POST'])
def api_return_book(record_id):
    if 'user_id' not in session and 'reader_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'}), 401
    try:
        db = get_db()
        cur = db.cursor()
        ph = db.placeholder()
        cd = db.curdate()
        cur.execute(f"SELECT br.*, b.title as book_title, r.name as reader_name FROM borrow_records br JOIN books b ON br.book_id=b.id JOIN readers r ON br.reader_id=r.id WHERE br.id = {ph}", (record_id,))
        record = fetch_one_dict(cur)
        if not record: db.close(); return jsonify({'success': False, 'message': '记录不存在'})
        if record['status'] == 'returned': db.close(); return jsonify({'success': False, 'message': '已归还'})
        cur.execute(f"UPDATE borrow_records SET status='returned', return_date={cd} WHERE id={ph}", (record_id,))
        cur.execute(f"UPDATE books SET available_copies = available_copies + 1 WHERE id = {ph}", (record['book_id'],))
        db.commit(); db.close()
        due_date = record['due_date']
        if isinstance(due_date, str): due_date = datetime.strptime(due_date, '%Y-%m-%d').date()
        overdue_days = (datetime.now().date() - due_date).days if datetime.now().date() > due_date else 0
        status_text = f"逾期{overdue_days}天" if overdue_days > 0 else "按期归还"
        detail = f"归还: 读者「{record['reader_name']}」归还《{record['book_title']}》，{status_text}"
        write_log('return', book_id=record['book_id'], book_title=record['book_title'],
                  reader_id=record['reader_id'], reader_name=record['reader_name'], record_id=record_id, detail=detail)
        return jsonify({'success': True, 'message': '归还成功'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/logs', methods=['GET'])
@admin_required
def api_get_logs():
    action = request.args.get('action', '')
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 15))
    offset = (page - 1) * page_size
    try:
        db = get_db()
        cur = db.cursor()
        ph = db.placeholder()
        if action:
            cur.execute(f"SELECT COUNT(*) as total FROM operation_logs WHERE action = {ph}", (action,))
            total = fetch_one_dict(cur)['total']
            cur.execute(f"SELECT * FROM operation_logs WHERE action = {ph} ORDER BY id DESC LIMIT {ph} OFFSET {ph}", (action, page_size, offset))
        else:
            cur.execute("SELECT COUNT(*) as total FROM operation_logs"); total = fetch_one_dict(cur)['total']
            cur.execute(f"SELECT * FROM operation_logs ORDER BY id DESC LIMIT {ph} OFFSET {ph}", (page_size, offset))
        logs = fetch_all_dict(cur); db.close()
        return jsonify({'success': True, 'data': logs, 'total': total})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/categories', methods=['GET'])
def api_get_categories():
    try:
        db = get_db(); cur = db.cursor()
        cur.execute("SELECT DISTINCT category FROM books WHERE category != '' ORDER BY category")
        cats = [row['category'] if USE_MYSQL else row[0] for row in cur.fetchall()]
        db.close()
        return jsonify({'success': True, 'data': cats})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# ==================== 读者自助系统 ====================

@app.route('/reader')
def reader_login_page():
    if 'reader_id' in session:
        return redirect(url_for('reader_dashboard'))
    return render_template('reader_login.html')


@app.route('/reader/logout')
def reader_logout():
    session.clear()
    return redirect(url_for('reader_login_page'))


@app.route('/api/reader/register', methods=['POST'])
def api_reader_register():
    data = request.get_json()
    name = data.get('name', '').strip()
    password = data.get('password', '')
    phone = data.get('phone', '').strip()
    email = data.get('email', '').strip()
    if not name or len(name) < 2: return jsonify({'success': False, 'message': '姓名至少2个字符'})
    if not password or len(password) < 4: return jsonify({'success': False, 'message': '密码至少4位'})
    try:
        db = get_db()
        cur = db.cursor()
        ph = db.placeholder()
        reader_no = f"R{datetime.now().strftime('%Y%m%d%H%M%S')}"
        cur.execute(f"INSERT INTO readers (reader_no, name, password, phone, email) VALUES ({ph},{ph},{ph},{ph},{ph})",
                    (reader_no, name, generate_password_hash(password), phone, email))
        db.commit()
        reader_id = cur.lastrowid
        db.close()
        session['reader_id'] = reader_id
        session['reader_name'] = name
        session['reader_no'] = reader_no
        return jsonify({'success': True, 'message': f'注册成功！欢迎 {name}，您的编号是 {reader_no}'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'注册失败: {e}'})


@app.route('/api/reader/login', methods=['POST'])
def api_reader_login():
    data = request.get_json()
    reader_no = data.get('reader_no', '').strip()
    password = data.get('password', '')
    if not reader_no or not password: return jsonify({'success': False, 'message': '请输入读者编号和密码'})
    try:
        db = get_db()
        cur = db.cursor()
        ph = db.placeholder()
        cur.execute(f"SELECT * FROM readers WHERE reader_no = {ph}", (reader_no,))
        reader = fetch_one_dict(cur)
        db.close()
        if reader and reader.get('password') and check_password_hash(reader['password'], password):
            session['reader_id'] = reader['id']
            session['reader_name'] = reader['name']
            session['reader_no'] = reader['reader_no']
            return jsonify({'success': True, 'message': '登录成功'})
        else:
            return jsonify({'success': False, 'message': '读者编号或密码错误'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'登录失败: {e}'})


@app.route('/reader/dashboard')
@reader_required
def reader_dashboard():
    try:
        db = get_db()
        cur = db.cursor()
        ph = db.placeholder()
        cd = db.curdate()
        reader_id = session['reader_id']

        cur.execute(f"SELECT COUNT(*) as cnt FROM borrow_records WHERE reader_id = {ph} AND status = 'borrowed'", (reader_id,))
        borrowing_count = fetch_one_dict(cur)['cnt']

        cur.execute(f"SELECT * FROM readers WHERE id = {ph}", (reader_id,))
        reader_info = fetch_one_dict(cur)

        cur.execute(f"""SELECT br.*, b.title as book_title, b.isbn as book_isbn
                       FROM borrow_records br JOIN books b ON br.book_id=b.id
                       WHERE br.reader_id = {ph} AND br.status = 'borrowed'
                       ORDER BY br.due_date ASC""", (reader_id,))
        active_borrows = fetch_all_dict(cur)
        for rec in active_borrows:
            if rec['due_date']:
                due = rec['due_date']
                if isinstance(due, str): due = datetime.strptime(due, '%Y-%m-%d').date()
                if due < datetime.now().date(): rec['status'] = 'overdue'

        cur.execute(f"""SELECT br.*, b.title as book_title, b.isbn as book_isbn
                       FROM borrow_records br JOIN books b ON br.book_id=b.id
                       WHERE br.reader_id = {ph}
                       ORDER BY br.id DESC LIMIT 20""", (reader_id,))
        all_records = fetch_all_dict(cur)
        for rec in all_records:
            if rec['status'] == 'borrowed' and rec['due_date']:
                due = rec['due_date']
                if isinstance(due, str): due = datetime.strptime(due, '%Y-%m-%d').date()
                if due < datetime.now().date(): rec['status'] = 'overdue'

        db.close()
        return render_template('reader_dashboard.html',
                               reader=reader_info, borrowing_count=borrowing_count,
                               active_borrows=active_borrows, all_records=all_records)
    except Exception as e:
        return f"加载失败: {e}"


@app.route('/reader/books')
@reader_required
def reader_books():
    return render_template('reader_books.html')


@app.route('/api/reader/info')
@reader_required
def api_reader_info():
    try:
        db = get_db()
        cur = db.cursor()
        ph = db.placeholder()
        cur.execute(f"SELECT * FROM readers WHERE id = {ph}", (session['reader_id'],))
        reader = fetch_one_dict(cur)
        cur.execute(f"SELECT COUNT(*) as cnt FROM borrow_records WHERE reader_id = {ph} AND status = 'borrowed'", (session['reader_id'],))
        reader['borrowing_count'] = fetch_one_dict(cur)['cnt']
        db.close()
        reader.pop('password', None)
        return jsonify({'success': True, 'data': reader})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# ==================== 启动 ====================

@app.route('/healthz')
def healthz():
    try:
        db = get_db()
        cur = db.cursor()
        cur.execute("SELECT COUNT(*) as cnt FROM books")
        book_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) as cnt FROM readers")
        reader_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) as cnt FROM users")
        user_count = cur.fetchone()[0]
        db.close()
        return jsonify({
            'status': 'ok',
            'database': 'MySQL' if USE_MYSQL else 'SQLite',
            'books': book_count,
            'readers': reader_count,
            'users': user_count
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# 模块加载时初始化数据库（gunicorn 导入时需要）
import sys
try:
    init_db()
    init_admin_user()
except Exception as e:
    print(f"[STARTUP ERROR] {e}", file=sys.stderr)
    import traceback
    traceback.print_exc()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("=" * 50)
    print("  图书馆管理系统")
    print(f"  数据库: {'MySQL' if USE_MYSQL else 'SQLite'}")
    print("=" * 50)
    print(f"  管理后台: http://localhost:{port}/login       (root / 1234)")
    print(f"  读者入口: http://localhost:{port}/reader      (自助注册)")
    print("=" * 50)
    app.run(debug=not os.environ.get('RENDER'), host='0.0.0.0', port=port)
