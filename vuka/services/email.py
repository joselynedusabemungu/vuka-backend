
import os
import smtplib
from email.message import EmailMessage

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", "no-reply@example.com")


def send_email(to_email: str, subject: str, body: str) -> None:
    if not SMTP_HOST:
        print(
            f"[email:not sent -- SMTP_HOST not configured]\n"
            f"To: {to_email}\nSubject: {subject}\n\n{body}\n"
        )
        return

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = SMTP_FROM_EMAIL
    msg["To"] = to_email
    msg.set_content(body)

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        if SMTP_USERNAME and SMTP_PASSWORD:
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(msg)


def send_password_reset_email(to_email: str, reset_token: str) -> None:
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    reset_link = f"{frontend_url}/reset-password?token={reset_token}"

    subject = "Reset your password"
    body = (
        "We received a request to reset your password.\n\n"
        f"Click the link below to choose a new password:\n{reset_link}\n\n"
        "This link expires in 30 minutes. If you didn't request this, "
        "you can safely ignore this email."
    )
    send_email(to_email, subject, body)