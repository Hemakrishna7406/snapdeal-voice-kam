"""One-page approach note — Sarvam build."""

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    ListFlowable, ListItem, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

S = getSampleStyleSheet()
NAVY = colors.HexColor("#1F3A5F")
BAND = colors.HexColor("#F3F5F8")
GREY = colors.HexColor("#5A6675")

TITLE = ParagraphStyle("t", parent=S["Title"], fontName="Helvetica-Bold", fontSize=15,
                       leading=18, alignment=TA_LEFT, spaceAfter=1)
SUB = ParagraphStyle("s", parent=S["Normal"], fontName="Helvetica", fontSize=8.3,
                     leading=10.4, textColor=GREY, spaceAfter=6)
H = ParagraphStyle("h", parent=S["Heading2"], fontName="Helvetica-Bold", fontSize=9.4,
                   leading=11.4, textColor=NAVY, spaceBefore=6.5, spaceAfter=2, keepWithNext=1)
B = ParagraphStyle("b", parent=S["Normal"], fontName="Helvetica", fontSize=8.3,
                   leading=10.9, spaceAfter=3.2)
CELL = ParagraphStyle("c", parent=B, fontSize=7.6, leading=9.4, spaceAfter=0)
HEAD = ParagraphStyle("ch", parent=CELL, fontName="Helvetica-Bold", textColor=colors.white)


def tbl(rows, fracs, w):
    t = Table(rows, colWidths=[f * w for f in fracs], repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("BACKGROUND", (0, 1), (-1, -1), BAND), ("TEXTCOLOR", (0, 1), (-1, -1), colors.HexColor("#1A1A1A")),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#9AA7B8")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 2.4), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.4),
        ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def bullets(items, kind="bullet"):
    return ListFlowable([ListItem(Paragraph(i, B)) for i in items],
                        bulletType=kind, leftIndent=12, bulletFontSize=7.2)


def build(path):
    doc = SimpleDocTemplate(path, pagesize=A4, leftMargin=0.58 * inch, rightMargin=0.58 * inch,
                            topMargin=0.48 * inch, bottomMargin=0.45 * inch,
                            title="Mini AI Voice KAM — approach note", author="Hema Krishna")
    W = doc.width
    st = []

    st.append(Paragraph("Mini AI Voice KAM — approach note", TITLE))
    st.append(Paragraph("Snapdeal AI First Intern · practical assignment · Hema Krishna · "
                        "runnable prototype: <font face='Courier'>uvicorn app:app</font>", SUB))

    st.append(Paragraph("What it does", H))
    st.append(Paragraph(
        "A voice-first Virtual Key Account Manager. The seller speaks; Aria transcribes, acknowledges the "
        "concern with the seller's own numbers, asks three diagnostic questions, names the most likely cause, "
        "gives three actions with an estimated impact, and closes with a summary and a next step. It is a "
        "conversation, not a form \u2014 the seller can interrupt, ask \u201cwhy\u201d, or push back at any point.", B))

    st.append(Paragraph("The AI stack \u2014 Sarvam for all three stages", H))
    rows = [[Paragraph("Stage", HEAD), Paragraph("Model", HEAD), Paragraph("Why this one", HEAD)],
            [Paragraph("Speech \u2192 text", CELL), Paragraph("Saaras <font face='Courier'>v3</font>", CELL),
             Paragraph("Auto-detects language, so an English-only seller and a Hinglish seller both work "
                       "without a setting", CELL)],
            [Paragraph("Understanding + reply", CELL), Paragraph("Sarvam-105B-conversations", CELL),
             Paragraph("Conversation-tuned; follows the KAM flow and keeps turns short and spoken", CELL)],
            [Paragraph("Text \u2192 speech", CELL), Paragraph("Bulbul <font face='Courier'>v3</font>", CELL),
             Paragraph("Indian voices \u2014 ishita (English) / priya (Hindi), correct rupee pronunciation", CELL)]]
    st.append(tbl(rows, [0.20, 0.24, 0.56], W))
    st.append(Spacer(1, 3))
    st.append(Paragraph(
        "All three go through the official <font face='Courier'>sarvamai</font> SDK. The key lives in "
        "<font face='Courier'>.env</font> on the server (git-ignored) and never reaches the browser.", B))

    st.append(Paragraph("Workflow", H))
    st.append(Paragraph(
        "Browser captures audio with MediaRecorder \u2192 <font face='Courier'>POST /api/stt</font> (Saaras) returns "
        "the transcript \u2192 <font face='Courier'>POST /api/chat</font> (Sarvam-105B) returns Aria's reply plus the "
        "diagnosis \u2192 <font face='Courier'>POST /api/tts</font> (Bulbul) returns WAV, played immediately. "
        "Starting the microphone stops her speech, so the seller can barge in.", B))

    st.append(Paragraph("Two design decisions worth defending", H))
    st.append(bullets([
        "<b>The diagnosis is computed in code, not by the model.</b> <font face='Courier'>kam.py</font> derives the "
        "cause and the numbers from the seller table; the model only phrases them. A language model that can "
        "invent a number is a liability on a call about money, so it is given the facts and forbidden to "
        "estimate. The LLM is used for what it is genuinely good at: natural, responsive conversation.",
        "<b>A stage directive keeps the call on the assignment's rails.</b> Each turn tells the model which part "
        "of the flow it is in (greet, probe stock, recommend, summarise). Without it the model drifts; with it, "
        "every call still hits all six required behaviours, while the wording stays natural.",
        "<b>Language is detected per turn, not configured once.</b> A seller who switches from English to Hindi "
        "mid-call is answered in Hindi from that turn on.",
    ]))

    st.append(Paragraph("The diagnosis, and why it is the interesting part", H))
    st.append(Paragraph(
        "The obvious answer to \u201csales are down\u201d is \u201clower your price\u201d. The data refuses it: sales fell "
        "32.5% and orders fell 32.5% while the average selling price stayed <b>flat at \u20b9500</b>. Revenue and "
        "units falling by the same percentage at an unchanged price means the loss is <b>volume, not price</b>. "
        "Two signals explain the volume: cancellations 8% \u2192 14% and out-of-stock SKUs 5 \u2192 18 (3.6\u00d7). Both "
        "remove units and both depress search ranking. So: restock the 18 SKUs, bring cancellations under 9%, "
        "and only then spend on visibility \u2014 ads before stock would pay for traffic that cannot convert.", B))

    st.append(Paragraph("Assumptions and limitations", H))
    st.append(bullets([
        "All data is the mock table supplied with the assignment; impact figures are labelled estimates, not forecasts.",
        "Needs a Chromium browser for microphone capture; the Play-demo button exercises the same pipeline without a mic.",
        "The browser client was chosen over telephony (Twilio/Vapi) to fit the assignment scope; the backend would carry over unchanged.",
        "A production version would add barge-in on the STT stream, per-seller data lookup, and a written-summary export.",
    ]))

    doc.build(st)
    return path


if __name__ == "__main__":
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else "Snapdeal_Voice_KAM_Note.pdf"
    print("Wrote", build(out))
