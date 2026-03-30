import streamlit as st
import pandas as pd
import time
from datetime import date, datetime, timedelta
import os
import numpy as np
import requests
import asyncio



# -----------------------------------------------------------------------------
# 1. PAGE CONFIGURATION & DARK THEME CSS
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Domain Specific AI Platform",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# COLOR PALETTE (Dark Mode)
# Background: #0E1117 (Streamlit Dark)
# Card BG: #1E1E1E
# Accent: #00ADB5 (Cyber Cyan)
# Text: #FAFAFA

st.markdown("""
<style>
    /* ── Fonts ─────────────────────────────────────────────────────── */
    @import url('https://fonts.googleapis.com/css2?family=Figtree:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500&display=swap');

    /* ── CSS Variables ──────────────────────────────────────────────── */
    :root {
        --bg:        #000000;
        --surface:   #0a0a0a;
        --surface2:  #141414;
        --border:    rgba(255,255,255,0.08);
        --border-hi: rgba(0,210,180,0.3);
        --accent:    #00d2b4;
        --accent2:   #0071e3;
        --accent3:   #f5a623;
        --danger:    #ff3b30;
        --text:      #f5f5f7;
        --text-sub:  #86868b;
        --text-dim:  #424245;
        --glow:      0 0 40px rgba(0,210,180,0.1);
        --font:      'Figtree', -apple-system, BlinkMacSystemFont, 'SF Pro Display', sans-serif;
        --mono:      'JetBrains Mono', 'SF Mono', monospace;
    }

    /* ── Base ───────────────────────────────────────────────────────── */
    html, body, .stApp {
        background-color: var(--bg) !important;
        font-family: var(--font);
        color: var(--text);
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }

    /* ── Typography ─────────────────────────────────────────────────── */
    h1, h2, h3, h4 {
        font-family: var(--font) !important;
        font-weight: 700 !important;
        letter-spacing: -0.025em !important;
        color: var(--text) !important;
        line-height: 1.15 !important;
    }

    /* ── Sidebar ────────────────────────────────────────────────────── */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0a0a0a 0%, #050505 100%) !important;
        border-right: 1px solid var(--border) !important;
        box-shadow: 4px 0 40px rgba(0,0,0,0.6);
    }
    section[data-testid="stSidebar"] > div {
        padding-top: 1.5rem;
    }

    /* Sidebar nav radio buttons */
    .stRadio > div {
        gap: 4px;
    }
    .stRadio label {
        background: transparent !important;
        border-radius: 8px !important;
        padding: 10px 14px !important;
        transition: all 0.2s ease !important;
        border: 1px solid transparent !important;
        font-family: var(--font) !important;
        font-size: 0.9rem !important;
        color: var(--text-sub) !important;
        cursor: pointer !important;
    }
    .stRadio label:hover {
        background: rgba(0,210,180,0.07) !important;
        border-color: rgba(0,210,180,0.2) !important;
        color: var(--text) !important;
    }
    .stRadio label[data-checked="true"] {
        background: rgba(0,210,180,0.1) !important;
        border-color: var(--border-hi) !important;
        color: var(--accent) !important;
    }

    /* ── Cards ──────────────────────────────────────────────────────── */
    .css-card {
        background: linear-gradient(135deg, #141414 0%, #0a0a0a 100%);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.04);
        transition: transform 0.25s cubic-bezier(.4,0,.2,1),
                    box-shadow 0.25s cubic-bezier(.4,0,.2,1),
                    border-color 0.25s ease;
        position: relative;
        overflow: hidden;
    }
    .css-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(0,210,180,0.4), transparent);
        opacity: 0;
        transition: opacity 0.3s ease;
    }
    .css-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 20px 60px rgba(0,0,0,0.5), var(--glow);
        border-color: var(--border-hi);
    }
    .css-card:hover::before {
        opacity: 1;
    }

    /* ── Metric tiles ───────────────────────────────────────────────── */
    .metric-value {
        font-family: var(--mono);
        font-size: 2rem;
        font-weight: 500;
        color: var(--accent);
        line-height: 1.1;
        letter-spacing: -0.03em;
    }
    .metric-label {
        color: var(--text-sub);
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 0.15em;
        font-weight: 600;
        margin-bottom: 6px;
    }
    .metric-sub {
        color: var(--text-dim);
        font-size: 0.75rem;
        margin-top: 4px;
    }

    /* ── Buttons ────────────────────────────────────────────────────── */
    div.stButton > button {
        background: linear-gradient(135deg, #00d2b4 0%, #0099ff 100%) !important;
        color: #07090f !important;
        border: none !important;
        border-radius: 10px !important;
        font-family: var(--font) !important;
        font-weight: 700 !important;
        font-size: 0.85rem !important;
        letter-spacing: 0.04em !important;
        padding: 0.55rem 1.4rem !important;
        transition: all 0.2s cubic-bezier(.4,0,.2,1) !important;
        box-shadow: 0 4px 20px rgba(0,210,180,0.25) !important;
    }
    div.stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 30px rgba(0,210,180,0.4) !important;
        color: #07090f !important;
    }
    div.stButton > button:active {
        transform: translateY(0) !important;
    }

    /* ── Inputs & selects ───────────────────────────────────────────── */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div,
    .stDateInput > div > div > input {
        background-color: #111827 !important;
        border: 1px solid var(--border) !important;
        border-radius: 10px !important;
        color: var(--text) !important;
        font-family: var(--font) !important;
        transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
    }
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus {
        border-color: var(--border-hi) !important;
        box-shadow: 0 0 0 3px rgba(0,210,180,0.12) !important;
    }

    /* Slider */
    .stSlider > div > div > div > div {
        background: linear-gradient(90deg, var(--accent), var(--accent2)) !important;
    }

    /* ── Chat ───────────────────────────────────────────────────────── */
    .stChatMessage {
        background: #111827 !important;
        border: 1px solid var(--border) !important;
        border-radius: 14px !important;
        padding: 1rem 1.2rem !important;
    }
    .stChatInputContainer {
        background: #0d1117 !important;
        border: 1px solid var(--border) !important;
        border-radius: 14px !important;
    }
    .stChatInputContainer > div > textarea {
        background: transparent !important;
        color: var(--text) !important;
        font-family: var(--font) !important;
    }

    /* ── Dataframe / table ──────────────────────────────────────────── */
    .stDataFrame {
        border: 1px solid var(--border) !important;
        border-radius: 14px !important;
        overflow: hidden !important;
    }

    /* ── Divider ────────────────────────────────────────────────────── */
    hr {
        border: none !important;
        border-top: 1px solid var(--border) !important;
        margin: 1.2rem 0 !important;
    }

    /* ── Status badges ──────────────────────────────────────────────── */
    .badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 999px;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.06em;
        font-family: var(--mono);
    }
    .badge-critical { background: rgba(239,68,68,0.15);  color: #f87171; border: 1px solid rgba(239,68,68,0.3); }
    .badge-high     { background: rgba(245,158,11,0.15); color: #fbbf24; border: 1px solid rgba(245,158,11,0.3); }
    .badge-medium   { background: rgba(59,130,246,0.15); color: #60a5fa; border: 1px solid rgba(59,130,246,0.3); }
    .badge-low      { background: rgba(0,210,180,0.12);  color: #00d2b4; border: 1px solid rgba(0,210,180,0.25); }

    /* ── Scrollbar ──────────────────────────────────────────────────── */
    ::-webkit-scrollbar       { width: 5px; height: 5px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: #1e293b; border-radius: 999px; }
    ::-webkit-scrollbar-thumb:hover { background: var(--accent); }

    /* ── Streamlit overrides ────────────────────────────────────────── */
    .stAlert {
        border-radius: 12px !important;
        border: 1px solid var(--border) !important;
    }
    .stSuccess { background: rgba(0,210,180,0.08) !important; border-color: rgba(0,210,180,0.3) !important; }
    .stWarning { background: rgba(245,158,11,0.08) !important; border-color: rgba(245,158,11,0.3) !important; }
    .stError   { background: rgba(239,68,68,0.08)  !important; border-color: rgba(239,68,68,0.3)  !important; }
    .stInfo    { background: rgba(59,130,246,0.08)  !important; border-color: rgba(59,130,246,0.3)  !important; }

    /* ── Caption & small text ───────────────────────────────────────── */
    .stCaption, small, .stMarkdown p:has(small) {
        color: var(--text-sub) !important;
        font-size: 0.78rem !important;
    }

    /* ── Form container ─────────────────────────────────────────────── */
    .stForm {
        background: #0d1117 !important;
        border: 1px solid var(--border) !important;
        border-radius: 16px !important;
        padding: 1.2rem !important;
    }

    /* ── Expander ───────────────────────────────────────────────────── */
    .streamlit-expanderHeader {
        background: #111827 !important;
        border-radius: 10px !important;
        font-family: var(--font) !important;
        font-weight: 600 !important;
    }

    /* ── Tabs ───────────────────────────────────────────────────────── */
    .stTabs [data-baseweb="tab-list"] {
        background: transparent !important;
        border-bottom: 1px solid var(--border) !important;
        gap: 0 !important;
    }
    .stTabs [data-baseweb="tab"] {
        background: transparent !important;
        border-radius: 8px 8px 0 0 !important;
        color: var(--text-sub) !important;
        font-family: var(--font) !important;
        font-weight: 600 !important;
        padding: 10px 20px !important;
        border: none !important;
    }
    .stTabs [aria-selected="true"] {
        color: var(--accent) !important;
        border-bottom: 2px solid var(--accent) !important;
    }

    /* ── Multiselect tags ───────────────────────────────────────────── */
    .stMultiSelect span[data-baseweb="tag"] {
        background: rgba(0,210,180,0.15) !important;
        border: 1px solid rgba(0,210,180,0.3) !important;
        border-radius: 6px !important;
        color: var(--accent) !important;
    }

    /* ── Plotly chart bg ────────────────────────────────────────────── */
    .js-plotly-plot .plotly .bg {
        fill: transparent !important;
    }

    /* ── Spinner ────────────────────────────────────────────────────── */
    .stSpinner > div {
        border-top-color: var(--accent) !important;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. SESSION STATE & MOCK DATA
# -----------------------------------------------------------------------------
if "login_state" not in st.session_state:
    st.session_state.login_state = False
if "user_role" not in st.session_state:
    st.session_state.user_role = "Student"


if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant",
         "content": "Welcome. I am your Domain Specific AI Assistant. I can help with University policies, Task Prioritization, and Course Recommendations."}
    ]

# Initial Chat History
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant",
         "content": "Welcome. I am your Domain Specific AI Assistant. I can help with University policies, Task Prioritization, and Course Recommendations."}
    ]

# Initial Tasks
if "tasks_df" not in st.session_state:
    data = {
        "Task": ["Final Year Project Proposal", "Machine Learning Assignment 1", "Research Methodology Review",
                 "Course Registration"],
        "Module": ["PROJ400", "ML201", "RES301", "ADMIN"],
        "Deadline": [date.today() + timedelta(days=2), date.today() + timedelta(days=10),
                     date.today() + timedelta(days=5), date.today() + timedelta(days=1)],
        "Priority": ["Critical", "Medium", "High", "Low"],
        "Status": ["In Progress", "Not Started", "Not Started", "Done"],
        "Progress": [65, 0, 10, 100]
    }
    st.session_state.tasks_df = pd.DataFrame(data)

if "saved_courses" not in st.session_state:
    st.session_state.saved_courses = []




# -----------------------------------------------------------------------------
# 8. MODULE: CHAT ASSISTANT
# -----------------------------------------------------------------------------


from rag_client import send_rag_query_event, wait_for_run_output
import nest_asyncio
nest_asyncio.apply()

def query_rag(user_input: str) -> str:
    """Send question to RAG pipeline via Inngest and wait for response."""
    try:
        event_id = asyncio.get_event_loop().run_until_complete(
            send_rag_query_event(question=user_input, top_k=5)
        )
        output = wait_for_run_output(event_id, timeout_s=120)
        return output.get("answer") or output.get("response") or str(output)

    except TimeoutError:
        return "⚠️ The RAG pipeline timed out. Please try again."
    except requests.exceptions.ConnectionError:
        return "⚠️ Cannot connect to Inngest. Make sure `inngest dev` is running."
    except Exception as e:
        return f"⚠️ Error: {str(e)}"

def stream_text(text: str, delay: float = 0.015):
    """Simulate streaming by yielding characters."""
    for char in text:
        yield char
        time.sleep(delay)

def handle_response(user_input: str):
    """Query RAG, stream the reply, persist both messages."""
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("🔍 Searching knowledge base..."):
            full_resp = query_rag(user_input)

        placeholder = st.empty()
        streamed = ""
        for chunk in stream_text(full_resp):
            streamed += chunk
            placeholder.markdown(streamed + "▌")
        placeholder.markdown(streamed)

        st.session_state.messages.append({"role": "assistant", "content": streamed})

# ─── Layout ───────────────────────────────────────────────
col_chat, col_info = st.columns([3, 1])

with col_info:
    st.markdown('<div class="css-card">', unsafe_allow_html=True)
    st.markdown("#### 💡 Quick Prompts")

    prompts = [
        "What are the learning outcomes of Programming fundamentals?",
        "Approved list of hospitals for mitigation form",
        "Difference between Programming Fundamentals and Object Oriented Programming?",
    ]

    for p in prompts:
        if st.button(p, key=f"qp_{p}", use_container_width=True):
            st.session_state.pending_prompt = p
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
    st.info("🔗 Connected to RAG pipeline via Inngest (local dev)")

with col_chat:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if st.session_state.pending_prompt:
        prompt = st.session_state.pending_prompt
        st.session_state.pending_prompt = None
        handle_response(prompt)

    if user_input := st.chat_input("Ask the Domain AI..."):
        handle_response(user_input)

