"""
ReAct Agent 的提示词模板
"""
from datetime import datetime, timedelta


def build_plan_prompt(user_input: str, existing_tasks: list[dict]) -> str:
    """构建规划阶段的提示词"""
    today = datetime.now().strftime("%Y-%m-%d")
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    tasks_desc = "无"
    if existing_tasks:
        tasks_desc = "\n".join([
            f"  - ID={t['id']} | 标题={t['title']} | 截止={t['due_date']} | 描述={t.get('description','')} | 完成={t.get('completed',False)}"
            for t in existing_tasks
        ])

    return f"""你是一个智能任务规划助手。分析用户输入，将其拆解为一个或多个操作步骤。

## 当前时间
今天是 {today}，明天是 {tomorrow}，当前时间 {now}。

## 用户已有任务
{tasks_desc}

## 用户输入
{user_input}

## 操作类型与选择规则

按以下优先级判断每条意图属于哪种操作：

### create（创建新任务）
- 用户表达要做某事，且已有任务中找不到对应项
- 需要 title(≤10字), due_date(YYYY-MM-DD HH:MM), description

### delete（删除任务）
满足以下任一条件时使用 delete：
- 用户明确说"删除"、"取消"、"去掉"、"不要了"
- 用户表示某个计划**不做了、没时间了、算了、放弃**
- 用户说"不需要"、"没必要"、"不去了"等否定意图
- 用户的意图是让某任务**消失**，而非改变其属性
- 需要 target_description 描述要删除的任务

### update（修改任务）
仅在以下情形使用 update：
- 用户明确要**改时间**（如"改到三点"、"推迟"、"提前"）
- 用户要**改内容**（如"改标题"、"加个备注"）
- 用户要**标记完成**（如"做完了"、"完成了"）
- 需要 target_description + 至少一个要修改的字段，不修改的字段设为 null

### query（查询任务）
- 用户询问有哪些任务、查看任务列表

### 关键区别
- "没时间做了" → **delete**（任务不要了），不是 update（不是改时间）
- "改到明天" → **update**（改时间），不是 delete
- "做完了" → **update**（改 completed 为 true），不是 delete
- "不做了" → **delete**（取消任务），不是 update

## 时间解析规则
基础规则（用户输入中直接包含时间）：
- "下午三点" → 今天 15:00
- "明天上午九点" → {tomorrow} 09:00
- "晚上八点" → 今天 20:00
- "下周一下午两点" → 计算下周一日期
- "半小时后" → 当前时间 + 30分钟
- 无明确时间 → 默认为今天 23:59

## 上下文时间推断（重要）
用户输入中可能包含相对时间词（如"下班后"、"饭后"、"会后"），这些词本身没有具体时间，需要从已有任务中推断：
- 扫描已有任务的标题和描述，提取其中包含的具体时间点
- 将提取到的时间点与相对时间词关联，确定 due_date
- 示例：已有任务含"六点下班"，则用户说"下班后" → 今天 18:00 之后，取 18:00 作为 due_date
- 示例：已有任务含"12点吃饭"，则用户说"饭后" → 今天 12:00 之后
- 如果已有任务中找不到对应的时间线索，则默认时间为 今天 23:59

## 规则
1. 逐条分析用户输入，每条独立意图拆为一个步骤
2. 仔细对照已有任务列表，判断每个意图是新增、修改还是删除
3. 创建任务时，结合上下文时间推断确定 due_date
4. update/delete 用 target_description 描述目标，不要猜 ID
5. update 至少提供一个非 null 的修改字段

## 输出格式
纯 JSON 数组，不要 markdown 代码块：
[
  {{
    "step": 1,
    "operation": "create",
    "description": "创建明天的会议提醒",
    "params": {{
      "title": "会议提醒",
      "due_date": "{tomorrow} 09:00",
      "description": "明天的会议，需提前准备材料"
    }}
  }},
  {{
    "step": 2,
    "operation": "update",
    "description": "把会议时间改到下午三点",
    "params": {{
      "target_description": "会议",
      "title": null,
      "due_date": "{today} 15:00",
      "description": null
    }}
  }},
  {{
    "step": 3,
    "operation": "delete",
    "description": "取消遛狗，没时间了",
    "params": {{
      "target_description": "遛狗"
    }}
  }}
]

如果只有查询意图，输出：[{{"step": 1, "operation": "query", "description": "查询所有任务", "params": {{}}}}]
如果无法确定任何操作，输出空数组：[]

只输出 JSON，不要其他内容。"""


def build_match_prompt(target_description: str, existing_tasks: list[dict], operation: str) -> str:
    """构建语义匹配的提示词"""
    tasks_desc = "\n".join([
        f"  ID={t['id']} | 标题={t['title']} | 截止={t['due_date']} | 描述={t.get('description','')}"
        for t in existing_tasks
    ])

    return f"""从任务列表中，找出与用户描述最匹配的任务，用于{operation}操作。

## 用户描述
{target_description}

## 任务列表
{tasks_desc}

## 输出格式
{{"task_id": 数字, "confidence": "high/medium/low"}}

匹配规则：
- 标题相似优先
- 描述内容相似次之
- 无法确定时 task_id 设为 null, confidence 为 "low"

只输出 JSON，不要其他内容。"""


def build_summarize_prompt(user_input: str, results: list[dict]) -> str:
    """构建总结阶段的提示词"""
    results_desc = "\n".join([
        f"  步骤{r['step_index']+1}: [{r['operation']}] {'成功' if r['success'] else '失败'} - {r['message']}"
        for r in results
    ])

    return f"""请用简洁友好的中文总结以下操作结果：

## 用户原始输入
{user_input}

## 执行结果
{results_desc}

## 要求
1. 一句话概括所有操作结果
2. 语气友好自然
3. 如果全部成功，表达肯定
4. 如果有失败，如实说明并给出建议
5. 不要使用 JSON 格式

直接输出总结文本。"""


def build_verify_prompt(step: dict, result: dict) -> str:
    """构建验证阶段的提示词"""
    return f"""验证以下操作是否成功执行：

操作类型: {step.get('operation')}
操作描述: {step.get('description')}
执行结果: {result}

判断标准：
- create: 返回了 task_id 且 > 0 即为成功
- update: success 为 true 即为成功
- delete: success 为 true 即为成功
- query: success 为 true 即为成功

输出格式：{{"valid": true/false, "reason": "简要说明"}}
只输出 JSON。"""