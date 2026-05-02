from fastapi import APIRouter, HTTPException
from app.models.schemas import CopilotQuery, CopilotResponse
from app.services.retrieval import get_risks_for_assessment, get_assessment
from app.services.context_builder import build_context, build_messages
from app.services.llm import reason, get_suggested_followups

router = APIRouter()

@router.post("/query", response_model=CopilotResponse)
async def copilot_query(payload: CopilotQuery):
    """
    Main copilot endpoint — now with function calling.
    The LLM can now decide to fetch additional data or take actions.
    """
    # 1. Retrieval — initial context
    assessment = await get_assessment(payload.assessment_id)
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    risks = await get_risks_for_assessment(payload.assessment_id)

    # 2. Context builder
    context = build_context(assessment, risks)
    messages = build_messages(context, payload.query, payload.conversation_history)

    # 3. LLM reasoning — now with assessment_id for function calling
    result = await reason(
        messages=messages,
        context=context,
        assessment_id=payload.assessment_id  # ← new: enables tool use
    )

    # 4. Format response
    followups = get_suggested_followups(payload.query)

    return CopilotResponse(
        answer=result["answer"],
        risks_referenced=result["risks_referenced"],
        suggested_followups=followups,
    )