from __future__ import annotations

import os
import threading
import traceback
from datetime import date, datetime

from flask import Flask, flash, redirect, render_template, request, url_for

from src.db.storage import get_department_counts, get_items, get_last_check_time

template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
app = Flask(__name__, template_folder=template_dir)
app.secret_key = "regulation-monitor-secret-key"


@app.route("/")
def index():
    limit = request.args.get("limit", 100, type=int)
    if limit not in (50, 100, 200, 500):
        limit = 100
    items = get_items(limit=limit)
    last_check = get_last_check_time()
    dept_counts = get_department_counts(items)
    today = date.today().isoformat()
    return render_template(
        "index.html",
        items=items,
        limit=limit,
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
    except Exception:
        print(f"[ERROR] Manual fetch failed for {day.isoformat()}")
        traceback.print_exc()


@app.route("/fetch", methods=["POST"])
def fetch():
    date_str = request.form.get("date")
    if date_str:
        try:
            day = datetime.strptime(date_str, "%Y-%m-%d").date()
            thread = threading.Thread(target=_fetch_worker, args=(day,), daemon=True)
            thread.start()
            flash(
                f"{date_str} tarihi için veri çekme işlemi başlatıldı. "
                "Birkaç dakika sonra sayfayı yenileyerek sonuçları görebilirsiniz.",
                "info",
            )
        except ValueError:
            flash("Geçersiz tarih formatı. YYYY-MM-DD kullanın.", "danger")
    return redirect(url_for("index"))
