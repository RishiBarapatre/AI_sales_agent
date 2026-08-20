"""
Simulated site-visit booking service for Northstar One.

Defined as a LangChain tool so the AI agent can invoke it via function calling.
Simulates a ~20% failure rate to demonstrate error handling.
"""

import random
from langchain_core.tools import tool


@tool
def book_site_visit(
    customer_name: str,
    phone_number: str,
    preferred_date: str,
    preferred_time: str,
) -> str:
    """Book a site visit for a customer at Northstar One, Sector 79, Gurugram.

    Use this tool when the customer has expressed interest in visiting the property
    and has provided their name, phone number, preferred date, and preferred time.

    Args:
        customer_name: Full name of the customer.
        phone_number: Customer's phone number for confirmation.
        preferred_date: Preferred date for the site visit, e.g. '25th August' or 'next Saturday'.
        preferred_time: Preferred time slot, e.g. '10:00 AM' or 'afternoon'.

    Returns:
        A string describing whether the booking was successful or failed,
        along with relevant details.
    """
    import re
    
    errors = []

    # 1. Validate Phone Number (must be exactly 10 digits)
    digits_only = re.sub(r'\D', '', phone_number)
    if len(digits_only) != 10:
        errors.append("Invalid phone number. Please provide a valid 10-digit mobile number.")

    # 2. Validate Reasonable Timing (e.g., 9 AM to 6 PM)
    time_lower = preferred_time.lower()
    time_invalid = False
    
    # Check for obvious night time keywords
    if "night" in time_lower or "midnight" in time_lower or "late" in time_lower:
        time_invalid = True
    else:
        # Try to extract the hour to do basic bounds checking
        # This handles formats like "3 AM", "3:00 PM", "15:00", "03:00 am"
        match = re.search(r'(\d{1,2})(?::\d{2})?\s*(am|pm)?', time_lower)
        if match:
            hour = int(match.group(1))
            am_pm = match.group(2)
            
            # Convert to 24-hour format for easier comparison
            if am_pm == 'pm' and hour < 12:
                hour += 12
            elif am_pm == 'am' and hour == 12:
                hour = 0
                
            # Reject times before 9 AM or after 6 PM (18:00)
            # Note: 6 PM (18) is okay, but 7 PM (19) is not
            if hour < 9 or hour > 18:
                time_invalid = True

    if time_invalid:
        errors.append("Site visits are only available between 9:00 AM and 6:00 PM. Please suggest a reasonable time during working hours.")

    if errors:
        return "BOOKING FAILED: " + " ".join(errors)

    # Simulate a ~20% failure rate
    if random.random() < 0.2:
        failure_reasons = [
            "The requested time slot is currently unavailable. Please suggest a different time.",
            "Our booking system is experiencing a temporary issue. Please try again shortly.",
            "The selected date is fully booked for site visits. Please choose another date.",
        ]
        reason = random.choice(failure_reasons)
        return f"BOOKING FAILED: {reason}"

    # Generate a confirmation number
    confirmation_number = f"NSH-{random.randint(10000, 99999)}"

    return (
        f"BOOKING CONFIRMED. "
        f"Confirmation Number: {confirmation_number}. "
        f"Customer Name: {customer_name}. "
        f"Phone: {phone_number}. "
        f"Date: {preferred_date}. "
        f"Time: {preferred_time}. "
        f"Location: Northstar One Sales Gallery, Sector 79, Gurugram. "
        f"The sales team will call the customer to reconfirm the visit."
    )


def book_site_visit_forced_fail(
    customer_name: str,
    phone_number: str,
    preferred_date: str,
    preferred_time: str,
) -> str:
    """Always-failing version of booking, used for testing failure handling."""
    return (
        "BOOKING FAILED: The requested time slot is currently unavailable. "
        "Please suggest a different time."
    )
