from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, field_validator
from datetime import datetime
import os
import json
import logging
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Reminder Backend", version="1.0.0")

# 检查是否设置了有效的 API Key
USE_MOCK_MODE = not os.getenv("DEEPSEEK_API_KEY") or os.getenv("DEEPSEEK_API_KEY") == "your_api_key_here"

if not USE_MOCK_MODE:
    client = OpenAI(
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
    )

class ReminderRequest(BaseModel):
    text: str

class ReminderResponse(BaseModel):
    title: str
    due_date: str
    description: str
    @field_validator("due_date")
    def validate_due_date(cls, v):
        try:
            # 尝试解析，若失败则抛出异常
            datetime.strptime(v, "%Y-%m-%d %H:%M")
        except ValueError:
            raise ValueError("due_date 必须为 YYYY-MM-DD HH:MM 格式")
        return v

# 模拟数据生成函数（用于测试）
def generate_mock_reminder(text: str) -> ReminderResponse:
    from datetime import datetime, timedelta
    
    today = datetime.now()
    
    # 解析文本中的时间信息
    due_date = today + timedelta(days=1)  # 默认明天
    if "下周三" in text:
        days_ahead = (2 - today.weekday() + 7) % 7 + 7  # 下周三
        due_date = today + timedelta(days=days_ahead)
    elif "明天" in text:
        due_date = today + timedelta(days=1)
    elif "本周五" in text:
        days_ahead = (4 - today.weekday() + 7) % 7
        due_date = today + timedelta(days=days_ahead)
    elif "后天" in text:
        due_date = today + timedelta(days=2)
    
    # 解析时间
    if "下午3点" in text:
        due_date = due_date.replace(hour=15, minute=0)
    elif "早上9点" in text:
        due_date = due_date.replace(hour=9, minute=0)
    elif "下午5点" in text:
        due_date = due_date.replace(hour=17, minute=0)
    elif "晚上7点" in text:
        due_date = due_date.replace(hour=19, minute=0)
    else:
        due_date = due_date.replace(hour=12, minute=0)
    
    return ReminderResponse(
        title=text[:10] + "任务",
        due_date=due_date.strftime("%Y-%m-%d %H:%M"),
        description=text
    )

def extract_reminder_from_text(text: str) -> ReminderResponse:
    return ReminderResponse(
        title="测试任务",
        due_date="2024-01-01 10:00",
        description="这是一个测试任务"
    )
    # 如果是模拟模式，使用模拟数据
    if USE_MOCK_MODE:
        return generate_mock_reminder(text)
    
    # 定义工具
    tool_definition = {
        "type": "function",
        "function": {
            "name": "create_reminder",
            "description": "从自然语言中分析并提取提醒任务信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "任务的简短标题"
                    },
                    "due_date": {
                        "type": "string",
                        "description": "任务的截止日期和时间，格式为 YYYY-MM-DD HH:MM"
                    },
                    "description": {
                        "type": "string",
                        "description": "任务的详细描述"
                    }
                },
                "required": ["title", "due_date", "description"]
            }
        }
    }
    
    try:
        response = client.chat.completions.create(
            model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
            messages=[
                {
                    "role": "system",
                    "content": "你是一个智能助手，专门从自然语言中分析并提取任务提醒信息。请使用提供的工具来完成此任务。"
                },
                {
                    "role": "user",
                    "content": text
                }
            ],
            tools=[tool_definition]
            # 移除 tool_choice 参数，让模型自动决定是否调用工具
        )

        # 检查是否有工具调用
        tool_calls = response.choices[0].message.tool_calls
        if tool_calls and tool_calls[0].function.arguments:
            # 使用工具调用结果
            reminder_data = json.loads(tool_calls[0].function.arguments)
        else:
            # 回退到直接解析响应内容
            content = response.choices[0].message.content
            if not content:
                raise HTTPException(status_code=400, detail="模型未返回有效内容")
            
            try:
                reminder_data = json.loads(content)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="模型返回的内容不是有效的JSON格式")

        if not all(key in reminder_data for key in ["title", "due_date", "description"]):
            raise HTTPException(status_code=400, detail="提取的任务信息不完整")

        return ReminderResponse(
            title=reminder_data["title"],
            due_date=reminder_data["due_date"],
            description=reminder_data["description"]
        )

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"值错误: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"提取提醒时发生未预期错误: {str(e)}")
        import traceback
        detailed_error = traceback.format_exc()
        logger.error(f"详细错误信息: {detailed_error}")
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {str(e)}")


@app.post("/api/reminder", response_model=ReminderResponse)
async def create_reminder(request: ReminderRequest):
    reminder = extract_reminder_from_text(request.text)
    return reminder

@app.get("/")
async def root():
    return {"message": "Reminder Backend API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)