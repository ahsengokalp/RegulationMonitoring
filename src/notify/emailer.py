from __future__ import annotations

import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Iterable

from src.notify.mail_log import append_mail_event


def send_html_email(
    *,
    smtp_host: str,
    smtp_port: int,
    smtp_user: str,
    smtp_password: str,
    smtp_secure: bool = True,
    smtp_auth: bool = True,
    smtp_tls_reject_unauthorized: bool = True,
    smtp_enabled: bool = True,
    mail_from: str,
    recipients: Iterable[str],
    subject: str,
    html_body: str,
) -> None:
    if not smtp_enabled:
        try:
            append_mail_event(
                status="skipped_disabled",
                mail_from=mail_from,
                recipients=recipients,
                subject=subject,
                html_body=html_body,
                message="SMTP disabled",
            )
        except Exception:
            pass
        return

    recipients = [r.strip() for r in recipients if r and r.strip()]
    if not recipients:
        try:
            append_mail_event(
                status="failed_no_recipients",
                mail_from=mail_from,
                recipients=recipients,
                subject=subject,
                html_body=html_body,
                message="No recipients provided",
            )
        except Exception:
            pass
        raise ValueError("No recipients provided")

    msg = MIMEMultipart("alternative")
    msg["From"] = mail_from
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            if smtp_secure:
                if smtp_tls_reject_unauthorized:
                    context = ssl.create_default_context()
                else:
                    context = ssl.create_default_context()
                    context.check_hostname = False
                    context.verify_mode = ssl.CERT_NONE
                server.starttls(context=context)

            if smtp_auth:
                server.login(smtp_user, smtp_password)

            server.sendmail(mail_from, recipients, msg.as_string())
    except Exception as exc:
        try:
            append_mail_event(
                status="failed",
                mail_from=mail_from,
                recipients=recipients,
                subject=subject,
                html_body=html_body,
                message=str(exc),
            )
        except Exception:
            pass
        raise

    try:
        append_mail_event(
            status="sent",
            mail_from=mail_from,
            recipients=recipients,
            subject=subject,
            html_body=html_body,
            message="Sent successfully",
        )
    except Exception:
        pass
