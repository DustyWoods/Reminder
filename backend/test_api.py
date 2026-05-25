import httpx
import json

async def test_reminder_api():
    """测试提醒后端API"""
    base_url = "http://localhost:8000"
    
    # 测试健康检查接口
    async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
        print("测试健康检查接口...")
        response = await client.get(f"{base_url}/health")
        print(f"健康检查响应: {response.status_code}")
        print(f"响应内容: {response.json()}")
        print()
        
        # 测试提醒创建接口
        print("测试提醒创建接口...")
        test_cases = [
            "下周三下午3点开会讨论项目进度",
            "明天早上9点提交报告",
            "本周五下午5点前完成代码审查",
            "后天晚上7点参加朋友聚会"
        ]
        
        for text in test_cases:
            print(f"输入文本: {text}")
            try:
                response = await client.post(
                    f"{base_url}/api/reminder",
                    json={"text": text}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"成功提取任务信息:")
                    print(f"  标题: {result.get('title')}")
                    print(f"  截止时间: {result.get('due_date')}")
                    print(f"  描述: {result.get('description')}")
                else:
                    print(f"请求失败，状态码: {response.status_code}")
                    print(f"错误信息: {response.text}")
            except Exception as e:
                print(f"请求发生错误: {str(e)}")
            print()

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_reminder_api())