"""
FastAPI application for the Northstar Homes AI Sales Agent.

Provides REST API endpoints for the Streamlit frontend:
- /api/chat      — Send a message, get AI response
- /api/analytics — Generate post-conversation analytics
- /api/reset     — Clear a session's conversation history
- /api/test      — Run automated test cases
- /health        — Health check
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from fastapi.responses import StreamingResponse
from .models import (
    ChatRequest,
    ChatResponse,
    ChatHistoryResponse,
    ChatMessage,
    AnalyticsRequest,
    ResetRequest,
    ResetResponse,
)
from .agent import chat, chat_stream, reset_session, get_conversation_history
from .analytics import generate_analytics
from .test_cases import run_all_tests


# ─── App Initialization ────────────────────────────────────────────────────────

app = FastAPI(
    title="Northstar Homes AI Sales Agent",
    description="AI conversational bot for Northstar Homes — Northstar One project",
    version="1.0.0",
)

# CORS — allow Streamlit frontend (typically on port 8501) to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Endpoints ──────────────────────────────────────────────────────────────────

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "Northstar Homes AI Agent"}


@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Process a customer message and return the AI agent's response.

    The agent maintains conversation history per session and may invoke
    the site-visit booking tool if the customer wants to schedule a visit.
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    try:
        result = await chat(request.session_id, request.message)
        print("DEBUG RESULT:", result, type(result["response"]))
        return ChatResponse(
            session_id=request.session_id,
            response=result["response"],
            booking_result=result.get("booking_result"),
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing message: {str(e)}",
        )


@app.post("/api/chat_stream")
async def chat_stream_endpoint(request: ChatRequest):
    """
    Process a customer message and stream the AI agent's response using Server-Sent Events (SSE).
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    return StreamingResponse(
        chat_stream(request.session_id, request.message),
        media_type="text/event-stream"
    )


@app.get("/api/chat/{session_id}", response_model=ChatHistoryResponse)
async def get_chat_history_endpoint(session_id: str):
    """
    Retrieve the conversation history for a specific session.
    """
    try:
        from langchain_core.messages import HumanMessage, AIMessage
        history = get_conversation_history(session_id)
        
        formatted_messages = []
        for msg in history:
            if isinstance(msg, HumanMessage):
                formatted_messages.append(ChatMessage(role="user", content=str(msg.content)))
            elif isinstance(msg, AIMessage):
                if msg.content:  # Skip empty AI messages
                    content = msg.content
                    if isinstance(content, list):
                        text_content = ""
                        for block in content:
                            if isinstance(block, dict):
                                text_content += str(block.get("text", ""))
                            else:
                                text_content += str(block)
                        content = text_content
                    else:
                        content = str(content)
                    
                    formatted_messages.append(ChatMessage(role="assistant", content=content))
        
        return ChatHistoryResponse(messages=formatted_messages)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving history: {str(e)}",
        )

@app.post("/api/analytics")
async def analytics_endpoint(request: AnalyticsRequest):
    """
    Generate analytics from a completed conversation.

    Sends the conversation history to the LLM for structured data extraction
    including lead quality score, interest level, objections, etc.
    """
    try:
        analytics = await generate_analytics(request.session_id)
        return analytics
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating analytics: {str(e)}",
        )


@app.post("/api/reset", response_model=ResetResponse)
async def reset_endpoint(request: ResetRequest):
    """Clear the conversation history for a session."""
    reset_session(request.session_id)
    return ResetResponse(
        status="ok",
        message=f"Session '{request.session_id}' reset successfully.",
    )


@app.get("/api/test")
async def test_endpoint():
    """
    Run all automated test cases and return results.

    Each test case simulates a multi-turn customer conversation and validates
    that the agent behaves correctly.
    """
    try:
        results = await run_all_tests()
        return results
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error running tests: {str(e)}",
        )
