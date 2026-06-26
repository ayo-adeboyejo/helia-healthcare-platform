import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import settings
from app.core.logger import logger


async def send_email(to: str, subject: str, html_body: str):
    try:
        message = MIMEMultipart("alternative")
        message["From"]    = settings.mail_from
        message["To"]      = to
        message["Subject"] = subject
        message.attach(MIMEText(html_body, "html"))

        await aiosmtplib.send(
            message,
            hostname=settings.mail_host,
            port=settings.mail_port,
            start_tls=False,
        )
        logger.info(f"Email sent to {to} — subject: {subject}")
    except Exception as e:
        logger.error(f"Failed to send email to {to}: {e}")


async def send_verification_email(email: str, code: str):
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #0ea5e9;">Welcome to Helia</h2>
        <p>Thank you for registering. Please verify your email address using the code below:</p>
        <div style="background: #f0f9ff; border: 1px solid #bae6fd; border-radius: 8px; padding: 24px; text-align: center; margin: 24px 0;">
            <h1 style="color: #0284c7; letter-spacing: 8px; font-size: 36px;">{code}</h1>
        </div>
        <p style="color: #64748b;">This code expires in {settings.otp_expire_minutes} minutes.</p>
        <p style="color: #64748b;">If you did not register, please ignore this email.</p>
    </div>
    """
    await send_email(email, "Verify your Helia account", html)


async def send_password_reset_email(email: str, token: str):
    reset_url = f"http://localhost/reset-password?token={token}"
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #0ea5e9;">Password Reset Request</h2>
        <p>We received a request to reset your Helia password.</p>
        <div style="text-align: center; margin: 32px 0;">
            <a href="{reset_url}"
               style="background: #0ea5e9; color: white; padding: 14px 32px; border-radius: 8px; text-decoration: none; font-weight: bold;">
                Reset Password
            </a>
        </div>
        <p style="color: #64748b;">Or copy this link: {reset_url}</p>
        <p style="color: #64748b;">This link expires in 1 hour. If you did not request this, please ignore this email.</p>
    </div>
    """
    await send_email(email, "Reset your Helia password", html)


async def send_2fa_otp_email(email: str, code: str):
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #0ea5e9;">Helia — Login Verification</h2>
        <p>Your one-time login code is:</p>
        <div style="background: #f0f9ff; border: 1px solid #bae6fd; border-radius: 8px; padding: 24px; text-align: center; margin: 24px 0;">
            <h1 style="color: #0284c7; letter-spacing: 8px; font-size: 36px;">{code}</h1>
        </div>
        <p style="color: #64748b;">This code expires in {settings.otp_expire_minutes} minutes.</p>
        <p style="color: #64748b;">Never share this code with anyone.</p>
    </div>
    """
    await send_email(email, "Helia Login Code", html)
