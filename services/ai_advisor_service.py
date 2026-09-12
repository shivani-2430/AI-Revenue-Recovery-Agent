import os

from dotenv import load_dotenv
from google import genai


# =========================================================
# ENVIRONMENT
# =========================================================

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY is missing. Check your .env file."
    )

client = genai.Client(
    api_key=API_KEY
)


# =========================================================
# MODEL
# =========================================================

MODEL_NAME = "gemini-3-flash-preview"


# =========================================================
# RECOVERAI AI ADVISOR
# =========================================================

def ask_project_advisor(
    project_context,
    question,
):
    """
    RecoverAI AI Advisor.

    Uses the supplied transaction, customer, ML prediction,
    failure, and recovery context as the source of truth.

    The advisor provides recovery-focused reasoning and
    recommendations without inventing transaction facts.
    """

    prompt = f"""
You are the AI Recovery Advisor inside RecoverAI,
an AI-powered revenue recovery system.

Your responsibility is to analyze failed payment transactions
and provide practical recovery intelligence.

This is NOT a generic chatbot.

You MUST use the supplied RECOVERY CONTEXT as the source
of truth.

STRICT RULES:

1. Use only information present in RECOVERY CONTEXT.
2. Never invent customer information.
3. Never invent transaction information.
4. Never invent payment amounts, failure reasons,
   recovery probabilities, or payment history.
5. Do not claim that an action was executed unless the
   context explicitly says it was executed.
6. Do not change the ML recovery probability.
7. Treat the ML prediction as an analytical signal,
   not as an absolute guarantee.
8. Consider customer history, transaction amount,
   failure reason, retry count, payment method,
   subscription status, and recovery probability
   when available.
9. Recommendations must be practical and recovery-focused.
10. If required information is unavailable, clearly state
    that it is unavailable.
11. Do not provide generic project-management advice.
12. Do not discuss budget, team risk, project health,
    project feasibility, or technology risk.
13. Focus specifically on recovering failed revenue.

RECOVERY CONTEXT:
{project_context}

USER QUESTION:
{question}

Provide a concise professional response.

Your response should contain:

- Diagnosis
- Recovery Recommendation
- Reasoning
- Expected Recovery Impact

Do not invent numerical values that are not present
in the supplied context.
"""

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
        )

        text = getattr(
            response,
            "text",
            None,
        )

        if not text:
            return (
                "The AI Recovery Advisor could not generate "
                "a response from the supplied recovery context."
            )

        return text.strip()

    except Exception as exc:
        return (
            "The AI Recovery Advisor is temporarily unavailable. "
            f"Reason: {str(exc)}"
        )