from app.core.config import settings
from datetime import datetime

# Only initialize clients if keys are available
openai_client = None
index = None

if settings.OPENAI_API_KEY and settings.PINECONE_API_KEY:
    try:
        from openai import OpenAI
        from pinecone import Pinecone
        openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        index = pc.Index(settings.PINECONE_INDEX)
    except Exception as e:
        print(f"[Warning] Vector memory unavailable: {e}")

EMBEDDING_MODEL = "text-embedding-3-small"


def get_embedding(text: str) -> list[float]:
    if not openai_client:
        return []
    response = openai_client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text,
    )
    return response.data[0].embedding


async def store_conversation_turn(
    assessment_id: str,
    query: str,
    answer: str,
    session_id: str = None,
) -> dict:
    if not index or not openai_client:
        return {"stored": False, "reason": "Vector memory not configured"}

    combined_text = f"Question: {query}\nAnswer: {answer}"
    embedding = get_embedding(combined_text)
    if not embedding:
        return {"stored": False, "reason": "Embedding failed"}

    timestamp = datetime.utcnow().isoformat()
    vector_id = f"{assessment_id}_{timestamp}"

    index.upsert(vectors=[{
        "id": vector_id,
        "values": embedding,
        "metadata": {
            "assessment_id": assessment_id,
            "query": query[:500],
            "answer": answer[:1000],
            "timestamp": timestamp,
            "session_id": session_id or "unknown",
        }
    }])

    return {"stored": True, "vector_id": vector_id}


async def search_relevant_memories(
    assessment_id: str,
    query: str,
    top_k: int = 3,
) -> list[dict]:
    if not index or not openai_client:
        return []

    query_embedding = get_embedding(query)
    if not query_embedding:
        return []

    results = index.query(
        vector=query_embedding,
        top_k=top_k,
        filter={"assessment_id": {"$eq": assessment_id}},
        include_metadata=True,
    )

    memories = []
    for match in results.matches:
        if match.score > 0.75:
            memories.append({
                "query": match.metadata.get("query", ""),
                "answer": match.metadata.get("answer", ""),
                "timestamp": match.metadata.get("timestamp", ""),
                "relevance_score": round(match.score, 3),
            })

    return memories


def format_memories_for_context(memories: list[dict]) -> str:
    if not memories:
        return ""

    lines = ["Relevant context from previous conversations:"]
    for i, mem in enumerate(memories, 1):
        lines.append(f"\n[Memory {i}] (relevance: {mem['relevance_score']})")
        lines.append(f"Previously asked: {mem['query']}")
        lines.append(f"Previous answer: {mem['answer'][:300]}...")

    return "\n".join(lines)