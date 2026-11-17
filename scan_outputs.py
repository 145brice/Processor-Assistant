"""Local scan summaries, downloads, and drafts. No AI or database calls."""
import csv
import hashlib
import io
import json
import textwrap
from pathlib import Path


def load_sample():
    return json.loads(Path(__file__).with_name("sample_loan.json").read_text(encoding="utf-8"))


def condition_rows(result):
    raw = result.get("conditions") or []
    if isinstance(raw, str):
        raw = [line.strip(" -*\t") for line in raw.splitlines() if line.strip()]
    if not isinstance(raw, list):
        return []
    rows = []
    for index, item in enumerate(raw, 1):
        item = item if isinstance(item, dict) else {"desc": str(item)}
        party = item.get("party") or item.get("responsible_party") or item.get("responsible") or "Unassigned"
        if isinstance(party, list):
            party = ", ".join(map(str, party))
        desc = item.get("desc") or item.get("description") or item.get("condition") or item.get("text") or ""
        if str(desc).strip():
            rows.append({"num": index, "desc": str(desc), "party": str(party),
                         "status": str(item.get("status") or "Needed")})
    return rows


def loan_label(batch):
    result = batch.get("result") or {}
    match = batch.get("loan_match") or {}
    data = result.get("extracted_data") or {}
    buyer = (data.get("buyer") or {}) if isinstance(data, dict) else {}
    contacts = result.get("contacts") or {}
    borrower = result.get("borrower") or match.get("borrower")
    if not borrower and isinstance(buyer, dict):
        borrower = buyer.get("name")
    if not borrower and isinstance(contacts, dict):
        for role, contact in contacts.items():
            if any(word in role.lower() for word in ("borrower", "buyer")) and isinstance(contact, dict):
                borrower = contact.get("name")
                if borrower:
                    break
    return str(borrower or "Borrower"), str(result.get("loan_num") or match.get("loan_num") or "Not identified")


def flattened_fields(value, prefix=""):
    if isinstance(value, dict):
        for key, child in value.items():
            yield from flattened_fields(child, f"{prefix}.{key}" if prefix else str(key))
    elif isinstance(value, list):
        for index, child in enumerate(value, 1):
            yield from flattened_fields(child, f"{prefix}[{index}]")
    else:
        yield prefix, str(value) if value is not None else ""


def export_fields(batch):
    # Do not export source document text, prompts, or internal parsing diagnostics.
    result = batch.get("result") or {}
    borrower, number = loan_label(batch)
    fields = [("Document", str(batch.get("file") or "Scan")), ("Type", str(batch.get("type") or "Document")),
              ("Borrower", borrower), ("Loan number", number)]
    for name in ("property", "loan_amount", "loan_program", "status", "extracted_data", "contacts",
                 "summary", "risks", "bank_rules", "bank_summary", "findings"):
        if result.get(name):
            fields.extend(flattened_fields(result[name], name))
    for row in condition_rows(result):
        fields.append((f"Condition {row['num']}", f"{row['desc']} | {row['party']} | {row['status']}"))
    return fields


def summary_text(batch):
    return "Processor Assistant - Scan results\n\n" + "\n".join(f"{key}: {value}" for key, value in export_fields(batch))


def csv_bytes(batch):
    def safe(value):
        return "'" + value if value.lstrip().startswith(("=", "+", "-", "@")) else value
    buf = io.StringIO(newline="")
    writer = csv.writer(buf)
    writer.writerow(["Field", "Value"])
    writer.writerows((safe(k), safe(v)) for k, v in export_fields(batch))
    return buf.getvalue().encode("utf-8-sig")


def pdf_bytes(batch):
    import fitz
    document = fitz.open()
    page = document.new_page()
    y = 45
    for paragraph in summary_text(batch).splitlines():
        for line in textwrap.wrap(paragraph, width=90, break_long_words=True) or [""]:
            if y > 795:
                page = document.new_page()
                y = 45
            page.insert_text((40, y), line, fontsize=10)
            y += 14
    data = document.tobytes()
    document.close()
    return data


def email_drafts(batch):
    borrower, number = loan_label(batch)
    rows = condition_rows(batch.get("result") or {})
    open_rows = [r for r in rows if r["status"].lower() not in {"cleared", "waived", "complete", "completed"}]
    borrower_rows = [r for r in open_rows if any(p in r["party"].lower() for p in ("borrower", "buyer"))]
    needs = "\n".join(f"- {r['desc']}" for r in borrower_rows)
    if needs:
        needs = "Please provide the following items to continue processing your loan:\n\n" + needs
    else:
        needs = "This scan did not identify additional items assigned to you. We will contact you if further documents are needed."
    borrower_email = (f"Subject: Documents needed for your loan {number}\n\nHi {borrower},\n\n{needs}\n\n"
                      "Please send documents through our secure document channel. Let us know if you have any questions.\n\nThank you,\nYour loan processing team")
    status = "\n".join(f"- {r['desc']} ({r['party']}; {r['status']})" for r in open_rows)
    officer_email = (f"Subject: Loan {number} - processing status update\n\nHi,\n\n"
                     f"Here is the latest scan summary for {borrower}, loan {number}.\n"
                     f"Document reviewed: {batch.get('file') or 'Loan document'}.\n\n"
                     f"Open items identified in this scan:\n{status or 'No open conditions were identified in this scan.'}\n\n"
                     "Please review these items and confirm any changes to priorities or timing.\n\nThank you,\nYour loan processing team")
    return borrower_email, officer_email


def copy_button(text, label="Copy"):
    import streamlit.components.v1 as components
    # JSON is escaped for a script context; document content is never inserted as HTML.
    payload = json.dumps(text).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    import html
    components.html('''<button id="copy" style="cursor:pointer;padding:9px 16px;border:1px solid #cbd5e1;
        border-radius:8px;background:#eff6ff;color:#1e3a5f;font:600 14px system-ui">'''
        + html.escape(label) + '''</button><span id="status" role="status"></span><script>
        const text = ''' + payload + ''';
        document.getElementById('copy').onclick = async () => {
          try {
            try { await navigator.clipboard.writeText(text); }
            catch (_) {
              const area = document.createElement('textarea'); area.value = text;
              document.body.appendChild(area); area.select();
              const ok = document.execCommand('copy'); area.remove();
              if (!ok) throw new Error('clipboard unavailable');
            }
            document.getElementById('copy').textContent = 'Copied!';
          } catch (_) { document.getElementById('status').textContent = 'Select the text below to copy.'; }
        };</script>''', height=46)


def render_outputs(batch, key, *, sample=False):
    import streamlit as st
    key = f"{key}_{hashlib.sha256(summary_text(batch).encode()).hexdigest()[:12]}"
    st.subheader("Sample loan results" if sample else "Scan outputs")
    if sample:
        st.info("Fictional sample loan. These are pre-run results; no documents are uploaded and no AI calls are made.")
        st.dataframe([{"Field": k, "Value": v} for k, v in export_fields(batch)], hide_index=True, use_container_width=True)
    a, b, c = st.columns(3)
    with a:
        copy_button(summary_text(batch), "Copy results")
    with b:
        st.download_button("Export PDF", data=pdf_bytes(batch), file_name="loan-scan.pdf", mime="application/pdf", key=f"{key}_pdf")
    with c:
        st.download_button("Export CSV", data=csv_bytes(batch), file_name="loan-scan.csv", mime="text/csv", key=f"{key}_csv")
    st.caption("Review the extracted details and drafts before sending.")
    for index, (title, draft) in enumerate(zip(("Borrower needs-list email", "Loan officer status update"), email_drafts(batch))):
        with st.expander(title, expanded=sample):
            edited = st.text_area(title, value=draft, height=240, key=f"{key}_draft_{index}")
            copy_button(edited, "Copy email")


def render_sample_button(key):
    import streamlit as st
    if st.button("Try with a sample loan", key=f"{key}_sample", use_container_width=True):
        st.session_state[f"{key}_show_sample"] = True
    if st.session_state.get(f"{key}_show_sample"):
        render_outputs(load_sample(), f"{key}_sample_result", sample=True)
        if st.button("Close sample", key=f"{key}_close_sample"):
            st.session_state[f"{key}_show_sample"] = False
            st.rerun()
