"""Deterministic KAM analytics for the Snapdeal seller data.

Kept out of the LLM on purpose: the numbers and the diagnosis are computed here,
so the model can phrase them but can never invent them.
"""

from __future__ import annotations

SELLER = {
    "sales": {"last": 200000, "this": 135000, "label": "Sales", "unit": "₹"},
    "orders": {"last": 400, "this": 270, "label": "Orders", "unit": ""},
    "cancel": {"last": 8, "this": 14, "label": "Cancellation rate", "unit": "%"},
    "asp": {"last": 500, "this": 500, "label": "Average selling price", "unit": "₹"},
    "oos": {"last": 5, "this": 18, "label": "Out-of-stock SKUs", "unit": ""},
}


def inr(n: float) -> str:
    """₹1,35,000 — Indian digit grouping."""
    s = f"{round(n):,}"
    if "." in s:
        s = s.split(".")[0]
    # 135,000 -> 1,35,000
    digits = str(abs(round(n)))
    if len(digits) > 3:
        head, tail = digits[:-3], digits[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        s = ",".join(parts) + "," + tail
    else:
        s = digits
    return ("-" if n < 0 else "") + "₹" + s


def metrics() -> dict:
    out = {}
    for k, d in SELLER.items():
        pct = 0.0 if d["last"] == 0 else (d["this"] - d["last"]) / d["last"] * 100
        out[k] = {**d, "pct": round(pct, 1), "abs": d["this"] - d["last"]}
    return out


def diagnose() -> dict:
    """The core insight: revenue and units fall equally while ASP is flat,
    so the loss is volume — driven by stock-outs and cancellations."""
    m = metrics()
    signals, score = [], 0

    volume_driven = abs(m["asp"]["pct"]) < 1 and abs(m["sales"]["pct"] - m["orders"]["pct"]) < 3
    if volume_driven:
        signals.append({"key": "price", "level": "ok",
                        "text": f"Price is not the problem — ASP flat at {inr(SELLER['asp']['this'])}"})
    elif m["asp"]["pct"] < -1:
        signals.append({"key": "price", "level": "warn",
                        "text": f"Average price fell {abs(m['asp']['pct'])}%"})
        score += 1

    if m["cancel"]["abs"] >= 3:
        signals.append({"key": "cancel", "level": "bad",
                        "text": f"Cancellations {SELLER['cancel']['last']}% → {SELLER['cancel']['this']}% "
                                f"(+{m['cancel']['abs']} pts)"})
        score += 2
    if m["oos"]["abs"] >= 5:
        signals.append({"key": "oos", "level": "bad",
                        "text": f"Out-of-stock SKUs {SELLER['oos']['last']} → {SELLER['oos']['this']} "
                                f"({SELLER['oos']['this'] / SELLER['oos']['last']:.1f}×)"})
        score += 2
    if m["orders"]["pct"] <= -20:
        signals.append({"key": "orders", "level": "bad",
                        "text": f"Orders down {abs(m['orders']['pct'])}%"})
        score += 1

    if m["cancel"]["abs"] >= 3 and m["oos"]["abs"] >= 5:
        primary = "Stock-outs and cancellations, not pricing"
    elif m["oos"]["abs"] >= 5:
        primary = "Stock-outs"
    elif m["cancel"]["abs"] >= 3:
        primary = "Cancellation spike"
    else:
        primary = "Visibility and traffic"

    return {
        "metrics": m,
        "signals": signals,
        "primary": primary,
        "confidence": "high" if score >= 5 else "medium" if score >= 3 else "low",
        "revenue_gap": SELLER["sales"]["last"] - SELLER["sales"]["this"],
    }


def recommendations(d: dict | None = None) -> list[dict]:
    d = d or diagnose()
    m, gap = d["metrics"], d["revenue_gap"]
    recs = []

    if m["oos"]["abs"] >= 5:
        recs.append({
            "title": f"Restock your top {SELLER['oos']['this']} out-of-stock SKUs first",
            "why": "Stock-outs lose the sale outright and push your listings down in search.",
            "impact": f"Recovering even half could be worth roughly {inr(gap * 0.18)}–{inr(gap * 0.25)}/month (estimate)",
        })
    if m["cancel"]["abs"] >= 3:
        monthly = round(SELLER["orders"]["this"] * SELLER["cancel"]["this"] / 100)
        recs.append({
            "title": "Bring cancellations back under 9%",
            "why": f"At {SELLER['cancel']['this']}% you cancel about {monthly} orders a month, and a high rate lowers your ranking.",
            "impact": f"Each point of cancellation is ~{round(SELLER['orders']['this'] / 100)} orders — packaging and dispatch SLA is the fastest lever (estimate)",
        })
    recs.append({
        "title": "Fix visibility after stock is healthy",
        "why": "OOS and cancellations suppress ranking, so ads now would pay for traffic you cannot convert.",
        "impact": "Re-list restored SKUs, then run a small ad test on your 3 best sellers (estimate)",
    })
    return recs[:3]


def context_block() -> str:
    """Compact, exact facts injected into the LLM system prompt."""
    d = diagnose()
    m = d["metrics"]
    lines = [
        "SELLER DATA (last month -> this month):",
        f"- Sales: {inr(SELLER['sales']['last'])} -> {inr(SELLER['sales']['this'])} ({m['sales']['pct']:+.1f}%)",
        f"- Orders: {SELLER['orders']['last']} -> {SELLER['orders']['this']} ({m['orders']['pct']:+.1f}%)",
        f"- Cancellation rate: {SELLER['cancel']['last']}% -> {SELLER['cancel']['this']}% ({m['cancel']['abs']:+d} pts)",
        f"- Average selling price: {inr(SELLER['asp']['last'])} -> {inr(SELLER['asp']['this'])} (flat)",
        f"- Out-of-stock SKUs: {SELLER['oos']['last']} -> {SELLER['oos']['this']}",
        "",
        f"COMPUTED DIAGNOSIS: {d['primary']} (confidence: {d['confidence']}).",
        "Key reasoning: sales and orders fell by the same percentage while the average selling "
        "price stayed flat, so the loss is in units sold, not in price.",
        "",
        "RECOMMENDATIONS (use these, do not invent others):",
    ]
    for i, r in enumerate(recommendations(d), 1):
        lines.append(f"{i}. {r['title']} — {r['why']} Impact: {r['impact']}")
    return "\n".join(lines)
