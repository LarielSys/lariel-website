"""
Lariel Systems — Website Chat Proxy
Bridges chat.html → Ollama (llama3.1:8b)
Run: python main.py
"""

import json
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles

# --- Config ---
OLLAMA_URL = "http://localhost:11434"  # native Ollama default port
MODEL = "qwen2.5:14b"
MAX_HISTORY = 20

SYSTEM_PROMPT = """You are Lariel, the AI assistant for Lariel Systems — a technology consulting company that builds practical AI solutions for small and mid-sized businesses.

Your personality:
- Professional but approachable. Warm, not corporate.
- Concise and clear. No jargon unless the user is technical.
- Confident about what Lariel Systems offers, honest about what you don't know.

Lariel Systems services:
1. **AI Assistants for Small Business** — Custom conversational AI deployed on local hardware. No cloud dependency, full data privacy. Trained on the company's own knowledge base.
2. **PDF → Interactive AI Manual** — Convert static PDFs, SOPs, and technical documents into searchable AI-powered knowledge bases that teams can query in plain language. RAG-powered with source citations.
3. **Custom AI Development** — Bespoke pipelines: computer vision, image classification, automated reporting, multi-model orchestration, API integration.
4. **Vi-En AI (Coming Soon)** — AI-powered visual inspection for industrial/infrastructure applications. Automated defect detection, deterioration classification, geo-tagged reporting.

Key selling points:
- Local-first: data stays on the client's network
- No subscription lock-in
- Clean architecture, documented code, no vendor lock-in
- We build in short cycles with weekly demos

Process: Discovery call → Solution design → Build & iterate → Deploy & train → Ongoing support

If asked about pricing, say it depends on scope and suggest they use the contact form or email marco@larielsystems.com.
If asked about things outside Lariel Systems' domain, you can have a friendly conversation but gently steer back to how you can help.
Do NOT make up capabilities or projects that aren't listed above."""

# --- Session storage (in-memory, resets on restart) ---
sessions: dict[str, list[dict]] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Verify Ollama is reachable
    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(OLLAMA_URL, timeout=5)
            print(f"[OK] Ollama reachable: {r.status_code}")
        except Exception as e:
            print(f"[WARN] Ollama not reachable: {e}")
    yield


app = FastAPI(title="Lariel Website Chat Proxy", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_or_create_session(session_id: str | None) -> tuple[str, list[dict]]:
    if not session_id or session_id not in sessions:
        session_id = str(uuid.uuid4())
        sessions[session_id] = []
    return session_id, sessions[session_id]


@app.post("/api/chat")
async def chat(request: Request):
    body = await request.json()
    message = body.get("message", "").strip()
    session_id = body.get("session_id")

    if not message:
        return {"error": "Empty message", "session_id": session_id}

    sid, history = get_or_create_session(session_id)

    # Append user message
    history.append({"role": "user", "content": message})

    # Trim history to keep context window manageable
    if len(history) > MAX_HISTORY:
        history[:] = history[-MAX_HISTORY:]

    # Build messages array for Ollama
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history

    async def stream():
        assistant_text = ""
        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream(
                "POST",
                f"{OLLAMA_URL}/api/chat",
                json={"model": MODEL, "messages": messages, "stream": True},
            ) as resp:
                async for line in resp.aiter_lines():
                    if not line:
                        continue
                    try:
                        chunk = json.loads(line)
                        token = chunk.get("message", {}).get("content", "")
                        if token:
                            assistant_text += token
                            yield f"data: {json.dumps({'token': token, 'session_id': sid})}\n\n"
                        if chunk.get("done"):
                            break
                    except json.JSONDecodeError:
                        continue

        # Save assistant response to history
        history.append({"role": "assistant", "content": assistant_text})
        yield f"data: {json.dumps({'done': True, 'session_id': sid})}\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")


@app.get("/api/health")
async def health():
    return {"status": "ok", "model": MODEL}


# Serve static website files from parent directory
STATIC_DIR = Path(__file__).resolve().parent.parent
app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8083)
