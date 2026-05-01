from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import Response
from app.db.mongo import get_db
from app.services.csv_parser import parse_csv, CSV_TEMPLATE
from datetime import datetime

router = APIRouter()

@router.get("/template")
async def download_template():
    """
    Returns a prefilled CSV template the user can download,
    fill in with their own risks, and upload back.
    """
    return Response(
        content=CSV_TEMPLATE,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=risks_template.csv"},
    )


@router.post("/upload")
async def upload_csv(
    file: UploadFile = File(...),
    company: str = Form(...),
    industry: str = Form(...),
    scope: str = Form(...),
):
    """
    Upload a CSV file to create a new assessment with risks.

    Flow:
    1. Validate file type
    2. Create assessment document
    3. Parse CSV rows
    4. Insert valid risks
    5. Return import summary
    """
    # Step 1 — validate file type
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only .csv files are accepted")

    # Step 2 — create the assessment
    db = get_db()
    assessment = {
        "company": company,
        "industry": industry,
        "scope": scope,
        "created_at": datetime.utcnow(),
        "source": "csv_upload",  # so we know how this assessment was created
    }
    result = await db.assessments.insert_one(assessment)
    assessment_id = str(result.inserted_id)

    # Step 3 — read and parse the CSV
    file_content = await file.read()
    parsed = parse_csv(file_content, assessment_id)

    # Step 4 — if we have valid risks, insert them
    if parsed["risks"]:
        await db.risks.insert_many(parsed["risks"])

    # Step 5 — if nothing was valid at all, roll back the assessment
    if parsed["valid_rows"] == 0:
        await db.assessments.delete_one({"_id": result.inserted_id})
        raise HTTPException(
            status_code=422,
            detail={
                "message": "No valid risks found in CSV — assessment was not created",
                "errors": parsed["errors"],
            },
        )

    return {
        "message": "Assessment created successfully",
        "assessment_id": assessment_id,
        "company": company,
        "total_rows": parsed["total_rows"],
        "valid_rows": parsed["valid_rows"],
        "skipped_rows": parsed["total_rows"] - parsed["valid_rows"],
        "errors": parsed["errors"],  # rows that were skipped
    }