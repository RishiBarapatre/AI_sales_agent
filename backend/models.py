"""
Pydantic models for API request/response schemas.
"""

from pydantic import BaseModel, Field
from typing import Optional


# ─── Chat ───────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    """Request body for the /api/chat endpoint."""
    session_id: str = Field(..., description="Unique session identifier")
    message: str = Field(..., description="User message text")


class ChatResponse(BaseModel):
    """Response body for the /api/chat endpoint."""
    session_id: str
    response: str = Field(..., description="AI agent response text")
    booking_result: Optional[dict] = Field(
        None, description="Booking result if a site visit was booked during this turn"
    )

class ChatMessage(BaseModel):
    role: str
    content: str
    
class ChatHistoryResponse(BaseModel):
    messages: list[ChatMessage]


# ─── Analytics ──────────────────────────────────────────────────────────────────

class AnalyticsRequest(BaseModel):
    """Request body for the /api/analytics endpoint."""
    session_id: str = Field(..., description="Session to analyze")


class AnalyticsResponse(BaseModel):
    """Post-conversation analytics extracted by the LLM."""
    customer_name: str = "Unknown"
    budget_range: str = "Not discussed"
    preferred_configuration: str = "Not discussed"
    interest_level: str = "unknown"
    key_objections: list[str] = []
    site_visit_status: str = "not_discussed"
    follow_up_required: bool = False
    follow_up_reason: Optional[str] = None
    lead_quality_score: int = 0
    language_preference: str = "English"
    conversation_summary: str = ""


# ─── Session ────────────────────────────────────────────────────────────────────

class ResetRequest(BaseModel):
    """Request body for the /api/reset endpoint."""
    session_id: str = Field(..., description="Session to reset")


class ResetResponse(BaseModel):
    """Response body for the /api/reset endpoint."""
    status: str = "ok"
    message: str = "Session reset successfully"


# ─── Test Cases ─────────────────────────────────────────────────────────────────

class TestTurn(BaseModel):
    """A single turn in a test conversation."""
    role: str
    content: str


class TestCaseResult(BaseModel):
    """Result of a single test case."""
    test_name: str
    scenario: str
    expected_behavior: str
    conversation: list[TestTurn]
    passed: bool
    notes: str = ""


class TestSuiteResponse(BaseModel):
    """Response from running all test cases."""
    total: int
    passed: int
    failed: int
    results: list[TestCaseResult]
