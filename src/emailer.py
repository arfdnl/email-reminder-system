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
    msg = EmailMessage()
    msg["From"] = from_email
    msg["To"] = to_email
    msg["Subject"] = subject

    msg.set_content(text_body)
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
            return
        except (smtplib.SMTPAuthenticationError,) as e:
            raise
        except (smtplib.SMTPException, socket.timeout, OSError) as e:
            last_err = e
            if attempt < retry_max:
                time.sleep(retry_backoff_seconds * (2 ** (attempt - 1)))
            else:
                break

    raise last_err if last_err else RuntimeError("Failed to send email")