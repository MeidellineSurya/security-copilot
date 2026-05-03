import asyncio
from celery import shared_task
from app.core.celery_app import celery_app
from app.db.mongo import connect_db, get_db
from app.services.aws_sync import sync_security_hub


async def _sync_all_assessments_async() -> dict:
    """
    Async implementation of the sync task.
    Fetches all assessments and syncs each one with AWS Security Hub.
    """
    # Celery workers don't share the FastAPI lifespan
    # so we need to connect to MongoDB manually here
    await connect_db()
    db = get_db()

    # Fetch all assessments
    cursor = db.assessments.find({})
    assessments = []
    async for doc in cursor:
        doc["id"] = str(doc.pop("_id"))
        assessments.append(doc)

    if not assessments:
        return {"message": "No assessments found", "synced": 0}

    total_synced = 0
    total_updated = 0
    all_new_criticals = []
    errors = []

    for assessment in assessments:
        try:
            result = await sync_security_hub(assessment["id"])
            total_synced += result.get("synced", 0)
            total_updated += result.get("updated", 0)

            # Collect new critical findings for alerting
            new_criticals = result.get("new_critical", [])
            if new_criticals:
                all_new_criticals.append({
                    "company": assessment.get("company", "Unknown"),
                    "assessment_id": assessment["id"],
                    "critical_risks": new_criticals,
                })

        except Exception as e:
            errors.append(f"Assessment {assessment['id']}: {str(e)}")

    # Trigger email alert if new critical risks found
    if all_new_criticals:
        try:
            from app.services.alert_service import send_critical_alert
            await send_critical_alert(all_new_criticals)
        except Exception as e:
            errors.append(f"Alert failed: {str(e)}")

    return {
        "assessments_synced": len(assessments),
        "new_risks": total_synced,
        "updated_risks": total_updated,
        "new_criticals": all_new_criticals,
        "errors": errors,
    }


@celery_app.task(name="app.tasks.sync_tasks.sync_all_assessments", bind=True, max_retries=3)
def sync_all_assessments(self):
    """
    Celery task — runs every 24h via beat schedule.

    Celery tasks are synchronous by default but our code is async.
    asyncio.run() bridges the gap — runs the async function in a
    new event loop within the Celery worker process.
    """
    try:
        result = asyncio.run(_sync_all_assessments_async())
        print(f"[Sync Task] Completed: {result}")
        return result
    except Exception as exc:
        # Retry with exponential backoff on failure
        print(f"[Sync Task] Failed: {exc}. Retrying...")
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))


@celery_app.task(name="app.tasks.sync_tasks.sync_single_assessment")
def sync_single_assessment(assessment_id: str):
    """
    Manually trigger sync for a single assessment.
    Can be called from the API for on-demand syncs.
    """
    async def _run():
        await connect_db()
        result = await sync_security_hub(assessment_id)
        return result

    return asyncio.run(_run())