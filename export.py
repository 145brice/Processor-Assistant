"""
Export Module — Processor Traien
Generates downloadable outputs from scan results:
  - CSV  : conditions table with status and party
  - HTML : professional one-page condition snapshot report (print-to-PDF)

No external dependencies. Uses Python stdlib only.
"""

import csv
import io
from datetime import date


# ─────────────────────────────────────────────────────────────────────────────
# CSV export
# ─────────────────────────────────────────────────────────────────────────────

def conditions_to_csv(condition_rows: list[dict], loan_info: dict | None = None) -> bytes:
    """
    Convert a list of condition dicts to CSV bytes.
    condition_rows: [{"num": 1, "desc": "...", "party": "Borrower", "status": "Needed"}, ...]
    Returns UTF-8 encoded CSV bytes suitable for st.download_button.
    """
    buf = io.StringIO()
    writer = csv.writer(buf)

    if loan_info:
        writer.writerow(["Loan Number", loan_info.get("loan_num", "")])
        writer.writerow(["Borrower",    loan_info.get("borrower", "")])
        writer.writerow(["Property",    loan_info.get("property", "")])
        writer.writerow(["Closing Date",loan_info.get("due_date", "")])
        writer.writerow(["Report Date", date.today().isoformat()])
        writer.writerow([])

    writer.writerow(["#", "Condition", "Responsible Party", "Status"])
    for row in condition_rows:
        writer.writerow([
            row.get("num", ""),
            row.get("desc", ""),
            row.get("party", ""),
            row.get("status", "Needed"),
        ])

    return buf.getvalue().encode("utf-8-sig")   # utf-8-sig = Excel-friendly BOM


# ─────────────────────────────────────────────────────────────────────────────
# Condition Snapshot HTML report
# ─────────────────────────────────────────────────────────────────────────────

_STATUS_COLOR = {
    "Important":       "#e74c3c",
    "Needed":          "#f1c40f",
    "Requested":       "#e67e22",
    "Ready to Clear":  "#27ae60",
    "Cleared":         "#3498db",
}

_PARTY_COLOR = {
    "Borrower":       "#1565C0",
    "Title":          "#6A1B9A",
    "Underwriter":    "#E65100",
    "Insurance":      "#00695C",
    "Closer":         "#F9A825",
    "Jr Underwriter": "#AD1457",
    "Manager":        "#283593",
    "Appraiser":      "#558B2F",
}


def snapshot_html(condition_rows: list[dict], loan_info: dict | None = None,
                  doc_type: str = "", processor_name: str = "") -> str:
    """
    Generate a print-ready HTML condition snapshot report.
    Returns an HTML string. Users can open in browser → Ctrl+P → Save as PDF.

    loan_info keys used: loan_num, borrower, property, due_date, lock_expiry
    condition_rows: same format as conditions_to_csv
    """
    info = loan_info or {}
    today = date.today().strftime("%B %d, %Y")

    loan_num  = info.get("loan_num", "—")
    borrower  = info.get("borrower", "—")
    prop      = info.get("property", info.get("folder_path", "—"))
    closing   = _fmt_date(info.get("due_date", ""))
    lock_exp  = _fmt_date(info.get("lock_expiry", ""))
    proc_name = processor_name or "Processor"

    # Split into active and cleared
    active  = [r for r in condition_rows if r.get("status", "Needed") != "Cleared"]
    cleared = [r for r in condition_rows if r.get("status", "Needed") == "Cleared"]

    # Count by status
    counts: dict[str, int] = {}
    for r in condition_rows:
        s = r.get("status", "Needed")
        counts[s] = counts.get(s, 0) + 1

    status_pills = "".join(
        f'<span style="background:{_STATUS_COLOR.get(s,"#888")};color:#fff;'
        f'padding:2px 10px;border-radius:12px;font-size:11px;margin-right:6px;">'
        f'{c} {s}</span>'
        for s, c in counts.items()
    )

    def _row_html(r: dict) -> str:
        num    = r.get("num", "")
        desc   = r.get("desc", "")
        party  = r.get("party", "")
        status = r.get("status", "Needed")
        sc = _STATUS_COLOR.get(status, "#888")
        pc = _PARTY_COLOR.get(party, "#555")
        return (
            f'<tr>'
            f'<td style="width:36px;text-align:center;color:#999;font-size:12px;">{num}</td>'
            f'<td style="padding:8px 10px;font-size:13px;color:#1a1a2e;">{_esc(desc)}</td>'
            f'<td style="width:130px;text-align:center;">'
            f'<span style="background:{pc};color:#fff;padding:2px 8px;border-radius:10px;'
            f'font-size:11px;white-space:nowrap;">{_esc(party)}</span></td>'
            f'<td style="width:130px;text-align:center;">'
            f'<span style="background:{sc};color:#fff;padding:2px 8px;border-radius:10px;'
            f'font-size:11px;white-space:nowrap;">{_esc(status)}</span></td>'
            f'</tr>'
        )

    active_rows  = "".join(_row_html(r) for r in active)
    cleared_rows = "".join(_row_html(r) for r in cleared)

    cleared_section = ""
    if cleared:
        cleared_section = f"""
        <h3 style="font-size:13px;font-weight:700;color:#3498db;margin:24px 0 8px;
                   text-transform:uppercase;letter-spacing:0.5px;">
            ✅ Cleared ({len(cleared)})
        </h3>
        <table style="width:100%;border-collapse:collapse;opacity:0.7;">
            <thead>
                <tr style="background:#f0f4f8;">
                    <th style="width:36px;"></th>
                    <th style="text-align:left;padding:6px 10px;font-size:11px;color:#666;">Condition</th>
                    <th style="width:130px;font-size:11px;color:#666;">Party</th>
                    <th style="width:130px;font-size:11px;color:#666;">Status</th>
                </tr>
            </thead>
            <tbody>{cleared_rows}</tbody>
        </table>
        """

    lock_row = ""
    if lock_exp:
        lock_color = _lock_color(info.get("lock_expiry", ""))
        lock_row = f'<div class="meta-item"><span class="meta-label">🔒 Lock Expires</span><span style="font-weight:700;color:{lock_color};">{lock_exp}</span></div>'

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Condition Snapshot — {_esc(borrower)}</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
          background: #fff; color: #1a1a2e; padding: 0; }}
  .page {{ max-width: 820px; margin: 0 auto; padding: 24px 32px 40px; }}

  .header {{ border-bottom: 3px solid #2d2060; padding-bottom: 16px; margin-bottom: 20px; }}
  .app-name {{ font-size: 11px; color: #7c6ff7; font-weight: 700;
               text-transform: uppercase; letter-spacing: 1px; margin-bottom: 6px; }}
  .report-title {{ font-size: 22px; font-weight: 800; color: #2d2060; }}
  .report-date {{ font-size: 11px; color: #888; margin-top: 3px; }}

  .meta-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8px 24px;
                background: #f7f6ff; border-radius: 8px; padding: 14px 18px;
                margin: 16px 0 20px; }}
  .meta-item {{ display: flex; flex-direction: column; gap: 2px; }}
  .meta-label {{ font-size: 10px; color: #888; text-transform: uppercase; letter-spacing: 0.5px; }}
  .meta-item span:last-child {{ font-size: 13px; font-weight: 600; color: #1a1a2e; }}

  .status-bar {{ margin-bottom: 18px; }}

  table {{ width: 100%; border-collapse: collapse; }}
  tr {{ border-bottom: 1px solid #f0f0f0; }}
  tr:hover {{ background: #fafafa; }}
  td {{ padding: 9px 6px; vertical-align: middle; }}

  h3.section-head {{ font-size: 13px; font-weight: 700; color: #2d2060; margin: 20px 0 8px;
                     text-transform: uppercase; letter-spacing: 0.5px; }}

  .footer {{ border-top: 1px solid #e8e8e8; margin-top: 32px; padding-top: 12px;
             font-size: 10px; color: #aaa; display: flex; justify-content: space-between; }}

  @media print {{
    body {{ print-color-adjust: exact; -webkit-print-color-adjust: exact; }}
    .page {{ padding: 12px 20px; }}
  }}
</style>
</head>
<body>
<div class="page">

  <div class="header">
    <div class="app-name">Processor Traien · Condition Snapshot</div>
    <div class="report-title">{_esc(borrower)}</div>
    <div class="report-date">Generated {today} by {_esc(proc_name)}</div>
  </div>

  <div class="meta-grid">
    <div class="meta-item">
      <span class="meta-label">Loan Number</span>
      <span>{_esc(loan_num)}</span>
    </div>
    <div class="meta-item">
      <span class="meta-label">Document Type</span>
      <span>{_esc(doc_type) or '—'}</span>
    </div>
    <div class="meta-item">
      <span class="meta-label">Property</span>
      <span>{_esc(prop)}</span>
    </div>
    <div class="meta-item">
      <span class="meta-label">🗓 Closing Date</span>
      <span style="font-weight:700;">{closing or '—'}</span>
    </div>
    {lock_row}
    <div class="meta-item">
      <span class="meta-label">Processor</span>
      <span>{_esc(proc_name)}</span>
    </div>
  </div>

  <div class="status-bar">{status_pills}</div>

  <h3 class="section-head">Open Conditions ({len(active)})</h3>
  <table>
    <thead>
      <tr style="background:#2d2060;">
        <th style="width:36px;"></th>
        <th style="text-align:left;padding:7px 10px;font-size:11px;color:#e6edf3;
                   font-weight:600;text-transform:uppercase;letter-spacing:0.5px;">Condition</th>
        <th style="width:130px;font-size:11px;color:#e6edf3;font-weight:600;
                   text-transform:uppercase;letter-spacing:0.5px;">Party</th>
        <th style="width:130px;font-size:11px;color:#e6edf3;font-weight:600;
                   text-transform:uppercase;letter-spacing:0.5px;">Status</th>
      </tr>
    </thead>
    <tbody>{active_rows}</tbody>
  </table>

  {cleared_section}

  <div class="footer">
    <span>Processor Traien — condition snapshot · {today}</span>
    <span>Loan {_esc(loan_num)} · {_esc(borrower)}</span>
  </div>
</div>
</body>
</html>"""

    return html


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _esc(s: str) -> str:
    return (str(s)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


def _fmt_date(iso: str) -> str:
    if not iso:
        return ""
    try:
        from datetime import datetime
        return datetime.strptime(iso, "%Y-%m-%d").strftime("%B %d, %Y")
    except Exception:
        return iso


def _lock_color(iso: str) -> str:
    """Red if expired/≤7 days, yellow if ≤14 days, green otherwise."""
    if not iso:
        return "#1a1a2e"
    try:
        from datetime import datetime
        exp = datetime.strptime(iso, "%Y-%m-%d").date()
        days = (exp - date.today()).days
        if days < 0:
            return "#e74c3c"
        if days <= 7:
            return "#e74c3c"
        if days <= 14:
            return "#f39c12"
        return "#27ae60"
    except Exception:
        return "#1a1a2e"
