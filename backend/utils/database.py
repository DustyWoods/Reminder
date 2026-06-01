import sqlite3
import os
import hashlib
import secrets
from contextlib import contextmanager
from typing import Optional

from .logging import get_logger

logger = get_logger(__name__)

# 数据库文件路径
DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DB_PATH = os.path.join(DB_DIR, "reminder.db")


def init_db():
    """初始化数据库和表"""
    os.makedirs(DB_DIR, exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tokens (
            token TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    conn.commit()
    conn.close()
    
    _init_default_admin()
    
    logger.info(f"Database initialized at {DB_PATH}")


def _init_default_admin():
    """初始化默认管理员用户"""
    admin = get_user_by_username("admin")
    if admin:
        logger.info("Admin user already exists")
        return
    
    salt = generate_salt()
    password_hash = hash_password("admin123", salt)
    create_user("admin", password_hash, salt)
    logger.info("Default admin user created: username=admin, password=admin123")


# ============== 密码工具函数 ==============

def generate_salt() -> str:
    """生成盐值"""
    return secrets.token_hex(16)


def hash_password(password: str, salt: str) -> str:
    """哈希密码"""
    return hashlib.sha256((password + salt).encode()).hexdigest()


def verify_password(password: str, salt: str, password_hash: str) -> bool:
    """验证密码"""
    return hash_password(password, salt) == password_hash


# ============== 数据库连接管理 ==============

@contextmanager
def get_db_connection():
    """获取数据库连接的上下文管理器"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def dict_from_row(row: sqlite3.Row) -> dict:
    """将 sqlite3.Row 转换为字典"""
    if row is None:
        return None
    return dict(zip(row.keys(), row))


# ============== 用户数据库操作 ==============

def create_user(username: str, password_hash: str, salt: str) -> int:
    """
    创建新用户
    
    Returns:
        用户ID
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, password_hash, salt) VALUES (?, ?, ?)",
            (username, password_hash, salt)
        )
        conn.commit()
        return cursor.lastrowid


def get_user_by_username(username: str) -> Optional[dict]:
    """根据用户名获取用户"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, username, password_hash, salt FROM users WHERE username = ?",
            (username,)
        )
        row = cursor.fetchone()
        return dict_from_row(row)


def get_user_by_id(user_id: int) -> Optional[dict]:
    """根据ID获取用户"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, username, password_hash, salt FROM users WHERE id = ?",
            (user_id,)
        )
        row = cursor.fetchone()
        return dict_from_row(row)


def user_exists(username: str) -> bool:
    """检查用户名是否存在"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM users WHERE username = ?", (username,))
        return cursor.fetchone() is not None


# ============== Token 数据库操作 ==============

def create_token(user_id: int) -> str:
    """
    创建新token
    
    Returns:
        生成的token字符串
    """
    token = secrets.token_urlsafe(32)
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO tokens (token, user_id) VALUES (?, ?)",
            (token, user_id)
        )
        conn.commit()
    return token


def delete_token(token: str) -> bool:
    """删除token"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tokens WHERE token = ?", (token,))
        conn.commit()
        return cursor.rowcount > 0


def get_token_user_id(token: str) -> Optional[int]:
    """根据token获取用户ID"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM tokens WHERE token = ?", (token,))
        row = cursor.fetchone()
        return row[0] if row else None