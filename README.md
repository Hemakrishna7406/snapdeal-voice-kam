# Snapdeal · Mini AI Voice KAM (Sarvam)

A voice-first Virtual Key Account Manager for Snapdeal sellers. The seller speaks,
Aria listens, asks the right questions, names the real cause of the sales drop and
gives three actions with an estimated impact.

**Sarvam does all three AI jobs:** speech-to-text, the conversation, and the voice.

| Stage | Model | Why |
|---|---|---|
| Speech → text | `saaras:v3` (auto language detect) | Handles English, Hindi and Hinglish without forcing a language |
| Understanding + reply | `sarvam-105b-conversations` | Conversation-tuned, follows the KAM flow |
| Text → speech | `bulbul:v3` | Indian voices (`ishita` for English, `priya` for Hindi) |

## Run it

```bash
pip install -r requirements.txt
# .env must contain: SARVAM_API_KEY=...
uvicorn app:app --reload --port 8000
```

Open **http://127.0.0.1:8000** in Chrome or Edge (they support microphone capture).

- **Start talking** — speak as the seller; tap again to stop and send.
- **Play demo** — runs a scripted 6-turn call through the real Sarvam pipeline (use this if your mic is noisy).
- Language selector switches Aria's voice; she also auto-detects the seller's language per turn.

## How it is built

```
browser (MediaRecorder)
   │  audio/webm
   ▼
POST /api/stt   → Sarvam Saaras        → transcript
POST /api/chat  → Sarvam-105B          → Aria's reply  (+ diagnosis + recommendations)
POST /api/tts   → Sarvam Bulbul        → WAV  → played in the browser
```

- `kam.py` — the seller data and the diagnosis, computed **deterministically**. The
  numbers and the reasoning are never left to the model; they are injected into the
  system prompt so Aria can phrase them but cannot invent them.
- `app.py` — FastAPI: static page + the three endpoints. The API key stays server-side
  in `.env` and never reaches the browser.
- `static/index.html` — the voice client: push-to-talk, barge-in (talking stops Aria),
  live transcript, data panel and live diagnosis panel.

## The diagnosis (the part that matters)

The obvious answer to "sales are down" is "cut your price". The data refuses it:

- Sales ₹2,00,000 → ₹1,35,000 (**−32.5%**)
- Orders 400 → 270 (**−32.5%**)
- Average selling price ₹500 → ₹500 (**flat**)
- Cancellation rate 8% → 14%
- Out-of-stock SKUs 5 → 18

Revenue and units fell by the *same* percentage while the price did not move — so the
loss is **volume, not price**. Volume is explained by cancellations and stock-outs,
which also suppress search ranking. Hence: restock → fix cancellations → then spend on
visibility (ads before stock would buy traffic that cannot convert).

## Assumptions

- All data is the mock table supplied with the assignment; impact figures are labelled estimates.
- The key lives in `.env`, which is git-ignored. Rotate it if it has ever been shared.
- A real deployment would put this behind Twilio/Vapi for phone calls; the browser
  client was chosen to fit the assignment's scope.
