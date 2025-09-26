
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from dotenv import load_dotenv
import google.generativeai as genai

# Load .env
load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-pro")

# FastAPI app
app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # <-- replace "*" with your frontend domain for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------
# Zalo Domain Verification
# -----------------------
@app.get("/zalo_verifierVVkmCuVa9IzywueJ_C8u2odXarN5bqGED3an.html")
async def zalo_verification():
    """
    Zalo will call this endpoint to verify domain ownership.
    Make sure the file exists in your project root.
    """
    filepath = os.path.join(
        os.path.dirname(__file__),
        "zalo_verifierVVkmCuVa9IzywueJ_C8u2odXarN5bqGED3an.html"
    )
    if os.path.exists(filepath):
        return FileResponse(filepath, media_type="text/html")
    return JSONResponse({"error": "Verification file missing"}, status_code=404)

# -----------------------
# Gemini Ask Endpoint
# -----------------------
@app.post("/ask")
async def ask(req: Request):
    data = await req.json()
    question = data.get("question", "")
    if not question:
        return {"error": "Missing 'question'"}

    response = model.generate_content(question)
    return {"answer": response.text}

# -----------------------
# Example Webhook for Zalo
# -----------------------
@app.post("/zalo/webhook")
async def zalo_webhook(req: Request):
    """
    Example webhook endpoint for Zalo.
    Extend this to handle events/messages from Zalo.
    """
    body = await req.json()
    # For now, just echo back
    return {"received": body}

# -----------------------
# Root Route
# -----------------------
@app.get("/")
async def root():
    return {"status": "ok", "message": "Backend is running 🚀"}
