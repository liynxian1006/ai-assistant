# 智能问答助手（Flask + 大模型 API 全栈小项目）

一个前后端完整、可运行的 AI 问答应用：**Flask 后端 + 大模型 API + 原生前端聊天页**。
对应简历中的「AI 应用开发」与「全栈能力」两条技能，写进项目经历。

## 项目结构

```
ai-assistant/
├── app.py             # Flask 后端：接口 + 大模型调用封装
├── static/index.html  # 前端聊天页（原生 HTML/CSS/JS，流式打字机效果）
├── requirements.txt   # 依赖
└── .env.example       # 配置模板（Key、模型地址）
```

## 三步跑起来

1. **装依赖**
   ```
   pip install -r requirements.txt
   ```
2. **配置 Key**：把 `.env.example` 复制一份命名为 `.env`，填入你的 API_KEY
   （推荐 DeepSeek，便宜且注册有赠送额度；也可用通义、智谱等 OpenAI 兼容接口）
   并设置环境变量加载方式：Windows PowerShell 下先执行
   ```
   $env:API_KEY="你的Key"
   ```
   再运行（或直接在 app.py 顶部填 Key，本地调试可以这样做，公开代码前务必移除）。
3. **启动**
   ```
   python app.py
   ```
   浏览器打开 http://127.0.0.1:5000

## 接口一览（可当接口测试练手）

| 方法 | 路径 | 说明 |
|---|---|---|
| GET  | /api/health | 健康检查，返回模型名与 Key 加载状态 |
| POST | /api/chat | 一次性返回完整回答 |
| POST | /api/chat/stream | SSE 流式逐字返回（前端打字机效果用的就是它） |

## 技术要点（面试可讲）

- 后端按「路由层 → 服务层（llm_chat 封装）」组织，模型接口可切换（改 .env 即可换 DeepSeek/通义/智谱）。
- SSE（Server-Sent Events）流式输出：后端逐块透传模型增量内容，前端边收边渲染。
- 前端维护最近 20 轮对话历史随请求回传，实现多轮上下文记忆。
- 系统提示词（System Prompt）可配置，即「人设」设计。

## 下一步可以加的功能（练手方向）

- [ ] 对话历史存 MySQL（messages 表：role / content / created_at）
- [ ] Markdown 渲染回答（代码块高亮）
- [ ] 文档问答：上传 txt/pdf → 切片 → 检索 → 拼 Prompt（简化版 RAG）
- [ ] 部署到服务器，配 Nginx + 域名上线
