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


auth_service = AuthService()