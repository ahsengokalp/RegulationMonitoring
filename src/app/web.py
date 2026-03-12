from __future__ import annotations

import os
import threading
import traceback
from datetime import date, datetime

from flask import Flask, flash, jsonify, redirect, render_template, request, url_for, send_file

from src.db.storage import get_department_counts, get_fetched_dates, get_items, get_last_check_time
from src.app.config import get_settings
from src.notify.emailer import send_html_email

template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
app.secret_key = "regulation-monitor-secret-key"


@app.route("/")
def index():
    limit = request.args.get("limit", 100, type=int)
    if limit not in (50, 100, 200, 500, 1000, 2000):
        limit = 100
    search = request.args.get("q", "").strip()
    dept = request.args.get("dept", "").strip() or None
    valid_depts = {"muhasebe", "isg", "ik", "lojistik", "it_siber", "kvkk"}
    if dept and dept not in valid_depts:
        dept = None
    items = get_items(limit=limit, search=search or None, dept=dept)
    last_check = get_last_check_time()
    dept_counts = get_department_counts(items)
    today = date.today().isoformat()
    return render_template(
        "index.html",
        items=items,
        limit=limit,
        search=search,
        dept=dept or "",
        last_check=last_check,
        dept_counts=dept_counts,
        today=today,
    )


def _fetch_worker(day: date) -> None:
    """Run pipeline for the given day in a background thread."""
    try:
        from src.pipeline.run_daily import default_policies, run

        run(day=day, policies=default_policies())
        print(f"[INFO] Manual fetch completed for {day.isoformat()}")
        # send admin notification if enabled
        try:
            settings = get_settings()
            if settings.admin_mail_enabled and settings.admin_recipients:
                recipients = [r.strip() for r in str(settings.admin_recipients).split(",") if r.strip()]
                subject = f"Regülasyon: Veri çekme tamamlandı ({day.isoformat()})"
                body = f"<p>Manuel olarak başlatılan veri çekme işlemi <strong>{day.isoformat()}</strong> başarıyla tamamlandı.</p>\n<p><a href=\"/\">Dashboard'ı görüntüleyin</a></p>"
                try:
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
                        html_body=body,
                    )
                except Exception:
                    print("[WARN] Admin notification email failed:")
                    traceback.print_exc()
        except Exception:
            print("[WARN] Failed to prepare/send admin notification:")
            traceback.print_exc()
    except Exception:
        print(f"[ERROR] Manual fetch failed for {day.isoformat()}")
        traceback.print_exc()
        # send failure notification
        try:
            settings = get_settings()
            if settings.admin_mail_enabled and settings.admin_recipients:
                recipients = [r.strip() for r in str(settings.admin_recipients).split(",") if r.strip()]
                subject = f"Regülasyon: Veri çekme başarısız ({day.isoformat()})"
                body = f"<p>Manuel olarak başlatılan veri çekme işlemi <strong>{day.isoformat()}</strong> sırasında bir hata oluştu. Lütfen sunucu loglarını kontrol edin.</p>"
                try:
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
                        html_body=body,
                    )
                except Exception:
                    print("[WARN] Admin failure notification email also failed:")
                    traceback.print_exc()
        except Exception:
            print("[WARN] Preparing failure notification also failed:")
            traceback.print_exc()


@app.route("/fetch", methods=["POST"])
def fetch():
    # Check if this is an AJAX/JSON request (from batch fetch JS)
    is_ajax = (
        request.headers.get("X-Requested-With") == "XMLHttpRequest"
        or "application/json" in (request.headers.get("Accept") or "")
    )
    date_str = request.form.get("date")
    if not date_str:
        if is_ajax:
            return jsonify({"ok": False, "error": "Tarih belirtilmedi."}), 400
        return redirect(url_for("index"))

    try:
        day = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        if is_ajax:
            return jsonify({"ok": False, "error": "Geçersiz tarih formatı."}), 400
        flash("Geçersiz tarih formatı. YYYY-MM-DD kullanın.", "danger")
        return redirect(url_for("index"))

    if is_ajax:
        # Synchronous execution for batch/AJAX requests so JS knows when it's done
        try:
            from src.pipeline.run_daily import default_policies, run

            report = run(day=day, policies=default_policies())
            print(f"[INFO] Fetch completed for {day.isoformat()} ({report.total_items} items)")
            return jsonify({
                "ok": True,
                "date": day.isoformat(),
                "items_found": report.total_items,
            })
        except Exception:
            traceback.print_exc()
            return jsonify({"ok": False, "error": f"{day.isoformat()} çekilirken hata oluştu."}), 500
    else:
        # Background execution for manual single-day fetch (form submit)
        thread = threading.Thread(target=_fetch_worker, args=(day,), daemon=True)
        thread.start()
        flash(
            f"{date_str} tarihi için veri çekme işlemi başlatıldı. "
            "Birkaç dakika sonra sayfayı yenileyerek sonuçları görebilirsiniz.",
            "info",
        )
        return redirect(url_for("index"))


@app.route("/fetched-dates")
def fetched_dates():
    """Return JSON list of dates already fetched."""
    dates = sorted(get_fetched_dates())
    return jsonify({"dates": dates})


@app.route("/download-db")
def download_db():
    """Send a copy of the SQLite database for download."""
    try:
        from src.db.storage import DB_PATH

        if not DB_PATH.exists():
            flash("Veritabanı bulunamadı.", "danger")
            return redirect(url_for("index"))

        filename = f"items-{datetime.now().strftime('%Y%m%d')}.db"
        return send_file(
            str(DB_PATH),
            as_attachment=True,
            download_name=filename,
            mimetype="application/x-sqlite3",
        )
    except Exception:
        traceback.print_exc()
        flash("Veritabanı indirilemedi.", "danger")
        return redirect(url_for("index"))
