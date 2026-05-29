from pydantic import BaseModel, field_validator
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
