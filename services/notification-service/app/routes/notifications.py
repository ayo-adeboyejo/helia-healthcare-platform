from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
import boto3
from botocore.exceptions import ClientError

from app.core.logger import logger
from app.config import settings

router = APIRouter()


class NotificationRequest(BaseModel):
    to_email:  EmailStr
    subject:   str
    body_html: str
    body_text: Optional[str] = None


class AppointmentNotification(BaseModel):
    to_email:          EmailStr
    patient_name:      str
    doctor_name:       str
    appointment_date:  str
    appointment_time:  str
    notification_type: str  # confirmed | reminder | cancelled


def send_email(to: str, subject: str, html: str, text: str = None) -> bool:
    """
    Send email.
    Development: uses Mailhog via SMTP (catches all emails, nothing sent externally)
    Production:  uses AWS SES
    """
    if settings.environment == "development":
        return _send_via_mailhog(to, subject, html)
    return _send_via_ses(to, subject, html, text)


def _send_via_mailhog(to: str, subject: str, html: str) -> bool:
    """Send via Mailhog SMTP — dev only. View at http://localhost:8025"""
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        msg = MIMEMultipart("alternative")
        msg["From"]    = settings.ses_from_email
        msg["To"]      = to
        msg["Subject"] = subject
        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP(settings.mail_host, settings.mail_port) as server:
            server.sendmail(settings.ses_from_email, [to], msg.as_string())

        logger.info(f"email_sent_mailhog to={to} subject={subject}")
        return True
    except Exception as e:
        logger.error(f"mailhog_send_failed to={to} error={e}")
        # In dev, log the email content so it's never silently lost
        logger.info(f"[DEV EMAIL FALLBACK] to={to} subject={subject}")
        return True  # Don't fail in dev even if Mailhog is down


def _send_via_ses(to: str, subject: str, html: str, text: str = None) -> bool:
    """Send via AWS SES — production only."""
    try:
        client = boto3.client("ses", region_name=settings.aws_region)
        body = {"Html": {"Charset": "UTF-8", "Data": html}}
        if text:
            body["Text"] = {"Charset": "UTF-8", "Data": text}

        client.send_email(
            Source=settings.ses_from_email,
            Destination={"ToAddresses": [to]},
            Message={
                "Subject": {"Charset": "UTF-8", "Data": subject},
                "Body":    body,
            },
        )
        logger.info(f"email_sent_ses to={to} subject={subject}")
        return True
    except ClientError as e:
        logger.error(f"ses_send_failed to={to} error={e.response['Error']['Message']}")
        return False


# ── Generic notification ───────────────────────────────────────────────────────
@router.post("/notifications/send")
async def send_notification(payload: NotificationRequest):
    success = send_email(
        to=payload.to_email,
        subject=payload.subject,
        html=payload.body_html,
        text=payload.body_text,
    )
    if not success:
        raise HTTPException(status_code=500, detail="Failed to send notification")
    return {"message": "Notification sent"}


# ── Appointment notifications ─────────────────────────────────────────────────
@router.post("/notifications/appointment")
async def send_appointment_notification(payload: AppointmentNotification):
    templates = {
        "confirmed": {
            "subject": "Appointment Confirmed — Helia",
            "html": f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background: #0ea5e9; padding: 32px 40px; border-radius: 12px 12px 0 0;">
                    <h1 style="color: #fff; font-family: Georgia, serif; margin: 0; font-size: 28px;">Helia</h1>
                    <p style="color: rgba(255,255,255,0.8); margin: 4px 0 0; font-size: 13px;">Healthcare Appointment Platform</p>
                </div>
                <div style="background: #fff; padding: 40px; border: 1px solid #e2e8f0; border-top: none; border-radius: 0 0 12px 12px;">
                    <h2 style="color: #1e293b; margin-top: 0;">Your appointment is confirmed ✓</h2>
                    <p style="color: #64748b;">Hi {payload.patient_name},</p>
                    <p style="color: #64748b;">Your appointment with <strong>Dr. {payload.doctor_name}</strong> has been confirmed.</p>
                    <div style="background: #f0f9ff; border: 1px solid #bae6fd; border-radius: 8px; padding: 20px; margin: 24px 0;">
                        <p style="margin: 6px 0; color: #0284c7;"><strong>📅 Date:</strong> {payload.appointment_date}</p>
                        <p style="margin: 6px 0; color: #0284c7;"><strong>🕐 Time:</strong> {payload.appointment_time}</p>
                        <p style="margin: 6px 0; color: #0284c7;"><strong>👨‍⚕️ Doctor:</strong> Dr. {payload.doctor_name}</p>
                    </div>
                    <p style="color: #64748b; font-size: 14px;">Please arrive 10 minutes early. To cancel or reschedule, log in to your Helia account at least 24 hours in advance.</p>
                </div>
            </div>""",
        },
        "reminder": {
            "subject": "Reminder: Appointment Tomorrow — Helia",
            "html": f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background: #f59e0b; padding: 32px 40px; border-radius: 12px 12px 0 0;">
                    <h1 style="color: #fff; font-family: Georgia, serif; margin: 0; font-size: 28px;">Helia</h1>
                </div>
                <div style="background: #fff; padding: 40px; border: 1px solid #e2e8f0; border-top: none; border-radius: 0 0 12px 12px;">
                    <h2 style="color: #1e293b; margin-top: 0;">Appointment reminder 🔔</h2>
                    <p style="color: #64748b;">Hi {payload.patient_name}, just a reminder about your appointment tomorrow.</p>
                    <div style="background: #fffbeb; border: 1px solid #fde68a; border-radius: 8px; padding: 20px; margin: 24px 0;">
                        <p style="margin: 6px 0; color: #92400e;"><strong>📅 Date:</strong> {payload.appointment_date}</p>
                        <p style="margin: 6px 0; color: #92400e;"><strong>🕐 Time:</strong> {payload.appointment_time}</p>
                        <p style="margin: 6px 0; color: #92400e;"><strong>👨‍⚕️ Doctor:</strong> Dr. {payload.doctor_name}</p>
                    </div>
                    <p style="color: #64748b; font-size: 14px;">See you tomorrow. Log in to Helia if you need to make any changes.</p>
                </div>
            </div>""",
        },
        "cancelled": {
            "subject": "Appointment Cancelled — Helia",
            "html": f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background: #f43f5e; padding: 32px 40px; border-radius: 12px 12px 0 0;">
                    <h1 style="color: #fff; font-family: Georgia, serif; margin: 0; font-size: 28px;">Helia</h1>
                </div>
                <div style="background: #fff; padding: 40px; border: 1px solid #e2e8f0; border-top: none; border-radius: 0 0 12px 12px;">
                    <h2 style="color: #1e293b; margin-top: 0;">Appointment cancelled</h2>
                    <p style="color: #64748b;">Hi {payload.patient_name},</p>
                    <p style="color: #64748b;">Your appointment with Dr. {payload.doctor_name} on <strong>{payload.appointment_date}</strong> at <strong>{payload.appointment_time}</strong> has been cancelled.</p>
                    <p style="color: #64748b;">Log in to Helia to book a new appointment at your convenience.</p>
                </div>
            </div>""",
        },
    }

    template = templates.get(payload.notification_type)
    if not template:
        raise HTTPException(status_code=400, detail=f"Unknown notification type: {payload.notification_type}")

    success = send_email(
        to=payload.to_email,
        subject=template["subject"],
        html=template["html"],
    )
    if not success:
        raise HTTPException(status_code=500, detail="Failed to send notification")

    return {"message": f"Appointment {payload.notification_type} notification sent"}
