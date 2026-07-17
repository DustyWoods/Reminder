<a id="readme-top"></a>
# 拾序（Reminder）

<div align="center">
  <p style="color: #2F63D0; font-size: 24px; font-weight: bold;">智能任务管理应用</p>
  <img src="assets/image1.png" alt="image1" height="300">
  <img src="assets/image2.png" alt="image2" height="300">
</div>

---

## 关于项目

**拾序（Reminder）** 是一个基于 Agent 的智能任务管理应用，旨在帮助用户通过自然语言交互高效地管理个人日常任务。该应用采用 ReAct（Reasoning + Acting）框架实现智能任务处理，支持任务的创建、删除、修改和智能规划等操作。

### 核心特色

- **自然语言交互**：用户可直接通过自然语言指令与应用进行交互，无需繁琐的操作流程
- **ReAct Agent 架构**：基于 Plan-Act-Observe-Summarize 四阶段工作流实现复杂任务处理
- **智能任务规划**：Agent 可从全局角度对任务列表进行梳理优化，帮助用户更高效地管理任务
- **全栈架构设计**：前后端分离，支持用户认证、数据持久化和实时任务同步

---

## 系统架构

### Agent 工作流

本项目采用经典的 **ReAct（Reasoning + Acting）** 框架，实现了四阶段的 Agent 工作流：

```
用户输入 → Plan（规划）→ Act（执行）→ Observe（观察）→ Summarize（总结）
                                    ↑                ↓
                                    └────────────────┘
```

| 阶段 | 功能描述 | 实现方式 |
|------|----------|----------|
| **Plan（规划）** | LLM 分析用户输入，拆解为具体操作步骤 | 使用 DeepSeek LLM 生成包含操作类型、参数的步骤列表 |
| **Act（执行）** | 执行当前步骤的操作 | 支持 create/update/delete/query/schedule 五种操作 |
| **Observe（观察）** | 验证执行结果，决定重试或继续 | 检查操作是否成功，支持最多 2 次重试 |
| **Summarize（总结）** | 生成用户友好的操作总结 | 全部成功时快速拼接，失败时调用 LLM 生成详细总结 |

### 技术架构

```
┌─────────────────────────────────────────────────────────────────┐
│                         前端层 (Flutter)                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────────────┐ │
│  │ 登录页面  │  │ 注册页面  │  │ 首页     │  │ 日历页面        │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────────┬────────┘ │
│       │             │             │                  │          │
│  ┌────┴─────┐  ┌────┴───────────────────────────────┴────────┐ │
│  │  API服务 │  │              State Management                 │ │
│  │ (Dio)   │  │  LoginManager          TaskManager           │ │
│  └────┬─────┘  └──────────────────────────────────────────────┘ │
└───────┼─────────────────────────────────────────────────────────┘
        │ HTTP/HTTPS
┌───────┴─────────────────────────────────────────────────────────┐
│                       后端层 (FastAPI)                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────────────┐ │
│  │ Auth API │  │ Task API │  │ Text API │  │  Voice API      │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────────┬────────┘ │
│       │             │             │                  │          │
│  ┌────┴──────────────────────────────────────────────┴────────┐ │
│  │                     Agent 核心引擎                           │ │
│  │  ┌──────┐ ┌──────┐ ┌────────┐ ┌──────────┐                │ │
│  │  │ Plan │→│ Act  │→│Observe │→│Summarize │                │ │
│  │  └──────┘ └──────┘ └────────┘ └──────────┘                │ │
│  └────────────────────────────────────────────────────────────┘ │
│                           │                                     │
│  ┌──────────┐  ┌─────────┴─────────┐  ┌─────────────────────┐   │
│  │ Database │  │    LLM Service    │  │   ASR Service       │   │
│  │ (SQLite) │  │   DeepSeek API    │  │   Sherpa-Onnx       │   │
│  └──────────┘  └───────────────────┘  └─────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 技术栈

| 层次 | 技术 | 版本 | 说明 |
|------|------|------|------|
| **前端框架** | Flutter | 3.13+ | 跨平台移动应用开发框架 |
| **前端语言** | Dart | 3.13+ | Flutter 官方编程语言 |
| **后端框架** | FastAPI | 0.104+ | 高性能 Python Web 框架 |
| **后端语言** | Python | 3.13 | 后端服务开发语言 |
| **数据库** | SQLite | 3.x | 轻量级关系型数据库 |
| **Agent 框架** | LangChain | 0.1+ | LLM 应用开发框架 |
| **LLM 服务** | DeepSeek API | - | 提供推理能力 |
| **语音识别** | Sherpa-Onnx | - | 流式语音识别引擎 |

---

## 功能描述

### 已实现功能

- [x] **用户认证系统**：支持用户注册、登录功能，基于 JWT 实现身份验证
- [x] **自然语言交互**：用户可通过自然语言指令与应用进行交互
- [x] **任务管理**：Agent 对用户任务列表进行全面管理
  - [x] **创建任务**：根据自然语言描述创建新任务
  - [x] **修改任务**：支持更新任务的标题、截止日期、描述等属性
  - [x] **删除任务**：根据自然语言描述删除指定任务
  - [x] **查询任务**：获取当前任务列表
  - [x] **智能规划**：Agent 从全局角度对任务进行梳理和优化
- [x] **任务列表展示**：支持按日期分组展示任务
- [x] **列表视图**：提供任务列表页面展示任务安排
- [x] **本地通知**：支持任务提醒通知

### 待开发功能

- [ ] **语音输入**：通过语音指令与应用进行交互
  - [ ] 语音流式输入
  - [ ] 语音识别能力优化

> 说明：项目初期实现了流式语音输入，但在后续agent和后端处理逻辑优化过程中，未关注语音输入的适配调整，故而目前项目中存在语音输入接口，但前后端未完成适配，导致语音输入功能暂未实现。
---

## 项目结构

```
reminder/
├── assets/                    # 静态资源
│   ├── image1.png             # 应用截图1
│   ├── image2.png             # 应用截图2
│   ├── demo1.mp4              # 功能演示视频1
│   └── demo2.mp4              # 功能演示视频2
├── backend/                   # 后端服务
│   ├── agent/                 # Agent 核心模块
│   │   ├── actions.py         # 操作执行函数
│   │   ├── config.py          # Agent 配置
│   │   ├── graph.py           # Agent 图定义
│   │   ├── nodes.py           # 工作流节点（Plan/Act/Observe/Summarize）
│   │   ├── prompts.py         # LLM 提示词模板
│   │   ├── state.py           # Agent 状态定义
│   │   └── env_example        # 环境变量示例
│   ├── config/                # 配置模块
│   │   └── settings.py        # 全局配置
│   ├── models/                # 数据模型
│   │   └── schemas.py         # API 数据结构定义
│   ├── routers/               # API 路由
│   │   ├── auth.py            # 用户认证接口
│   │   ├── task.py            # 任务管理接口
│   │   ├── text.py            # 文本交互接口
│   │   └── voice.py           # 语音交互接口
│   ├── services/              # 业务服务
│   │   ├── asr.py             # 语音识别服务
│   │   └── auth.py            # 认证服务
│   ├── utils/                 # 工具函数
│   │   ├── database.py        # 数据库操作
│   │   ├── llm_helpers.py     # LLM 辅助函数
│   │   └── logging.py         # 日志配置
│   ├── main.py                # 应用入口
│   └── requirements.txt       # Python 依赖
├── frontend/                  # 前端应用
│   ├── android/               # Android 原生配置
│   ├── assets/                # 前端资源
│   ├── lib/
│   │   ├── Components/        # UI 组件
│   │   │   ├── CalendarPage/  # 日历页面组件
│   │   │   ├── HomePage/      # 首页组件
│   │   │   ├── LoginPage/     # 登录页面组件
│   │   │   └── RegisterPage/  # 注册页面组件
│   │   ├── Page/              # 页面路由组件
│   │   │   ├── CalendarPage.dart
│   │   │   ├── HomePage.dart
│   │   │   ├── LoginPage.dart
│   │   │   └── RegisterPage.dart
│   │   ├── Route/             # 路由配置
│   │   ├── Services/          # 前端服务
│   │   │   └── NotificationService.dart
│   │   ├── Stores/            # 状态管理
│   │   │   ├── LoginManager.dart
│   │   │   └── TaskManager.dart
│   │   ├── Utils/             # 工具函数
│   │   ├── Viewmodels/        # 视图模型
│   │   ├── api/               # API 调用层
│   │   └── main.dart          # 应用入口
│   ├── pubspec.yaml           # Flutter 依赖配置
│   └── analysis_options.yaml  # 代码分析配置
└── README.md                  # 项目说明文档
```

---

## 运行依赖

### 后端启动

#### 前置要求

1. **配置环境变量**
   - 将 `backend/agent/env_example` 文件重命名为 `.env`
   - 补充 DeepSeek API Key

2. **（可选）下载语音识别模型**
   - 从 [HuggingFace](https://huggingface.co/csukuangfj/sherpa-onnx-streaming-zipformer-bilingual-zh-en-2023-02-20/tree/main) 下载以下文件并保存至 `backend/assets/models/zipformer/` 目录
     - `decoder-epoch-99-avg-1.onnx`
     - `encoder-epoch-99-avg-1.onnx`
     - `joiner-epoch-99-avg-1.onnx`
     - `tokens.txt`

#### 启动步骤

```bash
conda create -n reminder python=3.13
conda activate reminder
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 前端启动

#### 前置要求

- 配置 Flutter 开发环境（Dart SDK 3.13+）
- 配置 Android 模拟器（推荐使用 Pixel 9 Pro）

#### 启动步骤

```bash
cd frontend
flutter pub get
flutter run
```

---

## 演示视频

- [demo_1](https://github.com/DustyWoods/Reminder/releases/download/v1.0/demo1.mp4)：基础功能展示
  - 录制于 2026-07-09
  - 内容：注册、登录、任务创建、删除、修改、任务规划

- [demo_2](https://github.com/DustyWoods/Reminder/releases/download/v1.0/demo2.mp4)：任务列表展示
  - 录制于 2026-07-17
  - 内容：任务列表展示功能

> 说明：两个视频的录制设备（显示器）不同，而我未能解决系统对模拟器分辨率的处理问题（~~本人太菜了~~），导致demo_2中存在显示模糊，并非应用问题。
---

## 开发说明

### Agent 操作类型

Agent 任务处理支持以下四种操作类型，可正确识别并处理自然语言中的复杂需求：

| 操作类型 | 说明 | 示例指令 |
|----------|------|----------|
| `create` | 创建新任务 | "明天下午3点开会" |
| `update` | 更新任务信息 | "把会议时间改到4点" |
| `delete` | 删除任务 | "取消明天的会议" |
| `schedule` | 智能规划任务 | "帮我规划一下本周的任务" |

### 错误处理机制

- **重试机制**：每个步骤失败后最多重试 2 次
- **降级策略**：当 LLM 服务不可用时，使用预设的 fallback 规划
- **失败总结**：当操作失败时，生成详细的失败原因和建议

---

## 其他说明

本项目为个人独立开发的课程实践项目，主要在 Android 模拟器（Pixel 9 Pro）环境下进行开发和测试，未在真实设备上测试。由于开发时间和设备条件限制，项目存在以下已知限制：

- **语音输入功能**：该功能模块已完成基础架构搭建，但在与 Agent 系统集成过程中存在兼容性问题，暂未正式启用
- **设备兼容性**：应用仅在 Pixel 9 Pro 模拟器上进行了完整测试，在其他设备下可能存在界面渲染差异
- **性能优化**：当前版本优先保证功能完整性，部分场景下的性能优化仍有提升空间

若您在构建或运行过程中遇到问题，建议优先检查 Flutter 和 Android 开发环境配置是否符合要求。对于环境相关问题，可参考 Flutter 官方文档或相关社区资源获取解决方案。

<p align="right">(<a href="#readme-top">返回顶部</a>)</p>