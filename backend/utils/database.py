import sqlite3
import os
import hashlib
import secrets
from contextlib import contextmanager
from typing import Optional

from .logging import get_logger

logger = get_logger(__name__)

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
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            due_date TEXT NOT NULL,
            description TEXT,
            completed BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
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


def delete_user(user_id: int) -> bool:
    """删除用户"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        return cursor.rowcount > 0


# ============== 任务数据库操作 ==============

def create_task(user_id: int, title: str, due_date: str, description: str = None) -> int:
    """
    创建新任务
    
    Returns:
        任务ID
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO tasks (user_id, title, due_date, description) VALUES (?, ?, ?, ?)",
            (user_id, title, due_date, description)
        )
        conn.commit()
        return cursor.lastrowid


def get_tasks_by_user_id(user_id: int) -> list:
    """根据用户ID获取所有任务"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, user_id, title, due_date, description, completed, created_at FROM tasks WHERE user_id = ? ORDER BY due_date ASC",
            (user_id,)
        )
        rows = cursor.fetchall()
        tasks = []
        for row in rows:
            task = dict_from_row(row)
            if task and 'completed' in task:
                task['completed'] = bool(task['completed'])
            tasks.append(task)
        return tasks


def get_task_by_id(task_id: int, user_id: int = None) -> Optional[dict]:
    """根据任务ID获取任务"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if user_id:
            cursor.execute(
                "SELECT id, title, due_date, description, completed, created_at FROM tasks WHERE id = ? AND user_id = ?",
                (task_id, user_id)
            )
        else:
            cursor.execute(
                "SELECT id, title, due_date, description, completed, created_at FROM tasks WHERE id = ?",
                (task_id,)
            )
        row = cursor.fetchone()
        task = dict_from_row(row)
        if task and 'completed' in task:
            task['completed'] = bool(task['completed'])
        return task


def update_task(task_id: int, user_id: int, **kwargs) -> bool:
    """更新任务信息"""
    fields = []
    values = []
    
    if 'title' in kwargs:
        fields.append("title = ?")
        values.append(kwargs['title'])
    if 'due_date' in kwargs:
        fields.append("due_date = ?")
        values.append(kwargs['due_date'])
    if 'description' in kwargs:
        fields.append("description = ?")
        values.append(kwargs['description'])
    if 'completed' in kwargs:
        fields.append("completed = ?")
        values.append(kwargs['completed'])
    
    if not fields:
        return False
    
    values.extend([task_id, user_id])
    query = f"UPDATE tasks SET {', '.join(fields)} WHERE id = ? AND user_id = ?"
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, values)
        conn.commit()
        return cursor.rowcount > 0


def delete_task(task_id: int, user_id: int) -> bool:
    """删除任务"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE id = ? AND user_id = ?", (task_id, user_id))
        conn.commit()
        return cursor.rowcount > 0


def delete_all_tasks(user_id: int) -> bool:
    """删除用户所有任务"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE user_id = ?", (user_id,))
        conn.commit()
        return cursor.rowcount > 0
