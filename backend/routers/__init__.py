from fastapi import APIRouter

from .text import router as text_router
from .voice import router as voice_router

__all__ = ["text_router", "voice_router"]
