import json
import os
import time

from dotenv import load_dotenv
from google import genai
from langgraph.graph import StateGraph, START, END
from typing import TypedDict

from services.rag_service import retrieve_recovery_knowledge


load_dotenv()


API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY is not configured."
    )


client = genai.Client(
    api_key=API_KEY
)


MODEL_NAME = "gemini-3-flash-preview"


class RecoveryState(TypedDict, total=False):

    recovery_context: dict
    priority: str
    diagnosis: dict
    retrieved_knowledge: list
    recovery_actions: list
    final_strategy: dict


def _fallback_diagnosis(context):
    """
    Deterministic fallback used when Gemini is unavailable.
    Uses only supplied transaction facts.
    """

    failure_reason = (
        context.get("failure_reason")
        or "UNKNOWN"
    )

    payment_method = (
        context.get("payment_method")
        or "UNKNOWN"
    )

    retry_count = int(
        context.get("retry_count") or 0
    )

    amount = float(
        context.get("amount") or 0
    )

    probability = context.get(
        "recovery_probability"
    )

    evidence = [
        f"failure_reason: {failure_reason}",
        f"payment_method: {payment_method}",
        f"amount: {amount}",
        f"retry_count: {retry_count}",
    ]

    if probability is not None:
        evidence.append(
            f"recovery_probability: {probability}"
        )

    return {
        "diagnosis": (
            f"The transaction failed with "
            f"{failure_reason} while using "
            f"{payment_method}. "
            f"The current recovery context indicates "
            f"{retry_count} previous retry attempt(s)."
        ),
        "confidence": 0.70,
        "evidence": evidence,
    }


def _fallback_actions(context, priority):
    """
    Deterministic recovery actions used when Gemini
    is unavailable.
    """

    failure_reason = (
        context.get("failure_reason")
        or "UNKNOWN"
    )

    retry_count = int(
        context.get("retry_count") or 0
    )

    probability = context.get(
        "recovery_probability"
    )

    amount = float(
        context.get("amount") or 0
    )

    probability_percent = None

    if probability is not None:

        probability_percent = float(
            probability
        )

        if probability_percent <= 1:
            probability_percent *= 100

    actions = []

    if (
        probability_percent is not None
        and probability_percent >= 70
        and retry_count < 3
    ):

        actions.append(
            {
                "action": "RETRY_PAYMENT",
                "reason": (
                    "The transaction has a high "
                    "recovery probability and remains "
                    "within the retry limit."
                ),
                "priority": "HIGH",
                "expected_impact": (
                    f"Potential recovery of approximately "
                    f"{probability_percent:.1f}% of the "
                    f"₹{amount:,.2f} revenue at risk."
                )
            }
        )

    elif (
        probability_percent is not None
        and probability_percent >= 40
        and retry_count < 3
    ):

        actions.append(
            {
                "action": "SEND_PAYMENT_LINK",
                "reason": (
                    "The transaction has meaningful "
                    "recovery potential and remains "
                    "eligible for controlled recovery."
                ),
                "priority": priority,
                "expected_impact": (
                    "Provides the customer with another "
                    "payment path without claiming that "
                    "the payment has already succeeded."
                )
            }
        )

    elif retry_count >= 3:

        actions.append(
            {
                "action": "STOP_RECOVERY",
                "reason": (
                    "The transaction has reached the "
                    "maximum retry limit."
                ),
                "priority": "HIGH",
                "expected_impact": (
                    "Prevents additional automated "
                    "recovery attempts."
                )
            }
        )

    else:

        actions.append(
            {
                "action": "ESCALATE_TO_HUMAN",
                "reason": (
                    f"The failure reason is "
                    f"{failure_reason} and the available "
                    "recovery probability does not "
                    "support an automatic recovery action."
                ),
                "priority": "MEDIUM",
                "expected_impact": (
                    "Allows manual review without "
                    "performing an unsupported automated action."
                )
            }
        )

    return actions


def _fallback_final_strategy(
    context,
    priority,
    actions
):
    """
    Deterministic final strategy used when Gemini
    is unavailable.
    """

    if not actions:

        return {
            "recommended_action":
                "STOP_RECOVERY",
            "reason":
                "No safe automated recovery action "
                "was generated.",
            "expected_recovery_impact":
                "No automated recovery should be attempted.",
            "confidence":
                0.70,
        }

    selected = actions[0]

    return {
        "recommended_action":
            selected["action"],
        "reason":
            selected["reason"],
        "expected_recovery_impact":
            selected["expected_impact"],
        "confidence":
            0.70,
    }


def call_gemini(prompt, schema):

    last_error = None

    for attempt in range(3):

        try:

            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": schema,
                },
            )

            if not response or not response.text:

                raise RuntimeError(
                    "Gemini returned an empty response."
                )

            return json.loads(
                response.text
            )

        except Exception as error:

            last_error = error

            error_text = str(error)

            if "429" in error_text:

                raise RuntimeError(
                    "GEMINI_QUOTA_EXCEEDED"
                )

            if (
                "503" not in error_text
                and "UNAVAILABLE" not in error_text
            ):

                raise

            if attempt < 2:

                time.sleep(
                    2 ** attempt
                )

    raise RuntimeError(
        "Gemini is temporarily unavailable "
        "after 3 attempts: "
        f"{last_error}"
    )


def diagnose_recovery(state):

    context = state[
        "recovery_context"
    ]

    prompt = f"""
You are the failure diagnosis engine
inside RecoverAI.

Analyze ONLY the supplied transaction
and customer information.

Do not invent facts.

Transaction context:
{json.dumps(context, indent=2)}

Return JSON with:

diagnosis:
A concise explanation of the observed
payment failure.

confidence:
A number between 0 and 1.

evidence:
A list containing only facts present
in the supplied context.

Do not recommend an action yet.
"""

    schema = {
        "type": "OBJECT",
        "properties": {
            "diagnosis": {
                "type": "STRING"
            },
            "confidence": {
                "type": "NUMBER"
            },
            "evidence": {
                "type": "ARRAY",
                "items": {
                    "type": "STRING"
                }
            }
        },
        "required": [
            "diagnosis",
            "confidence",
            "evidence"
        ]
    }

    try:

        result = call_gemini(
            prompt,
            schema
        )

    except Exception as error:

        print(
            "Gemini diagnosis unavailable. "
            "Using deterministic fallback:",
            error
        )

        result = _fallback_diagnosis(
            context
        )

    state["diagnosis"] = result

    return state


def retrieve_knowledge(state):

    context = state[
        "recovery_context"
    ]

    query_parts = [
        str(
            context.get(
                "failure_reason",
                ""
            )
        ),
        str(
            context.get(
                "payment_method",
                ""
            )
        ),
        str(
            context.get(
                "customer_segment",
                ""
            )
        ),
        str(
            context.get(
                "subscription_status",
                ""
            )
        ),
        str(
            context.get(
                "retry_count",
                ""
            )
        )
    ]

    query = " ".join(
        query_parts
    )

    knowledge = retrieve_recovery_knowledge(
        query,
        top_k=5
    )

    state[
        "retrieved_knowledge"
    ] = knowledge

    return state


def generate_recovery_actions(state):

    context = state[
        "recovery_context"
    ]

    diagnosis = state[
        "diagnosis"
    ]

    knowledge = state[
        "retrieved_knowledge"
    ]

    prompt = f"""
You are the recovery-action planner
inside RecoverAI.

Use ONLY:
1. transaction context
2. diagnosis
3. retrieved recovery knowledge

Transaction:
{json.dumps(context, indent=2)}

Diagnosis:
{json.dumps(diagnosis, indent=2)}

Retrieved knowledge:
{json.dumps(knowledge, indent=2)}

Generate safe recovery actions.

Possible actions include:
- RETRY_PAYMENT
- SEND_PAYMENT_LINK
- REQUEST_PAYMENT_METHOD_UPDATE
- ESCALATE_TO_HUMAN
- STOP_RECOVERY

Do not claim an action was executed.

Return JSON containing a list of
recommended actions with:
action
reason
priority
expected_impact
"""

    schema = {
        "type": "OBJECT",
        "properties": {
            "actions": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "action": {
                            "type": "STRING"
                        },
                        "reason": {
                            "type": "STRING"
                        },
                        "priority": {
                            "type": "STRING"
                        },
                        "expected_impact": {
                            "type": "STRING"
                        }
                    },
                    "required": [
                        "action",
                        "reason",
                        "priority",
                        "expected_impact"
                    ]
                }
            }
        },
        "required": [
            "actions"
        ]
    }

    try:

        result = call_gemini(
            prompt,
            schema
        )

        actions = result.get(
            "actions",
            []
        )

    except Exception as error:

        print(
            "Gemini action planner unavailable. "
            "Using deterministic fallback:",
            error
        )

        actions = _fallback_actions(
            context,
            state.get(
                "priority",
                "NORMAL"
            )
        )

    state[
        "recovery_actions"
    ] = actions

    return state


def generate_final_strategy(state):

    context = state[
        "recovery_context"
    ]

    priority = state[
        "priority"
    ]

    diagnosis = state[
        "diagnosis"
    ]

    knowledge = state[
        "retrieved_knowledge"
    ]

    actions = state[
        "recovery_actions"
    ]

    prompt = f"""
You are the final recovery strategy
engine inside RecoverAI.

Create one deterministic,
evidence-grounded recovery recommendation.

Transaction:
{json.dumps(context, indent=2)}

Priority:
{priority}

Diagnosis:
{json.dumps(diagnosis, indent=2)}

Knowledge:
{json.dumps(knowledge, indent=2)}

Candidate actions:
{json.dumps(actions, indent=2)}

Rules:

- Use only supplied facts.
- Do not invent customer behavior.
- Do not invent payment details.
- Do not claim money was recovered.
- Do not claim an action was executed.
- Respect the supplied retry count.
- Respect the supplied recovery probability.
- Prefer a payment link for a failed
  payment when recovery is approved.
- Escalate when appropriate.
- Stop when recovery should not continue.

Return:
recommended_action
reason
expected_recovery_impact
confidence
"""

    schema = {
        "type": "OBJECT",
        "properties": {
            "recommended_action": {
                "type": "STRING"
            },
            "reason": {
                "type": "STRING"
            },
            "expected_recovery_impact": {
                "type": "STRING"
            },
            "confidence": {
                "type": "NUMBER"
            }
        },
        "required": [
            "recommended_action",
            "reason",
            "expected_recovery_impact",
            "confidence"
        ]
    }

    try:

        result = call_gemini(
            prompt,
            schema
        )

    except Exception as error:

        print(
            "Gemini final strategy unavailable. "
            "Using deterministic fallback:",
            error
        )

        result = _fallback_final_strategy(
            context,
            priority,
            actions
        )

    state[
        "final_strategy"
    ] = result

    return state


graph = StateGraph(
    RecoveryState
)

graph.add_node(
    "diagnose_recovery",
    diagnose_recovery
)

graph.add_node(
    "retrieve_knowledge",
    retrieve_knowledge
)

graph.add_node(
    "generate_recovery_actions",
    generate_recovery_actions
)

graph.add_node(
    "generate_final_strategy",
    generate_final_strategy
)


graph.add_edge(
    START,
    "diagnose_recovery"
)

graph.add_edge(
    "diagnose_recovery",
    "retrieve_knowledge"
)

graph.add_edge(
    "retrieve_knowledge",
    "generate_recovery_actions"
)

graph.add_edge(
    "generate_recovery_actions",
    "generate_final_strategy"
)

graph.add_edge(
    "generate_final_strategy",
    END
)


recovery_agent = graph.compile()


def generate_strategy(
    recovery_context,
    priority
):

    result = recovery_agent.invoke(
        {
            "recovery_context":
                recovery_context,
            "priority":
                priority
        }
    )

    return result