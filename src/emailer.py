import smtplib
import socket
import time
from email.message import EmailMessage


def send_email(
    smtp_host, smtp_port, smtp_user, smtp_pass,
    from_email, to_email, subject,
    text_body: str,
    html_body: str | None = None,
    retry_max: int = 3,
    retry_backoff_seconds: int = 2,
):
    """
    Sends an email with plain-text + optional HTML.
    Retries on temporary SMTP/network errors.
    """

    msg = EmailMessage()
    msg["From"] = from_email
    msg["To"] = to_email
    msg["Subject"] = subject

    # Always include plain-text fallback
    msg.set_content(text_body)

    # Optional HTML
    if html_body:
        msg.add_alternative(html_body, subtype="html")

    last_err = None

    for attempt in range(1, retry_max + 1):
        try:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)
            return  # success

        except (smtplib.SMTPServerDisconnected,
                smtplib.SMTPConnectError,
                smtplib.SMTPHeloError,
                smtplib.SMTPDataError,
                smtplib.SMTPResponseException,
                socket.timeout,
                OSError) as e:
            last_err = e

            # Some SMTP errors are permanent (e.g., bad credentials). Don’t retry those.
            if isinstance(e, smtplib.SMTPAuthenticationError):
                raise

            # Exponential backoff: 2, 4, 8...
            if attempt < retry_max:
                sleep_s = retry_backoff_seconds * (2 ** (attempt - 1))
                time.sleep(sleep_s)
            else:
                break

    raise last_err if last_err else RuntimeError("Failed to send email for unknown reason")