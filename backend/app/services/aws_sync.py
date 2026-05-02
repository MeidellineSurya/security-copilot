import boto3
from datetime import datetime
from app.core.config import settings
from app.db.mongo import get_db

# Map AWS severity labels to our severity schema
SEVERITY_MAP = {
    "CRITICAL": "Critical",
    "HIGH": "High",
    "MEDIUM": "Medium",
    "LOW": "Low",
    "INFORMATIONAL": "Low",
}

# Map AWS severity to a score out of 100
SCORE_MAP = {
    "CRITICAL": 95,
    "HIGH": 75,
    "MEDIUM": 50,
    "LOW": 25,
    "INFORMATIONAL": 10,
}


def get_hub_client():
    """Create a boto3 Security Hub client using credentials from config."""
    return boto3.client(
        "securityhub",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION,
    )


def parse_finding(finding: dict, assessment_id: str) -> dict:
    """
    Convert a raw AWS Security Hub finding into our Risk schema.

    AWS findings have a complex nested structure — this function
    extracts only what we need and maps it to our format.
    """
    severity_label = finding.get("Severity", {}).get("Label", "INFORMATIONAL")

    # Extract the most useful description available
    description = (
        finding.get("Description")
        or finding.get("Title")
        or "No description available"
    )

    # Extract remediation text if AWS provides it
    remediation = (
        finding.get("Remediation", {})
        .get("Recommendation", {})
        .get("Text", "Review AWS Security Hub for remediation guidance")
    )

    # Determine category from finding type
    finding_types = finding.get("Types", [])
    category = "AWS"
    if finding_types:
        # Types look like "Software and Configuration Checks/..."
        top_type = finding_types[0].split("/")[0]
        category = top_type if top_type else "AWS"

    return {
        "assessment_id": assessment_id,
        "title": finding.get("Title", "Untitled Finding"),
        "description": description,
        "severity": SEVERITY_MAP.get(severity_label, "Low"),
        "score": SCORE_MAP.get(severity_label, 10),
        "category": category,
        "remediation": remediation,
        "aws_finding_id": finding.get("Id"),  # store AWS ID for deduplication
        "source": "aws_security_hub",
        "created_at": datetime.utcnow(),
    }


async def sync_security_hub(assessment_id: str) -> dict:
    """
    Pull findings from AWS Security Hub and upsert into MongoDB.

    Uses pagination to handle large numbers of findings.
    Only pulls ACTIVE findings with severity >= LOW.

    Returns a summary of what was synced.
    """
    db = get_db()
    client = get_hub_client()

    findings = []
    filters = {
        # Only active findings — not archived or resolved
        "RecordState": [{"Value": "ACTIVE", "Comparison": "EQUALS"}],
        # Only findings with a workflow status of NEW or NOTIFIED
        "WorkflowStatus": [
            {"Value": "NEW", "Comparison": "EQUALS"},
            {"Value": "NOTIFIED", "Comparison": "EQUALS"},
        ],
    }

    # Security Hub paginates results — fetch all pages
    paginator = client.get_paginator("get_findings")
    pages = paginator.paginate(Filters=filters, PaginationConfig={"PageSize": 100})

    for page in pages:
        findings.extend(page.get("Findings", []))

    if not findings:
        return {
            "synced": 0,
            "updated": 0,
            "message": "No active findings in Security Hub",
        }

    # Parse and upsert each finding
    synced = 0
    updated = 0
    new_critical = []

    for finding in findings:
        risk = parse_finding(finding, assessment_id)
        aws_id = risk.get("aws_finding_id")

        if not aws_id:
            continue

        # Upsert — update if exists, insert if new
        existing = await db.risks.find_one({"aws_finding_id": aws_id})

        if existing:
            await db.risks.update_one(
                {"aws_finding_id": aws_id},
                {"$set": {**risk, "updated_at": datetime.utcnow()}},
            )
            updated += 1
        else:
            await db.risks.insert_one(risk)
            synced += 1
            # Track new critical findings for alerting
            if risk["severity"] == "Critical":
                new_critical.append(risk["title"])

    return {
        "synced": synced,
        "updated": updated,
        "total": len(findings),
        "new_critical": new_critical,
        "message": f"Synced {synced} new, updated {updated} existing findings",
    }