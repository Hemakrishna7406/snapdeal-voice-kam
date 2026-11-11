# 90-second screen-recording script (Sarvam build)

Start the server first: `uvicorn app:app --port 8000`, then open http://127.0.0.1:8000 in Chrome.

| Time | Do this | What should happen |
|---|---|---|
| 0:00 | Show the terminal with `uvicorn` running, then the browser page | Aria greets you **out loud** (Sarvam Bulbul); header shows Saaras / Sarvam-105B / Bulbul |
| 0:10 | Point at the seller-data panel | Sales ₹2,00,000 → ₹1,35,000, orders 400 → 270, cancellations 8% → 14%, OOS 5 → 18 |
| 0:15 | Click **Start talking**, say: *"Hi, my sales have dropped significantly this month and I don't understand why."* | She reads the real numbers back and asks about price/offers |
| 0:30 | *"No, I haven't changed prices or run any offers."* | Notes ASP is flat, asks about stock |
| 0:42 | *"Actually yes, a few of my top products are showing out of stock."* | Asks about cancellations |
| 0:52 | *"Yes, cancellations have gone up quite a bit this month."* | Names the cause and gives three actions; right panel fills in |
| 1:05 | *"Why do you think it's stock and not pricing?"* | Explains sales and orders both fell 32.5% while price stayed flat |
| 1:15 | *"That makes sense, thank you."* | Recap + next step |
| 1:22 | Switch the language selector to **हिन्दी**, ask one question in Hindi | She answers in Hindi with the priya voice |

**Shortcut:** if your mic is noisy, click **Play demo** — it runs the same six turns through the real Sarvam pipeline while you record.
Keep it under 2 minutes.
