from datetime import datetime
from app.db.mongo import get_db
from bson import ObjectId

# ── Tool definitions ──────────────────────────────────────────────────────────
# These are passed to the LLM so it knows what actions it can take.
# The LLM reads the "description" field to decide when to use each tool.
# The "parameters" field tells it what inputs each tool needs.

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_top_risks",
            "description": "Get the top N risks for an assessment sorted by severity score. Use this when the user asks about their biggest risks, top risks, or wants a prioritized list.",
            "parameters": {
                "type": "object",
                "properties": {
                    "assessment_id": {
                        "type": "string",
                        "description": "The assessment ID to fetch risks for"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of top risks to return (default 5)",
                        "default": 5
                    },
                    "severity": {
                        "type": "string",
                        "enum": ["Critical", "High", "Medium", "Low"],
                        "description": "Filter by severity level (optional)"
                    }
                },
                "required": ["assessment_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_risk_status",
            "description": "Update the status of a specific risk — mark it as resolved, in progress, or accepted. Use this when the user says they've fixed something or wants to update a risk's status.",
            "parameters": {
                "type": "object",
                "properties": {
                    "risk_id": {
                        "type": "string",
                        "description": "The MongoDB ID of the risk to update"
                    },
                    "status": {
                        "type": "string",
                        "enum": ["open", "in_progress", "resolved", "accepted"],
                        "description": "New status for the risk"
                    },
                    "note": {
                        "type": "string",
                        "description": "Optional note about why the status changed"
                    }
                },
                "required": ["risk_id", "status"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_risk_summary",
            "description": "Get a statistical summary of all risks for an assessment — counts by severity, average score, most common categories. Use when the user asks for an overview or summary.",
            "parameters": {
                "type": "object",
                "properties": {
                    "assessment_id": {
                        "type": "string",
                        "description": "The assessment ID to summarize"
                    }
                },
                "required": ["assessment_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_risks_by_category",
            "description": "Search risks filtered by category such as AWS, Application, Network. Use when user asks about a specific type or area of risk.",
            "parameters": {
                "type": "object",
                "properties": {
                    "assessment_id": {
                        "type": "string",
                        "description": "The assessment ID to search"
                    },
                    "category": {
                        "type": "string",
                        "description": "Category to filter by e.g. AWS, Application, Network"
                    }
                },
                "required": ["assessment_id", "category"]
            }
        }
    }
]


# ── Tool execution functions ───────────────────────────────────────────────────
# These are the actual Python functions that run when the LLM calls a tool.
# The LLM decides WHICH tool to call — Python actually executes it.

async def get_top_risks(assessment_id: str, limit: int = 5, severity: str = None) -> dict:
    """Fetch top risks sorted by score, optionally filtered by severity."""
    db = get_db()
    query = {"assessment_id": assessment_id}
    if severity:
        query["severity"] = severity

    cursor = db.risks.find(query).sort("score", -1).limit(limit)
    risks = []
    async for doc in cursor:
        doc["id"] = str(doc.pop("_id"))
        risks.append(doc)

    return {
        "risks": risks,
        "count": len(risks),
        "filtered_by_severity": severity
    }


async def update_risk_status(risk_id: str, status: str, note: str = None) -> dict:
    """Update the status of a risk in MongoDB."""
    db = get_db()

    update = {
        "$set": {
            "status": status,
            "updated_at": datetime.utcnow(),
        }
    }
    if note:
        update["$set"]["status_note"] = note

    result = await db.risks.update_one(
        {"_id": ObjectId(risk_id)},
        update
    )

    if result.matched_count == 0:
        return {"success": False, "message": f"Risk {risk_id} not found"}

    return {
        "success": True,
        "message": f"Risk status updated to '{status}'",
        "risk_id": risk_id,
        "new_status": status
    }


async def get_risk_summary(assessment_id: str) -> dict:
    """Return statistical summary of risks for an assessment."""
    db = get_db()

    total = await db.risks.count_documents({"assessment_id": assessment_id})
    critical = await db.risks.count_documents({"assessment_id": assessment_id, "severity": "Critical"})
    high = await db.risks.count_documents({"assessment_id": assessment_id, "severity": "High"})
    medium = await db.risks.count_documents({"assessment_id": assessment_id, "severity": "Medium"})
    low = await db.risks.count_documents({"assessment_id": assessment_id, "severity": "Low"})

    # Get average score
    pipeline = [
        {"$match": {"assessment_id": assessment_id}},
        {"$group": {"_id": None, "avg_score": {"$avg": "$score"}}}
    ]
    avg_result = await db.risks.aggregate(pipeline).to_list(1)
    avg_score = round(avg_result[0]["avg_score"], 1) if avg_result else 0

    # Get top categories
    category_pipeline = [
        {"$match": {"assessment_id": assessment_id}},
        {"$group": {"_id": "$category", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 5}
    ]
    categories = await db.risks.aggregate(category_pipeline).to_list(5)

    return {
        "total": total,
        "by_severity": {
            "critical": critical,
            "high": high,
            "medium": medium,
            "low": low
        },
        "average_score": avg_score,
        "top_categories": [{"category": c["_id"], "count": c["count"]} for c in categories]
    }


async def search_risks_by_category(assessment_id: str, category: str) -> dict:
    """Search risks by category."""
    db = get_db()

    cursor = db.risks.find({
        "assessment_id": assessment_id,
        "category": {"$regex": category, "$options": "i"}  # case-insensitive
    }).sort("score", -1)

    risks = []
    async for doc in cursor:
        doc["id"] = str(doc.pop("_id"))
        risks.append(doc)

    return {
        "category": category,
        "count": len(risks),
        "risks": risks
    }


# Map tool names to their Python functions
TOOL_FUNCTIONS = {
    "get_top_risks": get_top_risks,
    "update_risk_status": update_risk_status,
    "get_risk_summary": get_risk_summary,
    "search_risks_by_category": search_risks_by_category,
}