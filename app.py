"""
Processor Traien - Mortgage Document Processing App
Main Streamlit application.
"""

import streamlit as st

# --- Page Config ---
st.set_page_config(
    page_title="Processor Traien",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Custom CSS ---
st.markdown("""
<style>
.progress-nav {
    display: flex;
    gap: 2px;
    background: #0e1117;
    border-radius: 10px;
    padding: 6px;
    margin-bottom: 24px;
    border: 1px solid #333;
    position: sticky;
    top: 0;
    z-index: 999;
    flex-wrap: wrap;
}
.pn-step {
    flex: 1;
    min-width: 90px;
    text-align: center;
    padding: 8px 6px;
    border-radius: 8px;
    font-size: 11px;
    font-weight: 600;
    text-decoration: none;
    transition: all 0.2s;
    line-height: 1.3;
}
.pn-step.done {
    background: #1a5c2a;
    color: #8f8;
}
.pn-step.active {
    background: #0e4da4;
    color: #fff;
}
.pn-step.pending {
    background: #1e1e1e;
    color: #666;
}
.pn-step:hover {
    background: #2a2a2a;
    color: #fff;
    transform: scale(1.02);
}
.pn-num {
    display: block;
    font-size: 14px;
    font-weight: 700;
    margin-bottom: 2px;
}
.section-anchor {
    display: block;
    position: relative;
    top: -100px;
    visibility: hidden;
}
</style>
""", unsafe_allow_html=True)

# --- Session State Defaults ---
DEFAULTS = {
    "authenticated": False,
    "user_id": None,
    "user_email": None,
    "page": "login",
    "sandbox_mode": True,
    "scan_results": None,
    "history": [],
    "last_fetch_folder": "",
    "fetch_results": None,
    "guide_results": None,
    "reader_folder": "",
    "reader_files": [],
    "reader_open_file": None,
    "reader_page": 1,
}
for key, val in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = val


# --- All workflow steps ---
WORKFLOW_STEPS = [
    ("upload", "1", "Upload"),
    ("megachecklist", "2", "Mega Checklist"),
    ("conditions", "3", "Conditions"),
    ("contacts", "4", "Contacts"),
    ("emails", "5", "Emails"),
    ("research", "6", "Research"),
    ("bankrules", "7", "Bank Rules"),
    ("riskflags", "8", "Risk Flags"),
    ("stacking", "9", "Stacking Order"),
    ("submit", "10", "Submit"),
]


def render_progress_bar(completed_steps):
    """Render the full workflow progress bar."""
    html = '<div class="progress-nav">'
    for step_id, num, label in WORKFLOW_STEPS:
        if step_id in completed_steps:
            css = "pn-step done"
        else:
            css = "pn-step pending"
        html += f'<a href="#{step_id}" class="{css}"><span class="pn-num">{num}</span>{label}</a>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


def show_login_page():
    """Login / Signup page."""
    st.markdown("# Processor Traien")
    st.markdown("### Mortgage Document Processing - Offline Mode")

    # Sandbox button top center, compact
    _, sb_col, _ = st.columns([1, 1, 1])
    with sb_col:
        if st.button("Try Sandbox", type="primary"):
            st.session_state.authenticated = True
            st.session_state.user_id = "sandbox"
            st.session_state.user_email = "sandbox@demo"
            st.session_state.sandbox_mode = True
            st.session_state.page = "dashboard"
            st.rerun()
        st.caption("Free - No account needed")

    st.markdown("---")

    tab_login, tab_signup = st.tabs(["Login", "Sign Up"])

    with tab_login:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login", use_container_width=True)
            if submitted and email and password:
                from db import login
                result = login(email, password)
                if result.get("success"):
                    st.session_state.authenticated = True
                    st.session_state.user_id = result["user_id"]
                    st.session_state.user_email = result["email"]
                    st.session_state.page = "dashboard"
                    st.rerun()
                else:
                    st.error(result.get("error", "Login failed"))

    with tab_signup:
        with st.form("signup_form"):
            email = st.text_input("Email", key="signup_email")
            password = st.text_input("Password", type="password", key="signup_pass")
            confirm = st.text_input("Confirm Password", type="password", key="signup_confirm")
            tos = st.checkbox(
                "I agree to the Terms of Service. I acknowledge that documents "
                "are processed in memory and never stored. I have authorization "
                "to process any documents I upload."
            )
            submitted = st.form_submit_button("Create Account", use_container_width=True)
            if submitted:
                if not tos:
                    st.error("You must agree to the Terms of Service")
                elif password != confirm:
                    st.error("Passwords do not match")
                elif len(password) < 6:
                    st.error("Password must be at least 6 characters")
                elif email and password:
                    from db import signup
                    result = signup(email, password)
                    if result.get("success"):
                        st.success("Account created! Check your email to confirm, then log in.")
                    else:
                        st.error(result.get("error", "Signup failed"))




def show_sidebar():
    """Sidebar navigation."""
    with st.sidebar:
        st.markdown("### Processor Traien")
        st.markdown(f"**{st.session_state.user_email}**")
        st.markdown("---")

        is_sandbox = st.toggle(
            "Sandbox Mode (Free Practice)",
            value=st.session_state.sandbox_mode,
            help="Sandbox: unlimited free scans, results not saved.",
        )
        st.session_state.sandbox_mode = is_sandbox

        if is_sandbox:
            st.info("Sandbox: Free & unlimited. Results not saved.")
        else:
            if st.session_state.user_id != "sandbox":
                from db import get_file_count
                count = get_file_count(st.session_state.user_id)
                remaining_free = max(0, 5 - count)
                st.warning(f"Live Mode: {count} files processed. {remaining_free} free files remaining.")
            else:
                st.warning("Log in to use Live Mode.")

        st.markdown("---")
        if st.button("Document Scanner", use_container_width=True):
            st.session_state.page = "dashboard"
            st.rerun()
        if st.button("Document Reader", use_container_width=True):
            st.session_state.page = "reader"
            st.rerun()
        if st.button("My History", use_container_width=True):
            st.session_state.page = "history"
            st.rerun()
        st.markdown("---")
        if st.button("Logout", use_container_width=True):
            from db import logout
            logout()
            for key in DEFAULTS:
                st.session_state[key] = DEFAULTS[key]
            st.rerun()


def show_dashboard():
    """Main document scanning page."""
    st.markdown("## Document Scanner")

    # === STEP 1: UPLOAD ===
    st.markdown('<span class="section-anchor" id="upload"></span>', unsafe_allow_html=True)

    uploaded_files = st.file_uploader(
        "Upload mortgage documents (PDF)",
        type=["pdf"],
        accept_multiple_files=True,
        help="Drag and drop PDFs here. Files are processed in memory and never stored.",
    )

    if not uploaded_files:
        # Show progress bar with nothing done
        render_progress_bar(set())
        st.markdown("---")
        st.markdown("### How it works")
        st.markdown(
            "1. **Upload** a mortgage PDF\n"
            "2. **Select** the document type\n"
            "3. **Scan** - Pattern engine extracts everything in one shot\n"
            "4. **Review** conditions, contacts, research, emails, stacking order\n"
            "5. **Submit** to lender when ready"
        )
        return

    for file_idx, uploaded_file in enumerate(uploaded_files):
        fkey = f"{uploaded_file.name}_{file_idx}"
        with st.expander(f"📄 {uploaded_file.name}", expanded=True):
            col1, col2 = st.columns([1, 2])

            with col1:
                doc_type = st.selectbox(
                    "Document Type",
                    [
                        "Approval Letter",
                        "Closing Disclosure (CD)",
                        "Loan Estimate (LE)",
                        "1003 Application",
                        "Credit Report",
                        "Bank Statement",
                        "Change of Circumstance (COC)",
                        "Broker Package (BP)",
                    ],
                    key=f"doctype_{fkey}",
                )
                scan_btn = st.button(
                    "🔍 Scan Document",
                    key=f"scan_{fkey}",
                    use_container_width=True,
                )

            with col2:
                if scan_btn:
                    progress = st.progress(0, text="Starting scan...")
                    from ai_engine import process_document

                    pdf_bytes = uploaded_file.read()

                    user_history = []
                    if st.session_state.user_id and st.session_state.user_id != "sandbox":
                        from db import get_history
                        user_history = get_history(st.session_state.user_id, 5)

                    progress.progress(10, text="Extracting conditions...")

                    result = process_document(pdf_bytes, doc_type, user_history)
                    del pdf_bytes

                    progress.progress(100, text="Done!")

                    if result["success"]:
                        st.session_state.scan_results = result
                        if not st.session_state.sandbox_mode and st.session_state.user_id != "sandbox":
                            from db import save_result, log_pattern
                            save_result(
                                st.session_state.user_id, doc_type,
                                result["conditions"], result.get("risks", ""),
                                result.get("bank_rules", ""),
                            )
                            log_pattern(doc_type, {
                                "text_length": result["text_length"],
                            })
                    else:
                        st.error(result.get("error", "Processing failed"))

            # === DISPLAY RESULTS ===
            if st.session_state.scan_results and st.session_state.scan_results.get("doc_type") == doc_type:
                result = st.session_state.scan_results

                # === CONDITIONS (the main output) ===
                conditions_text = result["conditions"]
                condition_rows = []
                for line in conditions_text.split("\n"):
                    line = line.strip()
                    if line.startswith("|") and not line.startswith("| #") and not line.startswith("|--") and not line.startswith("|-"):
                        cells = [c.strip() for c in line.split("|") if c.strip()]
                        if len(cells) >= 4:
                            condition_rows.append({
                                "num": cells[0], "desc": cells[1],
                                "party": cells[2], "status": cells[3],
                            })

                st.markdown("### 📋 Conditions")
                st.markdown(conditions_text)

                # Email drafting - select multiple conditions to combine
                if condition_rows:
                    st.markdown("---")
                    st.markdown("**Draft an email - select conditions to include:**")

                    # Checkboxes for each condition
                    selected_conds = []
                    for cond in condition_rows:
                        if st.checkbox(
                            f"#{cond['num']} - {cond['desc'][:80]}  ({cond['party']})",
                            key=f"chk_{fkey}_{cond['num']}",
                        ):
                            selected_conds.append(cond)

                    if selected_conds:
                        st.markdown("---")
                        lc1, lc2, lc3 = st.columns(3)
                        with lc1:
                            email_lang = st.selectbox(
                                "Language", ["English", "Spanish"],
                                key=f"lang_{fkey}",
                            )
                        with lc2:
                            # Default recipient to most common party in selection
                            parties = list({c["party"] for c in selected_conds})
                            recipient = st.selectbox(
                                "Send to", parties,
                                key=f"recip_{fkey}",
                            )
                        with lc3:
                            st.markdown(f"**{len(selected_conds)} condition(s) selected**")

                        btn_col1, btn_col2, btn_col3 = st.columns(3)
                        with btn_col1:
                            draft_clicked = st.button("Draft Email", key=f"draft_{fkey}", use_container_width=True)
                        with btn_col2:
                            fetch_clicked = st.button("Fetch from Folder", key=f"fetch_{fkey}", use_container_width=True)
                        with btn_col3:
                            guidelines_clicked = st.button("Check Guidelines", key=f"guide_{fkey}", use_container_width=True)

                        # --- Draft Email ---
                        if draft_clicked:
                            from ai_engine import draft_email
                            cond_lines = []
                            for c in selected_conds:
                                cond_lines.append(
                                    f"- Condition #{c['num']}: {c['desc']} (Status: {c['status']})"
                                )
                            combined = "\n".join(cond_lines)
                            email_text = draft_email(combined, recipient, email_lang)
                            st.container(border=True).markdown(email_text)
                            st.caption("Copy and paste into your email client. Review before sending.")

                        # --- Fetch from Folder ---
                        if fetch_clicked:
                            st.session_state[f"show_fetch_{fkey}"] = True

                        if st.session_state.get(f"show_fetch_{fkey}"):
                            st.markdown("---")
                            st.markdown("**Fetch borrower folder?**")
                            folder_path = st.text_input(
                                "Folder path (paste or type the full path to the borrower's folder):",
                                value=st.session_state.get("last_fetch_folder", ""),
                                key=f"folder_{fkey}",
                                placeholder=r"C:\Users\...\BorrowerName",
                            )

                            search_col1, search_col2 = st.columns([1, 3])
                            with search_col1:
                                search_clicked = st.button("Search", key=f"search_{fkey}", use_container_width=True)
                            with search_col2:
                                cancel_clicked = st.button("Cancel", key=f"cancel_fetch_{fkey}")

                            if cancel_clicked:
                                st.session_state[f"show_fetch_{fkey}"] = False
                                st.rerun()

                            if search_clicked and folder_path:
                                st.session_state["last_fetch_folder"] = folder_path
                                import os
                                if not os.path.isdir(folder_path):
                                    st.error(f"Folder not found: {folder_path}")
                                else:
                                    from folder_search import scan_folder
                                    progress = st.progress(0, text="Scanning folder...")

                                    def update_progress(pct, msg):
                                        progress.progress(min(pct, 100), text=msg)

                                    fetch_results = scan_folder(
                                        folder_path, selected_conds,
                                        threshold=60, progress_callback=update_progress,
                                    )

                                    if "error" in fetch_results:
                                        st.error(fetch_results["error"])
                                    else:
                                        st.session_state["fetch_results"] = fetch_results
                                        st.session_state[f"show_fetch_{fkey}"] = False

                        # --- Display Fetch Results ---
                        if st.session_state.get("fetch_results"):
                            st.markdown("---")
                            st.markdown("### Fetch Results")
                            fetch_results = st.session_state["fetch_results"]
                            any_found = False

                            for cnum, cdata in fetch_results.items():
                                if cnum == "error":
                                    continue
                                matches = cdata.get("matches", [])
                                desc_short = cdata["desc"][:80]

                                if matches:
                                    any_found = True
                                    with st.expander(f"Condition #{cnum}: {desc_short} ({len(matches)} match{'es' if len(matches) != 1 else ''})"):
                                        for match in matches:
                                            score = match["score"]
                                            if score >= 80:
                                                badge = "🟢"
                                            elif score >= 65:
                                                badge = "🟡"
                                            else:
                                                badge = "🔴"
                                            pages_str = ""
                                            if match["matched_pages"]:
                                                pages_str = f" | Pages: {', '.join(str(p) for p in match['matched_pages'])}"
                                            st.markdown(
                                                f"{badge} **{match['file_name']}** — "
                                                f"{match['match_type']} match ({score}%){pages_str}"
                                            )
                                            st.caption(f"📁 {match['file_path']}")
                                            if match.get("snippet"):
                                                st.text(match["snippet"][:200])
                                else:
                                    st.caption(f"Condition #{cnum}: {desc_short} — no matches found")

                            if not any_found:
                                st.info("No matching documents found in that folder for the selected conditions.")

                            if st.button("Clear fetch results", key=f"clear_fetch_{fkey}"):
                                st.session_state["fetch_results"] = None
                                st.rerun()

                        # --- Check Guidelines ---
                        if guidelines_clicked:
                            from guidelines import check_conditions_against_guidelines, get_available_guidelines
                            available = get_available_guidelines()
                            if not available:
                                st.error("No guideline PDFs found. Place 'Fannie Mae.pdf' and/or 'Freddie Mac.pdf' on your Desktop.")
                            else:
                                guide_names = [g["name"] for g in available]
                                cached_status = ", ".join(
                                    f"{g['name']} ({'cached' if g['indexed'] else 'will index'})"
                                    for g in available
                                )
                                st.info(f"Guidelines found: {cached_status}")
                                progress = st.progress(0, text="Loading guidelines...")

                                def guide_progress(pct, msg):
                                    progress.progress(min(pct, 100), text=msg)

                                guide_results = check_conditions_against_guidelines(
                                    selected_conds,
                                    progress_callback=guide_progress,
                                )

                                if "error" in guide_results:
                                    st.error(guide_results["error"])
                                else:
                                    st.session_state["guide_results"] = guide_results

                        # --- Display Guidelines Results ---
                        if st.session_state.get("guide_results"):
                            st.markdown("---")
                            st.markdown("### Guideline References")
                            guide_results = st.session_state["guide_results"]

                            for cnum, cdata in guide_results.items():
                                if cnum == "error":
                                    continue
                                guidelines = cdata.get("guidelines", [])
                                desc_short = cdata["desc"][:80]

                                if guidelines:
                                    with st.expander(
                                        f"Condition #{cnum}: {desc_short} "
                                        f"({len(guidelines)} reference{'s' if len(guidelines) != 1 else ''})",
                                        expanded=False,
                                    ):
                                        for gi, ref in enumerate(guidelines):
                                            score = ref["score"]
                                            if score >= 80:
                                                badge = "🟢"
                                            elif score >= 65:
                                                badge = "🟡"
                                            else:
                                                badge = "🔴"

                                            section_str = f" | {ref['section']}" if ref.get("section") else ""
                                            st.markdown(
                                                f"{badge} **{ref['source']}** — "
                                                f"Page {ref['page']}{section_str} "
                                                f"(relevance: {score}%)"
                                            )
                                            st.container(border=True).markdown(
                                                ref["excerpt"][:500]
                                            )
                                else:
                                    st.caption(f"Condition #{cnum}: {desc_short} — no guideline references found")

                            if st.button("Clear guideline results", key=f"clear_guide_{fkey}"):
                                st.session_state["guide_results"] = None
                                st.rerun()

                st.markdown("---")
                st.caption(
                    f"Processed {result['text_length']:,} characters | "
                    f"{'Sandbox' if st.session_state.sandbox_mode else 'Live'} mode"
                )


def _show_pdf_reader(pdf_path: str, search_term: str = ""):
    """Read a PDF page by page, or search within it."""
    import time as _t
    from pypdf import PdfReader
    try:
        reader = PdfReader(pdf_path)
        total_pages = len(reader.pages)
    except Exception as e:
        st.error(f"Could not read PDF: {e}")
        return

    st.caption(f"{total_pages} pages total")

    if search_term:
        st.markdown(f"**Searching for:** `{search_term}`")
        found_pages = []
        search_lower = search_term.lower()
        with st.spinner("Searching through pages..."):
            for i, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                if search_lower in text.lower():
                    idx = text.lower().find(search_lower)
                    start = max(0, idx - 100)
                    end = min(len(text), idx + len(search_term) + 250)
                    snippet = text[start:end].replace('\n', ' ')
                    found_pages.append({"page": i + 1, "snippet": snippet})
                _t.sleep(0.02)

        if found_pages:
            st.success(f"Found on {len(found_pages)} page(s)")
            for fp in found_pages:
                with st.expander(f"Page {fp['page']}", expanded=len(found_pages) <= 6):
                    st.markdown(f"...{fp['snippet']}...")
        else:
            st.warning(f"'{search_term}' not found in this document.")
    else:
        page_num = st.number_input(
            "Go to page:", min_value=1, max_value=total_pages,
            value=st.session_state.get("reader_page", 1),
            key="reader_page_num",
        )
        st.session_state["reader_page"] = page_num
        text = reader.pages[page_num - 1].extract_text() or ""
        if text.strip():
            st.text_area("Page content:", value=text, height=450, key=f"reader_pg_{page_num}")
        else:
            st.warning("This page has no extractable text (may be a scanned image).")


def _show_text_reader(file_path: str, search_term: str = ""):
    """Read a text or CSV file with optional search."""
    try:
        with open(file_path, 'r', errors='ignore') as f:
            content = f.read(200_000)
    except Exception as e:
        st.error(f"Could not read file: {e}")
        return

    if search_term:
        lines = content.split('\n')
        matches = [(i + 1, line) for i, line in enumerate(lines)
                   if search_term.lower() in line.lower()]
        if matches:
            st.success(f"Found on {len(matches)} line(s)")
            for lnum, line in matches[:80]:
                st.markdown(f"**Line {lnum}:** {line}")
        else:
            st.warning(f"'{search_term}' not found.")
    else:
        st.text_area("File content:", value=content[:15000], height=450, key="reader_text_content")
        if len(content) > 15000:
            st.caption(f"Showing first 15,000 of {len(content):,} characters.")


def show_reader():
    """Document Reader - browse any folder, open any file, read or search through it."""
    import os

    st.markdown("## Document Reader")
    st.caption("Browse a local folder, open and read any document, or search inside it.")

    # --- Folder input ---
    col1, col2 = st.columns([4, 1])
    with col1:
        folder_path = st.text_input(
            "Folder path:",
            value=st.session_state.get("reader_folder", ""),
            placeholder=r"C:\Users\...\BorrowerName  (paste the full path)",
            key="reader_folder_input",
        )
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        browse_btn = st.button("Browse Folder", use_container_width=True, key="reader_browse_btn")

    if browse_btn:
        if not folder_path:
            st.warning("Paste a folder path first.")
        elif not os.path.isdir(folder_path):
            st.error(f"Folder not found: {folder_path}")
        else:
            st.session_state["reader_folder"] = folder_path
            st.session_state["reader_open_file"] = None
            st.session_state["reader_page"] = 1
            files = []
            _READABLE = {'.pdf', '.txt', '.csv'}
            for root, dirs, fnames in os.walk(folder_path):
                # Skip hidden/system dirs
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                for fname in sorted(fnames):
                    ext = os.path.splitext(fname)[1].lower()
                    if ext not in _READABLE:
                        continue
                    fpath = os.path.join(root, fname)
                    try:
                        size_kb = os.path.getsize(fpath) / 1024
                    except OSError:
                        size_kb = 0
                    if size_kb > 100_000:  # skip files > 100MB
                        continue
                    rel = os.path.relpath(fpath, folder_path)
                    files.append({"name": fname, "path": fpath, "rel": rel,
                                  "ext": ext, "size_kb": round(size_kb, 1)})
            st.session_state["reader_files"] = files
            st.rerun()

    files = st.session_state.get("reader_files", [])

    if not files:
        if st.session_state.get("reader_folder"):
            st.info("No readable files (.pdf, .txt, .csv) found. Try a different folder.")
        else:
            st.markdown(
                "### How to use\n"
                "1. Paste the full path to a borrower folder above\n"
                "2. Click **Browse Folder** to list all readable files\n"
                "3. Pick any file from the list and click **Open & Read**\n"
                "4. Read page by page, or type a keyword to **search inside** the document"
            )
        return

    st.markdown(f"**{len(files)} readable file(s) found**")

    # --- File selector ---
    file_labels = [f"{f['rel']}  ({f['size_kb']} KB)" for f in files]
    selected_idx = st.selectbox(
        "Select a file:",
        range(len(file_labels)),
        format_func=lambda i: file_labels[i],
        key="reader_file_select",
    )
    selected_file = files[selected_idx]

    r1, r2, r3 = st.columns([1, 2, 1])
    with r1:
        open_btn = st.button("Open & Read", use_container_width=True, key="reader_open_btn")
    with r2:
        search_term = st.text_input(
            "Search inside document:",
            placeholder="e.g. appraisal, HOA, verification of mortgage",
            key="reader_search_input",
        )
    with r3:
        if st.session_state.get("reader_open_file"):
            if st.button("Close File", use_container_width=True, key="reader_close_btn"):
                st.session_state["reader_open_file"] = None
                st.rerun()

    if open_btn:
        st.session_state["reader_open_file"] = selected_file
        st.session_state["reader_page"] = 1
        st.rerun()

    # --- Show file content ---
    open_file = st.session_state.get("reader_open_file")
    if open_file:
        st.markdown("---")
        st.markdown(f"### {open_file['name']}")
        st.caption(f"{open_file['path']}")

        if open_file["ext"] == ".pdf":
            _show_pdf_reader(open_file["path"], search_term)
        elif open_file["ext"] in {".txt", ".csv"}:
            _show_text_reader(open_file["path"], search_term)
        else:
            st.info("File type cannot be read here. Open it directly in File Explorer.")


def show_history():
    """Show user's scan history."""
    st.markdown("## My History")
    if st.session_state.user_id == "sandbox":
        st.info("Log in to save and view your scan history.")
        return
    from db import get_history
    history = get_history(st.session_state.user_id)
    if not history:
        st.info("No scans yet. Upload a document to get started.")
        return
    for entry in history:
        with st.expander(f"📄 {entry['doc_type']} - {entry['created_at'][:10]}"):
            st.markdown("**Summary:**")
            st.markdown(entry.get("summary", ""))
            if st.button("View Full Results", key=f"view_{entry['id']}"):
                st.markdown("---")
                st.markdown("### Conditions")
                st.markdown(entry.get("conditions", ""))
                if entry.get("bank_rules"):
                    st.markdown("### Bank Statement Rules")
                    st.markdown(entry["bank_rules"])
                st.markdown("### Risk Flags")
                st.markdown(entry.get("risks", ""))


# --- Main ---
def main():
    if not st.session_state.authenticated:
        show_login_page()
    else:
        show_sidebar()
        page = st.session_state.page
        if page == "dashboard":
            show_dashboard()
        elif page == "history":
            show_history()
        elif page == "reader":
            show_reader()
        else:
            show_dashboard()


if __name__ == "__main__":
    main()
