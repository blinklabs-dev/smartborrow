import openai
from sqlalchemy.orm import Session

from .. import models
from ..core.config import settings

# In a real app, you would initialize the client once, not in each function call.
# client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

def assess_risk_of_finding(db: Session, finding: dict) -> str:
    """
    Uses an LLM to assess the risk of applying a given optimization.

    Args:
        db: The database session.
        finding: A dictionary representing an optimization found by the scanner.

    Returns:
        A string representing the risk level: 'LOW', 'MEDIUM', or 'HIGH'.
    """

    check_id = finding.get("check_id")
    if not check_id:
        return "UNKNOWN" # Or raise an error

    check = db.query(models.optimization_check.OptimizationCheck).filter(models.optimization_check.OptimizationCheck.id == check_id).first()

    if not check:
        return "UNKNOWN"

    # In a real implementation, you would make an API call here.
    # For this MVP, we will simulate the AI's logic with a simple rule-based system
    # to avoid the need for a live API key during testing and development.

    complexity = check.complexity.lower()
    impact = check.impact_level.lower()
    description = check.description.lower()

    if "drop" in description or "delete" in description:
        return "HIGH"

    if complexity == "high" or impact == "strategic":
        return "HIGH"

    if complexity == "medium" or impact == "high_impact":
        return "MEDIUM"

    if complexity == "low" and impact == "quick_win":
        return "LOW"

    # Default fallback
    return "MEDIUM"

    # --- Example of what a real implementation would look like ---
    #
    # prompt = f"""
    # You are an expert Snowflake DBA and risk analyst. You have identified a potential optimization.
    #
    # Title: {check.title}
    # Category: {check.category}
    # Description: {check.description}
    # How to Implement: {check.how_to_implement}
    #
    # The proposed fix involves running a command like this: {check.code_snippet}
    #
    # Based on this information, analyze the risk of AUTOMATICALLY applying this change
    # to a production Snowflake environment. Consider the potential for data loss,
    # performance degradation, and operational disruption.
    #
    # Respond with only one word: 'LOW', 'MEDIUM', or 'HIGH'.
    # """
    #
    # try:
    #     response = client.chat.completions.create(
    #         model="gpt-4",
    #         messages=[{"role": "user", "content": prompt}],
    #         temperature=0.0,
    #     )
    #     risk_level = response.choices[0].message.content.strip().upper()
    #     if risk_level not in ['LOW', 'MEDIUM', 'HIGH']:
    #         return "UNKNOWN" # Or handle unexpected response
    #     return risk_level
    # except Exception as e:
    #     print(f"Error calling OpenAI API: {e}")
    #     return "UNKNOWN"
