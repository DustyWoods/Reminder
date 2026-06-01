from fastapi import APIRouter

from .text import router as text_router
from .voice import router as voice_router
from .auth import router as auth_router

__all__ = ["text_router", "voice_router", "auth_router"]