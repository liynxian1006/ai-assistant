# -*- coding: utf-8 -*-
"""
智能问答助手 - Flask + 大模型 API 全栈小项目
结构：
  app.py            Flask 后端（接口 + 大模型调用封装）
  static/index.html 前端聊天页面（原生 HTML/CSS/JS）
运行：
  1. pip install -r requirements.txt
  2. 在 .env 里填 API_KEY（DeepSeek / 通义 / OpenAI 兼容接口均可）
  3. python app.py  → 浏览器打开 http://127.0.0.1:5000
"""
import json
import os

import requests
from flask import Flask, jsonify, request, send_from_directory, stream_with_context

# ---------- 配置（优先读环境变量，方便部署） ----------
API_KEY = os.getenv("API_KEY", "")
BASE_URL = os.getenv("BASE_URL", "https://api.deepseek.com/v1")
MODEL = os.getenv("MODEL", "deepseek-chat")
SYSTEM_PROMPT = os.getenv(
    "SYSTEM_PROMPT",
    "你是一个友好的中文智能助手，回答简洁、准确、有条理。",
)

app = Flask(__name__, static_folder="static")


# ---------- 大模型调用封装（OpenAI 兼容协议） ----------
def llm_chat(messages: list, stream: bool = False):
    """调用 OpenAI 兼容的大模型接口。stream=True 时返回逐块内容。"""
    url = BASE_URL.rstrip("/") + "/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}",
    }
    payload = {"model": MODEL, "messages": messages, "stream": stream}
    resp = requests.post(url, headers=headers, json=payload, timeout=60, stream=stream)

    if resp.status_code != 200:
        raise RuntimeError(f"模型接口返回 {resp.status_code}: {resp.text[:300]}")

    if not stream:
        return resp.json()["choices"][0]["message"]["content"]

    def generate():
        for line in resp.iter_lines():
            if not line:
                continue
            data = line.decode("utf-8")
            if data.startswith("data: "):
                data = data[6:]
            if data.strip() == "[DONE]":
                break
            try:
                chunk = json.loads(data)
                delta = chunk["choices"][0].get("delta", {})
                content = delta.get("content", "")
                if content:
                    yield content
            except (json.JSONDecodeError, KeyError, IndexError):
                continue

    return generate()


# ---------- 接口 ----------
@app.get("/")
def index():
    return send_from_directory("static", "index.html")


@app.get("/api/health")
def health():
    return jsonify({"ok": True, "model": MODEL, "key_loaded": bool(API_KEY)})


@app.post("/api/chat")
def chat():
    """普通问答接口：一次返回完整回答"""
    data = request.get_json(silent=True) or {}
    user_msg = (data.get("message") or "").strip()
    history = data.get("history") or []  # 前端传回的对话历史 [{role, content}]
    if not user_msg:
        return jsonify({"error": "消息不能为空"}), 400
    if not API_KEY:
        return jsonify({"error": "未配置 API_KEY，请在 .env 中填写后重启"}), 500

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for m in history[-20:]:
        if m.get("role") in ("user", "assistant") and m.get("content"):
            messages.append({"role": m["role"], "content": m["content"]})
    messages.append({"role": "user", "content": user_msg})

    try:
        reply = llm_chat(messages)
        return jsonify({"reply": reply})
    except Exception as e:  # noqa: BLE001
        return jsonify({"error": str(e)}), 502


@app.post("/api/chat/stream")
def chat_stream():
    """流式接口：SSE 逐字返回，打字机效果"""
    data = request.get_json(silent=True) or {}
    user_msg = (data.get("message") or "").strip()
    history = data.get("history") or []
    if not user_msg:
        return jsonify({"error": "消息不能为空"}), 400
    if not API_KEY:
        return jsonify({"error": "未配置 API_KEY，请在 .env 中填写后重启"}), 500

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for m in history[-20:]:
        if m.get("role") in ("user", "assistant") and m.get("content"):
            messages.append({"role": m["role"], "content": m["content"]})
    messages.append({"role": "user", "content": user_msg})

    try:
        gen = llm_chat(messages, stream=True)
    except Exception as e:  # noqa: BLE001
        return jsonify({"error": str(e)}), 502

    def sse():
        try:
            for piece in gen:
                yield f"data: {json.dumps({'content': piece}, ensure_ascii=False)}\n\n"
        except Exception as e:  # noqa: BLE001
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    return app.response_class(
        stream_with_context(sse()), mimetype="text/event-stream"
    )


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    print(f"智能问答助手已启动 → http://127.0.0.1:{port}")
    print(f"当前模型：{MODEL}  API_KEY {'已加载' if API_KEY else '未配置（先填 .env）'}")
    app.run(host="127.0.0.1", port=port, debug=True)
