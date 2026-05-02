from typing import List

def build_context(assessment: dict, risks: List[dict]) -> str:
    """
    Convert raw DB data into structured LLM-friendly context block.
    Includes real Risk IDs so the LLM can use them in tool calls.
    """
    if not assessment or not risks:
        return "No risk data available for this assessment."

    lines = [
        f"Company: {assessment.get('company', 'Unknown')}",
        f"Industry: {assessment.get('industry', 'Unknown')}",
        f"Assessment scope: {assessment.get('scope', 'Unknown')}",
        "",
        f"Total risks identified: {len(risks)}",
        "",
        "Risk inventory (sorted by severity score):",
    ]

    for i, risk in enumerate(risks, 1):
        lines.append(
            f"{i}. [{risk['severity'].upper()}] {risk['title']} "
            f"(Score: {risk['score']}/100)"
        )
        # Include real MongoDB ID so LLM can pass it to update_risk_status tool
        lines.append(f"   Risk ID: {risk.get('id', 'unknown')}")
        lines.append(f"   Category: {risk['category']}")
        lines.append(f"   Description: {risk['description']}")
        lines.append(f"   Remediation: {risk['remediation']}")
        lines.append(f"   Status: {risk.get('status', 'open')}")
        lines.append("")

    return "\n".join(lines)


SYSTEM_PROMPT = """You are an expert cybersecurity consultant and analyst.

You have been given structured risk assessment data for a client. Your job is to:
1. Answer the analyst's question clearly and precisely using ONLY the provided risk data
2. Prioritise findings by business impact and severity score
3. Give actionable, specific recommendations — not generic advice
4. Explain technical risks in both business and technical terms
5. Never invent risks or data not present in the context

You have access to tools that let you fetch specific data, update risk statuses, and search by category.
When you use a tool, NEVER show the raw tool call or function syntax in your response.
Always present tool results in clean, professional language as if you retrieved the information naturally.
When updating a risk status, use the exact Risk ID provided in the context above.
After marking a risk as resolved or updating a status, confirm it clearly in plain English.

Tone: Professional, direct, consultant-grade. Not a chatbot.

Format your response with:
- A direct answer to the question
- Bullet points for lists
- Bold for risk names
- End with 1-2 specific next steps the analyst should take
"""

def build_messages(context: str, query: str, history: list) -> list:
    """Build the full messages array for the LLM."""
    user_content = f"""Current risk assessment context:

{context}

---

Analyst question: {query}"""

    messages = list(history)
    messages.append({"role": "user", "content": user_content})
    return messages