"""One working Sarvam chat call.

The key is read from the environment (loaded from .env). It is never hardcoded
and never printed.

Run:  python sarvam_smoke.py
"""

from __future__ import annotations

import os
from pathlib import Path


def load_env(path: str = ".env") -> None:
    """Minimal .env loader — avoids pulling in an extra dependency."""
    p = Path(path)
    if not p.exists():
        return
    for line in p.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


load_env()

from sarvamai import SarvamAI  # noqa: E402  (import after env is loaded)

key = os.environ.get("SARVAM_API_KEY")
if not key:
    raise SystemExit("SARVAM_API_KEY is not set. Put it in .env as SARVAM_API_KEY=...")

client = SarvamAI(api_subscription_key=key)

response = client.chat.completions(
    messages=[
        {"role": "system", "content": "You are a concise assistant."},
        {"role": "user", "content": "In one sentence, what does a key account manager do for an online seller?"},
    ],
    model="sarvam-105b-conversations",
    temperature=0.3,
    max_tokens=120,
)

print(response.choices[0].message.content)
