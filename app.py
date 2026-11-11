"""Snapdeal Mini AI Voice KAM — Sarvam-powered backend.

Three Sarvam models do the work:
  * Saaras (speech-to-text)  -> what the seller said
  * Sarvam-105B-conversations -> what Aria says back
  * Bulbul (text-to-speech)   -> Aria's voice

The diagnosis is computed deterministically in kam.py and injected into the
prompt, so the model phrases the numbers but can never invent them.

Run:  uvicorn app:app --reload --port 8000
"""

from __future__ import annotations

import base64
import os
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import kam


def load_env(path: str = ".env") -> None:
    p = Path(path)
    if not p.exists():
        return
    for line in p.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


load_env()

from sarvamai import SarvamAI  # noqa: E402

_KEY = os.environ.get("SARVAM_API_KEY")
if not _KEY:
    raise SystemExit("SARVAM_API_KEY is not set. Put it in .env")

client = SarvamAI(api_subscription_key=_KEY)

CHAT_MODEL = "sarvam-105b-conversations"
STT_MODEL = "saaras:v3"
TTS_MODEL = "bulbul:v3"
SPEAKER = {"hi-IN": "ritu_hi_customer", "en-IN": "ishita_en_customer", "bn-IN": "priya",
           "ta-IN": "priya", "te-IN": "kavitha_te_conversation", "mr-IN": "ishita_mr_conversational",
           "gu-IN": "pooja_gu_customer", "kn-IN": "chaitra_kn_conversation",
           "ml-IN": "priya", "pa-IN": "anand_pa_customer", "or-IN": "priya"}
# Fallback map: generic speaker per language for codes without a specialised voice
SPEAKER_FALLBACK = {"hi-IN": "priya", "en-IN": "ishita", "bn-IN": "priya", "ta-IN": "priya",
                    "te-IN": "priya", "mr-IN": "priya", "gu-IN": "priya", "kn-IN": "priya",
                    "ml-IN": "priya", "pa-IN": "priya", "or-IN": "priya"}

BASE_DIR = Path(__file__).resolve().parent
STATIC = BASE_DIR / "static"

app = FastAPI(title="Snapdeal Mini AI Voice KAM")

SYSTEM_PROMPT = f"""You are Aria, a warm and efficient Virtual Key Account Manager for Snapdeal, \
speaking to a seller on a VOICE call.

HOW TO SPEAK
- This is speech, not text: 1 to 2 short sentences per turn. No lists, no markdown, no emoji, no bullet points.
- Ask at most ONE question per turn.
- Use ONLY the numbers given below. Never invent, estimate or round a number.
- If the seller speaks Hindi or Hinglish, reply in the same language and script they used.

THE SELLER'S SITUATION
{kam.context_block()}

CONVERSATION FLOW
Greet and find the concern -> acknowledge it with their own numbers -> ask a few sharp diagnostic \
questions (price/offers, stock, cancellations) -> name the most likely cause -> give the three \
recommendations -> summarise and state the next step.

GUARDRAILS
- If asked about anything outside this seller's store, say you can only help with their Snapdeal store.
- Never promise a specific recovery figure; the impact numbers are estimates and you should say so.
- If the seller disputes the data, acknowledge it and offer to check the specific metric."""


DEVANAGARI = range(0x0900, 0x0980)
HINDI_ROMAN = ("hai", "nahi", "nahin", "mera", "meri", "aap", "aapka", "kya", "kyun", "kyu",
               "hua", "hui", "gaya", "gayi", "karo", "karna", "bhai", "yaar", "matlab", "batao",
               "chahiye", "raha", "rahi", "hoga", "kitna", "kaise", "accha", "theek")


def detect_lang(text: str, fallback: str = "en-IN") -> str:
    """Reply in the seller's language: Devanagari or romanised Hindi -> hi-IN."""
    if not text:
        return fallback
    if any(ord(ch) in DEVANAGARI for ch in text):
        return "hi-IN"
    words = {w.strip(".,!?;:'\"()").lower() for w in text.split()}
    if len(words & set(HINDI_ROMAN)) >= 2:
        return "hi-IN"
    return "en-IN"


def stage_directive(n_user_turns: int) -> str:
    """Keeps the call on the assignment's rails without killing the model's naturalness."""
    if n_user_turns <= 1:
        return "STAGE: open the call. Greet the seller warmly and ask what has been happening with their sales."
    if n_user_turns == 2:
        return "STAGE: acknowledge their concern using their real numbers, then ask whether they changed prices or ran offers."
    if n_user_turns == 3:
        return "STAGE: ask about stock — are their top products showing out of stock?"
    if n_user_turns == 4:
        return "STAGE: ask whether cancellations or returns have increased."
    if n_user_turns == 5:
        return "STAGE: state the most likely cause in one sentence, then give the three recommendations briefly. Offer a summary."
    if n_user_turns == 6:
        return "STAGE: give a tight summary — the issue, the three actions, and the next step."
    return ("STAGE: answer the seller's question in one or two sentences, then close with a one-line "
            "summary of the issue, the three actions, and the next step.")


class ChatRequest(BaseModel):
    messages: list[dict]
    lang: str = "en-IN"


class TtsRequest(BaseModel):
    text: str
    lang: str = "en-IN"


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "chat": CHAT_MODEL, "stt": STT_MODEL, "tts": TTS_MODEL}


@app.post("/api/chat")
def chat(req: ChatRequest) -> dict:
    msgs = [m for m in req.messages if m.get("role") in ("user", "assistant") and m.get("content")]
    n_user = sum(1 for m in msgs if m["role"] == "user")

    last_user = next((m["content"] for m in reversed(msgs) if m["role"] == "user"), "")
    lang = detect_lang(last_user, req.lang)
    lang_name = "Hindi (Devanagari script)" if lang == "hi-IN" else "English"

    payload = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "system", "content":
            f"LANGUAGE: reply ONLY in {lang_name}. Do not switch language unless the seller does. "
            f"Write numbers the way they are spoken."},
        {"role": "system", "content": stage_directive(n_user)},
        *[{"role": m["role"], "content": m["content"]} for m in msgs],
    ]

    try:
        resp = client.chat.completions(
            messages=payload, model=CHAT_MODEL,
            temperature=0.4, max_tokens=220, reasoning_effort="low",
        )
        reply = (resp.choices[0].message.content or "").strip()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"chat model failed: {type(exc).__name__}") from exc

    if not reply:
        raise HTTPException(status_code=502, detail="chat model returned an empty reply")

    d = kam.diagnose()
    return {
        "reply": reply,
        "lang": lang,
        "diagnosis": {
            "primary": d["primary"],
            "confidence": d["confidence"],
            "signals": d["signals"],
            "metrics": {k: {"label": v["label"], "last": v["last"], "this": v["this"],
                            "pct": v["pct"], "unit": v["unit"]} for k, v in d["metrics"].items()},
        },
        "recommendations": kam.recommendations(d),
    }


@app.post("/api/stt")
async def stt(file: UploadFile = File(...), lang: str = "unknown") -> dict:
    audio = await file.read()
    if not audio:
        raise HTTPException(status_code=400, detail="empty audio")
    try:
        res = client.speech_to_text.transcribe(
            file=(file.filename or "audio.webm", audio, file.content_type or "audio/webm"),
            model=STT_MODEL, mode="transcribe", language_code=lang or "unknown",
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"speech-to-text failed: {type(exc).__name__}") from exc
    return {"transcript": (res.transcript or "").strip(),
            "language_code": getattr(res, "language_code", None)}


@app.post("/api/tts")
def tts(req: TtsRequest) -> Response:
    text = req.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="empty text")
    lang = req.lang if req.lang in SPEAKER else "en-IN"
    speaker = SPEAKER.get(lang, "ishita")
    try:
        res = client.text_to_speech.convert(
            text=text[:490], language_code=lang, speaker=speaker,
            model=TTS_MODEL, output_audio_codec="wav",
        )
        audio = base64.b64decode(res.audios[0])
    except Exception:  # noqa: BLE001
        # Fall back to a generic speaker if the specialised one is unavailable
        fallback = SPEAKER_FALLBACK.get(lang, "ishita")
        if fallback != speaker:
            try:
                res = client.text_to_speech.convert(
                    text=text[:490], language_code=lang, speaker=fallback,
                    model=TTS_MODEL, output_audio_codec="wav",
                )
                audio = base64.b64decode(res.audios[0])
            except Exception as exc2:  # noqa: BLE001
                raise HTTPException(status_code=502, detail=f"text-to-speech failed: {type(exc2).__name__}") from exc2
        else:
            raise HTTPException(status_code=502, detail="text-to-speech failed") from None
    return Response(content=audio, media_type="audio/wav")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC / "index.html")


app.mount("/static", StaticFiles(directory=STATIC), name="static")
