from __future__ import annotations

import threading
import time
import traceback
from datetime import date, datetime, timedelta

from src.app.config import get_settings
from src.app.web import app
from src.notify.emailer import send_html_email
from src.notify.templates import build_admin_status_email_html, build_admin_status_email_subject
from src.pipeline.run_daily import RunReport, default_policies, run


def _split_recipients(raw: str) -> list[str]:
    return [value.strip() for value in raw.split(",") if value and value.strip()]


def _send_admin_status_email(
    *,
    day: date,
    report: RunReport | None,
    run_error: Exception | None,
    traceback_text: str = "",
) -> None:
    settings = get_settings()
    if not settings.admin_mail_enabled:
        print("[INFO] ADMIN_MAIL_ENABLED is false. Admin status email skipped.")
        return

    recipients = _split_recipients(settings.admin_recipients)
    if not recipients:
        print("[WARN] ADMIN_RECIPIENTS is empty. Admin status email skipped.")
        return

    rows: list[dict[str, str]] = []
    total_items: int | None = None
    if report is not None:
        total_items = report.total_items
        for result in report.department_results:
            rows.append(
                {
                    "department": result.department.upper(),
                    "status": result.status,
                    "hit_count": str(result.hit_count),
                    "recipients": ", ".join(result.recipients) if result.recipients else "-",
                    "subject": result.subject or "-",
                    "titles": " | ".join(result.sample_titles) if result.sample_titles else "-",
                    "error": result.error or "-",
                }
            )

    success = run_error is None
    subject = build_admin_status_email_subject(day=day, success=success)
    html_body = build_admin_status_email_html(
        day=day,
        success=success,
        total_items=total_items,
        rows=rows,
        error_message=str(run_error) if run_error else "",
        traceback_text=traceback_text if run_error else "",
    )

    send_html_email(
        smtp_host=settings.smtp_host,
        smtp_port=settings.smtp_port,
        smtp_user=settings.smtp_user,
        smtp_password=settings.smtp_password,
        smtp_secure=settings.smtp_secure,
        smtp_auth=settings.smtp_auth,
        smtp_tls_reject_unauthorized=settings.smtp_tls_reject_unauthorized,
        smtp_enabled=settings.smtp_enabled,
        mail_from=settings.mail_from,
        recipients=recipients,
        subject=subject,
        html_body=html_body,
    )
    print(f"[INFO] ADMIN: status email sent to {', '.join(recipients)}")


# ---------------------------------------------------------------------------
# Scheduler: run pipeline for today, then sleep until next full hour
# ---------------------------------------------------------------------------

def _run_check() -> None:
    """Run the pipeline once for today's date."""
    day = date.today()
    print(f"\n[SCHEDULER] Running check for {day.isoformat()} ...")

    report: RunReport | None = None
    run_error: Exception | None = None
    tb_text = ""

    try:
        report = run(day=day, policies=default_policies())
    except Exception as exc:
        run_error = exc
        tb_text = traceback.format_exc()
        print(tb_text)

    try:
        _send_admin_status_email(
            day=day, report=report, run_error=run_error, traceback_text=tb_text,
        )
    except Exception as admin_exc:
        print(f"[ERROR] ADMIN: status email failed -> {admin_exc}")


def _scheduler_loop() -> None:
    """Background thread: immediate run, then every hour on the hour."""
    _run_check()

    while True:
        now = datetime.now()
        next_hour = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
        sleep_secs = (next_hour - now).total_seconds()
        print(f"[SCHEDULER] Next check at {next_hour.strftime('%Y-%m-%d %H:%M')}, sleeping {sleep_secs:.0f}s")
        time.sleep(sleep_secs)
        _run_check()


# ---------------------------------------------------------------------------
# Entry-point
# ---------------------------------------------------------------------------

def main() -> None:
    # Start the hourly scheduler in a daemon thread
    scheduler = threading.Thread(target=_scheduler_loop, daemon=True)
    scheduler.start()

    # Start Flask web server (blocking, keeps the process alive)
    print("[INFO] Web dashboard starting on http://0.0.0.0:5048")
    app.run(host="0.0.0.0", port=5048, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()
