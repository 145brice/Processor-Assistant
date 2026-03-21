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
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* ── Global reset & base ──────────────────────────────────────── */
html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}
.stApp {
    background: #2d2060;
}

/* ── Hide Streamlit chrome ────────────────────────────────────── */
#MainMenu, footer, header { visibility: hidden; height: 0; }
.stDeployButton { display: none; }

/* ── Sidebar ──────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: #231959 !important;
    border-right: 1px solid #4a3a8a !important;
}
[data-testid="stSidebar"] > div:first-child {
    padding: 1.5rem 1rem;
}

/* Sidebar nav buttons */
[data-testid="stSidebar"] button[kind="secondary"] {
    background: transparent !important;
    border: 1px solid #4a3a8a !important;
    color: #cdd9e5 !important;
    border-radius: 8px !important;
    font-size: 14px !important;
    font-weight: 600 !important;
    text-align: left !important;
    padding: 10px 14px !important;
    margin-bottom: 2px !important;
    transition: all 0.15s ease !important;
    width: 100% !important;
}
[data-testid="stSidebar"] button[kind="secondary"]:hover {
    background: #3a2878 !important;
    border-color: #7c6ff7 !important;
    color: #f0f6fc !important;
}

/* Sidebar toggle */
[data-testid="stSidebar"] [data-testid="stToggle"] label {
    font-size: 13px !important;
    color: #cdd9e5 !important;
    font-weight: 500 !important;
}

/* ── Main content area ────────────────────────────────────────── */
.block-container {
    padding: 1.5rem 2rem 3rem 2rem !important;
    max-width: 1300px !important;
}

/* Page headings */
h1 { font-size: 28px !important; font-weight: 800 !important; color: #f0f6fc !important; letter-spacing: -0.5px; }
h2 { font-size: 22px !important; font-weight: 700 !important; color: #f0f6fc !important; }
h3 { font-size: 16px !important; font-weight: 700 !important; color: #e6edf3 !important; }
p, li { color: #cdd9e5 !important; font-size: 14px !important; font-weight: 400 !important; }
label { color: #cdd9e5 !important; font-size: 14px !important; font-weight: 500 !important; }

/* Markdown text inside the app */
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li,
[data-testid="stMarkdownContainer"] span {
    color: #cdd9e5 !important;
    font-size: 14px !important;
}
[data-testid="stMarkdownContainer"] strong {
    color: #f0f6fc !important;
    font-weight: 700 !important;
}

/* Checkbox labels */
[data-testid="stCheckbox"] label p {
    color: #cdd9e5 !important;
    font-size: 14px !important;
    font-weight: 500 !important;
}

/* Selectbox selected value text */
[data-testid="stSelectbox"] > div > div > div {
    color: #e6edf3 !important;
    font-size: 14px !important;
    font-weight: 500 !important;
}

/* Radio / number input labels */
[data-testid="stNumberInput"] label,
[data-testid="stDateInput"] label,
[data-testid="stTextArea"] label {
    color: #cdd9e5 !important;
    font-size: 14px !important;
    font-weight: 500 !important;
}

/* ── Buttons ──────────────────────────────────────────────────── */
button[kind="primary"] {
    background: linear-gradient(135deg, #4f8ef7 0%, #2563eb 100%) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    padding: 0 20px !important;
    height: 38px !important;
    box-shadow: 0 2px 8px #4f8ef730 !important;
    transition: all 0.15s ease !important;
}
button[kind="primary"]:hover {
    background: linear-gradient(135deg, #6ea8fe 0%, #3b82f6 100%) !important;
    box-shadow: 0 4px 16px #4f8ef750 !important;
    transform: translateY(-1px) !important;
}
button[kind="secondary"] {
    background: #3a2878 !important;
    color: #e6edf3 !important;
    border: 1px solid #6a56b8 !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    height: 38px !important;
    transition: all 0.15s ease !important;
}
button[kind="secondary"]:hover {
    border-color: #7c6ff7 !important;
    color: #f0f6fc !important;
    background: #4a3a8a !important;
}

/* ── Inputs & selects ─────────────────────────────────────────── */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea,
[data-testid="stSelectbox"] > div > div,
[data-testid="stNumberInput"] input {
    background: #3a2878 !important;
    border: 1px solid #6a56b8 !important;
    border-radius: 8px !important;
    color: #f0f6fc !important;
    font-size: 14px !important;
    font-family: 'Inter', sans-serif !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {
    border-color: #7c6ff7 !important;
    box-shadow: 0 0 0 3px #7c6ff730 !important;
}

/* ── File uploader ────────────────────────────────────────────── */
[data-testid="stFileUploader"] {
    background: #3a2878 !important;
    border: 2px dashed #6a56b8 !important;
    border-radius: 12px !important;
    padding: 20px !important;
    transition: border-color 0.2s !important;
}
[data-testid="stFileUploader"]:hover {
    border-color: #7c6ff7 !important;
}
[data-testid="stFileUploader"] label {
    color: #cdd9e5 !important;
}

/* ── Expanders ────────────────────────────────────────────────── */
[data-testid="stExpander"] {
    background: #3a2878 !important;
    border: 1px solid #4a3a8a !important;
    border-radius: 8px !important;
    margin-bottom: 3px !important;
}
[data-testid="stExpander"] summary {
    font-weight: 600 !important;
    color: #f0f6fc !important;
    font-size: 13px !important;
    padding: 7px 12px !important;
    min-height: 0 !important;
    line-height: 1.4 !important;
}
[data-testid="stExpander"] summary:hover {
    color: #ffffff !important;
    background: #4a3a8a !important;
    border-radius: 8px !important;
}
/* Compact the expanded content area */
[data-testid="stExpander"] > div[data-testid="stExpanderDetails"] {
    padding: 8px 12px 10px 12px !important;
}

/* ── Info / warning / error boxes ────────────────────────────── */
[data-testid="stAlert"] {
    border-radius: 8px !important;
    border-width: 1px !important;
    font-size: 14px !important;
}

/* ── Dividers ─────────────────────────────────────────────────── */
hr { border-color: #4a3a8a !important; margin: 16px 0 !important; }

/* ── Tabs ─────────────────────────────────────────────────────── */
[data-testid="stTabs"] [role="tab"] {
    font-size: 14px !important;
    font-weight: 500 !important;
    color: #a89ec9 !important;
    border-radius: 6px 6px 0 0 !important;
    padding: 8px 18px !important;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    color: #b794f4 !important;
    border-bottom: 2px solid #7c6ff7 !important;
    background: transparent !important;
}

/* ── Checkbox ─────────────────────────────────────────────────── */
[data-testid="stCheckbox"] label {
    font-size: 14px !important;
    color: #e6edf3 !important;
}

/* ── Caption / small text ─────────────────────────────────────── */
[data-testid="stCaptionContainer"] p,
.stCaption { color: #a89ec9 !important; font-size: 12px !important; font-weight: 500 !important; }

/* ── Progress bar ─────────────────────────────────────────────── */
[data-testid="stProgress"] > div > div {
    background: linear-gradient(90deg, #7c6ff7, #4f8ef7) !important;
    border-radius: 4px !important;
}
[data-testid="stProgress"] {
    background: #3a2878 !important;
    border-radius: 4px !important;
}

/* ── Containers (bordered) ────────────────────────────────────── */
[data-testid="stVerticalBlockBorderWrapper"] {
    background: #3a2878 !important;
    border: 1px solid #4a3a8a !important;
    border-radius: 12px !important;
    padding: 16px !important;
}

/* ── Selectbox dropdown ───────────────────────────────────────── */
[data-testid="stSelectbox"] svg { color: #cdd9e5 !important; }

/* Dropdown popup list */
[data-baseweb="popover"] ul,
[data-baseweb="menu"] {
    background: #3a2878 !important;
    border: 1px solid #6a56b8 !important;
    border-radius: 8px !important;
}
[data-baseweb="popover"] li,
[data-baseweb="menu"] li {
    background: #3a2878 !important;
    color: #f0f6fc !important;
    font-size: 14px !important;
    font-weight: 500 !important;
}
[data-baseweb="popover"] li:hover,
[data-baseweb="menu"] li:hover {
    background: #5540a8 !important;
    color: #ffffff !important;
}
[data-baseweb="select"] > div {
    background: #3a2878 !important;
    border-color: #6a56b8 !important;
    color: #f0f6fc !important;
}

/* ── Toggle ───────────────────────────────────────────────────── */
[data-testid="stToggle"] > label > div[data-checked="true"] {
    background: #7c6ff7 !important;
}

/* ── Condition status buttons (inside expander) ──────────────── */
div[data-testid="stHorizontalBlock"] button[kind="secondary"] {
    font-size: 12px !important;
    font-weight: 700 !important;
    padding: 4px 6px !important;
    height: 32px !important;
    border-radius: 6px !important;
}

/* ── Multiselect ──────────────────────────────────────────────── */
[data-testid="stMultiSelect"] > div {
    background: #3a2878 !important;
    border: 1px solid #6a56b8 !important;
    border-radius: 8px !important;
}
[data-testid="stMultiSelect"] span[data-baseweb="tag"] {
    background: #5540a8 !important;
    color: #f0f6fc !important;
    border-radius: 6px !important;
    font-size: 13px !important;
    font-weight: 600 !important;
}
[data-testid="stMultiSelect"] input {
    color: #f0f6fc !important;
    background: transparent !important;
    border: none !important;
}

/* ── Markdown tables (conditions output) ─────────────────────── */
[data-testid="stMarkdownContainer"] table {
    width: 100% !important;
    border-collapse: collapse !important;
    background: #3a2878 !important;
    border-radius: 10px !important;
    overflow: hidden !important;
    font-size: 14px !important;
}
[data-testid="stMarkdownContainer"] thead tr {
    background: #4a3a8a !important;
}
[data-testid="stMarkdownContainer"] th {
    color: #b794f4 !important;
    font-size: 13px !important;
    font-weight: 700 !important;
    padding: 10px 14px !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
    border-bottom: 1px solid #6a56b8 !important;
}
[data-testid="stMarkdownContainer"] td {
    color: #f0f6fc !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    padding: 9px 14px !important;
    border-bottom: 1px solid #4a3a8a !important;
}
[data-testid="stMarkdownContainer"] tr:hover td {
    background: #4a3a8a !important;
    color: #ffffff !important;
}

/* ── Progress nav bar ─────────────────────────────────────────── */
.progress-nav {
    display: flex;
    gap: 3px;
    background: #3a2878;
    border-radius: 10px;
    padding: 5px;
    margin-bottom: 20px;
    border: 1px solid #4a3a8a;
    position: sticky;
    top: 0;
    z-index: 999;
    flex-wrap: wrap;
}
.pn-step {
    flex: 1;
    min-width: 80px;
    text-align: center;
    padding: 7px 5px;
    border-radius: 7px;
    font-size: 10px;
    font-weight: 600;
    text-decoration: none;
    transition: all 0.15s;
    line-height: 1.3;
    color: #484f58;
}
.pn-step.done    { background: #0d2818; color: #3fb950; border: 1px solid #238636; }
.pn-step.active  { background: #1c2d4f; color: #79c0ff; border: 1px solid #4f8ef7; }
.pn-step.pending { background: transparent; color: #484f58; }
.pn-step:hover   { background: #161b22; color: #c9d1d9; }
.pn-num { display: block; font-size: 13px; font-weight: 700; margin-bottom: 1px; }
.section-anchor  { display: block; position: relative; top: -100px; visibility: hidden; }

/* ── Party / condition badges ─────────────────────────────────── */
.badge {
    display: inline-block;
    padding: 2px 9px;
    border-radius: 10px;
    font-size: 11px;
    font-weight: 600;
    margin: 1px 2px;
    letter-spacing: 0.2px;
}
.badge-borrower    { background: #1c2d4f; color: #79c0ff; border: 1px solid #2563eb; }
.badge-title       { background: #2d1b4f; color: #d2a8ff; border: 1px solid #6A1B9A; }
.badge-underwriter { background: #3d1a00; color: #ffa657; border: 1px solid #E65100; }
.badge-insurance   { background: #0d2f2b; color: #56d364; border: 1px solid #00695C; }
.badge-closer      { background: #2e2200; color: #e3b341; border: 1px solid #c8971a; }
.badge-jr          { background: #3d0d25; color: #f778ba; border: 1px solid #AD1457; }
.badge-manager     { background: #0d1433; color: #79c0ff; border: 1px solid #283593; }
.badge-appraiser   { background: #1a2b0d; color: #7ee787; border: 1px solid #558B2F; }
.badge-default     { background: #161b22; color: #8b949e; border: 1px solid #30363d; }

/* ── Pipeline status chips ────────────────────────────────────── */
.status-chip {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 10px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.3px;
}
.status-pending   { background: #3d0d0d; color: #ff7b72; border: 1px solid #c0392b; }
.status-requested { background: #3d2200; color: #ffa657; border: 1px solid #e67e22; }
.status-cleared   { background: #0d2818; color: #56d364; border: 1px solid #27ae60; }
.status-overdue   { background: #1e2530; color: #8b949e; border: 1px solid #484f58; }
.status-closed    { background: #0d1117; color: #484f58; border: 1px solid #30363d; }

/* ── Loan pipeline cards ──────────────────────────────────────── */
.loan-card {
    background: #3a2878;
    border: 1px solid #4a3a8a;
    border-radius: 10px;
    padding: 12px 16px;
    margin-bottom: 4px;
    transition: border-color 0.15s;
}
.loan-card:hover { border-color: #7c6ff7; }
.loan-num   { font-size: 15px; font-weight: 800; color: #79c0ff; font-family: 'Inter', monospace; }
.loan-name  { font-size: 14px; color: #e6edf3; font-weight: 600; }
.loan-due   { font-size: 12px; color: #8b949e; font-weight: 500; }
.loan-missing { font-size: 12px; color: #ffa657; font-weight: 500; }

/* ── Stat cards (pipeline counts) ────────────────────────────── */
.stat-card {
    text-align: center;
    padding: 12px 8px;
    border-radius: 10px;
    background: #3a2878;
    border: 1px solid #4a3a8a;
}
.stat-num  { font-size: 26px; font-weight: 800; color: #f0f6fc; line-height: 1; }
.stat-label { font-size: 11px; color: #8b949e; margin-top: 3px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }

/* ── Login card ───────────────────────────────────────────────── */
.login-card {
    max-width: 420px;
    margin: 40px auto 0 auto;
    background: #3a2878;
    border: 1px solid #4a3a8a;
    border-radius: 16px;
    padding: 36px 32px;
}
.login-title {
    font-size: 24px;
    font-weight: 800;
    color: #e6edf3;
    text-align: center;
    margin-bottom: 4px;
}
.login-sub {
    font-size: 13px;
    color: #484f58;
    text-align: center;
    margin-bottom: 24px;
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
    "pipeline_add_open": False,
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
    st.markdown("""
    <div style="text-align:center; padding: 48px 0 8px 0;">
      <div style="font-size:36px; margin-bottom:6px;">📋</div>
      <div style="font-size:28px; font-weight:800; color:#e6edf3; letter-spacing:-0.5px;">
        Processor Traien
      </div>
      <div style="font-size:13px; color:#484f58; margin-top:4px;">
        Offline Mortgage Processing &nbsp;·&nbsp; No cloud &nbsp;·&nbsp; No API keys
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    _, sb_col, _ = st.columns([1, 1, 1])
    with sb_col:
        if st.button("⚡ Try Sandbox — No Account Needed", type="primary", use_container_width=True):
            st.session_state.authenticated = True
            st.session_state.user_id = "sandbox"
            st.session_state.user_email = "sandbox@demo"
            st.session_state.sandbox_mode = True
            st.session_state.page = "dashboard"
            st.rerun()
        st.caption("Free & unlimited — results not saved between sessions")

    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
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
        st.markdown("""
        <div style="padding: 4px 0 16px 0;">
          <div style="font-size:18px; font-weight:800; color:#e6edf3; letter-spacing:-0.3px;">
            📋 Processor Traien
          </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown(
            f'<div style="font-size:11px; color:#484f58; margin-bottom:12px;">'
            f'{st.session_state.user_email}</div>',
            unsafe_allow_html=True,
        )
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
        if st.button("📋 Document Scanner", use_container_width=True):
            st.session_state.page = "dashboard"
            st.rerun()
        if st.button("🗂️ My Pipeline", use_container_width=True):
            st.session_state.page = "pipeline"
            st.rerun()
        if st.button("📂 Document Reader", use_container_width=True):
            st.session_state.page = "reader"
            st.rerun()
        if st.button("🕑 My History", use_container_width=True):
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

                PARTY_OPTIONS = [
                    "Borrower", "Title", "Underwriter", "Jr Underwriter",
                    "Closer", "Insurance", "Appraiser", "Manager", "Processor",
                ]

                # Condition status definitions
                COND_STATUSES = {
                    "Needed":          {"emoji": "🟡", "color": "#f1c40f", "label": "Needed"},
                    "Requested":       {"emoji": "🟠", "color": "#e67e22", "label": "Requested"},
                    "Important":       {"emoji": "🔴", "color": "#e74c3c", "label": "Important"},
                    "Ready to Clear":  {"emoji": "🟢", "color": "#27ae60", "label": "Ready to Clear"},
                    "Cleared":         {"emoji": "🔵", "color": "#5dade2", "label": "Cleared"},
                }

                def _render_condition(cond, fkey, PARTY_OPTIONS, COND_STATUSES):
                    """Render one compact condition row with expandable details."""
                    cnum       = cond["num"]
                    party_key  = f"party_{fkey}_{cnum}"
                    notes_key  = f"notes_{fkey}_{cnum}"
                    status_key = f"cstatus_{fkey}_{cnum}"

                    # Init party
                    raw_default = cond["party"] if cond["party"] in PARTY_OPTIONS else "Borrower"
                    if party_key not in st.session_state:
                        st.session_state[party_key] = [raw_default]
                    saved_parties = st.session_state.get(party_key, [raw_default])
                    if not isinstance(saved_parties, list):
                        saved_parties = [raw_default]
                    saved_parties = [p for p in saved_parties if p in PARTY_OPTIONS] or [raw_default]

                    # Init status
                    if status_key not in st.session_state:
                        st.session_state[status_key] = "Needed"
                    cur_status = st.session_state.get(status_key, "Needed")
                    if cur_status not in COND_STATUSES:
                        cur_status = "Needed"
                    status_info = COND_STATUSES[cur_status]

                    saved_notes = st.session_state.get(notes_key, "")

                    # Build expander label: emoji + # + truncated desc
                    short_desc  = cond["desc"][:72] + ("…" if len(cond["desc"]) > 72 else "")
                    exp_label   = f"{status_info['emoji']} #{cnum}  {short_desc}"

                    col_chk, col_exp = st.columns([1, 11])
                    with col_chk:
                        checked = st.checkbox("", key=f"chk_{fkey}_{cnum}",
                                              label_visibility="collapsed")
                    with col_exp:
                        with st.expander(exp_label, expanded=False):
                            # ── Status buttons row ───────────────────────
                            st.markdown("**Status:**")
                            sb = st.columns(len(COND_STATUSES))
                            for i, (sname, sinfo) in enumerate(COND_STATUSES.items()):
                                with sb[i]:
                                    active = "✓ " if cur_status == sname else ""
                                    border = "3px solid #fff" if cur_status == sname else f"2px solid {sinfo['color']}"
                                    if st.button(
                                        f"{sinfo['emoji']} {active}{sinfo['label']}",
                                        key=f"sbtn_{fkey}_{cnum}_{sname}",
                                        use_container_width=True,
                                    ):
                                        st.session_state[status_key] = sname
                                        st.rerun()

                            st.markdown('<div style="height:4px"></div>', unsafe_allow_html=True)

                            # ── Party multiselect ────────────────────────
                            new_parties = st.multiselect(
                                "Responsible parties",
                                PARTY_OPTIONS,
                                default=saved_parties,
                                key=party_key,
                                placeholder="Add parties...",
                            )
                            if new_parties:
                                st.markdown(
                                    " ".join(_party_badge(p) for p in new_parties),
                                    unsafe_allow_html=True,
                                )

                            # ── Notes ────────────────────────────────────
                            st.text_input(
                                "Update / notes",
                                key=notes_key,
                                placeholder="Add update or note...",
                            )
                            if saved_notes:
                                st.caption(f"💬 {saved_notes}")

                    return checked, cur_status, saved_parties

                # ── Split into active and cleared ──────────────────────────
                active_conds  = []
                cleared_conds = []
                for cond in condition_rows:
                    sk = f"cstatus_{fkey}_{cond['num']}"
                    if st.session_state.get(sk, "Needed") == "Cleared":
                        cleared_conds.append(cond)
                    else:
                        active_conds.append(cond)

                # Count per status for header summary
                status_counts = {}
                for cond in condition_rows:
                    sk  = f"cstatus_{fkey}_{cond['num']}"
                    s   = st.session_state.get(sk, "Needed")
                    status_counts[s] = status_counts.get(s, 0) + 1
                summary_parts = [
                    f"{COND_STATUSES[s]['emoji']} {c} {s}"
                    for s, c in status_counts.items() if s in COND_STATUSES
                ]
                st.caption("  ·  ".join(summary_parts) if summary_parts else f"{len(condition_rows)} conditions")

                # ── Render active conditions ───────────────────────────────
                selected_conds = []
                for cond in active_conds:
                    checked, cur_status, saved_parties = _render_condition(
                        cond, fkey, PARTY_OPTIONS, COND_STATUSES
                    )
                    if checked:
                        selected_conds.append({
                            **cond,
                            "party":       saved_parties[0] if saved_parties else "Borrower",
                            "all_parties": saved_parties,
                            "cond_status": cur_status,
                        })

                # ── Cleared section at the bottom ──────────────────────────
                if cleared_conds:
                    st.markdown("---")
                    with st.expander(f"🔵 Cleared ({len(cleared_conds)})", expanded=False):
                        for cond in cleared_conds:
                            checked, cur_status, saved_parties = _render_condition(
                                cond, fkey, PARTY_OPTIONS, COND_STATUSES
                            )
                            if checked:
                                selected_conds.append({
                                    **cond,
                                    "party":       saved_parties[0] if saved_parties else "Borrower",
                                    "all_parties": saved_parties,
                                    "cond_status": cur_status,
                                })

                if selected_conds:
                        st.markdown("---")
                        st.markdown(f"**{len(selected_conds)} condition(s) selected — choose action:**")
                        lc1, lc2, lc3 = st.columns(3)
                        with lc1:
                            email_lang = st.selectbox(
                                "Language", ["English", "Spanish"],
                                key=f"lang_{fkey}",
                            )
                        with lc2:
                            # All parties across all selected conditions
                            all_parties_flat = []
                            for c in selected_conds:
                                for p in c.get("all_parties", [c["party"]]):
                                    if p not in all_parties_flat:
                                        all_parties_flat.append(p)
                            recipient = st.selectbox(
                                "Send to", all_parties_flat,
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


def _party_badge(party: str) -> str:
    """Return an HTML badge span for a condition party."""
    key = party.lower().replace(" ", "").replace("jr", "jr")
    mapping = {
        "borrower": "borrower",
        "title": "title",
        "underwriter": "underwriter",
        "insurance": "insurance",
        "closer": "closer",
        "jrunderwriter": "jr",
        "manager": "manager",
        "appraiser": "appraiser",
    }
    css = mapping.get(key, "default")
    return f'<span class="badge badge-{css}">{party}</span>'


def _status_chip(status: str) -> str:
    """Return an HTML status chip for pipeline rows."""
    css = status.lower()
    from crm import STATUS_EMOJI
    emoji = STATUS_EMOJI.get(status, "")
    return f'<span class="status-chip status-{css}">{emoji} {status}</span>'


def show_pipeline():
    """Color-coded CRM loan pipeline dashboard."""
    import os
    from crm import (
        get_all_loans, add_loan, set_status, delete_loan, update_loan,
        STATUS_OPTIONS, STATUS_EMOJI,
    )

    st.markdown("## 🗂️ My Pipeline")
    st.caption("Track every loan — color-coded by status, one-click actions.")

    # ── Top action bar ──────────────────────────────────────────────────────
    tb1, tb2, tb3, tb4 = st.columns([2, 2, 2, 2])
    with tb1:
        if st.button("➕ Add Loan", use_container_width=True, type="primary"):
            st.session_state.pipeline_add_open = not st.session_state.get("pipeline_add_open", False)
    with tb2:
        filter_status = st.selectbox(
            "Filter by status:", ["All"] + STATUS_OPTIONS,
            key="pipeline_filter", label_visibility="collapsed",
        )
    with tb3:
        search_loan = st.text_input(
            "Search:", placeholder="Loan # or borrower name",
            key="pipeline_search", label_visibility="collapsed",
        )
    with tb4:
        st.markdown(
            " &nbsp; ".join(
                f'<span class="status-chip status-{s.lower()}">{STATUS_EMOJI[s]} {s}</span>'
                for s in STATUS_OPTIONS[:4]
            ),
            unsafe_allow_html=True,
        )

    # ── Add Loan form ────────────────────────────────────────────────────────
    if st.session_state.get("pipeline_add_open"):
        with st.container(border=True):
            st.markdown("**Add New Loan to Pipeline**")
            f1, f2, f3 = st.columns(3)
            with f1:
                new_loan_num = st.text_input("Loan #", key="pl_new_num")
                new_borrower = st.text_input("Borrower Name", key="pl_new_borrower")
            with f2:
                new_status = st.selectbox("Status", STATUS_OPTIONS, key="pl_new_status")
                new_due = st.date_input("Due Date", key="pl_new_due")
            with f3:
                new_missing = st.text_area(
                    "Missing Docs (comma separated)",
                    key="pl_new_missing", height=68,
                )
                new_folder = st.text_input(
                    "Borrower Folder Path (optional)", key="pl_new_folder",
                    placeholder=r"C:\Loans\SmithJohn",
                )

            sa1, sa2 = st.columns([1, 4])
            with sa1:
                if st.button("Save Loan", use_container_width=True, key="pl_save_btn"):
                    if new_loan_num and new_borrower:
                        add_loan(
                            new_loan_num, new_borrower, new_status,
                            str(new_due), new_missing, new_folder,
                        )
                        st.session_state.pipeline_add_open = False
                        st.rerun()
                    else:
                        st.error("Loan # and Borrower Name are required.")
            with sa2:
                if st.button("Cancel", key="pl_cancel_btn"):
                    st.session_state.pipeline_add_open = False
                    st.rerun()

    st.markdown("---")

    # ── Load and filter loans ────────────────────────────────────────────────
    loans = get_all_loans()

    if filter_status != "All":
        loans = [l for l in loans if l["status"] == filter_status]
    if search_loan:
        q = search_loan.lower()
        loans = [l for l in loans
                 if q in l.get("loan_num", "").lower()
                 or q in l.get("borrower", "").lower()]

    if not loans:
        st.info("No loans in pipeline yet. Click **➕ Add Loan** to get started.")
        return

    # ── Stats row ────────────────────────────────────────────────────────────
    all_loans = get_all_loans()
    counts = {s: sum(1 for l in all_loans if l["status"] == s) for s in STATUS_OPTIONS}
    sc = st.columns(len(STATUS_OPTIONS))
    for i, status in enumerate(STATUS_OPTIONS):
        with sc[i]:
            st.markdown(
                f'<div class="stat-card">'
                f'<div class="stat-num">{STATUS_EMOJI[status]} {counts[status]}</div>'
                f'<div class="stat-label">{status}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.markdown("---")

    # ── Loan rows ────────────────────────────────────────────────────────────
    for loan in loans:
        lid = loan.get("id")
        status = loan.get("status", "Pending")
        status_css = status.lower()
        emoji = STATUS_EMOJI.get(status, "")

        # Color left-border by status
        border_colors = {
            "Pending":   "#c0392b",
            "Requested": "#e67e22",
            "Cleared":   "#27ae60",
            "Overdue":   "#7f8c8d",
            "Closed":    "#2c3e50",
        }
        border_color = border_colors.get(status, "#444")

        st.markdown(
            f'<div class="loan-card" style="border-left: 4px solid {border_color};">'
            f'<span class="loan-num">#{loan.get("loan_num","—")}</span> &nbsp;'
            f'<span class="loan-name">{loan.get("borrower","—")}</span> &nbsp;'
            f'{_status_chip(status)}'
            f'<br><span class="loan-due">📅 Due: {loan.get("due_date","—")}</span> &nbsp;'
            f'<span class="loan-missing">📋 Missing: {loan.get("missing_docs","—") or "None"}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # Action buttons in a compact row
        ac1, ac2, ac3, ac4, ac5 = st.columns([1, 1, 1, 1, 2])
        with ac1:
            if st.button("✅ Cleared", key=f"clr_{lid}", use_container_width=True):
                set_status(lid, "Cleared")
                st.rerun()
        with ac2:
            if st.button("📤 Requested", key=f"req_{lid}", use_container_width=True):
                set_status(lid, "Requested")
                st.rerun()
        with ac3:
            if st.button("⏰ Overdue", key=f"ovr_{lid}", use_container_width=True):
                set_status(lid, "Overdue")
                st.rerun()
        with ac4:
            folder = loan.get("folder_path", "")
            if folder and os.path.isdir(folder):
                if st.button("📂 Open Folder", key=f"ofld_{lid}", use_container_width=True):
                    os.startfile(folder)
            else:
                folder_in = st.text_input(
                    "Set folder:", key=f"fpath_{lid}",
                    label_visibility="collapsed",
                    placeholder="Paste folder path",
                )
                if folder_in and st.button("Save", key=f"fsave_{lid}"):
                    update_loan(lid, folder_path=folder_in)
                    st.rerun()
        with ac5:
            notes = st.text_input(
                "Notes:", value=loan.get("notes", ""),
                key=f"notes_{lid}", label_visibility="collapsed",
                placeholder="Notes...",
            )
            nc1, nc2 = st.columns([1, 1])
            with nc1:
                if st.button("Save Notes", key=f"nsave_{lid}", use_container_width=True):
                    update_loan(lid, notes=notes)
                    st.rerun()
            with nc2:
                if st.button("🗑️ Remove", key=f"del_{lid}", use_container_width=True):
                    delete_loan(lid)
                    st.rerun()

        st.markdown('<div style="height:6px"></div>', unsafe_allow_html=True)


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
        elif page == "pipeline":
            show_pipeline()
        elif page == "history":
            show_history()
        elif page == "reader":
            show_reader()
        else:
            show_dashboard()


if __name__ == "__main__":
    main()
