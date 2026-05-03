from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.aws_sync import sync_security_hub
from app.db.mongo import get_db
from bson import ObjectId

router = APIRouter()


class SyncRequest(BaseModel):
    assessment_id: str


@router.post("/aws")
async def sync_aws(payload: SyncRequest):
    db = get_db()

    assessment = await db.assessments.find_one(
        {"_id": ObjectId(payload.assessment_id)}
    )
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    try:
        result = await sync_security_hub(payload.assessment_id)
        return {
            "message": result["message"],
            "synced": result.get("synced", 0),
            "updated": result.get("updated", 0),
            "total": result.get("total", 0),
            "new_critical": result.get("new_critical", []),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"AWS sync failed: {str(e)}"
        )


@router.get("/status/{assessment_id}")
async def sync_status(assessment_id: str):
    db = get_db()

    total = await db.risks.count_documents({"assessment_id": assessment_id})
    critical = await db.risks.count_documents({
        "assessment_id": assessment_id,
        "severity": "Critical"
    })
    high = await db.risks.count_documents({
        "assessment_id": assessment_id,
        "severity": "High"
    })
    aws_sourced = await db.risks.count_documents({
        "assessment_id": assessment_id,
        "source": "aws_security_hub"
    })

    return {
        "assessment_id": assessment_id,
        "total_risks": total,
        "critical": critical,
        "high": high,
        "aws_sourced": aws_sourced,
        "manual": total - aws_sourced,
    }


@router.post("/test-alert")
async def test_alert():
    """
    Send a test alert email to verify Resend is configured correctly.
    Use this to confirm email works before relying on the nightly sync.
    """
    from app.services.alert_service import send_test_alert
    result = await send_test_alert()
    return result