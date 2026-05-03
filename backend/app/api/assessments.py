# 7 hardcoded ACMEPAY risk, fake seed data 
from fastapi import APIRouter
from app.db.mongo import get_db
from datetime import datetime
from bson import ObjectId

router = APIRouter()

@router.post("/seed")
async def seed_data():
    """Seed mock data for development."""
    db = get_db()

    # Create assessment
    assessment = {
        "company": "AcmePay",
        "industry": "Fintech",
        "scope": "AWS infrastructure, web application, internal APIs",
        "created_at": datetime.utcnow(),
    }
    result = await db.assessments.insert_one(assessment)
    assessment_id = str(result.inserted_id)

    # Seed risks
    risks = [
        {
            "assessment_id": assessment_id,
            "title": "S3 bucket publicly accessible",
            "description": "Production S3 bucket 'acmepay-docs' has public read enabled, exposing customer PII and financial documents.",
            "severity": "Critical",
            "score": 96,
            "category": "AWS",
            "remediation": "Disable public access block, apply bucket policy restricting to VPC only, enable S3 access logs.",
            "created_at": datetime.utcnow(),
        },
        {
            "assessment_id": assessment_id,
            "title": "API keys hardcoded in source code",
            "description": "Stripe and internal API keys found in GitHub repository history. Keys have not been rotated.",
            "severity": "Critical",
            "score": 91,
            "category": "Application",
            "remediation": "Rotate all exposed keys immediately. Move secrets to AWS Secrets Manager. Add pre-commit hook to detect secrets.",
            "created_at": datetime.utcnow(),
        },
        {
            "assessment_id": assessment_id,
            "title": "Missing rate limiting on payment API",
            "description": "The /api/payments endpoint has no rate limiting, enabling brute-force and enumeration attacks.",
            "severity": "High",
            "score": 78,
            "category": "Application",
            "remediation": "Implement rate limiting (100 req/min per IP). Add CAPTCHA on repeated failures. Alert on anomalous patterns.",
            "created_at": datetime.utcnow(),
        },
        {
            "assessment_id": assessment_id,
            "title": "EC2 instances expose SSH to 0.0.0.0/0",
            "description": "14 production EC2 instances have port 22 open to the internet in their security groups.",
            "severity": "High",
            "score": 74,
            "category": "AWS",
            "remediation": "Restrict SSH to bastion host IP only. Migrate to AWS Systems Manager Session Manager to eliminate SSH exposure.",
            "created_at": datetime.utcnow(),
        },
        {
            "assessment_id": assessment_id,
            "title": "No MFA on AWS root account",
            "description": "The AWS root account does not have multi-factor authentication enabled.",
            "severity": "High",
            "score": 70,
            "category": "AWS",
            "remediation": "Enable MFA immediately on root account. Store MFA device securely. Avoid using root except for billing.",
            "created_at": datetime.utcnow(),
        },
        {
            "assessment_id": assessment_id,
            "title": "Reflected XSS in search endpoint",
            "description": "User input in the /search?q= parameter is reflected unsanitised in the HTML response.",
            "severity": "Medium",
            "score": 55,
            "category": "Application",
            "remediation": "Implement output encoding. Add Content-Security-Policy header. Use DOMPurify for any dynamic HTML rendering.",
            "created_at": datetime.utcnow(),
        },
        {
            "assessment_id": assessment_id,
            "title": "CloudTrail logging disabled in eu-west-1",
            "description": "AWS CloudTrail is not enabled in the EU region, creating a blind spot for audit and incident response.",
            "severity": "Medium",
            "score": 48,
            "category": "AWS",
            "remediation": "Enable CloudTrail in all regions. Send logs to centralised S3 bucket with MFA delete enabled.",
            "created_at": datetime.utcnow(),
        },
    ]

    await db.risks.insert_many(risks)

    return {
        "message": "Seed data created",
        "assessment_id": assessment_id,
        "risks_created": len(risks),
    }

@router.get("/")
async def list_assessments():
    db = get_db()
    cursor = db.assessments.find().sort("created_at", -1).limit(20)
    assessments = []
    async for doc in cursor:
        doc["id"] = str(doc.pop("_id"))
        assessments.append(doc)
    return assessments