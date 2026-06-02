from fastapi import APIRouter

from models import UserRegisterRequest, UserLoginRequest, AuthResponse, UserResponse
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