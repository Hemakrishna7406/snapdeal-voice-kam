"""End-to-end pipeline test: Audio -> STT -> Chat -> TTS."""
import httpx

base = "http://127.0.0.1:8000"

print("--- Step 1: Synthesizing mock seller speech using Sarvam Bulbul TTS ---")
tts_prep = httpx.post(f"{base}/api/tts", json={
    "text": "Hi, my sales have dropped significantly this month and I do not understand why. Can you help me?",
    "lang": "en-IN"
}, timeout=30)
assert tts_prep.status_code == 200, f"TTS prep failed: {tts_prep.text}"
audio_bytes = tts_prep.content
print(f"Generated test audio: {len(audio_bytes)} bytes WAV")

print("\n--- Step 2: Testing STT (/api/stt) via Sarvam Saaras ---")
files = {"file": ("seller_sample.wav", audio_bytes, "audio/wav")}
stt_res = httpx.post(f"{base}/api/stt?lang=en-IN", files=files, timeout=30)
assert stt_res.status_code == 200, f"STT failed: {stt_res.text}"
stt_data = stt_res.json()
transcript = stt_data.get("transcript", "")
print(f"STT Transcript: \"{transcript}\"")
print(f"Detected Lang:  {stt_data.get('language_code')}")

print("\n--- Step 3: Testing Chat (/api/chat) via Sarvam-105B ---")
chat_res = httpx.post(f"{base}/api/chat", json={
    "messages": [
        {"role": "user", "content": "(The seller has just connected to the call.)"},
        {"role": "assistant", "content": "Hi there, I am Aria from Snapdeal. I see your sales dropped this month. What has been happening?"},
        {"role": "user", "content": transcript}
    ],
    "lang": "en-IN"
}, timeout=30)
assert chat_res.status_code == 200, f"Chat failed: {chat_res.text}"
chat_data = chat_res.json()
reply = chat_data.get("reply", "")
print(f"Aria Reply:     \"{reply}\"")
print(f"Primary Cause:  {chat_data.get('diagnosis', {}).get('primary')}")
print(f"Confidence:     {chat_data.get('diagnosis', {}).get('confidence')}")
print(f"Recommendations count: {len(chat_data.get('recommendations', []))}")

print("\n--- Step 4: Testing TTS (/api/tts) for Aria's reply ---")
final_tts = httpx.post(f"{base}/api/tts", json={"text": reply, "lang": "en-IN"}, timeout=30)
assert final_tts.status_code == 200, f"Final TTS failed: {final_tts.text}"
print(f"Aria's audio response: {len(final_tts.content)} bytes WAV (Header: {final_tts.content[:4]})")

print("\n" + "="*50)
print("SUCCESS: Full pipeline (Audio -> STT -> Chat -> TTS) verified!")
print("="*50)

