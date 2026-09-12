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

    result = call_gemini(
        prompt,
        schema
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

    result = call_gemini(
        prompt,
        schema
    )

    state[
        "recovery_actions"
    ] = result.get(
        "actions",
        []
    )

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

    result = call_gemini(
        prompt,
        schema
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