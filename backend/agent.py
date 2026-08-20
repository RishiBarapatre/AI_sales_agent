"""
LangChain-based conversational agent for Northstar Homes.

Manages per-session chat memory using ChatMessageHistory with proper
LangChain message types (SystemMessage, HumanMessage, AIMessage, ToolMessage).
Supports tool calling for site-visit booking.
"""

import os
from dotenv import load_dotenv
from langchain_core.messages import (
    SystemMessage,
    HumanMessage,
    AIMessage,
    ToolMessage,
)
from langchain_community.chat_message_histories import ChatMessageHistory

from .prompt import SYSTEM_PROMPT
from .booking import book_site_visit

load_dotenv()

# ─── In-memory session store ────────────────────────────────────────────────────
# Each session_id maps to a ChatMessageHistory containing the full conversation.
sessions: dict[str, ChatMessageHistory] = {}

# ─── Tools available to the agent ───────────────────────────────────────────────
tools = [book_site_visit]


def get_llm():
    """Initialize the LLM based on the configured provider."""
    provider = os.getenv("LLM_PROVIDER", "gemini").lower()

    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=os.getenv("GEMINI_MODEL", "gemini-3.6-flash"),
            api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.7,
        )
    elif provider == "groq":
        from langchain_groq import ChatGroq

        return ChatGroq(
            model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
            api_key=os.getenv("GROQ_API_KEY"),
            temperature=0.7,
        )
    else:
        raise ValueError(
            f"Unsupported LLM_PROVIDER: '{provider}'. Use 'gemini' or 'groq'."
        )


# ─── Session Management ────────────────────────────────────────────────────────

def get_session(session_id: str) -> ChatMessageHistory:
    """Get or create a ChatMessageHistory for the given session."""
    if session_id not in sessions:
        sessions[session_id] = ChatMessageHistory()
    return sessions[session_id]


def reset_session(session_id: str) -> None:
    """Clear the conversation history for a session."""
    if session_id in sessions:
        del sessions[session_id]


def get_conversation_history(session_id: str) -> list:
    """Return the raw list of LangChain messages for a session."""
    session = get_session(session_id)
    return session.messages


# ─── Core Chat Function ────────────────────────────────────────────────────────

async def chat(session_id: str, user_message: str) -> dict:
    """
    Process a user message and return the agent's response.

    Flow:
    1. Add user message to session history
    2. Build full message list: [SystemMessage] + history
    3. Invoke LLM with tools bound
    4. If LLM returns tool calls → execute tools → add ToolMessage → re-invoke
    5. Add final AI response to history
    6. Return response text + any booking results

    Args:
        session_id: Unique session identifier.
        user_message: The customer's message text.

    Returns:
        dict with keys:
          - "response": str — the AI agent's response text
          - "booking_result": dict | None — booking details if a visit was booked
    """
    session = get_session(session_id)
    llm = get_llm()
    llm_with_tools = llm.bind_tools(tools)

    # Step 1: Add user message to history
    session.add_user_message(user_message)

    # Step 2: Build full message list with system prompt
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + list(session.messages)

    # Step 3: Invoke LLM
    response = await llm_with_tools.ainvoke(messages)

    booking_result = None

    # Step 4: Handle tool calls (agentic loop)
    max_tool_iterations = 3  # Safety limit
    iteration = 0

    while response.tool_calls and iteration < max_tool_iterations:
        iteration += 1

        # Add the AI message (with tool call metadata) to history
        session.add_message(response)

        # Execute each tool call
        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            tool_call_id = tool_call["id"]

            if tool_name == "book_site_visit":
                # Execute the booking tool
                result = book_site_visit.invoke(tool_args)

                # Parse booking result for the API response
                if "BOOKING CONFIRMED" in result:
                    booking_result = {
                        "status": "confirmed",
                        "details": result,
                        **tool_args,
                    }
                else:
                    booking_result = {
                        "status": "failed",
                        "details": result,
                        **tool_args,
                    }

                # Add tool result as ToolMessage
                tool_msg = ToolMessage(
                    content=result,
                    tool_call_id=tool_call_id,
                )
                session.add_message(tool_msg)
            else:
                # Unknown tool — add error message
                tool_msg = ToolMessage(
                    content=f"Error: Unknown tool '{tool_name}'",
                    tool_call_id=tool_call_id,
                )
                session.add_message(tool_msg)

        # Re-invoke LLM with updated history (including tool results)
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + list(session.messages)
        response = await llm_with_tools.ainvoke(messages)

    # Step 5: Add final AI response to history
    session.add_ai_message(response.content)

    # Step 6: Return response
    # Format response properly (langchain sometimes returns a list of blocks for Gemini 3.6+)
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
        
    return {
        "response": content,
        "booking_result": booking_result
    }

import json

async def chat_stream(session_id: str, user_message: str):
    session = get_session(session_id)
    llm = get_llm()
    llm_with_tools = llm.bind_tools(tools)

    session.add_user_message(user_message)
    
    max_tool_iterations = 3
    iteration = 0
    booking_result = None

    while iteration < max_tool_iterations:
        iteration += 1
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + list(session.messages)

        try:
            stream = llm_with_tools.astream(messages)
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': 'I am currently receiving too many requests. Please try again in a minute.'})}\n\n"
            return

        full_message = None
        
        # Async iterate over chunks
        try:
            async for chunk in stream:
                if not full_message:
                    full_message = chunk
                else:
                    full_message += chunk
                
                # If there is content in the chunk, and it's a string, stream it
                if chunk.content and isinstance(chunk.content, str):
                    yield f"data: {json.dumps({'type': 'chunk', 'content': chunk.content})}\n\n"
                elif chunk.content and isinstance(chunk.content, list):
                    # Gemini sometimes streams lists
                    for block in chunk.content:
                        if isinstance(block, dict) and 'text' in block:
                            yield f"data: {json.dumps({'type': 'chunk', 'content': block['text']})}\n\n"
                        elif isinstance(block, str):
                            yield f"data: {json.dumps({'type': 'chunk', 'content': block})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': 'I am currently receiving too many requests. Please try again in a minute.'})}\n\n"
            return

        # Check if the LLM decided to call a tool
        if full_message.tool_calls:
            session.add_message(full_message)
            for tool_call in full_message.tool_calls:
                tool_name = tool_call['name']
                tool_args = tool_call['args']
                tool_call_id = tool_call['id']

                if tool_name == 'book_site_visit':
                    result = book_site_visit.invoke(tool_args)
                    if 'BOOKING CONFIRMED' in result:
                        booking_result = {'status': 'confirmed', 'details': result, **tool_args}
                    else:
                        booking_result = {'status': 'failed', 'details': result, **tool_args}
                    tool_msg = ToolMessage(content=result, tool_call_id=tool_call_id)
                    session.add_message(tool_msg)
                else:
                    tool_msg = ToolMessage(content=f"Error: Unknown tool '{tool_name}'", tool_call_id=tool_call_id)
                    session.add_message(tool_msg)
        else:
            # No tool calls, the response is complete
            content = full_message.content
            if isinstance(content, list):
                text_content = ''
                for block in content:
                    if isinstance(block, dict):
                        text_content += str(block.get('text', ''))
                    else:
                        text_content += str(block)
                content = text_content
            else:
                content = str(content)
            
            session.add_ai_message(content)

            if booking_result:
                yield f"data: {json.dumps({'type': 'booking_result', 'result': booking_result})}\n\n"
                
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            break
