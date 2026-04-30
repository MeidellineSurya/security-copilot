from app.db.mongo import get_db
from app.models.schemas import Risk
from typing import List
from bson import ObjectId

async def get_risks_for_assessment(assessment_id: str, limit: int = 10) -> List[dict]:
    """Fetch top risks for an assessment, sorted by score descending."""
    db = get_db() # grab the MongoDB connection
    cursor = db.risks.find(
        {"assessment_id": assessment_id} # only risks for THIS assessment
    ).sort("score", -1).limit(limit) # highest score first, max 10

    risks = []
    async for doc in cursor:
        doc["id"] = str(doc.pop("_id")) # MongoDB uses _id, we rename to id
        risks.append(doc)

    return risks

async def get_assessment(assessment_id: str) -> dict | None:
    """Fetch assessment metadata."""
    db = get_db()
    doc = await db.assessments.find_one({"_id": ObjectId(assessment_id)})
    if doc:
        doc["id"] = str(doc.pop("_id"))
    return doc