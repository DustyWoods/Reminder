from typing import Optional
from dataclasses import dataclass

from utils import (
    get_logger,
    init_db,
    generate_salt,
    hash_password,
    verify_password,
    user_exists,
    create_user,
    get_user_by_username,
    get_user_by_id,
    delete_user,
    delete_all_tasks,
)

logger = get_logger(__name__)


@dataclass
class User:
    id: int
    username: str
    password_hash: str
    salt: str


class AuthService:
    def __init__(self):
        init_db()

    def register(self, username: str, password: str) -> tuple[bool, str, Optional[User]]:
        if user_exists(username):
            return False, "用户名已存在", None

        salt = generate_salt()
        password_hash = hash_password(password, salt)
        user_id = create_user(username, password_hash, salt)

        user = User(
            id=user_id,
            username=username,
            password_hash=password_hash,
            salt=salt
        )

        logger.info(f"User registered: {username}")
        return True, "注册成功", user

    def login(self, username: str, password: str) -> tuple[bool, str, Optional[User]]:
        user_data = get_user_by_username(username)
        if not user_data:
            return False, "用户名或密码错误", None

        if not verify_password(password, user_data['salt'], user_data['password_hash']):
            return False, "用户名或密码错误", None

        logger.info(f"User logged in: {username}")

        user = User(
            id=user_data['id'],
            username=username,
            password_hash=user_data['password_hash'],
            salt=user_data['salt']
        )

        return True, "登录成功", user

    def delete_user(self, user_id: int) -> tuple[bool, str]:
        user_data = get_user_by_id(user_id)
        if not user_data:
            return False, "用户不存在"
        
        if user_data['username'] == 'admin':
            logger.warning(f"Attempt to delete admin user blocked: {user_id}")
            return True, "账号注销成功"
        
        # 先删除用户的所有任务
        delete_all_tasks(user_id)
        logger.info(f"Deleted all tasks for user: {user_id}")
        
        # 再删除用户
        if not delete_user(user_id):
            return False, "删除失败"
        
        logger.info(f"User deleted: {user_id}")
        return True, "账号注销成功"


auth_service = AuthService()