"""
Streamlit Chat UI for the Northstar Homes AI Sales Agent.

A premium dark-themed chat interface that communicates with the FastAPI backend.
Features: chat bubbles, typing indicator, analytics panel, and test case runner.
"""

import streamlit as st
import requests
import uuid
import json
import time

# ─── Configuration ──────────────────────────────────────────────────────────────

API_BASE_URL = "http://localhost:8000"

st.set_page_config(
    page_title="Northstar Homes — AI Sales Agent",
    page_icon="🏠",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS for Premium Dark Theme ──────────────────────────────────────────

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* ── Global Theme ── */
    .stApp {
        background: linear-gradient(135deg, #0f0c29 0%, #1a1a3e 40%, #24243e 100%);
        font-family: 'Inter', sans-serif;
    }

    /* ── Header ── */
    .main-header {
        text-align: center;
        padding: 1.5rem 1rem 1rem 1rem;
        margin-bottom: 0.5rem;
    }
    .main-header h1 {
        background: linear-gradient(135deg, #00d2ff 0%, #7b2ff7 50%, #ff6b9d 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2rem;
        font-weight: 700;
        margin-bottom: 0.3rem;
        letter-spacing: -0.5px;
    }
    .main-header p {
        color: #8b8fa3;
        font-size: 0.9rem;
        margin: 0;
    }

    /* ── Chat Container ── */
    .stChatMessage {
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 255, 255, 0.06) !important;
        border-radius: 16px !important;
        backdrop-filter: blur(10px) !important;
        margin-bottom: 0.5rem !important;
        padding: 1rem 1.2rem !important;
    }

    /* ── Chat Input ── */
    .stChatInput > div {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 14px !important;
    }
    .stChatInput textarea {
        color: #e0e0e0 !important;
        font-family: 'Inter', sans-serif !important;
    }

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #141428 0%, #1a1a3e 100%) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.06) !important;
    }
    section[data-testid="stSidebar"] .stMarkdown h2 {
        color: #c8cad0 !important;
        font-size: 1.1rem !important;
        font-weight: 600 !important;
    }
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown li {
        color: #9a9cb0 !important;
        font-size: 0.85rem !important;
    }

    /* ── Buttons ── */
    .stButton > button {
        background: linear-gradient(135deg, #7b2ff7 0%, #00d2ff 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.6rem 1.5rem !important;
        font-weight: 600 !important;
        font-family: 'Inter', sans-serif !important;
        transition: all 0.3s ease !important;
        width: 100% !important;
    }
    .stButton > button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 20px rgba(123, 47, 247, 0.4) !important;
    }

    /* ── Analytics Card ── */
    .analytics-card {
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1rem 0;
        backdrop-filter: blur(10px);
    }
    .analytics-card h3 {
        color: #00d2ff;
        font-size: 1.1rem;
        margin-bottom: 1rem;
        font-weight: 600;
    }
    .analytics-row {
        display: flex;
        justify-content: space-between;
        padding: 0.5rem 0;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    }
    .analytics-label {
        color: #8b8fa3;
        font-size: 0.85rem;
        font-weight: 500;
    }
    .analytics-value {
        color: #e0e0e0;
        font-size: 0.85rem;
        font-weight: 600;
        text-align: right;
        max-width: 60%;
    }

    /* ── Score Badge ── */
    .score-badge {
        display: inline-block;
        padding: 0.2rem 0.8rem;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.85rem;
    }
    .score-high { background: rgba(0, 210, 100, 0.15); color: #00d264; }
    .score-medium { background: rgba(255, 183, 0, 0.15); color: #ffb700; }
    .score-low { background: rgba(255, 75, 75, 0.15); color: #ff4b4b; }

    /* ── Interest Badge ── */
    .interest-high { color: #00d264; font-weight: 700; }
    .interest-medium { color: #ffb700; font-weight: 700; }
    .interest-low { color: #ff6b6b; font-weight: 700; }
    .interest-not_interested { color: #ff4b4b; font-weight: 700; }

    /* ── Expander ── */
    .streamlit-expanderHeader {
        background: rgba(255, 255, 255, 0.03) !important;
        border-radius: 10px !important;
        color: #c8cad0 !important;
    }

    /* ── Typing Indicator ── */
    .typing-indicator {
        display: flex;
        gap: 4px;
        padding: 8px 0;
        align-items: center;
    }
    .typing-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #7b2ff7;
        animation: bounce 1.4s infinite ease-in-out;
    }
    .typing-dot:nth-child(1) { animation-delay: 0s; }
    .typing-dot:nth-child(2) { animation-delay: 0.2s; }
    .typing-dot:nth-child(3) { animation-delay: 0.4s; }

    @keyframes bounce {
        0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
        40% { transform: scale(1); opacity: 1; }
    }

    /* ── Divider ── */
    .custom-divider {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(123, 47, 247, 0.3), transparent);
        margin: 1rem 0;
    }

    /* ── Test Results ── */
    .test-pass { color: #00d264; font-weight: 600; }
    .test-fail { color: #ff4b4b; font-weight: 600; }

    /* ── Hide Streamlit branding ── */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ─── Session State Initialization ───────────────────────────────────────────────

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

if "analytics_data" not in st.session_state:
    st.session_state.analytics_data = None

if "conversation_ended" not in st.session_state:
    st.session_state.conversation_ended = False

if "past_sessions" not in st.session_state:
    st.session_state.past_sessions = []


# ─── Helper Functions ───────────────────────────────────────────────────────────

import json

def process_chat_stream(prompt: str, placeholder) -> dict:
    """Send message to backend and stream response into the placeholder."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/chat_stream",
            json={"session_id": st.session_state.session_id, "message": prompt},
            stream=True,
            timeout=60,
        )
        response.raise_for_status()
        
        full_text = ""
        booking_result = None
        
        for line in response.iter_lines():
            if line:
                line_text = line.decode('utf-8')
                if line_text.startswith("data: "):
                    data_str = line_text[6:]
                    try:
                        data = json.loads(data_str)
                        if data["type"] == "chunk":
                            full_text += data["content"]
                            placeholder.markdown(full_text + "▌")
                        elif data["type"] == "booking_result":
                            booking_result = data["result"]
                        elif data["type"] == "error":
                            full_text = data["content"]
                            placeholder.markdown(full_text)
                        elif data["type"] == "done":
                            placeholder.markdown(full_text)
                    except Exception as e:
                        pass
        
        return {"response": full_text, "booking_result": booking_result}

    except requests.exceptions.ConnectionError:
        error_msg = "⚠️ Cannot connect to the backend server. Please make sure the FastAPI server is running on port 8000."
        placeholder.markdown(error_msg)
        return {"response": error_msg, "booking_result": None}
    except Exception as e:
        error_msg = f"⚠️ Error: {str(e)}"
        placeholder.markdown(error_msg)
        return {"response": error_msg, "booking_result": None}


def get_analytics() -> dict:
    """Request analytics from the backend."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/analytics",
            json={"session_id": st.session_state.session_id},
            timeout=60,
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}


def reset_conversation():
    """Reset the conversation on both frontend and backend."""
    try:
        requests.post(
            f"{API_BASE_URL}/api/reset",
            json={"session_id": st.session_state.session_id},
            timeout=10,
        )
    except Exception:
        pass

def fetch_chat_history(session_id: str) -> list:
    """Fetch the chat history for a session from the backend."""
    try:
        response = requests.get(f"{API_BASE_URL}/api/chat/{session_id}", timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get("messages", [])
    except Exception as e:
        st.error(f"Error fetching history: {e}")
        return []

def switch_chat(session_id: str):
    """Switch to a different chat session."""
    st.session_state.session_id = session_id
    st.session_state.messages = fetch_chat_history(session_id)
    st.session_state.analytics_data = None
    st.session_state.conversation_ended = False
    
def reset_conversation():
    """Start a new chat window and save the current session."""
    # Only save if there's actual conversation history
    if st.session_state.messages:
        # Avoid duplicate saves
        if not any(s['id'] == st.session_state.session_id for s in st.session_state.past_sessions):
            st.session_state.past_sessions.append({
                "id": st.session_state.session_id,
                "title": f"Chat {len(st.session_state.past_sessions) + 1}"
            })

    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.messages = []
    st.session_state.analytics_data = None
    st.session_state.conversation_ended = False


def run_tests() -> dict:
    """Run test cases via the backend."""
    try:
        response = requests.get(f"{API_BASE_URL}/api/test", timeout=300)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}


def render_analytics(data: dict):
    """Render the analytics panel with styled cards."""
    if "error" in data:
        st.error(f"Analytics Error: {data['error']}")
        if "raw_response" in data:
            with st.expander("Raw LLM Response"):
                st.text(data["raw_response"])
        return

    # Score badge color
    score = data.get("lead_quality_score", 0)
    if score >= 7:
        score_class = "score-high"
    elif score >= 4:
        score_class = "score-medium"
    else:
        score_class = "score-low"

    # Interest badge
    interest = data.get("interest_level", "unknown")
    interest_class = f"interest-{interest}"

    # Build analytics HTML
    objections = ", ".join(data.get("key_objections", [])) or "None"
    follow_up = "Yes" if data.get("follow_up_required") else "No"
    follow_up_reason = data.get("follow_up_reason") or "N/A"

    analytics_html = f"""
    <div class="analytics-card">
        <h3>📊 Conversation Analytics</h3>

        <div class="analytics-row">
            <span class="analytics-label">Customer Name</span>
            <span class="analytics-value">{data.get('customer_name', 'Unknown')}</span>
        </div>

        <div class="analytics-row">
            <span class="analytics-label">Phone Number</span>
            <span class="analytics-value">{data.get('customer_phone', 'Unknown')}</span>
        </div>

        <div class="analytics-row">
            <span class="analytics-label">Budget Range</span>
            <span class="analytics-value">{data.get('budget_range', 'Not discussed')}</span>
        </div>

        <div class="analytics-row">
            <span class="analytics-label">Preferred Configuration</span>
            <span class="analytics-value">{data.get('preferred_configuration', 'Not discussed')}</span>
        </div>

        <div class="analytics-row">
            <span class="analytics-label">Interest Level</span>
            <span class="analytics-value {interest_class}">{interest.upper()}</span>
        </div>

        <div class="analytics-row">
            <span class="analytics-label">Lead Quality Score</span>
            <span class="analytics-value"><span class="score-badge {score_class}">{score}/10</span></span>
        </div>

        <div class="analytics-row">
            <span class="analytics-label">Key Objections</span>
            <span class="analytics-value">{objections}</span>
        </div>

        <div class="analytics-row">
            <span class="analytics-label">Site Visit Status</span>
            <span class="analytics-value">{data.get('site_visit_status', 'Not discussed').replace('_', ' ').title()}</span>
        </div>

        <div class="analytics-row">
            <span class="analytics-label">Follow-up Required</span>
            <span class="analytics-value">{follow_up}</span>
        </div>

        <div class="analytics-row">
            <span class="analytics-label">Follow-up Reason</span>
            <span class="analytics-value">{follow_up_reason}</span>
        </div>

        <div class="analytics-row">
            <span class="analytics-label">Language Preference</span>
            <span class="analytics-value">{data.get('language_preference', 'English')}</span>
        </div>

        <div class="analytics-row" style="border-bottom: none;">
            <span class="analytics-label">Summary</span>
            <span class="analytics-value">{data.get('conversation_summary', 'N/A')}</span>
        </div>
    </div>
    """
    st.markdown(analytics_html, unsafe_allow_html=True)


# ─── Sidebar ────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 🏠 Northstar Homes")
    st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)

    st.markdown("""
    **Project:** Northstar One  
    **Location:** Sector 79, Gurugram  
    **Configs:** 2 BHK & 3 BHK  
    **Pricing:**  
    - 2 BHK: ₹1.35 Cr onwards  
    - 3 BHK: ₹1.75 Cr onwards
    """)

    st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)

    if st.session_state.past_sessions:
        st.markdown("### 🕒 Past Chats")
        for session in st.session_state.past_sessions:
            if st.button(session["title"], key=f"btn_{session['id']}"):
                # Save current if needed before switching
                if st.session_state.messages and not any(s['id'] == st.session_state.session_id for s in st.session_state.past_sessions):
                    st.session_state.past_sessions.append({
                        "id": st.session_state.session_id,
                        "title": f"Chat {len(st.session_state.past_sessions) + 1}"
                    })
                switch_chat(session["id"])
                st.rerun()
        st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)

    # New Conversation button
    if st.button("🔄 New Conversation", key="new_conv"):
        reset_conversation()
        st.rerun()

    # End & Analyze button
    if st.button("📊 End & Analyze", key="end_analyze"):
        if st.session_state.messages:
            st.session_state.conversation_ended = True
            with st.spinner("Generating analytics..."):
                st.session_state.analytics_data = get_analytics()
            st.rerun()
        else:
            st.warning("No conversation to analyze yet.")

    st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)

    # Test Cases section
    st.markdown("## 🧪 Test Cases")
    if st.button("▶️ Run All Tests", key="run_tests"):
        with st.spinner("Running test cases... This may take a minute."):
            test_results = run_tests()

        if "error" in test_results:
            st.error(f"Error: {test_results['error']}")
        else:
            st.markdown(
                f"**Results:** {test_results['passed']}/{test_results['total']} passed"
            )

            for result in test_results.get("results", []):
                status = "✅" if result["passed"] else "❌"
                with st.expander(f"{status} {result['test_name']}"):
                    st.markdown(f"**Scenario:** {result['scenario']}")
                    st.markdown(f"**Expected:** {result['expected_behavior']}")
                    st.markdown(f"**Notes:** {result.get('notes', 'N/A')}")
                    st.markdown("**Conversation:**")
                    for turn in result.get("conversation", []):
                        role_emoji = "👤" if turn["role"] == "user" else "🤖"
                        st.markdown(f"{role_emoji} **{turn['role'].title()}:** {turn['content']}")

    st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)
    st.markdown(
        "<p style='text-align:center; color:#555; font-size:0.75rem;'>"
        "Powered by LangChain + FastAPI</p>",
        unsafe_allow_html=True,
    )


# ─── Main Chat Area ────────────────────────────────────────────────────────────

# Header
st.markdown("""
<div class="main-header">
    <h1>Northstar Homes AI Agent</h1>
    <p>Your intelligent property consultant for Northstar One, Sector 79, Gurugram</p>
</div>
""", unsafe_allow_html=True)

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Display analytics if conversation ended
if st.session_state.analytics_data and st.session_state.conversation_ended:
    st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)
    render_analytics(st.session_state.analytics_data)

# Chat input (disabled if conversation ended)
if not st.session_state.conversation_ended:
    if prompt := st.chat_input("Type your message... (English, Hindi, or Hinglish)"):
        # Add user message to display
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Show typing indicator and get response
        with st.chat_message("assistant"):
            # Typing indicator
            typing_placeholder = st.empty()
            typing_placeholder.markdown("""
            <div class="typing-indicator">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
            """, unsafe_allow_html=True)

            # Get response from backend (streams directly into the placeholder)
            result = process_chat_stream(prompt, typing_placeholder)
            agent_response = result["response"]

        # Add assistant message to display
        st.session_state.messages.append(
            {"role": "assistant", "content": agent_response}
        )

        # Show booking notification if applicable
        if result.get("booking_result"):
            booking = result["booking_result"]
            if booking["status"] == "confirmed":
                st.success("✅ Site visit booked successfully!")
            else:
                st.warning("⚠️ Booking attempt was unsuccessful. The agent will suggest alternatives.")
else:
    st.info("📊 Conversation ended. Review the analytics above, or start a new conversation from the sidebar.")
