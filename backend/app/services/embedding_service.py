from openai import OpenAI
from pinecone import Pinecone
from datetime import datetime
from app.core.config import settings

# Initialize clients
openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
pc = Pinecone(api_key=settings.PINECONE_API_KEY)
index = pc.Index(settings.PINECONE_INDEX)

EMBEDDING_MODEL = "text-embedding-3-small"  # 1536 dimensions, cheap and accurate


def get_embedding(text: str) -> list[float]:
    """
    Convert text into a 1536-dimensional vector using OpenAI.

    This is the core operation that enables semantic search.
    Similar text → similar vectors → findable by meaning not keywords.
    """
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
    """
    Store a conversation turn in Pinecone for long-term memory.

    We embed the query + answer together so semantic search
    can find this memory when similar questions are asked later.

    Args:
        assessment_id: links memory to a specific assessment
        query: what the user asked
        answer: what the LLM responded
        session_id: optional session identifier
    """
    # Combine query + answer for richer embedding
    combined_text = f"Question: {query}\nAnswer: {answer}"
    embedding = get_embedding(combined_text)

    # Create a unique ID for this memory
    timestamp = datetime.utcnow().isoformat()
    vector_id = f"{assessment_id}_{timestamp}"

    # Store in Pinecone with metadata
    # Metadata lets us filter searches by assessment_id
    index.upsert(vectors=[{
        "id": vector_id,
        "values": embedding,
        "metadata": {
            "assessment_id": assessment_id,
            "query": query[:500],        # truncate for metadata limit
            "answer": answer[:1000],     # truncate for metadata limit
            "timestamp": timestamp,
            "session_id": session_id or "unknown",
        }
    }])

    return {
        "stored": True,
        "vector_id": vector_id,
        "assessment_id": assessment_id,
    }


async def search_relevant_memories(
    assessment_id: str,
    query: str,
    top_k: int = 3,
) -> list[dict]:
    """
    Search Pinecone for past conversations relevant to the current query.

    Uses cosine similarity to find the most semantically similar
    past Q&A pairs — regardless of exact wording.

    Args:
        assessment_id: only search memories for this assessment
        query: the current user question
        top_k: how many memories to retrieve (default 3)

    Returns:
        List of relevant past Q&A pairs sorted by relevance
    """
    query_embedding = get_embedding(query)

    results = index.query(
        vector=query_embedding,
        top_k=top_k,
        filter={"assessment_id": {"$eq": assessment_id}},  # scoped to assessment
        include_metadata=True,
    )

    memories = []
    for match in results.matches:
        # Only include memories with decent similarity score
        if match.score > 0.75:
            memories.append({
                "query": match.metadata.get("query", ""),
                "answer": match.metadata.get("answer", ""),
                "timestamp": match.metadata.get("timestamp", ""),
                "relevance_score": round(match.score, 3),
            })

    return memories


def format_memories_for_context(memories: list[dict]) -> str:
    """
    Format retrieved memories into a readable context block
    that can be injected into the LLM prompt.
    """
    if not memories:
        return ""

    lines = ["Relevant context from previous conversations:"]
    for i, mem in enumerate(memories, 1):
        lines.append(f"\n[Memory {i}] (relevance: {mem['relevance_score']})")
        lines.append(f"Previously asked: {mem['query']}")
        lines.append(f"Previous answer: {mem['answer'][:300]}...")

    return "\n".join(lines)