import os
import smtplib
from email.message import EmailMessage

from dotenv import load_dotenv


load_dotenv()


SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")


def send_password_reset_email(
    recipient_email: str,
    reset_token: str,
) -> None:
    """Send a password-reset link through Gmail SMTP."""

    if not SMTP_USERNAME or not SMTP_PASSWORD:
        raise RuntimeError(
            "Email delivery is not configured. "
            "Check SMTP_USERNAME and SMTP_PASSWORD."
        )

    reset_url = (
        "http://localhost:8501/"
        f"?reset_token={reset_token}"
    )

    message = EmailMessage()
    message["Subject"] = "Reset your Enterprise RAG password"
    message["From"] = SMTP_USERNAME
    message["To"] = recipient_email

    message.set_content(
        f"""Hello,

We received a request to reset your Enterprise RAG password.

Open this link to reset your password:

{reset_url}

This link expires in 30 minutes and can only be used once.

If you did not request a password reset, you can ignore this email.

For security reasons, do not share this link with anyone.
"""
    )

    with smtplib.SMTP(
        SMTP_HOST,
        SMTP_PORT,
        timeout=15,
    ) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()

        server.login(
            SMTP_USERNAME,
            SMTP_PASSWORD,
        )

        server.send_message(message)