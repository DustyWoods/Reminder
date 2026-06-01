from fastapi import APIRouter, HTTPException, Header

from models import UserRegisterRequest, UserLoginRequest, AuthResponse, UserResponse
from services import auth_service
from utils import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse)
async def register(request: UserRegisterRequest) -> AuthResponse:
    """
    用户注册接口
    
    Args:
        request: 注册请求（用户名、密码）
        
    Returns:
        AuthResponse: 包含成功状态、消息和用户信息
    """
    logger.info(f"Register request for username: {request.username}")
    
    success, message, user = auth_service.register(
        username=request.username,
        password=request.password
    )
    
    if not success:
        logger.warning(f"Registration failed: {message}")
        return AuthResponse(success=False, message=message)
    
    logger.info(f"Registration successful for username: {request.username}")
    
    return AuthResponse(
        success=True,
        message=message,
        user=UserResponse(id=user.id, username=user.username)
    )


@router.post("/login", response_model=AuthResponse)
async def login(request: UserLoginRequest) -> AuthResponse:
    """
    用户登录接口
    
    Args:
        request: 登录请求（用户名、密码）
        
    Returns:
        AuthResponse: 包含成功状态、消息、token 和用户信息
    """
    logger.info(f"Login request for username: {request.username}")
    
    success, message, token, user = auth_service.login(
        username=request.username,
        password=request.password
    )
    
    if not success:
        logger.warning(f"Login failed: {message}")
        return AuthResponse(success=False, message=message)
    
    logger.info(f"Login successful for username: {request.username}")
    
    return AuthResponse(
        success=True,
        message=message,
        user=UserResponse(id=user.id, username=user.username),
        token=token
    )


@router.post("/logout")
async def logout(authorization: str = Header(None)) -> AuthResponse:
    """
    用户登出接口
    
    Args:
        authorization: Bearer token
        
    Returns:
        AuthResponse: 包含成功状态和消息
    """
    if not authorization or not authorization.startswith("Bearer "):
        return AuthResponse(success=False, message="无效的 Token")
    
    token = authorization[7:]  # 去掉 "Bearer " 前缀
    
    if auth_service.logout(token):
        logger.info("Logout successful")
        return AuthResponse(success=True, message="登出成功")
    else:
        logger.warning("Logout failed: invalid token")
        return AuthResponse(success=False, message="无效的 Token")


@router.get("/check")
async def check_auth(authorization: str = Header(None)) -> AuthResponse:
    """
    检查认证状态接口
    
    Args:
        authorization: Bearer token
        
    Returns:
        AuthResponse: 包含成功状态、用户信息
    """
    if not authorization or not authorization.startswith("Bearer "):
        return AuthResponse(success=False, message="未登录")
    
    token = authorization[7:]  # 去掉 "Bearer " 前缀
    
    user_id = auth_service.verify_token(token)
    if not user_id:
        return AuthResponse(success=False, message="Token 已过期")
    
    user = auth_service.get_user_by_id(user_id)
    if not user:
        return AuthResponse(success=False, message="用户不存在")
    
    return AuthResponse(
        success=True,
        message="已登录",
        user=UserResponse(id=user.id, username=user.username),
        token=token
    )