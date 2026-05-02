import json
import re
from datetime import datetime, date
from groq import Groq
from app.core.config import settings
from app.services.context_builder import SYSTEM_PROMPT
from app.services.tools import TOOLS, TOOL_FUNCTIONS

def json_serializer(obj):
    """Handle datetime and other non-serializable types."""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

def clean_response(text: str) -> str:
    """
    Remove any raw function call syntax the LLM accidentally outputs.
    LLaMA sometimes prints <function>...</function> instead of calling tools properly.
    We strip these and return a clean fallback message.
    """
    # Remove <function(...)>...</function> patterns
    cleaned = re.sub(r'<function[^>]*>.*?</function>', '', text, flags=re.DOTALL)
    cleaned = cleaned.strip()

    # If nothing left after cleaning, return a helpful message
    if not cleaned:
        return "I've processed your request. Please ask a follow-up question or specify which risk you'd like to update."
    return cleaned

client = Groq(api_key=settings.GROQ_API_KEY)
MODEL = "llama-3.3-70b-versatile"

SUGGESTED_FOLLOWUPS = [
    "What should I fix first?",
    "Explain the top risk in detail",
    "What are the quick wins?",
    "Show me only Critical risks",
    "What's the business impact of these risks?",
    "How long would remediation take?",
]

def get_suggested_followups(query: str) -> list[str]:
    q = query.lower()
    if "fix first" in q or "priorit" in q:
        return ["What are the quick wins?", "Explain the top risk in detail", "What's the business impact?"]
    if "critical" in q or "top" in q:
        return ["How do I remediate these?", "What's the business impact?", "Show me High risks too"]
    if "explain" in q:
        return ["What should I fix first?", "How long will remediation take?", "What are the quick wins?"]
    if "mark" in q or "resolve" in q or "status" in q:
        return ["What other risks need attention?", "Show me remaining open risks", "What's the overall summary?"]
    return SUGGESTED_FOLLOWUPS[:3]


async def reason(messages: list, context: str, assessment_id: str = None) -> dict:
    """
    Agentic reasoning loop with function calling.

    Flow:
    1. Send messages + tools to Groq
    2. If LLM calls a tool → execute it → append result → loop again
    3. If LLM gives a text response → clean it → return it

    Max 5 iterations to prevent infinite loops.
    """
    full_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + messages

    if assessment_id:
        full_messages[0]["content"] += f"\n\nCurrent assessment_id: {assessment_id}\n\nIMPORTANT: When taking actions like updating risk status, use the available tools directly. Never output raw function call syntax in your response text."

    max_iterations = 5
    iteration = 0

    while iteration < max_iterations:
        iteration += 1

        response = client.chat.completions.create(
            model=MODEL,
            messages=full_messages,
            tools=TOOLS,
            tool_choice="auto",
            max_tokens=1500,
            temperature=0.3,
        )

        message = response.choices[0].message

        # ── Case 1: LLM properly called a tool ──
        if message.tool_calls:
            full_messages.append({
                "role": "assistant",
                "content": message.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in message.tool_calls
                ]
            })

            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)

                if "assessment_id" in TOOL_FUNCTIONS[tool_name].__code__.co_varnames:
                    if "assessment_id" not in tool_args and assessment_id:
                        tool_args["assessment_id"] = assessment_id

                tool_fn = TOOL_FUNCTIONS.get(tool_name)
                if tool_fn:
                    tool_result = await tool_fn(**tool_args)
                else:
                    tool_result = {"error": f"Tool {tool_name} not found"}

                full_messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(tool_result, default=json_serializer)
                })

            continue

        # ── Case 2: LLM gave a text response ──
        raw_answer = message.content or "I could not generate a response."

        # Clean any accidentally leaked function call syntax
        answer = clean_response(raw_answer)

        return {
            "answer": answer,
            "risks_referenced": [],
            "usage": {
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
                "iterations": iteration,
            }
        }

    return {
        "answer": "I reached the maximum reasoning steps. Please try rephrasing your question.",
        "risks_referenced": [],
        "usage": {"iterations": max_iterations}
    }