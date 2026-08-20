# Northstar Homes — AI Sales Agent

An AI-powered conversational sales agent for **Northstar Homes**, built to qualify leads, answer customer questions, handle objections, and book site visits for the **Northstar One** project in Sector 79, Gurugram.

The agent communicates naturally in **English, Hindi, and Hinglish**, and is designed to work across both chat and voice interactions.

---

## Architecture

```
┌──────────────────┐         HTTP/REST          ┌────────────────────────────┐
│   Streamlit UI   │ ◄─────────────────────────► │   FastAPI Backend          │
│   (Port 8501)    │                             │   (Port 8000)              │
│                  │   POST /api/chat_stream     │                            │
│  - Chat bubbles  │   POST /api/analytics       │  - LangChain Agent         │
│  - Analytics     │   POST /api/reset           │  - ChatMessageHistory      │
│  - Test runner   │   GET  /api/test            │  - Tool Calling (Booking)  │
└──────────────────┘                             │  - Analytics Extraction    │
                                                 └──────────┬─────────────────┘
                                                            │
                                                   LangChain │ API Call
                                                            ▼
                                                 ┌────────────────────────┐
                                                 │   LLM Provider         │
                                                 │   (Gemini / Groq)      │
                                                 └────────────────────────┘
```

### Tech Stack
- **Backend:** FastAPI (Python) + LangChain (with Server-Sent Events Streaming)
- **Frontend:** Streamlit
- **LLM:** Google Gemini (`gemini-3.6-flash` or `gemini-3.1-flash-lite`) or Groq (`llama-3.3-70b-versatile`)
- **Memory:** LangChain `ChatMessageHistory` (per-session, in-memory)
- **Sidebar Chat History:** Switch between active sessions via `GET /api/chat/{session_id}`
- **Tool Calling:** LangChain `@tool` for site-visit booking (with validation for 10-digit phones and working hours)

---

## How to Run

### Prerequisites
- Python 3.10+
- A Google Gemini API key (free tier) OR a Groq API key (free tier)

### Setup

```bash
# 1. Clone the repository
git clone https://github.com/RishiBarapatre/AI_sales_agent.git
cd huvo-assignment

# 2. Create a virtual environment (recommended)
python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate  # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env          # macOS/Linux
# copy .env.example .env        # Windows (cmd)
# Edit .env and add your API key
```

### Run the Application

You need **two terminals** running simultaneously:

```bash
# Terminal 1 — Start the FastAPI backend
uvicorn backend.main:app --reload --port 8000
```

```bash
# Terminal 2 — Start the Streamlit frontend
streamlit run frontend/app.py
```

Then open your browser to **http://localhost:8501**

### Run Test Cases

Either:
- Click **"Run All Tests"** in the Streamlit sidebar, or
- Visit `http://localhost:8000/api/test` directly

---

## Prompt Approach

The system prompt (`prompt.md` / `backend/prompt.py`) is designed with these principles:

1. **Readable Formatting:** Uses markdown bolding and short paragraphs to make responses easy to scan for users.
2. **Language-adaptive:** The agent detects and mirrors the customer's language (English, Hindi, Hinglish).
3. **Anti-hallucination:** Strict rules against fabricating information. The agent only knows what's explicitly provided.
4. **Natural qualification:** Lead qualification questions are woven into conversation naturally, not asked as a checklist.
5. **Scenario-complete:** Explicit handling for all required scenarios (objections, busy customers, stop requests, unknown questions, booking, failures, escalation).

---

## Test Cases

| # | Scenario | What it Tests |
|---|----------|---------------|
| 1 | Happy Path — Buyer books visit | Full qualification → booking flow |
| 2 | Price Objection | Agent doesn't offer discounts, highlights value |
| 3 | Busy Customer | Agent respects time, offers callback |
| 4 | Stop Communication | Agent complies immediately, no sales pitch |
| 5 | Unknown Question (amenities) | Agent admits lack of info, doesn't fabricate |
| 6 | Hindi Conversation | Language detection and Hindi responses |
| 7 | Human Escalation | Agent offers to connect with sales team |
| 8 | Invalid Booking Details | Agent handles invalid phone numbers (10 digits) and non-working hours |

---

## Key Assumptions

1. **In-memory sessions:** Conversation history is stored in-memory on the FastAPI server. Restarting the server clears all sessions. This is acceptable for a demo/assignment scope.
2. **Simulated booking:** Site-visit booking is simulated with a ~20% random failure rate to demonstrate error handling.
3. **Single-user demo:** The app is designed for demo purposes and doesn't include authentication or multi-user session management beyond session IDs.
4. **LLM-dependent analytics:** Post-conversation analytics are extracted by the LLM, so accuracy depends on the model's understanding.

---

## Known Limitations

1. **No persistent storage:** Sessions are lost on server restart (in-memory only).
2. **No real booking system:** Booking is simulated — in production, this would integrate with a CRM.
3. **Rate limits:** Free-tier API keys have rate limits. Groq/gemini's free tier may throttle under heavy test case load.
4. **No authentication:** No user login or API key protection on endpoints.
5. **Tool calling consistency:** Different LLM providers may have slightly different tool-calling behaviors. The agent is primarily tested with Gemini `gemini-3.6-flash` and `gemini-3.1-flash-lite`.

---

## AI Tools Used

- **LangChain** — Chat agent framework, message types, tool calling, and memory management
- **Google Gemini API** — Primary LLM for conversational responses and analytics extraction
- **Groq API** — Alternative LLM provider (fallback option)
- **Gemini Code Assist** — Used during development for code generation and prompt engineering assistance

---

## Project Structure

```
├── backend/
│   ├── __init__.py          # Package init
│   ├── main.py              # FastAPI app + endpoints
│   ├── prompt.py            # System prompt
│   ├── agent.py             # LangChain agent with memory + tool calling
│   ├── analytics.py         # Post-conversation analytics
│   ├── booking.py           # Simulated booking tool
│   ├── models.py            # Pydantic schemas
│   └── test_cases.py        # Automated test scenarios
├── frontend/
│   └── app.py               # Streamlit chat UI
├── prompt.md                # Final prompt (standalone)
├── requirements.txt         # Python dependencies
├── .env.example             # Environment variable template
└── README.md                # This file
```
