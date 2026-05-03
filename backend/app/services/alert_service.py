import resend
from app.core.config import settings

resend.api_key = settings.RESEND_API_KEY


def build_email_html(critical_findings: list) -> str:
    """
    Build a clean HTML email body for critical risk alerts.
    Each finding includes company name and list of critical risks found.
    """
    rows = ""
    for finding in critical_findings:
        company = finding.get("company", "Unknown")
        risks = finding.get("critical_risks", [])
        risk_items = "".join(f"<li>{r}</li>" for r in risks)
        rows += f"""
        <div style="margin-bottom:24px; padding:16px; border-left:4px solid #ef4444; background:#fef2f2; border-radius:4px;">
            <p style="margin:0 0 8px; font-weight:bold; color:#111;">{company}</p>
            <ul style="margin:0; padding-left:20px; color:#374151;">
                {risk_items}
            </ul>
        </div>
        """

    return f"""
    <div style="font-family:sans-serif; max-width:600px; margin:0 auto; padding:24px;">
        <div style="background:#111827; padding:16px 24px; border-radius:8px; margin-bottom:24px;">
            <h1 style="color:white; margin:0; font-size:18px;">
                🛡️ Security Copilot — Critical Risk Alert
            </h1>
        </div>

        <p style="color:#374151; margin-bottom:24px;">
            The automated security scan has detected new <strong>Critical</strong> risks
            that require immediate attention:
        </p>

        {rows}

        <div style="margin-top:32px; padding:16px; background:#f3f4f6; border-radius:8px;">
            <p style="margin:0; color:#6b7280; font-size:13px;">
                This alert was generated automatically by Security Copilot.<br>
                Log in to review full details and remediation steps.
            </p>
        </div>
    </div>
    """


async def send_critical_alert(critical_findings: list) -> dict:
    """
    Send an email alert when new critical risks are detected.

    Called automatically by the Celery sync task when
    new Critical severity findings are found in AWS Security Hub.

    Args:
        critical_findings: list of dicts with company + critical_risks
    """
    if not critical_findings:
        return {"sent": False, "reason": "No critical findings to alert"}

    # Count total critical risks across all assessments
    total_criticals = sum(
        len(f.get("critical_risks", [])) for f in critical_findings
    )

    subject = f"🚨 {total_criticals} New Critical Risk{'s' if total_criticals > 1 else ''} Detected"

    try:
        response = resend.Emails.send({
            "from": settings.ALERT_EMAIL_FROM,
            "to": settings.ALERT_EMAIL_TO,
            "subject": subject,
            "html": build_email_html(critical_findings),
        })

        return {
            "sent": True,
            "email_id": response.get("id"),
            "to": settings.ALERT_EMAIL_TO,
            "total_criticals": total_criticals,
        }

    except Exception as e:
        return {
            "sent": False,
            "error": str(e),
        }


async def send_test_alert() -> dict:
    """
    Send a test alert email to verify Resend is configured correctly.
    Call this from /docs to confirm email works before relying on it.
    """
    test_findings = [
        {
            "company": "AcmePay (Test)",
            "assessment_id": "test-123",
            "critical_risks": [
                "S3 bucket publicly accessible (Score: 96)",
                "API keys hardcoded in source code (Score: 91)",
            ]
        }
    ]
    return await send_critical_alert(test_findings)