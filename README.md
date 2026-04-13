# Lariel Systems Website

Business website for Lariel Systems with an AI chat page powered by Ollama.

## Prerequisites

- **Python 3.10+**
- **Ollama** installed and running — download from [ollama.com](https://ollama.com)
- **qwen2.5:14b** model pulled

## Setup

### 1. Pull the Ollama model

```bash
ollama pull qwen2.5:14b
```

### 2. Install Python dependencies

```bash
cd backend
pip install fastapi uvicorn httpx
```

### 3. Start the website server

```bash
cd backend
python main.py
```

The site runs at **http://localhost:8083**

### 4. Verify

```bash
curl http://localhost:8083/api/health
```

Should return: `{"status":"ok","model":"qwen2.5:14b"}`

## Structure

```
larielsystems/
├── backend/
│   ├── main.py           # FastAPI proxy (chat API + static file server)
│   └── requirements.txt
├── css/
│   └── style.css         # Holographic dark theme
├── images/
│   ├── ar-worker.png
│   ├── logo.png
│   └── vien-ai-hero.png
├── js/
│   └── main.js           # Nav toggle, mobile menu
├── index.html            # Home page
├── services.html         # Services page
├── process.html          # Process page
├── chat.html             # AI Chat (connects to Ollama via proxy)
└── contact.html          # Contact page
```

## Pages

- **Home** — Hero + overview of services
- **Services** — 6 service offerings + differentiators
- **Process** — Discovery → Design → Build → Deploy → Support
- **AI Chat** — Live chat powered by Ollama (qwen2.5:14b) with Lariel personality
- **Contact** — Contact form + email + phone numbers

## Configuration

Edit `backend/main.py` to change:
- `OLLAMA_URL` — Ollama endpoint (default: `http://localhost:11434`)
- `MODEL` — Ollama model name (default: `qwen2.5:14b`)
- Port — default `8083`, change in the `uvicorn.run()` call at bottom
