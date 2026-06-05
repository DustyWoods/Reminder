import asyncio
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Request

from models import (
    VoiceStreamStartRequest,
    VoiceStreamEndRequest,
    ReminderResponse,
)
from services import asr_manager, SHERPA_AVAILABLE
from agent import get_task_agent
from utils import get_logger, create_task

logger = get_logger(__name__)

router = APIRouter(prefix="/api/voice", tags=["voice"])

# 存储活跃的语音识别会话
active_sessions: Dict[str, Dict[str, Any]] = {}


@router.post("/start")
async def start_voice_session(request: VoiceStreamStartRequest):
    """
    开始语音识别会话

    前端调用此接口初始化一个语音识别会话
    """
    try:
        await asr_manager.initialize()
        stream = asr_manager.create_stream()
        active_sessions[request.session_id] = {
            "stream": stream,
            "text": "",
            "is_active": True
        }
        logger.info(f"Voice session started: {request.session_id}")
        return {"session_id": request.session_id, "status": "started"}
    except Exception as e:
        logger.error(f"Failed to start voice session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/audio")
async def process_audio_chunk(request: Request, session_id: str):
    """
    处理音频数据块

    前端实时发送录音数据，后端进行 ASR 识别并返回中间结果
    """
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found or expired")

    session = active_sessions[session_id]
    if not session["is_active"]:
        raise HTTPException(status_code=400, detail="Session is not active")

    try:
        # 从请求体中获取二进制音频数据
        audio_data = await request.body()

        stream = session["stream"]

        # 导入 numpy（延迟导入避免模块加载问题）
        import numpy as np

        # 确保音频数据长度为偶数
        if len(audio_data) % 2 != 0:
            audio_data = audio_data[:-1]

        # 转换为 numpy 数组，然后归一化到 [-1, 1]
        int16_array = np.frombuffer(audio_data, dtype=np.int16)
        samples = (int16_array / 32768.0).astype(np.float32)

        # 将样本添加到识别流
        stream.accept_waveform(sample_rate=16000, waveform=samples)

        logger.info(f"Audio chunk processed: {len(samples)} samples")

        # 持续解码直到没有更多准备好处理的音频
        decode_count = 0
        while asr_manager.recognizer.is_ready(stream):
            asr_manager.recognizer.decode_stream(stream)
            decode_count += 1

        logger.info(f"Decoded {decode_count} times")

        # 获取当前识别结果
        current_text = asr_manager.recognizer.get_result(stream)

        # 如果识别到新文本，更新会话状态
        if current_text:
            session["text"] = current_text

        return {
            "session_id": session_id,
            "text": current_text,
            "is_final": False
        }

    except Exception as e:
        logger.error(f"Error processing audio chunk: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop")
async def stop_voice_session(request: VoiceStreamEndRequest, user_id: int):
    """
    停止语音识别会话，处理最终识别结果

    前端松开语音按键时调用此接口，后端完成识别并调用 LLM 进行任务提取
    """
    if request.session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found or expired")

    session = active_sessions[request.session_id]
    session["is_active"] = False

    try:
        stream = session["stream"]

        # 标记输入完成并处理剩余音频
        stream.input_finished()
        logger.info("Input finished for stream")

        # 解码剩余音频 - 需要多次迭代确保完全解码
        max_iterations = 50
        decode_count = 0
        for _ in range(max_iterations):
            if asr_manager.recognizer.is_ready(stream):
                asr_manager.recognizer.decode_stream(stream)
                decode_count += 1
            else:
                break

        logger.info(f"Decoded {decode_count} times after input_finished (max {max_iterations})")

        # 获取最终识别结果
        final_text = asr_manager.recognizer.get_result(stream)
        logger.info(f"Final recognized text: '{final_text}'")

        # 清理资源
        asr_manager.reset_stream(stream)
        asr_manager.free_stream(stream)

        # 从活跃会话中移除
        del active_sessions[request.session_id]

        logger.info(f"Voice session ended: {request.session_id}, recognized text: {final_text}")

        # 使用 Task Agent 处理识别文本，提取任务信息
        try:
            task_agent = get_task_agent()
            if task_agent.is_available():
                reminder = task_agent.invoke(final_text)
                
                # 保存任务到数据库
                task_id = create_task(
                    user_id=user_id,
                    title=reminder.title,
                    due_date=reminder.due_date,
                    description=reminder.description
                )
                
                logger.info(f"Task saved to database with id: {task_id}")
                
                return {
                    "session_id": request.session_id,
                    "text": final_text,
                    "is_final": True,
                    "task": {
                        "id": task_id,
                        "title": reminder.title,
                        "due_date": reminder.due_date,
                        "description": reminder.description,
                        "completed": False
                    }
                }
            else:
                return {
                    "session_id": request.session_id,
                    "text": final_text,
                    "is_final": True,
                    "error": "LLM service not available"
                }
        except Exception as e:
            logger.warning(f"LLM processing failed for session {request.session_id}: {str(e)}")
            return {
                "session_id": request.session_id,
                "text": final_text,
                "is_final": True,
                "error": f"Failed to process text into task: {str(e)}"
            }

    except Exception as e:
        logger.error(f"Error stopping voice session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cancel")
async def cancel_voice_session(request: VoiceStreamEndRequest):
    """
    取消语音识别会话

    前端可以在任何时候调用此接口取消当前语音输入
    """
    if request.session_id in active_sessions:
        session = active_sessions[request.session_id]
        stream = session["stream"]

        # 清理资源
        asr_manager.reset_stream(stream)
        asr_manager.free_stream(stream)
        del active_sessions[request.session_id]

        logger.info(f"Voice session cancelled: {request.session_id}")

    return {"session_id": request.session_id, "status": "cancelled"}
