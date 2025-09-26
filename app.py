import os
import requests
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any
from dotenv import load_dotenv
import google.generativeai as genai

# ===== Load .env =====
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ZALO_ACCESS_TOKEN = os.getenv("ZALO_ACCESS_TOKEN")

# ===== Configure Gemini =====
genai.configure(api_key=GEMINI_API_KEY)

# ===== System Prompt (like GPT-5) =====
SYSTEM_PROMPT = """
You are Locaith AI, an advanced AI agent (like GPT-5).
Your role is to handle customer support, analyze images, generate images, and provide advice.
Always be concise, helpful, and professional.
"""

# ===== Zalo Config =====
ZALO_API_URL = "https://openapi.zalo.me/v3.0/oa/message/cs"

# ===== FastAPI =====
app = FastAPI()

# ===== Enable CORS =====
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # you can restrict this to your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== Tools (Layer 2) =====

def chat_tool(user_input: str) -> str:
    """Chat Q&A with Gemini"""
    model = genai.GenerativeModel("gemini-2.5-pro")
    response = model.generate_content(
        [{"role": "system", "parts": SYSTEM_PROMPT},
         {"role": "user", "parts": user_input}]
    )
    return response.text


def image_generate_tool(prompt: str) -> str:
    """Generate an image using Gemini"""
    model = genai.GenerativeModel("gemini-2.5-pro")
    response = model.generate_content([f"Generate an image for: {prompt}"])
    return response.text or "Image generated (URL/Base64 depending on API plan)."


def image_analyze_tool(image_url: str) -> str:
    """Analyze an image with Gemini"""
    model = genai.GenerativeModel("gemini-2.5-pro")
    response = model.generate_content(
        [SYSTEM_PROMPT, {"mime_type": "image/png", "data": image_url}]
    )
    return response.text

# ===== Router (Layer 1) =====
def ai_agent_router(message: Dict[str, Any]) -> str:
    msg_type = message.get("type", "text")
    content = message.get("content", "")

    if msg_type == "text":
        if content.lower().startswith("draw") or content.lower().startswith("generate image"):
            return image_generate_tool(content)
        elif content.lower().startswith("analyze"):
            return image_analyze_tool(content.split(" ", 1)[-1])
        else:
            return chat_tool(content)

    elif msg_type == "image":
        return image_analyze_tool(content)

    return "Sorry, I don’t understand this request."

# ===== Send reply to Zalo =====
def send_zalo_message(user_id: str, text: str):
    headers = {"access_token": ZALO_ACCESS_TOKEN}
    payload = {
        "recipient": {"user_id": user_id},
        "message": {"text": text}
    }
    requests.post(ZALO_API_URL, headers=headers, json=payload)

# ===== Webhook =====
class WebhookEvent(BaseModel):
    event_name: str
    sender: Dict[str, Any]
    message: Dict[str, Any] = None

# ---- Zalo Domain Verification ----
# Serve the HTML file Zalo gave you
@app.get("/zalo_verifierVVkmCuVa9IzywueJ_C8u2odXarN5bqGED3an.html")
async def zalo_verification():
    """
    Zalo will call this endpoint to verify domain ownership.
    Make sure the file `zalo_verifierVVkmCuVa9IzywueJ_C8u2odXarN5bqGED3an.html`
    exists in your project root.
    """
    filepath = os.path.join(os.path.dirname(__file__),
                            "zalo_verifierVVkmCuVa9IzywueJ_C8u2odXarN5bqGED3an.html")
    if os.path.exists(filepath):
        return FileResponse(filepath, media_type="text/html")
    return JSONResponse({"error": "Verification file missing"}, status_code=404)

@app.post("/zalo/webhook")
async def zalo_webhook(event: WebhookEvent, request: Request):
    user_id = event.sender.get("id")
    message = event.message or {}

    reply = ai_agent_router(message)
    send_zalo_message(user_id, reply)

    return {"status": "ok", "reply": reply}
