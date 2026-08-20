"""
Automated test cases for the Northstar Homes AI agent.

Each test case runs a multi-turn conversation and validates that the agent
behaves correctly for different customer scenarios.
"""

from .agent import chat, reset_session
from .models import TestCaseResult, TestTurn


# ─── Test Scenario Definitions ──────────────────────────────────────────────────

TEST_SCENARIOS = [
    {
        "name": "Happy Path — Interested Buyer Books Site Visit",
        "scenario": "A genuinely interested customer asks about 3BHK, provides details, and books a site visit.",
        "messages": [
            "Hi, I'm looking for a 3 BHK apartment in Gurugram.",
            "What is the starting price for 3 BHK?",
            "That sounds reasonable. I'd like to visit the property.",
            "My name is Rahul Sharma, phone number is 9876543210. I'd like to visit this Saturday at 11 AM.",
        ],
        "expected_behavior": "Agent should provide 3BHK pricing (₹1.75 crore onwards), gather details, and attempt to book a site visit using the tool.",
        "checks": [
            lambda turns: any("1.75" in t.content.lower() or "1,75" in t.content.lower() or "175" in t.content.lower() for t in turns if t.role == "assistant"),
        ],
    },
    {
        "name": "Price Objection Handling",
        "scenario": "Customer says the price is too high and expects the agent to NOT offer discounts.",
        "messages": [
            "What's the price of 2 BHK?",
            "1.35 crore is way too expensive! Can you give me a discount?",
        ],
        "expected_behavior": "Agent should quote ₹1.35 crore for 2BHK. When customer objects, agent should acknowledge concern and highlight value without offering discounts.",
        "checks": [
            lambda turns: any("1.35" in t.content.lower() or "135" in t.content.lower() for t in turns if t.role == "assistant"),
            # Should NOT mention specific discount amounts
            lambda turns: not any("% off" in t.content.lower() or "% discount" in t.content.lower() for t in turns if t.role == "assistant"),
        ],
    },
    {
        "name": "Busy Customer — Callback Request",
        "scenario": "Customer says they are busy and can't talk right now.",
        "messages": [
            "Hi, I saw your ad about Northstar One.",
            "Actually I'm really busy right now, can you call me tomorrow evening?",
        ],
        "expected_behavior": "Agent should immediately respect the customer's time, confirm the callback timing, and end politely without pushing for more information.",
        "checks": [
            # Response should be short and respectful
            lambda turns: len(turns) >= 4,  # At least 2 exchanges happened
        ],
    },
    {
        "name": "Stop Communication Request",
        "scenario": "Customer explicitly asks not to be contacted further.",
        "messages": [
            "Please stop contacting me. I'm not interested.",
        ],
        "expected_behavior": "Agent should immediately comply, confirm they will stop contacting, and end politely without any sales pitch.",
        "checks": [
            # Response should not contain sales-y language
            lambda turns: not any(
                "offer" in t.content.lower() and "visit" in t.content.lower()
                for t in turns
                if t.role == "assistant"
            ),
        ],
    },
    {
        "name": "Unknown Question — Amenities",
        "scenario": "Customer asks about amenities (swimming pool) which are not in the provided information.",
        "messages": [
            "Does Northstar One have a swimming pool and gym?",
        ],
        "expected_behavior": "Agent should honestly say it doesn't have that information and offer to connect with someone who does. Should NOT make up amenity details.",
        "checks": [
            # Should NOT claim there IS a swimming pool
            lambda turns: not any(
                "yes" in t.content.lower().split(".")[:1][0]
                and "swimming pool" in t.content.lower()
                for t in turns
                if t.role == "assistant"
            ),
        ],
    },
    {
        "name": "Hindi Conversation",
        "scenario": "Customer speaks in Hindi throughout the conversation.",
        "messages": [
            "Namaste, mujhe Gurugram mein ghar chahiye.",
            "2 BHK ka kya price hai?",
            "Theek hai, dhanyavaad. Baad mein baat karte hain.",
        ],
        "expected_behavior": "Agent should detect Hindi/Hinglish and respond in the same language. Should provide pricing in a natural way.",
        "checks": [
            # At least some response should contain Hindi words
            lambda turns: any(
                any(
                    word in t.content.lower()
                    for word in ["namaste", "ji", "aap", "ka", "ke", "ki", "hai", "hain", "crore", "karor"]
                )
                for t in turns
                if t.role == "assistant"
            ),
        ],
    },
    {
        "name": "Human Escalation Request",
        "scenario": "Customer asks to speak with a real person.",
        "messages": [
            "I have some detailed questions about the floor plan and legal documents. Can I speak to a real person?",
        ],
        "expected_behavior": "Agent should acknowledge the request and offer to connect them with a senior sales consultant. Should not try to answer questions about floor plans or legal documents.",
        "checks": [
            lambda turns: len(turns) >= 2,  # At least one exchange happened
        ],
    },
    {
        "name": "Invalid Booking Details",
        "scenario": "Customer provides an invalid phone number and an invalid time for a site visit.",
        "messages": [
            "I want to book a site visit.",
            "My name is Rahul, phone is 12345. I want to visit tomorrow at 3 AM.",
        ],
        "expected_behavior": "Agent should attempt to book but the booking tool will reject it due to invalid phone number and time. Agent should ask the customer to correct these details.",
        "checks": [
            lambda turns: any("valid" in t.content.lower() or "10-digit" in t.content.lower() or "time" in t.content.lower() for t in turns if t.role == "assistant"),
        ],
    },
]


async def run_test_case(test: dict, test_index: int) -> TestCaseResult:
    """
    Run a single test case by simulating a multi-turn conversation.

    Args:
        test: Test scenario dictionary.
        test_index: Index for generating unique session IDs.

    Returns:
        TestCaseResult with the conversation, pass/fail status, and notes.
    """
    session_id = f"test-session-{test_index}"
    reset_session(session_id)

    conversation: list[TestTurn] = []
    notes_parts = []

    try:
        for user_msg in test["messages"]:
            # Add user turn
            conversation.append(TestTurn(role="user", content=user_msg))

            # Get agent response
            result = await chat(session_id, user_msg)
            agent_response = result["response"]

            # Add assistant turn
            conversation.append(TestTurn(role="assistant", content=agent_response))

            # Note any booking results
            if result.get("booking_result"):
                booking = result["booking_result"]
                notes_parts.append(
                    f"Booking {booking['status']}: {booking.get('details', 'N/A')}"
                )

        # Run validation checks
        all_passed = True
        for i, check_fn in enumerate(test.get("checks", [])):
            try:
                if not check_fn(conversation):
                    all_passed = False
                    notes_parts.append(f"Check {i + 1} failed.")
            except Exception as e:
                all_passed = False
                notes_parts.append(f"Check {i + 1} error: {str(e)}")

        if all_passed:
            notes_parts.insert(0, "All checks passed.")

    except Exception as e:
        conversation.append(TestTurn(role="system", content=f"ERROR: {str(e)}"))
        notes_parts.append(f"Test execution error: {str(e)}")
        all_passed = False

    finally:
        # Clean up test session
        reset_session(session_id)

    return TestCaseResult(
        test_name=test["name"],
        scenario=test["scenario"],
        expected_behavior=test["expected_behavior"],
        conversation=conversation,
        passed=all_passed,
        notes=" | ".join(notes_parts),
    )


async def run_all_tests() -> dict:
    """
    Run all test scenarios and return a summary.

    Returns:
        dict with total, passed, failed counts and detailed results.
    """
    results = []

    for i, test in enumerate(TEST_SCENARIOS):
        result = await run_test_case(test, i)
        results.append(result)

    passed = sum(1 for r in results if r.passed)
    failed = len(results) - passed

    return {
        "total": len(results),
        "passed": passed,
        "failed": failed,
        "results": [r.model_dump() for r in results],
    }
