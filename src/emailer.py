import os
import smtplib
import socket
import time
from email.message import EmailMessage
from email.utils import formataddr
from config import FROM_EMAIL

def send_email(
    smtp_host: str,
    smtp_port: int,
    smtp_user: str,
    smtp_pass: str,
    from_email: str,
    to_email: str,
    subject: str,
    text_body: str,
    html_body: str | None = None,
    inline_image_path: str | None = None,
    inline_image_cid: str = "kyrol_logo",
    retry_max: int = 3,
    retry_backoff_seconds: int = 2,
):
    """
    Send an email with optional HTML and optional CID inline image (Outlook-friendly).
    In HTML use: <img src="cid:kyrol_logo">
    """
    msg = EmailMessage()
    msg["From"] = formataddr(("KyrolSecurityLabs", from_email))
    msg["To"] = to_email
    msg["Subject"] = subject
    msg["Subject"] = smtp_user

    # Plain text
    msg.set_content(text_body)

    # HTML 
    if html_body:
        msg.add_alternative(html_body, subtype="html")

        # Inline CID image 
        if inline_image_path:
            if not os.path.exists(inline_image_path):
                raise FileNotFoundError(f"Inline image not found: {inline_image_path}")

            html_part = msg.get_payload()[-1]  # the HTML alternative part

            with open(inline_image_path, "rb") as f:
                img_bytes = f.read()

            # Must include <> for Content-ID
            content_id = f"<{inline_image_cid}>"

            html_part.add_related(
                img_bytes,
                maintype="image",
                subtype="png",
                cid=content_id,
                filename=os.path.basename(inline_image_path),
                disposition="inline",
            )

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
        except smtplib.SMTPAuthenticationError:
            raise
        except (smtplib.SMTPException, socket.timeout, OSError) as e:
            last_err = e
            if attempt < retry_max:
                time.sleep(retry_backoff_seconds * (2 ** (attempt - 1)))
            else:
                break

    raise last_err if last_err else RuntimeError("Failed to send email")