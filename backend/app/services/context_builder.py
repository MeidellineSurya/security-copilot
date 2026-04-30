from typing import List

def build_context(assessment: dict, risks: List[dict]) -> str:
    """
    Convert raw DB data into a structured, LLM-friendly context block.
    This is what separates a copilot from a generic chatbot.
    """
    if not assessment or not risks:
        return "No risk data available for this assessment."

    lines = [ # takes raw MongoDB documents to build clean numbered briefing document
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
        lines.append(f"   Category: {risk['category']}")
        lines.append(f"   Description: {risk['description']}")
        lines.append(f"   Remediation: {risk['remediation']}")
        lines.append("")

    return "\n".join(lines)


# personality and ruleset of copilot.
# key rule: only reason over provided data to prevent hallucination
SYSTEM_PROMPT = """You are an expert cybersecurity consultant and analyst.

You have been given structured risk assessment data for a client. Your job is to:
1. Answer the analyst's question clearly and precisely using ONLY the provided risk data
2. Prioritise findings by business impact and severity score
3. Give actionable, specific recommendations — not generic advice
4. Explain technical risks in both business and technical terms
5. Never invent risks or data not present in the context

Tone: Professional, direct, consultant-grade. Not a chatbot.

Format your response with:
- A direct answer to the question
- Bullet points for lists
- Bold for risk names
- End with 1-2 specific next steps the analyst should take
"""

def build_messages(context: str, query: str, history: list) -> list:
    """Build the full messages array for the Anthropic API."""
    user_content = f"""Current risk assessment context:

{context}

---

Analyst question: {query}"""

    messages = list(history)  # preserve conversation memory from all previous turns
    messages.append({"role": "user", "content": user_content}) # this allows followup questions
    return messages