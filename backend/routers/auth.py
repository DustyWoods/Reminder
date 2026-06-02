from fastapi import APIRouter

from models import UserRegisterRequest, UserLoginRequest, UserDeleteRequest, AuthResponse, UserResponse
from services import auth_service
from utils import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse)
async def register(request: UserRegisterRequest) -> AuthResponse:
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
    logger.info(f"Login request for username: {request.username}")
    
    success, message, user = auth_service.login(
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
        user=UserResponse(id=user.id, username=user.username)
    )


@router.delete("/delete", response_model=AuthResponse)
async def delete_user(request: UserDeleteRequest) -> AuthResponse:
    logger.info(f"Delete user request for user_id: {request.user_id}")
    
    success, message = auth_service.delete_user(user_id=request.user_id)
    
    if not success:
        logger.warning(f"Delete user failed: {message}")
        return AuthResponse(success=False, message=message)
    
    logger.info(f"User deleted successfully: {request.user_id}")
    
    return AuthResponse(
        success=True,
        message=message
    )