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
    create_token,
    delete_token,
    get_token_user_id,
)

logger = get_logger(__name__)


@dataclass
class User:
    """用户数据类"""
    id: int
    username: str
    password_hash: str
    salt: str


class AuthService:
    """
    认证服务类
    
    职责：
    - 用户注册业务逻辑
    - 用户登录业务逻辑
    - Token 管理业务逻辑
    """

    def __init__(self):
        init_db()

    def register(self, username: str, password: str) -> tuple[bool, str, Optional[User]]:
        """
        注册新用户
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            (是否成功, 消息, 用户对象)
        """
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

    def login(self, username: str, password: str) -> tuple[bool, str, Optional[str], Optional[User]]:
        """
        用户登录
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            (是否成功, 消息, token, 用户对象)
        """
        user_data = get_user_by_username(username)
        if not user_data:
            return False, "用户名或密码错误", None, None

        if not verify_password(password, user_data['salt'], user_data['password_hash']):
            return False, "用户名或密码错误", None, None

        token = create_token(user_data['id'])
        logger.info(f"User logged in: {username}")

        user = User(
            id=user_data['id'],
            username=username,
            password_hash=user_data['password_hash'],
            salt=user_data['salt']
        )

        return True, "登录成功", token, user

    def logout(self, token: str) -> bool:
        """
        用户登出
        
        Args:
            token: 用户 token
            
        Returns:
            是否成功
        """
        result = delete_token(token)
        if result:
            logger.info("Logout successful")
        return result

    def verify_token(self, token: str) -> Optional[int]:
        """
        验证 token
        
        Args:
            token: 用户 token
            
        Returns:
            user_id 或 None
        """
        return get_token_user_id(token)

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """根据 ID 获取用户"""
        user_data = get_user_by_id(user_id)
        if not user_data:
            return None

        return User(
            id=user_data['id'],
            username=user_data['username'],
            password_hash=user_data['password_hash'],
            salt=user_data['salt']
        )


# 全局认证服务实例
auth_service = AuthService()