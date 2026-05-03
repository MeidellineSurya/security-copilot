from fastapi import APIRouter, HTTPException
from app.models.schemas import CopilotQuery, CopilotResponse
from app.services.retrieval import get_risks_for_assessment, get_assessment
from app.services.context_builder import build_context, build_messages
from app.services.llm import reason, get_suggested_followups
from app.services.embedding_service import (
    store_conversation_turn,
    search_relevant_memories,
    format_memories_for_context,
)

router = APIRouter()

@router.post("/query", response_model=CopilotResponse)
async def copilot_query(payload: CopilotQuery):
    """
    Main copilot endpoint — now with long-term vector memory.

    Flow:
    1. Retrieve risks from MongoDB
    2. Search Pinecone for relevant past conversations
    3. Build context (risks + memories)
    4. LLM reasons with function calling
    5. Store this turn in Pinecone for future sessions
    """
    # 1. Retrieval layer
    assessment = await get_assessment(payload.assessment_id)
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    risks = await get_risks_for_assessment(payload.assessment_id)

    # 2. Search long-term memory for relevant past conversations
    memories = []
    memory_context = ""
    try:
        memories = await search_relevant_memories(
            assessment_id=payload.assessment_id,
            query=payload.query,
            top_k=3,
        )
        memory_context = format_memories_for_context(memories)
    except Exception:
        # Memory search failing should never break the main flow
        pass

    # 3. Build context — risks + memories injected together
    risk_context = build_context(assessment, risks)
    full_context = risk_context
    if memory_context:
        full_context = f"{risk_context}\n\n{memory_context}"

    messages = build_messages(full_context, payload.query, payload.conversation_history)

    # 4. LLM reasoning with function calling
    result = await reason(
        messages=messages,
        context=full_context,
        assessment_id=payload.assessment_id,
    )

    # 5. Store this turn in Pinecone for future sessions
    try:
        await store_conversation_turn(
            assessment_id=payload.assessment_id,
            query=payload.query,
            answer=result["answer"],
        )
    except Exception:
        # Memory storage failing should never break the response
        pass

    followups = get_suggested_followups(payload.query)

    return CopilotResponse(
        answer=result["answer"],
        risks_referenced=result["risks_referenced"],
        suggested_followups=followups,
    )