from __future__ import annotations

from datetime import date
from typing import Mapping, Sequence

from src.core.models import GazetteItem


def build_generic_email_subject(dept: str, day: date, count: int) -> str:
    return f"[{dept.upper()}] Resmi Gazete ({day:%d.%m.%Y}) - {count} yeni kayit"


def build_generic_email_html(
    dept: str,
    day: date,
    items: Sequence[GazetteItem],
    text_map: Mapping[str, str] | None = None,
    evidence_map: Mapping[str, str] | None = None,
) -> str:
    title = dept.upper()
    text_map = text_map or {}
    evidence_map = evidence_map or {}

    dept_labels = {
        "isg": "Is Sagligi ve Guvenligi",
        "ik": "Insan Kaynaklari",
        "muhasebe": "Muhasebe / Vergi / Finans",
        "lojistik": "Lojistik / Dis Ticaret / Gumruk",
        "it_siber": "IT / Siber Guvenlik",
        "kvkk": "KVKK / Kisisel Verilerin Korunmasi",
    }
    dept_display = dept_labels.get(dept, dept.upper())

    rows_html = []
    for i in items:
        evidence = evidence_map.get(i.url, "")
        detail = text_map.get(i.url, "")
        # Truncate detail for email (first 1000 chars)
        detail_preview = detail[:1000].strip() if detail else ""
        if len(detail) > 1000:
            detail_preview += "\n... (devami icin uygulamaya bakiniz)"

        evidence_block = ""
        if evidence:
            evidence_block = f"""
            <div style="background:#e8f5e9;border-left:3px solid #4caf50;padding:8px 12px;margin:6px 0;font-size:13px;">
              <b>AI Degerlendirmesi:</b> {_escape(evidence)}
            </div>
            """

        detail_block = ""
        if detail_preview:
            detail_block = f"""
            <div style="background:#f5f5f5;border:1px solid #e0e0e0;padding:10px;margin:6px 0;font-size:12px;white-space:pre-wrap;max-height:300px;overflow:hidden;">
              {_escape(detail_preview)}
            </div>
            """

        rows_html.append(f"""
        <tr>
          <td style="padding:12px;border-bottom:2px solid #e0e0e0;">
            <div style="font-weight:600;font-size:15px;">{_escape(i.title)}</div>
            <div style="margin:4px 0;"><a href="{i.url}" style="color:#1a73e8;">{i.url}</a></div>
            <div style="color:#666;font-size:12px;">
              {_escape(i.section or '')} {(' / ' + _escape(i.subsection)) if i.subsection else ''}
            </div>
            {evidence_block}
            {detail_block}
          </td>
        </tr>
        """)

    return f"""
    <div style="font-family:Arial, sans-serif; max-width:700px;">
      <h2 style="margin:0 0 12px 0; color:#1a237e;">{dept_display}</h2>
      <h3 style="margin:0 0 12px 0; color:#333;">Resmi Gazete Bildirimi</h3>
      <div style="color:#444;margin-bottom:16px;padding:10px;background:#e3f2fd;border-radius:6px;">
        Tarih: <b>{day:%d.%m.%Y}</b> &nbsp;|&nbsp;
        Bulunan kayit: <b>{len(items)}</b>
      </div>

      <table style="width:100%; border-collapse:collapse; border:1px solid #e0e0e0;">
        {"".join(rows_html)}
      </table>

      <p style="color:#999;font-size:11px;margin-top:16px;">
        Bu e-posta Regulasyon Takip Sistemi tarafindan otomatik olarak gonderilmistir.
      </p>
    </div>
    """


def build_isg_email_subject(day: date, count: int) -> str:
    return build_generic_email_subject("isg", day, count)


def build_isg_email_html(day: date, items: Sequence[GazetteItem]) -> str:
    return build_generic_email_html("isg", day, items)


def build_admin_status_email_subject(*, day: date, success: bool) -> str:
    status = "CALISTI" if success else "CALISMADI"
    return f" {status} :[ADMIN] Regulation Monitor {status} ({day:%d.%m.%Y})"


def build_admin_status_email_html(
    *,
    day: date,
    success: bool,
    total_items: int | None,
    rows: Sequence[Mapping[str, str]],
    error_message: str = "",
    traceback_text: str = "",
) -> str:
    status_text = "Calisti" if success else "Calismadi"
    status_color = "#166534" if success else "#991b1b"
    summary_rows = "".join(
        f"""
        <tr>
          <td style="padding:8px;border-bottom:1px solid #eee;">{_escape(r.get('department', '-'))}</td>
          <td style="padding:8px;border-bottom:1px solid #eee;">{_escape(r.get('status', '-'))}</td>
          <td style="padding:8px;border-bottom:1px solid #eee;">{_escape(r.get('hit_count', '0'))}</td>
          <td style="padding:8px;border-bottom:1px solid #eee;">{_escape(r.get('recipients', '-'))}</td>
          <td style="padding:8px;border-bottom:1px solid #eee;">{_escape(r.get('subject', '-'))}</td>
          <td style="padding:8px;border-bottom:1px solid #eee;">{_escape(r.get('titles', '-'))}</td>
          <td style="padding:8px;border-bottom:1px solid #eee;">{_escape(r.get('error', '-'))}</td>
        </tr>
        """
        for r in rows
    )

    total_items_text = str(total_items) if total_items is not None else "-"
    error_block = ""
    if error_message:
        error_block = (
            "<h3 style='margin:14px 0 8px 0;'>Hata Ozeti</h3>"
            f"<div style='background:#fee2e2;border:1px solid #fecaca;padding:10px;color:#7f1d1d;'>{_escape(error_message)}</div>"
        )

    traceback_block = ""
    if traceback_text:
        traceback_block = (
            "<h3 style='margin:14px 0 8px 0;'>Traceback</h3>"
            f"<pre style='white-space:pre-wrap;background:#111827;color:#e5e7eb;padding:10px;border-radius:6px;'>{_escape(traceback_text)}</pre>"
        )

    return f"""
    <div style="font-family:Arial, sans-serif; max-width:1000px;">
      <h2 style="margin:0 0 12px 0;">Regulation Monitor - Admin Durum Bildirimi</h2>
      <div style="margin-bottom:12px;">
        Tarih: <b>{day:%d.%m.%Y}</b><br/>
        Durum: <b style="color:{status_color};">{status_text}</b><br/>
        Toplam fihrist kaydi: <b>{total_items_text}</b>
      </div>

      <table style="width:100%; border-collapse:collapse; border:1px solid #eee;">
        <thead>
          <tr style="background:#f8fafc;">
            <th style="padding:8px;border-bottom:1px solid #eee;text-align:left;">Departman</th>
            <th style="padding:8px;border-bottom:1px solid #eee;text-align:left;">Mail Durumu</th>
            <th style="padding:8px;border-bottom:1px solid #eee;text-align:left;">Hit</th>
            <th style="padding:8px;border-bottom:1px solid #eee;text-align:left;">Alicilar</th>
            <th style="padding:8px;border-bottom:1px solid #eee;text-align:left;">Konu</th>
            <th style="padding:8px;border-bottom:1px solid #eee;text-align:left;">Ilgili Basliklar</th>
            <th style="padding:8px;border-bottom:1px solid #eee;text-align:left;">Hata</th>
          </tr>
        </thead>
        <tbody>
          {summary_rows if summary_rows else "<tr><td colspan='7' style='padding:8px;'>Departman raporu yok.</td></tr>"}
        </tbody>
      </table>

      {error_block}
      {traceback_block}
    </div>
    """


def _escape(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )
