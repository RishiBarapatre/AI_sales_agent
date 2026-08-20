"""
Post-conversation analytics generator.

Sends the full conversation history to the LLM with an analytics extraction prompt.
Returns structured JSON with lead qualification data.
"""

import json
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage

from .agent import get_llm, get_conversation_history


ANALYTICS_PROMPT = """You are a data analyst reviewing a sales conversation between an AI agent (Priya) and a potential home buyer for Northstar Homes.

Analyze the conversation below and extract structured analytics. Return ONLY a valid JSON object with exactly these fields. Do not include any text before or after the JSON.

{
    "customer_name": "The customer's name if they shared it, otherwise 'Unknown'",
    "customer_phone": "The customer's phone number if they shared it, otherwise 'Unknown'",
    "budget_range": "The customer's stated or implied budget range, or 'Not discussed'",
    "preferred_configuration": "2BHK or 3BHK or Both or Undecided or Not discussed",
    "interest_level": "high or medium or low or not_interested",
    "key_objections": ["list", "of", "objections", "raised"],
    "site_visit_status": "booked or attempted_failed or not_discussed",
    "follow_up_required": true,
    "follow_up_reason": "Reason why follow-up is needed, or null if not required",
    "lead_quality_score": 7,
    "language_preference": "English or Hindi or Hinglish or Mixed",
    "conversation_summary": "A 2-3 sentence summary of the conversation and outcome"
}

Rules for scoring:
- lead_quality_score is 1-10 where 10 is highest quality lead
- A customer who booked a site visit is at least 7
- A customer who expressed interest but didn't book is 4-6
- A customer who was not interested or asked to stop communication is 1-3
- interest_level should reflect the customer's final sentiment, not just initial interest

Return ONLY the JSON object, no explanation or markdown formatting."""


async def generate_analytics(session_id: str) -> dict:
    """
    Generate analytics from the conversation history of a session.

    Args:
        session_id: The session to analyze.

    Returns:
        A dictionary containing the extracted analytics fields,
        or an error dictionary if analysis fails.
    """
    history = get_conversation_history(session_id)

    if not history:
        return {"error": "No conversation found for this session."}

    # Format conversation for analysis
    conversation_lines = []
    for msg in history:
        if isinstance(msg, HumanMessage):
            conversation_lines.append(f"Customer: {msg.content}")
        elif isinstance(msg, AIMessage):
            if msg.content:  # Skip empty AI messages (tool call only messages)
                conversation_lines.append(f"Agent (Priya): {msg.content}")
        elif isinstance(msg, ToolMessage):
            conversation_lines.append(f"[System - Booking Tool Result]: {msg.content}")

    conversation_text = "\n".join(conversation_lines)

    # Invoke LLM for analytics extraction
    llm = get_llm()
    messages = [
        SystemMessage(content=ANALYTICS_PROMPT),
        HumanMessage(content=f"Conversation to analyze:\n\n{conversation_text}"),
    ]

    response = await llm.ainvoke(messages)

    # Parse JSON from response
    try:
        content = response.content
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
            
        content = content.strip()

        # Handle markdown code blocks if the LLM wraps the JSON
        if content.startswith("```"):
            # Remove opening ```json or ``` and closing ```
            lines = content.split("\n")
            # Find the first and last ``` lines
            start_idx = 0
            end_idx = len(lines)
            for i, line in enumerate(lines):
                if line.strip().startswith("```") and i == 0:
                    start_idx = i + 1
                elif line.strip() == "```":
                    end_idx = i
            content = "\n".join(lines[start_idx:end_idx])

        analytics = json.loads(content)

        # Ensure all expected fields are present with defaults
        defaults = {
            "customer_name": "Unknown",
            "customer_phone": "Unknown",
            "budget_range": "Not discussed",
            "preferred_configuration": "Not discussed",
            "interest_level": "unknown",
            "key_objections": [],
            "site_visit_status": "not_discussed",
            "follow_up_required": False,
            "follow_up_reason": None,
            "lead_quality_score": 0,
            "language_preference": "English",
            "conversation_summary": "",
        }
        for key, default_value in defaults.items():
            if key not in analytics:
                analytics[key] = default_value

        return analytics

    except json.JSONDecodeError:
        return {
            "error": "Failed to parse analytics from LLM response.",
            "raw_response": response.content,
        }
