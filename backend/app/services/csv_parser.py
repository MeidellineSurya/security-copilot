import csv
import io
from typing import List
from app.models.schemas import Severity

# These are the exact column names the CSV must have
REQUIRED_COLUMNS = {"title", "description", "severity", "score", "category", "remediation"}

VALID_SEVERITIES = {s.value for s in Severity}  # {"Critical", "High", "Medium", "Low"}

# This is the template content users download
CSV_TEMPLATE = """title,description,severity,score,category,remediation
S3 bucket publicly accessible,Production S3 bucket has public read enabled exposing customer data,Critical,95,AWS,Disable public access block and apply bucket policy restricting to VPC only
API keys hardcoded in source code,Stripe API keys found in GitHub repository history,Critical,91,Application,Rotate all exposed keys immediately and move to secrets manager
Missing rate limiting on payment API,The /api/payments endpoint has no rate limiting enabling brute-force attacks,High,78,Application,Implement rate limiting at 100 req/min per IP
SSH exposed to 0.0.0.0/0,14 production EC2 instances have port 22 open to the internet,High,74,AWS,Restrict SSH to bastion host IP only
Reflected XSS in search endpoint,User input in search param is reflected unsanitised in HTML response,Medium,55,Application,Implement output encoding and add Content-Security-Policy header
"""


def parse_csv(file_content: bytes, assessment_id: str) -> dict:
    """
    Parse a CSV file and return valid risks + any errors found.

    Returns:
        {
            "risks": [...],       # valid rows ready to insert
            "errors": [...],      # rows that failed validation
            "total_rows": int,
            "valid_rows": int,
        }
    """
    risks = []
    errors = []

    # Decode bytes to string
    try:
        text = file_content.decode("utf-8")
    except UnicodeDecodeError:
        return {
            "risks": [],
            "errors": ["File encoding error — please save your CSV as UTF-8"],
            "total_rows": 0,
            "valid_rows": 0,
        }

    reader = csv.DictReader(io.StringIO(text))

    # Check all required columns exist
    if not reader.fieldnames:
        return {
            "risks": [],
            "errors": ["CSV file is empty or has no headers"],
            "total_rows": 0,
            "valid_rows": 0,
        }

    actual_columns = {col.strip().lower() for col in reader.fieldnames}
    missing = REQUIRED_COLUMNS - actual_columns
    if missing:
        return {
            "risks": [],
            "errors": [f"Missing required columns: {', '.join(missing)}"],
            "total_rows": 0,
            "valid_rows": 0,
        }

    # Parse each row
    for row_num, row in enumerate(reader, start=2):  # start=2 because row 1 is headers
        row_errors = []

        # Clean whitespace from all values
        row = {k.strip().lower(): v.strip() for k, v in row.items() if k}

        title = row.get("title", "")
        description = row.get("description", "")
        severity = row.get("severity", "")
        score_raw = row.get("score", "")
        category = row.get("category", "")
        remediation = row.get("remediation", "")

        # Validate each field
        if not title:
            row_errors.append("title is empty")

        if not description:
            row_errors.append("description is empty")

        if severity not in VALID_SEVERITIES:
            row_errors.append(
                f"severity '{severity}' is invalid — must be one of: {', '.join(VALID_SEVERITIES)}"
            )

        try:
            score = int(score_raw)
            if not (0 <= score <= 100):
                row_errors.append(f"score '{score}' must be between 0 and 100")
        except ValueError:
            score = 0
            row_errors.append(f"score '{score_raw}' must be a number")

        if not category:
            row_errors.append("category is empty")

        if not remediation:
            row_errors.append("remediation is empty")

        # If any errors, skip this row and record the problem
        if row_errors:
            errors.append(f"Row {row_num} ({title or 'untitled'}): {'; '.join(row_errors)}")
            continue

        # Valid row — build the risk document
        risks.append({
            "assessment_id": assessment_id,
            "title": title,
            "description": description,
            "severity": severity,
            "score": score,
            "category": category,
            "remediation": remediation,
        })

    return {
        "risks": risks,
        "errors": errors,
        "total_rows": row_num - 1 if 'row_num' in locals() else 0,
        "valid_rows": len(risks),
    }