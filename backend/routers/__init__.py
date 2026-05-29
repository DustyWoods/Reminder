from fastapi import APIRouter

from .reminder import router as reminder_router
from .voice import router as voice_router

__all__ = ["reminder_router", "voice_router"]
