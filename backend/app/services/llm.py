from groq import Groq
from app.core.config import settings
from app.services.context_builder import SYSTEM_PROMPT

client = Groq(api_key=settings.GROQ_API_KEY) 

# groq client created once when app starts
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
    """Return contextual follow-up suggestions based on query intent."""
    q = query.lower()
    # simple keyword matching on user's query to offer relevant next questions
    if "fix first" in q or "priorit" in q:
        return ["What are the quick wins?", "Explain the top risk in detail", "What's the business impact?"]
    if "critical" in q or "top" in q:
        return ["How do I remediate these?", "What's the business impact?", "Show me High risks too"]
    if "explain" in q:
        return ["What should I fix first?", "How long will remediation take?", "What are the quick wins?"]
    return SUGGESTED_FOLLOWUPS[:3]


async def reason(messages: list, context: str) -> dict:
    """
    Send structured messages to Groq and return the response.

    Groq uses the OpenAI-compatible chat completions format:
    - system: sets the persona and rules
    - user/assistant: the conversation history
    """
    # Groq expects system message prepended to the messages list.
    # LLM always know role before reading the conversation
    full_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + messages

    response = client.chat.completions.create(
        model=MODEL,
        messages=full_messages,
        max_tokens=1500,
        temperature=0.3,  # lower = more consistent, factual responses
    )

    answer = response.choices[0].message.content # pick first response from list of choices

    return {
        "answer": answer,
        "risks_referenced": [],
        "usage": {
            "input_tokens": response.usage.prompt_tokens,
            "output_tokens": response.usage.completion_tokens,
        }
    }