from pydantic import BaseModel, field_validator, Field
from datetime import datetime


class ReminderRequest(BaseModel):
    """提醒创建请求"""
    text: str


class ReminderResponse(BaseModel):
    """提醒响应"""
    title: str
    due_date: str
    description: str

    @field_validator("due_date")
    @classmethod
    def validate_due_date(cls, v: str) -> str:
        try:
            datetime.strptime(v, "%Y-%m-%d %H:%M")
        except ValueError:
            raise ValueError("due_date 必须为 YYYY-MM-DD HH:MM 格式")
        return v


class VoiceStreamStartRequest(BaseModel):
    """开始语音识别会话请求"""
    session_id: str


class VoiceStreamEndRequest(BaseModel):
    """结束语音识别会话请求"""
    session_id: str


class VoiceRecognitionResult(BaseModel):
    """语音识别结果"""
    session_id: str
    text: str
    is_final: bool = False
    error: str | None = None


# ============== 用户认证相关模型 ==============

class UserRegisterRequest(BaseModel):
    """用户注册请求"""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=100)


class UserLoginRequest(BaseModel):
    """用户登录请求"""
    username: str
    password: str


class UserDeleteRequest(BaseModel):
    """用户删除请求"""
    user_id: int


class UserResponse(BaseModel):
    """用户响应"""
    id: int
    username: str


class AuthResponse(BaseModel):
    success: bool
    message: str
    user: UserResponse | None = None