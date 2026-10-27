import os
import json
import re

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="AI Email Assistant",
    page_icon="📧",
    layout="wide",
)

# -----------------------------
# SAMPLE EMAILS
# -----------------------------

SAMPLES = {
    "Delivery Complaint": (
        "Subject: Urgent - Order Not Delivered\n\n"
        "Hello,\n\n"
        "I placed an order five days ago, but I still haven't "
        "received my package. The tracking information hasn't "
        "been updated for three days, and I need the order "
        "before Friday.\n\n"
        "Could you please check the delivery status?\n\n"
        "Thank you,\nSarah"
    ),
    "Refund Request": (
        "Hello,\n\n"
        "I would like to request a refund for my recent order. "
        "The product was damaged when it arrived.\n\n"
        "Thank you."
    ),
    "Booking Question": (
        "Hello,\n\n"
        "I would like to book an appointment next Tuesday. "
        "Could you please let me know your availability?"
    ),
    "Invoice Question": (
        "Hello,\n\n"
        "I have a question about invoice 12345. "
        "Could you explain the additional charge?"
    ),
    "General Question": (
        "Hello,\n\n"
        "Could you please tell me your opening hours "
        "during the weekend?\n\n"
        "Thank you."
    ),
}

# -----------------------------
# CATEGORY KEYWORDS
# -----------------------------

CATEGORIES = {
    "Refund Request": [
        "refund",
        "money back",
        "return my money",
        "reimbursement",
    ],
    "Booking": [
        "booking",
        "reservation",
        "appointment",
        "schedule a meeting",
        "book a",
    ],
    "Invoice / Payment": [
        "invoice",
        "payment",
        "charged",
        "billing",
        "receipt",
        "additional charge",
    ],
    "Complaint": [
        "complaint",
        "damaged",
        "broken",
        "not arrived",
        "haven't received",
        "have not received",
        "didn't receive",
        "not delivered",
        "order not delivered",
        "delivery status",
        "tracking information",
        "tracking number",
        "late delivery",
        "missing package",
        "disappointed",
        "delayed order",
        "package is late",
    ],
}

# -----------------------------
# RESPONSE TEMPLATES
# -----------------------------

REPLIES = {
    "Refund Request": (
        "Hello,\n\n"
        "Thank you for contacting us. We're sorry to hear "
        "about the issue with your order.\n\n"
        "We would be happy to review your refund request. "
        "Could you please provide your order number and "
        "any relevant details?\n\n"
        "Once we receive this information, we can "
        "investigate further.\n\n"
        "Best regards,\nCustomer Support Team"
    ),
    "Booking": (
        "Hello,\n\n"
        "Thank you for your message.\n\n"
        "We would be happy to help with your booking. "
        "Please share your preferred date and time, "
        "and we'll check availability.\n\n"
        "Best regards,\nCustomer Support Team"
    ),
    "Invoice / Payment": (
        "Hello,\n\n"
        "Thank you for reaching out.\n\n"
        "We'd be happy to review your billing question. "
        "Please provide your invoice or order number "
        "so we can investigate the charge.\n\n"
        "Best regards,\nCustomer Support Team"
    ),
    "Complaint": (
        "Hello,\n\n"
        "Thank you for bringing this issue to our attention. "
        "We're sorry to hear about the inconvenience.\n\n"
        "We understand your concern and would like to "
        "investigate the situation. Could you please "
        "share your order number and any relevant details?\n\n"
        "Once we have this information, we can look "
        "into the issue further.\n\n"
        "Best regards,\nCustomer Support Team"
    ),
    "General Question": (
        "Hello,\n\n"
        "Thank you for contacting us.\n\n"
        "We'd be happy to help with your question. "
        "Please let us know if there are any additional "
        "details we should consider.\n\n"
        "Best regards,\nCustomer Support Team"
    ),
}

# -----------------------------
# DEMO ANALYSIS
# -----------------------------

def demo_analyze(email):
    text = email.lower()

    category = "General Question"

    for name, keywords in CATEGORIES.items():
        if any(keyword in text for keyword in keywords):
            category = name
            break

    high_priority_words = [
        "urgent",
        "asap",
        "immediately",
        "emergency",
        "critical",
        "before friday",
        "deadline",
    ]

    medium_priority_words = [
        "problem",
        "issue",
        "delay",
        "damaged",
        "not arrived",
        "haven't received",
        "not delivered",
        "refund",
    ]

    if any(word in text for word in high_priority_words):
        priority = "High"
    elif any(word in text for word in medium_priority_words):
        priority = "Medium"
    else:
        priority = "Low"

    # Rule-based summary, not an AI-generated summary.
    summary_templates = {
        "Refund Request": (
            "The customer is requesting a refund or "
            "assistance with returning a purchase."
        ),
        "Booking": (
            "The customer is asking about making "
            "or changing a booking."
        ),
        "Invoice / Payment": (
            "The customer has a question about "
            "an invoice, payment, or charge."
        ),
        "Complaint": (
            "The customer is reporting a problem "
            "with an order, product, or service."
        ),
        "General Question": (
            "The customer is requesting general information."
        ),
    }

    summary = summary_templates[category]

    if category == "Complaint":
        if any(
            word in text
            for word in [
                "not delivered",
                "haven't received",
                "not arrived",
                "tracking information",
                "delivery status",
            ]
        ):
            summary = (
                "The customer has not received their order "
                "and is requesting an update on its delivery."
            )

        elif "damaged" in text or "broken" in text:
            summary = (
                "The customer reports receiving a damaged "
                "or broken product."
            )

    if category == "Refund Request" and "damaged" in text:
        summary = (
            "The customer is requesting a refund "
            "because the product arrived damaged."
        )

    return {
        "category": category,
        "priority": priority,
        "summary": summary,
        "response": REPLIES[category],
    }


# -----------------------------
# AI ANALYSIS
# -----------------------------

def ai_analyze(email):
    from openai import OpenAI

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise ValueError("OPENAI_API_KEY is missing.")

    client = OpenAI(api_key=api_key)

    prompt = f"""
You are a professional customer support assistant.

Analyze the customer email below.

Return ONLY valid JSON with these keys:

{{
  "category": "Complaint | Refund Request | Booking | Invoice / Payment | General Question",
  "priority": "Low | Medium | High",
  "summary": "Concise summary of the customer's request",
  "response": "Professional, empathetic email response"
}}

Use only one value for category and priority.

Do not promise refunds, deliveries, or actions
that have not been confirmed.

Customer email:
{email}
"""

    ai_response = client.responses.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        input=prompt,
    )

    return json.loads(ai_response.output_text)


# -----------------------------
# INTERFACE
# -----------------------------

st.title("📧 AI Email Assistant")

st.caption(
    "Classify customer emails, detect priority, "
    "summarize requests, and draft professional replies."
)

with st.sidebar:
    st.header("⚙️ Settings")

    mode = st.radio(
        "Analysis Mode",
        [
            "Demo Mode (Free)",
            "AI Mode (API Required)",
        ],
    )

    st.info(
        "Demo Mode uses predefined rules and templates. "
        "AI Mode uses an external AI model."
    )

st.subheader("📨 Customer Email")

sample = st.selectbox(
    "Try a sample email",
    ["Custom Email"] + list(SAMPLES.keys()),
)

email = st.text_area(
    "Email Content",
    value=SAMPLES.get(sample, ""),
    height=220,
    placeholder="Paste a customer email here...",
    key=f"email_{sample}",
)

if "analysis" not in st.session_state:
    st.session_state.analysis = None

if st.button("🔍 Analyze Email", type="primary"):

    st.session_state.analysis = None

    if not email.strip():
        st.warning("Please enter a customer email.")

    else:
        with st.spinner("Analyzing email..."):
            try:
                if mode == "Demo Mode (Free)":
                    result = demo_analyze(email)
                else:
                    result = ai_analyze(email)

                required_fields = [
                    "category",
                    "priority",
                    "summary",
                    "response",
                ]

                if not isinstance(result, dict) or not all(
                    isinstance(result.get(field), str)
                    and result[field].strip()
                    for field in required_fields
                ):
                    raise ValueError(
                        "The analysis returned an invalid format."
                    )

                st.session_state.analysis = result

            except Exception as error:
                error_text = str(error).lower()

                if (
                    "insufficient_quota" in error_text
                    or "credit_balance_exhausted" in error_text
                ):
                    st.error(
                        "Your OpenAI API account has no remaining "
                        "credits. Switch to Demo Mode to continue."
                    )
                else:
                    st.error(
                        "Analysis failed. Please check your "
                        "configuration and try again."
                    )

# -----------------------------
# DISPLAY RESULTS
# -----------------------------

if st.session_state.analysis:

    result = st.session_state.analysis

    st.divider()

    st.subheader("📊 Email Analysis")

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "Category",
            result["category"],
        )

    with col2:
        st.metric(
            "Priority",
            result["priority"],
        )

    st.subheader("📝 Summary")
    st.info(result["summary"])

    st.subheader("✉️ Suggested Response")

    st.text_area(
        "Generated Reply",
        value=result["response"],
        height=260,
    )

    col1, col2 = st.columns(2)

    with col1:
        st.download_button(
            "⬇️ Download Analysis (JSON)",
            data=json.dumps(
                result,
                indent=2,
                ensure_ascii=False,
            ),
            file_name="email_analysis.json",
            mime="application/json",
        )

    with col2:
        st.download_button(
            "⬇️ Download Reply (TXT)",
            data=result["response"],
            file_name="suggested_reply.txt",
            mime="text/plain",
        )

    if mode == "Demo Mode (Free)":
        st.caption(
            "Demo result: generated using keyword rules "
            "and predefined response templates, not AI."
        )
