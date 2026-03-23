"""
Processor Traien - Mortgage Document Processing App
Main Streamlit application.
"""

import os
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
/* Uploaded file chip — name + size shown after upload */
[data-testid="stFileUploaderFile"] {
    background: #2a1f55 !important;
    border: 1px solid #4a3a8a !important;
    border-radius: 6px !important;
    color: #e6edf3 !important;
}
[data-testid="stFileUploaderFile"] span,
[data-testid="stFileUploaderFile"] small,
[data-testid="stFileUploaderFile"] p {
    color: #e6edf3 !important;
    font-weight: 500 !important;
}
[data-testid="stFileUploaderFileName"] {
    color: #f0f6fc !important;
    font-weight: 600 !important;
}
[data-testid="stFileUploaderFileData"] {
    color: #a89ec9 !important;
}

/* ── Form submit buttons (Add to Team, Save, etc.) ────────────── */
[data-testid="stForm"] [data-testid="stBaseButton-secondaryFormSubmit"],
[data-testid="stForm"] button[kind="primaryFormSubmit"],
[data-testid="stForm"] button[kind="secondaryFormSubmit"] {
    background: #3a2878 !important;
    border: 1px solid #6a56b8 !important;
    color: #e6edf3 !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
}
[data-testid="stForm"] button[kind="primaryFormSubmit"]:hover,
[data-testid="stForm"] button[kind="secondaryFormSubmit"]:hover {
    background: #4a3a8a !important;
    border-color: #7c6ff7 !important;
    color: #ffffff !important;
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
    "page": "dashboard",
    "authenticated": False,
    "user_id": None,
    "user_email": "",
    "user_name": "",
    "user_role": "",
    "sandbox_mode": False,
    "scan_results": None,
    "last_fetch_folder": "",
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
            st.session_state.user_name = "Sandbox User"
            st.session_state.user_role = "Processor"
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
                    st.session_state.user_name = result.get("display_name") or result["email"].split("@")[0]
                    st.session_state.user_role = result.get("role", "Processor")
                    st.session_state.sandbox_mode = False
                    st.session_state.page = "dashboard"
                    st.rerun()
                else:
                    st.error(result.get("error", "Login failed"))

    with tab_signup:
        with st.form("signup_form"):
            from db import ROLE_OPTIONS
            display_name = st.text_input("Your Name", placeholder="e.g. Maria Garcia", key="signup_name")
            role = st.selectbox("Your Role", ROLE_OPTIONS, key="signup_role")
            email = st.text_input("Email", key="signup_email")
            password = st.text_input("Password", type="password", key="signup_pass")
            confirm = st.text_input("Confirm Password", type="password", key="signup_confirm")
            tos = st.checkbox(
                "I acknowledge that documents are processed in memory only and never stored. "
                "I have authorization to process any documents I upload."
            )
            submitted = st.form_submit_button("Create Account", use_container_width=True)
            if submitted:
                if not tos:
                    st.error("Please check the acknowledgment above")
                elif password != confirm:
                    st.error("Passwords do not match")
                elif len(password) < 6:
                    st.error("Password must be at least 6 characters")
                elif not display_name.strip():
                    st.error("Please enter your name")
                elif email and password:
                    from db import signup
                    result = signup(email, password, display_name=display_name, role=role)
                    if result.get("success"):
                        st.success(f"Account created for {display_name}! You can now log in.")
                    else:
                        st.error(result.get("error", "Signup failed"))




def show_sidebar():
    """Sidebar navigation."""
    with st.sidebar:
        user_name = st.session_state.get("user_name", "")
        user_role = st.session_state.get("user_role", "")
        is_sandbox = st.session_state.get("sandbox_mode", False)

        st.markdown("""
        <div style="padding: 4px 0 16px 0;">
          <div style="font-size:20px; font-weight:800; color:#e6edf3; letter-spacing:-0.3px;">
            📋 Processor Traien
          </div>
          <div style="font-size:11px; color:#a89ec9; margin-top:4px;">Offline · Local · No cloud</div>
        </div>
        """, unsafe_allow_html=True)

        # ── Who's logged in ──────────────────────────────────────────────────
        if is_sandbox:
            st.markdown(
                '<div style="background:#2a1f55;border:1px solid #4a3a8a;border-radius:8px;'
                'padding:8px 12px;margin-bottom:12px;">'
                '<span style="font-size:12px;color:#a89ec9;">⚡ Sandbox Mode</span></div>',
                unsafe_allow_html=True,
            )
        elif user_name:
            role_color = {"Loan Officer": "#e67e22", "Manager": "#2980b9",
                          "Jr Underwriter": "#c0392b"}.get(user_role, "#7c6ff7")
            st.markdown(
                f'<div style="background:#2a1f55;border:1px solid #4a3a8a;border-radius:8px;'
                f'padding:8px 12px;margin-bottom:12px;">'
                f'<div style="font-size:13px;font-weight:700;color:#f0f6fc;">{user_name}</div>'
                f'<div style="font-size:11px;color:{role_color};font-weight:600;">{user_role}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

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
        if st.button("👥 My Team", use_container_width=True):
            st.session_state.page = "team"
            st.rerun()
        if st.button("📧 Email Watch", use_container_width=True):
            st.session_state.page = "email_watch"
            st.rerun()
        if st.button("🤖 Ollama", use_container_width=True):
            st.session_state.page = "ollama"
            st.rerun()
        if not is_sandbox:
            if st.button("🕑 My History", use_container_width=True):
                st.session_state.page = "history"
                st.rerun()

        st.markdown("---")

        # ── Email Watch status indicator ──────────────────────────────────────
        import email_watch as _ew
        _ew_status = _ew.get_status()
        _ew_running = _ew_status["running"]
        _ew_pending = _ew_status["pending_count"]
        _ew_last    = _ew_status["last_time"] or "—"
        if _ew_running:
            _dot = "🟢"
            _label = f"Watching · {_ew_last}"
        else:
            _dot = "⚫"
            _label = "Inbox watch off"
        _badge = f' <span style="background:#7c6ff7;color:#fff;font-size:10px;border-radius:8px;padding:1px 6px;">{_ew_pending}</span>' if _ew_pending else ""
        st.markdown(
            f'<div style="background:#1e1645;border:1px solid #4a3a8a;border-radius:8px;'
            f'padding:7px 10px;margin-bottom:4px;cursor:default;">'
            f'<span style="font-size:12px;color:#cdd9e5;">{_dot} {_label}{_badge}</span></div>',
            unsafe_allow_html=True,
        )

        # ── Ollama status indicator ───────────────────────────────────────────
        import ollama_client as _oc
        _oc_cfg = _oc.get_config()
        if _oc_cfg.get("enabled"):
            _oc_ok, _ = _oc.ping(_oc_cfg.get("endpoint"))
            _oc_dot   = "🟣" if _oc_ok else "🔴"
            _oc_label = f"Ollama · {_oc_cfg.get('model','?')}" if _oc_ok else "Ollama · offline"
        else:
            _oc_dot, _oc_label = "⚫", "Ollama off"
        st.markdown(
            f'<div style="background:#1e1645;border:1px solid #4a3a8a;border-radius:8px;'
            f'padding:7px 10px;margin-bottom:8px;cursor:default;">'
            f'<span style="font-size:12px;color:#cdd9e5;">{_oc_dot} {_oc_label}</span></div>',
            unsafe_allow_html=True,
        )

        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            for key in DEFAULTS:
                st.session_state[key] = DEFAULTS[key]
            st.rerun()


def show_dashboard():
    """Main document scanning page."""
    st.markdown("## Document Scanner")

    # === QUICK DOC VERIFY — drop any PDF, get instant check ===
    import email_watch as _ew_mod
    _ew_pending = _ew_mod.get_status()["pending_count"]
    _qv_label   = f"📥 Quick Verify  ({_ew_pending} from inbox waiting)" if _ew_pending else "📥 Quick Verify — drop any PDF for instant check"

    with st.expander(_qv_label, expanded=bool(_ew_pending)):
        st.markdown(
            "Drop any PDF here — no doc type selection needed. "
            "The app figures out what it is, checks the dates, counts pages, "
            "and tries to match it to a loan in your pipeline. "
            "**Nothing is saved until you say so.**"
        )

        qv_file = st.file_uploader(
            "Drop a PDF to verify",
            type=["pdf"],
            key="qv_uploader",
            help="Works for any doc: bank statement, pay stub, W-2, appraisal, etc.",
        )
        if qv_file:
            qv_bytes = qv_file.read()
            from doc_verify import verify as _dv
            with st.spinner("Checking..."):
                result = _dv(qv_bytes, qv_file.name)

            verdict = result["verdict"]
            if verdict == "pass":
                vcard_bg, vcard_bdr, vcard_icon = "#152a1e", "#27ae60", "✅"
                vcard_title = "Looks good — ready for review"
            elif verdict == "review":
                vcard_bg, vcard_bdr, vcard_icon = "#2d2808", "#f1c40f", "⚠️"
                vcard_title = "Probably fine — double-check flagged items"
            else:
                vcard_bg, vcard_bdr, vcard_icon = "#3d1515", "#e74c3c", "🔍"
                vcard_title = "Needs attention before saving"

            st.markdown(
                f'<div style="background:{vcard_bg};border-left:4px solid {vcard_bdr};'
                f'border-radius:8px;padding:12px 16px;margin:12px 0;">'
                f'<div style="font-size:15px;font-weight:700;color:#f0f6fc;">'
                f'{vcard_icon} {result["doc_type"]} · {vcard_title}</div>'
                f'<div style="font-size:12px;color:#a89ec9;margin-top:4px;">{qv_file.name}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

            vc1, vc2 = st.columns(2)
            with vc1:
                st.markdown("**✅ Passed**")
                for ok in result["ok_list"]:
                    st.markdown(
                        f'<div style="display:flex;gap:8px;margin-bottom:3px;">'
                        f'<span style="color:#27ae60;">✓</span>'
                        f'<span style="color:#cdd9e5;font-size:13px;">{ok}</span></div>',
                        unsafe_allow_html=True,
                    )
            with vc2:
                st.markdown("**⚠️ Flagged**")
                if result["flags"]:
                    for fl in result["flags"]:
                        st.markdown(
                            f'<div style="display:flex;gap:8px;margin-bottom:3px;">'
                            f'<span style="color:#e74c3c;">⚑</span>'
                            f'<span style="color:#f5b7b1;font-size:13px;">{fl}</span></div>',
                            unsafe_allow_html=True,
                        )
                else:
                    st.markdown(
                        '<span style="color:#a89ec9;font-size:13px;">No flags — all clear</span>',
                        unsafe_allow_html=True,
                    )

            # ── Action row ───────────────────────────────────────────────────
            st.markdown("---")
            folder = result.get("suggested_folder", "")
            borrower = result.get("borrower", "")
            loan_num = result.get("loan_num", "")

            if borrower:
                st.markdown(
                    f'<div style="background:#1e1645;border:1px solid #4a3a8a;border-radius:8px;'
                    f'padding:10px 14px;margin-bottom:10px;">'
                    f'<span style="font-size:13px;color:#cdd9e5;">Pipeline match: </span>'
                    f'<span style="font-size:14px;font-weight:700;color:#f0f6fc;">{borrower}</span>'
                    f'<span style="font-size:12px;color:#7c6ff7;margin-left:8px;">Loan {loan_num}</span>'
                    f'<span style="font-size:12px;color:#a89ec9;margin-left:8px;">'
                    f'{result["confidence"]}% confidence</span></div>',
                    unsafe_allow_html=True,
                )

            act1, act2, act3, act4 = st.columns(4)
            with act1:
                if folder and os.path.isdir(folder):
                    if st.button("💾 Save to folder", key="qv_save", type="primary", use_container_width=True):
                        import shutil
                        dest = os.path.join(folder, qv_file.name)
                        with open(dest, "wb") as _f:
                            _f.write(qv_bytes)
                        st.success(f"Saved to {dest} — marked Pending Review in pipeline.")
                else:
                    save_path = st.text_input("Save to folder:", placeholder=r"C:\Loans\Smith", key="qv_savepath")
                    if save_path and st.button("💾 Save here", key="qv_save_manual", use_container_width=True):
                        os.makedirs(save_path, exist_ok=True)
                        dest = os.path.join(save_path, qv_file.name)
                        with open(dest, "wb") as _f:
                            _f.write(qv_bytes)
                        st.success(f"Saved to {dest}")
            with act2:
                if st.button("📋 Scan this doc", key="qv_scan", use_container_width=True):
                    st.session_state["qv_promote"] = qv_bytes
                    st.session_state["qv_promote_name"] = qv_file.name
                    st.rerun()
            with act3:
                if st.button("📂 Open in Reader", key="qv_reader", use_container_width=True):
                    st.session_state.reader_open_file = None
                    st.session_state.page = "reader"
                    st.rerun()
            with act4:
                pass   # space

        # ── Email Watch inbox inside Verify tab ──────────────────────────────
        ew_matches = _ew_mod.get_matches()
        if ew_matches:
            st.markdown("---")
            st.markdown(f"### 📬 Email Inbox — {len(ew_matches)} attachment(s) waiting")
            for ei, em in enumerate(ew_matches):
                v_icon = {"pass": "✅", "review": "⚠️", "check": "🔍"}.get(em.get("verdict", "check"), "📄")
                with st.expander(
                    f"{v_icon} {em['filename']} · {em.get('received','')} · "
                    f"From: {em['sender'][:40]}",
                    expanded=False,
                ):
                    ec1, ec2 = st.columns([3, 1])
                    with ec1:
                        for ok in em.get("ok_list", []):
                            st.markdown(
                                f'<div style="color:#a9dfbf;font-size:12px;">✓ {ok}</div>',
                                unsafe_allow_html=True,
                            )
                        for fl in em.get("flags", []):
                            st.markdown(
                                f'<div style="color:#f5b7b1;font-size:12px;">⚑ {fl}</div>',
                                unsafe_allow_html=True,
                            )
                    with ec2:
                        efolder = em.get("suggested_folder", "")
                        if efolder and os.path.isdir(efolder):
                            if st.button("💾 Save", key=f"ew_qv_save_{ei}", use_container_width=True, type="primary"):
                                import shutil
                                shutil.copy2(em["file_path"], os.path.join(efolder, em["filename"]))
                                _ew_mod.dismiss(ei)
                                st.success("Saved.")
                                st.rerun()
                        if st.button("Dismiss", key=f"ew_qv_dis_{ei}", use_container_width=True):
                            _ew_mod.dismiss(ei)
                            st.rerun()

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
                        "Purchase Contract",
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

                # === BANK STATEMENT — special display ===
                if doc_type == "Bank Statement":
                    bank_rules = result.get("bank_rules", "")
                    if not bank_rules:
                        st.warning("Bank statement analysis returned no results. The PDF may be a scanned image with no readable text.")
                        continue

                    st.markdown("## 🏦 Bank Statement Analysis")
                    st.caption("Offline pattern scan — manual review always recommended.")

                    # Parse structured output
                    raw_lines = bank_rules.strip().split("\n")
                    ok_c = flag_c = miss_c = info_c = 0
                    current_section = ""

                    for raw in raw_lines:
                        parts = raw.split("|")
                        tag = parts[0] if parts else ""

                        if tag == "SUMMARY":
                            ok_c, flag_c, miss_c, info_c = (
                                int(parts[1]), int(parts[2]),
                                int(parts[3]), int(parts[4]),
                            )
                            sc1, sc2, sc3, sc4 = st.columns(4)
                            with sc1:
                                st.markdown(
                                    f'<div class="stat-card"><div class="stat-num" style="color:#27ae60;">{ok_c}</div>'
                                    f'<div class="stat-label">✅ Passed</div></div>',
                                    unsafe_allow_html=True,
                                )
                            with sc2:
                                st.markdown(
                                    f'<div class="stat-card"><div class="stat-num" style="color:#e74c3c;">{flag_c}</div>'
                                    f'<div class="stat-label">🚩 Flagged</div></div>',
                                    unsafe_allow_html=True,
                                )
                            with sc3:
                                st.markdown(
                                    f'<div class="stat-card"><div class="stat-num" style="color:#f1c40f;">{miss_c}</div>'
                                    f'<div class="stat-label">⚠️ Missing</div></div>',
                                    unsafe_allow_html=True,
                                )
                            with sc4:
                                st.markdown(
                                    f'<div class="stat-card"><div class="stat-num" style="color:#5dade2;">{info_c}</div>'
                                    f'<div class="stat-label">ℹ️ Note</div></div>',
                                    unsafe_allow_html=True,
                                )
                            st.markdown("---")

                        elif tag == "SECTION":
                            current_section = parts[1] if len(parts) > 1 else ""
                            st.markdown(
                                f'<div style="font-size:13px;font-weight:700;color:#b794f4;'
                                f'margin:14px 0 6px 0;text-transform:uppercase;letter-spacing:0.5px;">'
                                f'{current_section}</div>',
                                unsafe_allow_html=True,
                            )

                        elif tag == "OK":
                            num, label, msg = parts[1], parts[2], parts[3] if len(parts) > 3 else ""
                            st.markdown(
                                f'<div style="display:flex;gap:10px;align-items:flex-start;'
                                f'background:#152a1e;border-left:3px solid #27ae60;'
                                f'border-radius:6px;padding:7px 12px;margin-bottom:3px;">'
                                f'<span style="color:#27ae60;font-weight:700;font-size:12px;min-width:20px;">✓</span>'
                                f'<div><span style="color:#cdd9e5;font-size:13px;font-weight:600;">{label}</span>'
                                f'<br><span style="color:#a89ec9;font-size:12px;">{msg}</span></div></div>',
                                unsafe_allow_html=True,
                            )

                        elif tag == "FLAG":
                            num, label, msg = parts[1], parts[2], parts[3] if len(parts) > 3 else ""
                            st.markdown(
                                f'<div style="display:flex;gap:10px;align-items:flex-start;'
                                f'background:#3d1515;border-left:3px solid #e74c3c;'
                                f'border-radius:6px;padding:7px 12px;margin-bottom:3px;">'
                                f'<span style="color:#e74c3c;font-weight:700;font-size:12px;min-width:20px;">🚩</span>'
                                f'<div><span style="color:#f0f6fc;font-size:13px;font-weight:700;">{label}</span>'
                                f'<br><span style="color:#e8b4b4;font-size:12px;">{msg}</span></div></div>',
                                unsafe_allow_html=True,
                            )

                        elif tag == "MISSING":
                            num, label, msg = parts[1], parts[2], parts[3] if len(parts) > 3 else ""
                            st.markdown(
                                f'<div style="display:flex;gap:10px;align-items:flex-start;'
                                f'background:#3d3015;border-left:3px solid #f1c40f;'
                                f'border-radius:6px;padding:7px 12px;margin-bottom:3px;">'
                                f'<span style="color:#f1c40f;font-weight:700;font-size:12px;min-width:20px;">⚠</span>'
                                f'<div><span style="color:#f0f6fc;font-size:13px;font-weight:600;">{label}</span>'
                                f'<br><span style="color:#e8d8a0;font-size:12px;">{msg}</span></div></div>',
                                unsafe_allow_html=True,
                            )

                        elif tag == "INFO":
                            num, label, msg = parts[1], parts[2], parts[3] if len(parts) > 3 else ""
                            st.markdown(
                                f'<div style="display:flex;gap:10px;align-items:flex-start;'
                                f'background:#1a2a3d;border-left:3px solid #5dade2;'
                                f'border-radius:6px;padding:7px 12px;margin-bottom:3px;">'
                                f'<span style="color:#5dade2;font-weight:700;font-size:12px;min-width:20px;">ℹ</span>'
                                f'<div><span style="color:#f0f6fc;font-size:13px;font-weight:600;">{label}</span>'
                                f'<br><span style="color:#a8c8e8;font-size:12px;">{msg}</span></div></div>',
                                unsafe_allow_html=True,
                            )

                        elif tag == "MANUAL":
                            num, label = parts[1], parts[2] if len(parts) > 2 else ""
                            st.markdown(
                                f'<div style="display:flex;gap:10px;align-items:center;'
                                f'background:#252040;border-left:3px solid #6a56b8;'
                                f'border-radius:6px;padding:6px 12px;margin-bottom:3px;">'
                                f'<span style="color:#6a56b8;font-size:12px;min-width:20px;">👁</span>'
                                f'<span style="color:#a89ec9;font-size:13px;">{label}</span>'
                                f'</div>',
                                unsafe_allow_html=True,
                            )

                    # ── Fetch & Analyze from Folder ──────────────────────────
                    st.markdown("---")
                    st.markdown("### 📂 Fetch & Analyze Bank Statements from Folder")
                    st.caption(
                        "Search a borrower's folder for bank statement PDFs and run "
                        "the full analysis on any file — right here."
                    )

                    # Pre-fill folder: last used → pipeline match → blank
                    from crm import get_all_loans as _get_pipe_loans
                    _default_bs_folder = st.session_state.get("last_fetch_folder", "")
                    if not _default_bs_folder:
                        for _pl in _get_pipe_loans():
                            _fp = _pl.get("folder_path", "")
                            if _fp and os.path.isdir(_fp):
                                _default_bs_folder = _fp
                                break

                    bsf1, bsf2, bsf3 = st.columns([4, 2, 1])
                    with bsf1:
                        bs_folder = st.text_input(
                            "Borrower folder:",
                            value=_default_bs_folder,
                            placeholder=r"C:\Loans\SmithJohn",
                            key=f"bs_folder_{fkey}",
                            label_visibility="collapsed",
                        )
                    with bsf2:
                        bs_scope = st.selectbox(
                            "Scope",
                            ["Bank statements only", "All PDFs in folder"],
                            key=f"bs_scope_{fkey}",
                            label_visibility="collapsed",
                        )
                    with bsf3:
                        bs_search = st.button(
                            "🔍 Search", key=f"bs_search_{fkey}",
                            use_container_width=True, type="primary",
                        )

                    if bs_search and bs_folder:
                        st.session_state["last_fetch_folder"] = bs_folder
                        from folder_search import find_bank_statements
                        scope_val = "bank_only" if "only" in bs_scope else "all_pdfs"
                        with st.spinner("Scanning folder..."):
                            bs_hits = find_bank_statements(bs_folder, scope=scope_val)

                        if not bs_hits:
                            st.info(
                                "No bank statement PDFs found. Try switching to "
                                "**All PDFs in folder** or check the folder path."
                            )
                        else:
                            st.session_state[f"bs_hits_{fkey}"] = bs_hits

                    bs_hits = st.session_state.get(f"bs_hits_{fkey}", [])
                    if bs_hits:
                        st.markdown(
                            f"<div style='font-size:13px;color:#a89ec9;margin-bottom:8px;'>"
                            f"Found {len(bs_hits)} file(s) — click Analyze to run the 50-rule scan</div>",
                            unsafe_allow_html=True,
                        )
                        for hi, hit in enumerate(bs_hits):
                            conf_color = "#27ae60" if hit["score"] >= 70 else (
                                "#f1c40f" if hit["score"] >= 40 else "#e74c3c"
                            )
                            conf_label = "High" if hit["score"] >= 70 else (
                                "Medium" if hit["score"] >= 40 else "Low"
                            )
                            hc1, hc2, hc3 = st.columns([4, 2, 1])
                            with hc1:
                                st.markdown(
                                    f'<div style="font-weight:600;color:#f0f6fc;font-size:13px;">'
                                    f'{hit["file_name"]}</div>'
                                    f'<div style="font-size:11px;color:#a89ec9;">'
                                    f'{hit["snippet"][:120]}...</div>',
                                    unsafe_allow_html=True,
                                )
                            with hc2:
                                st.markdown(
                                    f'<div style="font-size:12px;color:{conf_color};font-weight:700;">'
                                    f'{conf_label} confidence ({hit["score"]}%)</div>'
                                    f'<div style="font-size:11px;color:#a89ec9;">{hit["reason"]}</div>',
                                    unsafe_allow_html=True,
                                )
                            with hc3:
                                if st.button("Analyze", key=f"bs_analyze_{fkey}_{hi}",
                                             use_container_width=True):
                                    st.session_state[f"bs_analyzing_{fkey}"] = hit["file_path"]

                            # If this file is selected for analysis, run it
                            if st.session_state.get(f"bs_analyzing_{fkey}") == hit["file_path"]:
                                with st.spinner(f"Running bank analysis on {hit['file_name']}..."):
                                    from pypdf import PdfReader as _PR
                                    from ai_engine import check_bank_rules as _cbr
                                    try:
                                        _rdr = _PR(hit["file_path"])
                                        _txt = "\n".join(
                                            (p.extract_text() or "") for p in _rdr.pages
                                        )
                                        _bank_out = _cbr(_txt)
                                    except Exception as _e:
                                        _bank_out = ""
                                        st.error(f"Could not read file: {_e}")

                                if _bank_out:
                                    st.markdown(
                                        f"<div style='font-size:13px;font-weight:700;"
                                        f"color:#b794f4;margin:10px 0 6px 0;'>"
                                        f"📊 Analysis: {hit['file_name']}</div>",
                                        unsafe_allow_html=True,
                                    )
                                    _raw2 = _bank_out.strip().split("\n")
                                    for _raw in _raw2:
                                        _pts = _raw.split("|")
                                        _tag = _pts[0] if _pts else ""
                                        if _tag == "SUMMARY":
                                            _ok2, _fl2, _ms2, _in2 = (
                                                int(_pts[1]), int(_pts[2]),
                                                int(_pts[3]), int(_pts[4]),
                                            )
                                            _s1, _s2, _s3, _s4 = st.columns(4)
                                            for _col, _val, _clr, _lbl in [
                                                (_s1, _ok2, "#27ae60", "✅ Passed"),
                                                (_s2, _fl2, "#e74c3c", "🚩 Flagged"),
                                                (_s3, _ms2, "#f1c40f", "⚠️ Missing"),
                                                (_s4, _in2, "#5dade2", "ℹ️ Note"),
                                            ]:
                                                with _col:
                                                    st.markdown(
                                                        f'<div class="stat-card">'
                                                        f'<div class="stat-num" style="color:{_clr};">{_val}</div>'
                                                        f'<div class="stat-label">{_lbl}</div></div>',
                                                        unsafe_allow_html=True,
                                                    )
                                        elif _tag == "SECTION":
                                            st.markdown(
                                                f'<div style="font-size:12px;font-weight:700;color:#b794f4;'
                                                f'margin:10px 0 4px 0;text-transform:uppercase;">'
                                                f'{_pts[1] if len(_pts)>1 else ""}</div>',
                                                unsafe_allow_html=True,
                                            )
                                        elif _tag in ("OK", "FLAG", "MISSING", "INFO", "MANUAL"):
                                            _lbl2 = _pts[2] if len(_pts) > 2 else ""
                                            _msg2 = _pts[3] if len(_pts) > 3 else ""
                                            _styles = {
                                                "OK":     ("#152a1e", "#27ae60", "✓"),
                                                "FLAG":   ("#3d1515", "#e74c3c", "🚩"),
                                                "MISSING":("#3d3015", "#f1c40f", "⚠"),
                                                "INFO":   ("#1a2a3d", "#5dade2", "ℹ"),
                                                "MANUAL": ("#252040", "#6a56b8", "👁"),
                                            }
                                            _bg, _bdr, _ico = _styles.get(
                                                _tag, ("#252040", "#6a56b8", "·")
                                            )
                                            st.markdown(
                                                f'<div style="display:flex;gap:8px;'
                                                f'background:{_bg};border-left:3px solid {_bdr};'
                                                f'border-radius:5px;padding:5px 10px;margin-bottom:2px;">'
                                                f'<span style="color:{_bdr};min-width:18px;">{_ico}</span>'
                                                f'<div><span style="color:#f0f6fc;font-size:12px;'
                                                f'font-weight:600;">{_lbl2}</span>'
                                                + (f'<br><span style="color:#a89ec9;font-size:11px;">{_msg2}</span>' if _msg2 else "")
                                                + f'</div></div>',
                                                unsafe_allow_html=True,
                                            )

                    # ── Fraud Check (bank statements) ───────────────────────
                    st.markdown("---")
                    fc_key = f"fraud_on_{fkey}"
                    fc_col1, fc_col2 = st.columns([1, 4])
                    with fc_col1:
                        fraud_on = st.toggle("🔍 Fraud Check", key=fc_key, value=False)
                    with fc_col2:
                        if fraud_on:
                            st.caption("Scanning for fraud indicators — SSN mismatches, "
                                       "zero withholding, balance jumps, uniform pay, date gaps.")

                    if fraud_on:
                        from fraud_check import check as _fc
                        _pdf_bytes_fc = uploaded_file.getvalue()
                        _fc_result = _fc(_pdf_bytes_fc, doc_type)
                        _fc_risk   = _fc_result["risk_level"]
                        _fc_flags  = _fc_result["flags"]
                        _fc_bg = {"high": "#3d1515", "medium": "#2d2808", "low": "#152a1e"}[_fc_risk]
                        _fc_bdr = {"high": "#e74c3c", "medium": "#f1c40f", "low": "#27ae60"}[_fc_risk]
                        st.markdown(
                            f'<div style="background:{_fc_bg};border-left:4px solid {_fc_bdr};'
                            f'border-radius:8px;padding:10px 16px;margin:8px 0;">'
                            f'<div style="font-size:14px;font-weight:700;color:#f0f6fc;">'
                            f'{_fc_result["summary"]}</div></div>',
                            unsafe_allow_html=True,
                        )
                        if _fc_flags:
                            for _ffl in _fc_flags:
                                _ffl_clr = {"high": "#f5b7b1", "medium": "#fdebd0"}.get(
                                    _ffl["severity"], "#cdd9e5"
                                )
                                st.markdown(
                                    f'<div style="display:flex;gap:8px;margin-bottom:4px;">'
                                    f'<span style="color:#e74c3c;font-size:14px;">⚑</span>'
                                    f'<div><span style="color:#f0f6fc;font-size:13px;font-weight:600;">'
                                    f'{_ffl["rule"]}</span><br>'
                                    f'<span style="color:{_ffl_clr};font-size:12px;">'
                                    f'{_ffl["detail"]}</span></div></div>',
                                    unsafe_allow_html=True,
                                )

                    # skip the rest of the condition-rendering code for this file
                    continue

                # === 1003 APPLICATION — structured data display ===
                if doc_type == "1003 Application":
                    data = result.get("extracted_data", {})
                    if not data:
                        st.warning("Could not extract structured data. The PDF may be a scanned image.")
                        continue

                    b = data.get("borrower", {})
                    cb = data.get("co_borrower", {})
                    emp = data.get("employment", {})
                    loan = data.get("loan", {})
                    missing = data.get("missing_required", [])

                    st.markdown("## 📝 1003 Application — Extracted Fields")
                    if missing:
                        st.markdown(
                            f'<div style="background:#3d1515;border-left:3px solid #e74c3c;border-radius:6px;'
                            f'padding:8px 14px;margin-bottom:12px;font-size:13px;color:#f5b7b1;">'
                            f'⚠️ <b>Missing required fields:</b> {", ".join(missing)}</div>',
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(
                            '<div style="background:#152a1e;border-left:3px solid #27ae60;border-radius:6px;'
                            'padding:8px 14px;margin-bottom:12px;font-size:13px;color:#a9dfbf;">'
                            '✅ All required fields found.</div>',
                            unsafe_allow_html=True,
                        )

                    _nf = '<i style="color:#6a56b8;">not found</i>'

                    def _field(label, value, editable_key=None):
                        dot = '<span style="color:#27ae60;font-weight:700;">●</span>' if value else \
                              '<span style="color:#e74c3c;font-weight:700;">●</span>'
                        disp = value if value else _nf
                        st.markdown(
                            f'<div style="display:flex;gap:8px;align-items:baseline;margin-bottom:2px;">'
                            f'{dot}<span style="color:#a89ec9;font-size:12px;min-width:140px;">{label}</span>'
                            f'<span style="color:#f0f6fc;font-size:13px;font-weight:600;">{disp}</span></div>',
                            unsafe_allow_html=True,
                        )

                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.markdown("**🧑 Borrower**")
                        _field("Name", b.get("name"))
                        _field("SSN", b.get("ssn"))
                        _field("Date of Birth", b.get("dob"))
                        _field("Phone", b.get("phone"))
                        _field("Email", b.get("email"))
                        _field("Present Address", b.get("present_address"))
                        _field("Previous Address", b.get("previous_address"))
                        st.markdown("---")
                        st.markdown("**💼 Employment**")
                        _field("Employer", emp.get("employer"))
                        _field("Position / Title", emp.get("position"))
                        _field("Employer Phone", emp.get("employer_phone"))
                        _field("Years on Job", emp.get("years_on_job"))
                        _field("Years in Field", emp.get("years_in_field"))
                        _field("Base Monthly Income", emp.get("base_monthly_income"))

                    with col_b:
                        st.markdown("**👥 Co-Borrower**")
                        _field("Name", cb.get("name"))
                        _field("SSN", cb.get("ssn"))
                        _field("Employer", cb.get("employer"))
                        st.markdown("---")
                        st.markdown("**🏠 Loan / Property**")
                        _field("Loan Amount", loan.get("amount"))
                        _field("Loan Purpose", loan.get("purpose"))
                        _field("Term", loan.get("term"))
                        _field("Interest Rate", loan.get("interest_rate"))
                        _field("Property Address", loan.get("property_address"))
                        _field("Property Use", loan.get("property_use"))

                    st.markdown("---")
                    pp_col1, pp_col2 = st.columns([2, 1])
                    with pp_col1:
                        st.caption("Push to Pipeline to create a tracked loan from this 1003.")
                    with pp_col2:
                        if st.button("➕ Push to Pipeline", key=f"push1003_{fkey}", use_container_width=True, type="primary"):
                            from crm import add_loan
                            add_loan(
                                loan_num=f"1003-{b.get('name', 'Unknown')[:8]}",
                                borrower=b.get("name", "Unknown"),
                                status="Pending",
                                due_date="",
                                missing_docs=", ".join(missing) if missing else "",
                                folder_path="",
                            )
                            st.success(f"✅ Added {b.get('name', 'borrower')} to pipeline.")
                    continue

                # === PURCHASE CONTRACT — structured data display ===
                if doc_type == "Purchase Contract":
                    data = result.get("extracted_data", {})
                    if not data:
                        st.warning("Could not extract structured data. The PDF may be a scanned image.")
                        continue

                    buyer = data.get("buyer", {})
                    seller = data.get("seller", {})
                    prop = data.get("property", {})
                    txn = data.get("transaction", {})
                    la = data.get("listing_agent", {})
                    sa = data.get("selling_agent", {})
                    title = data.get("title", {})
                    cont = data.get("contingencies", {})
                    addendums = data.get("addendums", [])
                    missing = data.get("missing_required", [])

                    st.markdown("## 📃 Purchase Contract — Extracted Fields")
                    if missing:
                        st.markdown(
                            f'<div style="background:#3d1515;border-left:3px solid #e74c3c;border-radius:6px;'
                            f'padding:8px 14px;margin-bottom:12px;font-size:13px;color:#f5b7b1;">'
                            f'⚠️ <b>Missing required fields:</b> {", ".join(missing)}</div>',
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(
                            '<div style="background:#152a1e;border-left:3px solid #27ae60;border-radius:6px;'
                            'padding:8px 14px;margin-bottom:12px;font-size:13px;color:#a9dfbf;">'
                            '✅ All required fields found.</div>',
                            unsafe_allow_html=True,
                        )

                    _nf2 = '<i style="color:#6a56b8;">not found</i>'

                    def _cfield(label, value):
                        dot = '<span style="color:#27ae60;font-weight:700;">●</span>' if value else \
                              '<span style="color:#e74c3c;font-weight:700;">●</span>'
                        disp = value if value else _nf2
                        st.markdown(
                            f'<div style="display:flex;gap:8px;align-items:baseline;margin-bottom:2px;">'
                            f'{dot}<span style="color:#a89ec9;font-size:12px;min-width:140px;">{label}</span>'
                            f'<span style="color:#f0f6fc;font-size:13px;font-weight:600;">{disp}</span></div>',
                            unsafe_allow_html=True,
                        )

                    pc1, pc2, pc3 = st.columns(3)
                    with pc1:
                        st.markdown("**🤝 Parties**")
                        _cfield("Buyer", buyer.get("name"))
                        _cfield("Buyer Phone", buyer.get("phone"))
                        _cfield("Buyer Email", buyer.get("email"))
                        _cfield("Seller", seller.get("name"))
                        _cfield("Seller Phone", seller.get("phone"))
                        st.markdown("---")
                        st.markdown("**🏠 Property**")
                        _cfield("Address", prop.get("address"))

                    with pc2:
                        st.markdown("**💵 Transaction**")
                        _cfield("Purchase Price", txn.get("purchase_price"))
                        _cfield("Closing Date", txn.get("closing_date"))
                        _cfield("Earnest Money", txn.get("earnest_money"))
                        _cfield("Down Payment", txn.get("down_payment"))
                        _cfield("Seller Concessions", txn.get("seller_concessions"))
                        st.markdown("---")
                        st.markdown("**🏛️ Title Company**")
                        _cfield("Company", title.get("company"))
                        _cfield("Contact", title.get("contact"))
                        _cfield("Phone", title.get("phone"))

                    with pc3:
                        st.markdown("**🏡 Listing Agent**")
                        _cfield("Name", la.get("name"))
                        _cfield("Brokerage", la.get("brokerage"))
                        _cfield("Phone", la.get("phone"))
                        _cfield("Email", la.get("email"))
                        st.markdown("---")
                        st.markdown("**🤝 Selling / Buyer's Agent**")
                        _cfield("Name", sa.get("name"))
                        _cfield("Brokerage", sa.get("brokerage"))
                        _cfield("Phone", sa.get("phone"))
                        _cfield("Email", sa.get("email"))

                    st.markdown("---")
                    st.markdown("**📋 Contingencies**")
                    conc1, conc2, conc3 = st.columns(3)
                    with conc1:
                        _cfield("Inspection", cont.get("inspection"))
                    with conc2:
                        _cfield("Appraisal", cont.get("appraisal"))
                    with conc3:
                        _cfield("Financing", cont.get("financing"))

                    if addendums:
                        st.markdown("**📎 Addendums / Riders**")
                        for add in addendums:
                            st.markdown(
                                f'<div style="color:#cdd9e5;font-size:12px;margin-left:12px;">• {add}</div>',
                                unsafe_allow_html=True,
                            )

                    st.markdown("---")
                    act_c1, act_c2, act_c3 = st.columns(3)
                    with act_c1:
                        if st.button("➕ Push to Pipeline", key=f"pushpc_{fkey}", use_container_width=True, type="primary"):
                            from crm import add_loan
                            add_loan(
                                loan_num=f"PC-{buyer.get('name', 'Unknown')[:8]}",
                                borrower=buyer.get("name", "Unknown"),
                                status="Pending",
                                due_date=txn.get("closing_date", ""),
                                missing_docs=", ".join(missing) if missing else "",
                                folder_path="",
                            )
                            st.success(f"✅ Added {buyer.get('name', 'buyer')} to pipeline.")
                    with act_c2:
                        if title.get("company") and st.button("✉️ Draft Title Email", key=f"titlemailpc_{fkey}", use_container_width=True):
                            title_body = (
                                f"Dear {title.get('contact') or title.get('company')} Team,\n\n"
                                f"Please be advised that we are working on the following transaction "
                                f"and require your assistance:\n\n"
                                f"  Property: {prop.get('address', 'See contract')}\n"
                                f"  Buyer: {buyer.get('name', '')}\n"
                                f"  Seller: {seller.get('name', '')}\n"
                                f"  Purchase Price: ${txn.get('purchase_price', '')}\n"
                                f"  Closing Date: {txn.get('closing_date', '')}\n\n"
                                f"Please provide your title commitment, CPL, wiring instructions, "
                                f"and preliminary CD at your earliest convenience.\n\n"
                                f"Thank you,\n[Your Name]"
                            )
                            st.text_area("Title Company Email — copy to Outlook:", title_body, height=260, key=f"titleemailout_{fkey}")
                    continue

                # === CONDITIONS (the main output — non-bank-statement docs) ===
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
                    """Compact condition row — expand for status, parties, notes, fetch, guidelines."""
                    import os as _os
                    cnum       = cond["num"]
                    party_key  = f"party_{fkey}_{cnum}"
                    notes_key  = f"notes_{fkey}_{cnum}"
                    status_key = f"cstatus_{fkey}_{cnum}"
                    fetch_key  = f"cfetch_{fkey}_{cnum}"
                    guide_key  = f"cguide_{fkey}_{cnum}"

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

                    short_desc = cond["desc"][:72] + ("…" if len(cond["desc"]) > 72 else "")
                    exp_label  = f"{status_info['emoji']} #{cnum}  {short_desc}"

                    col_chk, col_exp = st.columns([1, 11])
                    with col_chk:
                        checked = st.checkbox("", key=f"chk_{fkey}_{cnum}",
                                              label_visibility="collapsed")
                    with col_exp:
                        with st.expander(exp_label, expanded=False):
                            # ── Status buttons ───────────────────────────
                            st.markdown("**Status:**")
                            sb = st.columns(len(COND_STATUSES))
                            for i, (sname, sinfo) in enumerate(COND_STATUSES.items()):
                                with sb[i]:
                                    active = "✓ " if cur_status == sname else ""
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
                                "Responsible parties", PARTY_OPTIONS,
                                default=saved_parties, key=party_key,
                                placeholder="Add parties...",
                            )
                            if new_parties:
                                st.markdown(
                                    " ".join(_party_badge(p) for p in new_parties),
                                    unsafe_allow_html=True,
                                )

                            # ── Notes ────────────────────────────────────
                            st.text_input("Update / notes", key=notes_key,
                                          placeholder="Add update or note...")
                            if saved_notes:
                                st.caption(f"💬 {saved_notes}")

                            st.markdown("---")

                            # ── Detect if condition is bank-statement-related ──
                            _bs_keywords = {
                                "bank statement", "bank stmt", "checking account",
                                "savings account", "deposit", "bank", "statement",
                                "60 days", "2 months", "3 months",
                            }
                            _desc_lower = cond["desc"].lower()
                            _is_bs_cond = any(kw in _desc_lower for kw in _bs_keywords)

                            # ── Fetch from Folder ────────────────────────
                            if _is_bs_cond:
                                fa, fb, fc = st.columns([1, 1, 1])
                            else:
                                fa, fb = st.columns([1, 1])
                                fc = None

                            with fa:
                                fetch_btn = st.button("📂 Fetch from Folder",
                                    key=f"fetchbtn_{fkey}_{cnum}", use_container_width=True)
                            with fb:
                                guide_btn = st.button("📋 Check Guidelines",
                                    key=f"guidebtn_{fkey}_{cnum}", use_container_width=True)
                            if fc:
                                with fc:
                                    bs_fetch_btn = st.button(
                                        "🏦 Find & Analyze Bank Stmt",
                                        key=f"bsfetchbtn_{fkey}_{cnum}",
                                        use_container_width=True,
                                        help="Search borrower folder for bank statement PDFs and run the 50-rule analysis.",
                                    )
                            else:
                                bs_fetch_btn = False

                            if fetch_btn:
                                st.session_state[f"show_cfetch_{fkey}_{cnum}"] = True
                            if bs_fetch_btn:
                                st.session_state[f"show_bsfetch_{fkey}_{cnum}"] = True

                            # ── Standard fetch flow ────────────────────
                            if st.session_state.get(f"show_cfetch_{fkey}_{cnum}"):
                                folder_path = st.text_input(
                                    "Folder path:",
                                    value=st.session_state.get("last_fetch_folder", ""),
                                    key=f"cfolder_{fkey}_{cnum}",
                                    placeholder=r"C:\Users\...\BorrowerName",
                                )
                                sc1, sc2 = st.columns([1, 3])
                                with sc1:
                                    do_search = st.button("Search",
                                        key=f"csearch_{fkey}_{cnum}", use_container_width=True)
                                with sc2:
                                    if st.button("Cancel", key=f"ccancel_{fkey}_{cnum}"):
                                        st.session_state[f"show_cfetch_{fkey}_{cnum}"] = False
                                        st.rerun()
                                if do_search and folder_path:
                                    st.session_state["last_fetch_folder"] = folder_path
                                    if not _os.path.isdir(folder_path):
                                        st.error(f"Folder not found: {folder_path}")
                                    else:
                                        from folder_search import scan_folder
                                        prog = st.progress(0, text="Scanning...")
                                        res = scan_folder(folder_path, [cond], threshold=60,
                                            progress_callback=lambda p, m: prog.progress(min(p,100), text=m))
                                        st.session_state[fetch_key] = res
                                        st.session_state[f"show_cfetch_{fkey}_{cnum}"] = False

                            # ── Bank statement fetch + analyze flow ─────
                            if st.session_state.get(f"show_bsfetch_{fkey}_{cnum}"):
                                from crm import get_all_loans as _pipe_loans
                                _def_bs = st.session_state.get("last_fetch_folder", "")
                                if not _def_bs:
                                    for _pl2 in _pipe_loans():
                                        _fp2 = _pl2.get("folder_path", "")
                                        if _fp2 and _os.path.isdir(_fp2):
                                            _def_bs = _fp2
                                            break

                                bsf_path = st.text_input(
                                    "Borrower folder:",
                                    value=_def_bs,
                                    key=f"bsfolder_{fkey}_{cnum}",
                                    placeholder=r"C:\Loans\SmithJohn",
                                )
                                bsc1, bsc2, bsc3 = st.columns([2, 2, 1])
                                with bsc1:
                                    bss_scope = st.selectbox(
                                        "Scope",
                                        ["Bank statements only", "All PDFs"],
                                        key=f"bsscope_{fkey}_{cnum}",
                                        label_visibility="collapsed",
                                    )
                                with bsc2:
                                    pass
                                with bsc3:
                                    bss_go = st.button(
                                        "Search", key=f"bsgo_{fkey}_{cnum}",
                                        use_container_width=True,
                                    )
                                if bss_go and bsf_path:
                                    st.session_state["last_fetch_folder"] = bsf_path
                                    from folder_search import find_bank_statements
                                    _bss = "bank_only" if "only" in bss_scope else "all_pdfs"
                                    with st.spinner("Searching for bank statements..."):
                                        _bs_results = find_bank_statements(bsf_path, scope=_bss)
                                    st.session_state[f"bshits_{fkey}_{cnum}"] = _bs_results

                                _bs_hits2 = st.session_state.get(f"bshits_{fkey}_{cnum}", [])
                                if _bs_hits2:
                                    for _bhi, _bht in enumerate(_bs_hits2):
                                        _conf_c = "#27ae60" if _bht["score"] >= 70 else (
                                            "#f1c40f" if _bht["score"] >= 40 else "#e74c3c"
                                        )
                                        _bhc1, _bhc2, _bhc3, _bhc4 = st.columns([3, 2, 1, 1])
                                        with _bhc1:
                                            st.markdown(
                                                f'<div style="font-weight:600;color:#f0f6fc;font-size:12px;">'
                                                f'{_bht["file_name"]}</div>'
                                                f'<div style="font-size:11px;color:#a89ec9;">'
                                                f'{_bht["snippet"][:100]}</div>',
                                                unsafe_allow_html=True,
                                            )
                                        with _bhc2:
                                            st.markdown(
                                                f'<div style="font-size:11px;color:{_conf_c};">'
                                                f'{_bht["score"]}% match · {_bht["reason"][:40]}</div>',
                                                unsafe_allow_html=True,
                                            )
                                        with _bhc3:
                                            if st.button("Analyze", key=f"bsana_{fkey}_{cnum}_{_bhi}",
                                                         use_container_width=True):
                                                st.session_state[f"bsana_file_{fkey}_{cnum}"] = _bht["file_path"]
                                        with _bhc4:
                                            if st.button("Read", key=f"bsread_{fkey}_{cnum}_{_bhi}",
                                                         use_container_width=True):
                                                st.session_state["reader_open_file"] = {
                                                    "name": _bht["file_name"],
                                                    "path": _bht["file_path"],
                                                    "ext": ".pdf",
                                                }
                                                st.session_state["page"] = "reader"
                                                st.rerun()

                                        # Inline analysis
                                        if st.session_state.get(f"bsana_file_{fkey}_{cnum}") == _bht["file_path"]:
                                            with st.spinner(f"Analyzing {_bht['file_name']}..."):
                                                from pypdf import PdfReader as _PRx
                                                from ai_engine import check_bank_rules as _cbrx
                                                try:
                                                    _rdrx = _PRx(_bht["file_path"])
                                                    _txtx = "\n".join(
                                                        (p.extract_text() or "") for p in _rdrx.pages
                                                    )
                                                    _bkout = _cbrx(_txtx)
                                                except Exception as _ex:
                                                    _bkout = ""
                                                    st.error(str(_ex))

                                            if _bkout:
                                                _rawx = _bkout.strip().split("\n")
                                                for _rx in _rawx:
                                                    _ptx = _rx.split("|")
                                                    _tgx = _ptx[0] if _ptx else ""
                                                    if _tgx == "SUMMARY":
                                                        _ox, _fx, _mx, _ix = int(_ptx[1]), int(_ptx[2]), int(_ptx[3]), int(_ptx[4])
                                                        st.markdown(
                                                            f'<div style="font-size:12px;color:#cdd9e5;padding:4px 0;">'
                                                            f'✅ {_ox} Passed &nbsp; 🚩 {_fx} Flagged &nbsp; '
                                                            f'⚠️ {_mx} Missing &nbsp; ℹ️ {_ix} Info</div>',
                                                            unsafe_allow_html=True,
                                                        )
                                                    elif _tgx == "FLAG":
                                                        st.markdown(
                                                            f'<div style="background:#3d1515;border-left:2px solid #e74c3c;'
                                                            f'border-radius:4px;padding:4px 8px;margin-bottom:2px;font-size:11px;color:#f0f6fc;">'
                                                            f'🚩 {_ptx[2] if len(_ptx)>2 else ""} — {_ptx[3] if len(_ptx)>3 else ""}</div>',
                                                            unsafe_allow_html=True,
                                                        )
                                                    elif _tgx == "MISSING":
                                                        st.markdown(
                                                            f'<div style="background:#3d3015;border-left:2px solid #f1c40f;'
                                                            f'border-radius:4px;padding:4px 8px;margin-bottom:2px;font-size:11px;color:#f0f6fc;">'
                                                            f'⚠ {_ptx[2] if len(_ptx)>2 else ""} — {_ptx[3] if len(_ptx)>3 else ""}</div>',
                                                            unsafe_allow_html=True,
                                                        )

                            # Fetch results for this condition
                            if st.session_state.get(fetch_key):
                                fr = st.session_state[fetch_key]
                                matches = fr.get(cond["num"], {}).get("matches", [])
                                if matches:
                                    for m in matches:
                                        score = m["score"]
                                        dot = "🟢" if score >= 80 else ("🟡" if score >= 65 else "🔴")
                                        pages_str = f" | Pages: {', '.join(str(p) for p in m['matched_pages'])}" if m["matched_pages"] else ""
                                        st.markdown(f"{dot} **{m['file_name']}** — {m['match_type']} ({score}%){pages_str}")
                                        st.caption(f"📁 {m['file_path']}")
                                        if m.get("snippet"):
                                            st.text(m["snippet"][:180])
                                else:
                                    st.info("No matching files found for this condition.")
                                if st.button("Clear", key=f"clrfetch_{fkey}_{cnum}"):
                                    st.session_state[fetch_key] = None
                                    st.rerun()

                            # ── Check Guidelines ─────────────────────────
                            if guide_btn:
                                from guidelines import check_conditions_against_guidelines, get_available_guidelines
                                available = get_available_guidelines()
                                if not available:
                                    st.error("No guideline PDFs found on Desktop.")
                                else:
                                    gprog = st.progress(0, text="Searching guidelines...")
                                    gres = check_conditions_against_guidelines(
                                        [cond],
                                        progress_callback=lambda p, m: gprog.progress(min(p,100), text=m),
                                    )
                                    st.session_state[guide_key] = gres

                            if st.session_state.get(guide_key):
                                gr = st.session_state[guide_key]
                                refs = gr.get(cond["num"], {}).get("guidelines", [])
                                if refs:
                                    for ref in refs:
                                        score = ref["score"]
                                        dot = "🟢" if score >= 80 else ("🟡" if score >= 65 else "🔴")
                                        sec = f" | {ref['section']}" if ref.get("section") else ""
                                        st.markdown(f"{dot} **{ref['source']}** — Page {ref['page']}{sec} ({score}%)")
                                        st.container(border=True).markdown(ref["excerpt"][:400])
                                else:
                                    st.info("No guideline references found.")
                                if st.button("Clear", key=f"clrguide_{fkey}_{cnum}"):
                                    st.session_state[guide_key] = None
                                    st.rerun()

                    return checked, cur_status, saved_parties

                # ── Draft Email — always visible, above conditions ─────────
                st.markdown("### ✉️ Draft Email")
                # Read which conditions are checked from session state (persists across reruns)
                pre_selected = []
                for cond in condition_rows:
                    if st.session_state.get(f"chk_{fkey}_{cond['num']}", False):
                        pk = f"party_{fkey}_{cond['num']}"
                        sp = st.session_state.get(pk, [cond["party"]])
                        if not isinstance(sp, list):
                            sp = [cond["party"]]
                        sp = [p for p in sp if p in PARTY_OPTIONS] or ["Borrower"]
                        pre_selected.append({**cond, "party": sp[0], "all_parties": sp})

                em_c1, em_c2, em_c3 = st.columns([2, 2, 3])
                with em_c1:
                    email_lang = st.selectbox("Language", ["English", "Spanish"],
                                              key=f"lang_{fkey}")
                with em_c2:
                    flat_parties = []
                    for c in pre_selected:
                        for p in c.get("all_parties", [c["party"]]):
                            if p not in flat_parties:
                                flat_parties.append(p)
                    if not flat_parties:
                        flat_parties = PARTY_OPTIONS
                    recipient = st.selectbox("Send to", flat_parties, key=f"recip_{fkey}")
                with em_c3:
                    if pre_selected:
                        st.markdown(
                            f'<div style="padding-top:8px; font-size:13px; color:#cdd9e5;">'
                            f'✅ {len(pre_selected)} condition(s) checked</div>',
                            unsafe_allow_html=True,
                        )
                    else:
                        st.caption("Check conditions below to include them")

                _draft_col1, _draft_col2 = st.columns([1, 1])
                with _draft_col1:
                    draft_clicked = st.button("✉️ Draft Email", key=f"draft_{fkey}",
                                              type="primary", use_container_width=True)
                with _draft_col2:
                    ollama_draft_clicked = st.button("🤖 Draft with Ollama", key=f"odraft_{fkey}",
                                                     use_container_width=True)

                if draft_clicked:
                    from ai_engine import draft_email
                    if pre_selected:
                        cond_lines = [f"- Condition #{c['num']}: {c['desc']}" for c in pre_selected]
                    else:
                        cond_lines = ["(No conditions selected — add details manually)"]
                    email_text = draft_email("\n".join(cond_lines), recipient, email_lang)
                    st.container(border=True).markdown(email_text)
                    st.caption("Copy and paste into your email client. Review before sending.")

                if ollama_draft_clicked:
                    import ollama_client as _oc
                    if not _oc.is_enabled():
                        st.warning("Ollama is disabled. Enable it in the 🤖 Ollama page.")
                    else:
                        conds_for_ollama = pre_selected if pre_selected else []
                        with st.spinner("Drafting with Ollama…"):
                            _oe_text, _oe_log = _oc.draft_email_enhanced(
                                conds_for_ollama, recipient, email_lang
                            )
                        if _oe_text:
                            st.container(border=True).markdown(_oe_text)
                            st.caption(f"🤖 Ollama draft · {_oe_log.split('|')[-1].strip() if '|' in _oe_log else ''}")
                        else:
                            st.info("Ollama didn't return a draft — is it running? Check the 🤖 Ollama page.")

                st.markdown("---")
                st.markdown("### 📋 Conditions")

                # ── Split into active and cleared ──────────────────────────
                STATUS_PRIORITY = {
                    "Important":      0,
                    "Needed":         1,
                    "Requested":      2,
                    "Ready to Clear": 3,
                }
                active_conds  = []
                cleared_conds = []
                for cond in condition_rows:
                    sk = f"cstatus_{fkey}_{cond['num']}"
                    if st.session_state.get(sk, "Needed") == "Cleared":
                        cleared_conds.append(cond)
                    else:
                        active_conds.append(cond)

                # Sort active: 1st by status priority, 2nd by primary party name
                def _sort_key(cond):
                    sk = f"cstatus_{fkey}_{cond['num']}"
                    status = st.session_state.get(sk, "Needed")
                    pk = f"party_{fkey}_{cond['num']}"
                    parties = st.session_state.get(pk, [cond.get("party", "Borrower")])
                    primary_party = parties[0] if isinstance(parties, list) and parties else cond.get("party", "Borrower")
                    return (STATUS_PRIORITY.get(status, 99), primary_party)

                active_conds.sort(key=_sort_key)

                # Count per status for header summary
                status_counts = {}
                for cond in condition_rows:
                    sk  = f"cstatus_{fkey}_{cond['num']}"
                    s   = st.session_state.get(sk, "Needed")
                    status_counts[s] = status_counts.get(s, 0) + 1
                summary_parts = [
                    f"{COND_STATUSES[s]['emoji']} {status_counts[s]} {s}"
                    for s in ["Important", "Needed", "Requested", "Ready to Clear", "Cleared"]
                    if s in status_counts
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

                # (Fetch and Guidelines are now inside each condition expander above)

                # ── Fraud Check — available for W-2, pay stub, 1003 scans ───
                st.markdown("---")
                _fc2_key = f"fraud_on_cond_{fkey}"
                _fc2c1, _fc2c2 = st.columns([1, 4])
                with _fc2c1:
                    _fraud_on2 = st.toggle("🔍 Fraud Check", key=_fc2_key, value=False)
                with _fc2c2:
                    if _fraud_on2:
                        st.caption("Scanning for SSN mismatches, zero withholding, uniform pay, "
                                   "date gaps, round-dollar income.")
                if _fraud_on2:
                    from fraud_check import check as _fc2
                    _fc2_bytes  = uploaded_file.getvalue()
                    _fc2_result = _fc2(_fc2_bytes, doc_type)
                    _fc2_risk   = _fc2_result["risk_level"]
                    _fc2_bdr    = {"high": "#e74c3c", "medium": "#f1c40f", "low": "#27ae60"}[_fc2_risk]
                    _fc2_bg     = {"high": "#3d1515", "medium": "#2d2808", "low": "#152a1e"}[_fc2_risk]
                    st.markdown(
                        f'<div style="background:{_fc2_bg};border-left:4px solid {_fc2_bdr};'
                        f'border-radius:8px;padding:10px 16px;margin:8px 0;">'
                        f'<div style="font-size:14px;font-weight:700;color:#f0f6fc;">'
                        f'{_fc2_result["summary"]}</div></div>',
                        unsafe_allow_html=True,
                    )
                    for _ffl2 in _fc2_result.get("flags", []):
                        _ffl2_clr = {"high": "#f5b7b1", "medium": "#fdebd0"}.get(
                            _ffl2["severity"], "#cdd9e5"
                        )
                        st.markdown(
                            f'<div style="display:flex;gap:8px;margin-bottom:4px;">'
                            f'<span style="color:#e74c3c;font-size:14px;">⚑</span>'
                            f'<div><span style="color:#f0f6fc;font-size:13px;font-weight:600;">'
                            f'{_ffl2["rule"]}</span><br>'
                            f'<span style="color:{_ffl2_clr};font-size:12px;">'
                            f'{_ffl2["detail"]}</span></div></div>',
                            unsafe_allow_html=True,
                        )

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

    import json as _json

    st.markdown("## 🗂️ My Pipeline")
    st.caption("Track every loan — color-coded by status, one-click actions.")

    from db import get_all_users
    all_users = get_all_users()
    user_names = ["(Unassigned)"] + [
        u.get("display_name") or u["email"] for u in all_users
    ]
    my_name = st.session_state.get("user_name", "")

    # ── Top action bar ──────────────────────────────────────────────────────
    tb1, tb2, tb3, tb4, tb5 = st.columns([2, 2, 2, 1, 2])
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
        my_loans_only = st.checkbox("My loans", key="pipeline_myloans")
    with tb5:
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
            fa1, fa2 = st.columns(2)
            with fa1:
                # Default assign-to the current user
                default_idx = user_names.index(my_name) if my_name in user_names else 0
                new_assigned = st.selectbox(
                    "Assign To", user_names, index=default_idx, key="pl_new_assigned",
                )

            sa1, sa2 = st.columns([1, 4])
            with sa1:
                if st.button("Save Loan", use_container_width=True, key="pl_save_btn"):
                    if new_loan_num and new_borrower:
                        assigned_val = "" if new_assigned == "(Unassigned)" else new_assigned
                        add_loan(
                            new_loan_num, new_borrower, new_status,
                            str(new_due), new_missing, new_folder,
                            created_by=my_name,
                            assigned_to=assigned_val,
                        )
                        st.session_state.pipeline_add_open = False
                        st.rerun()
                    else:
                        st.error("Loan # and Borrower Name are required.")
            with sa2:
                if st.button("Cancel", key="pl_cancel_btn"):
                    st.session_state.pipeline_add_open = False
                    st.rerun()

    # ── Inbox (incoming shared loans) ────────────────────────────────────────
    from sharing import scan_inbox, dismiss_from_inbox, inbox_count
    inbox_items = scan_inbox()
    if inbox_items:
        n = len(inbox_items)
        with st.expander(f"📬 Inbox — {n} shared loan{'s' if n != 1 else ''} waiting", expanded=True):
            st.caption("Loans shared directly with you by teammates. Accept to add to your pipeline.")
            for item in inbox_items:
                ib1, ib2, ib3, ib4 = st.columns([3, 2, 1, 1])
                share_id = item.get("share_id", "?")
                with ib1:
                    st.markdown(
                        f"<div style='font-weight:700;color:#f0f6fc;'>"
                        f"#{item.get('loan_num','—')} &nbsp; {item.get('borrower','—')}</div>"
                        f"<div style='font-size:12px;color:#a89ec9;'>"
                        f"From: {item.get('last_updated_by','?')} &nbsp;·&nbsp; "
                        f"Updated: {item.get('last_updated','')[:10]}</div>",
                        unsafe_allow_html=True,
                    )
                with ib2:
                    shared_with_list = ", ".join(item.get("shared_with", []))
                    st.markdown(
                        f"<div style='font-size:12px;color:#cdd9e5;'>"
                        f"Status: <b>{item.get('status','—')}</b><br>"
                        f"Shared with: {shared_with_list or 'you'}</div>",
                        unsafe_allow_html=True,
                    )
                with ib3:
                    if st.button("✅ Accept", key=f"inbox_accept_{share_id}", use_container_width=True):
                        # Import into local pipeline
                        add_loan(
                            loan_num=item.get("loan_num", ""),
                            borrower=item.get("borrower", ""),
                            status=item.get("status", "Pending"),
                            due_date=item.get("due_date", ""),
                            missing_docs=item.get("missing_docs", ""),
                            folder_path=item.get("folder_path", ""),
                            created_by=item.get("owner", ""),
                            assigned_to=my_name,
                        )
                        # Store share metadata on the loan for "Send Update"
                        all_local = get_all_loans()
                        for ln in all_local:
                            if ln.get("loan_num") == item.get("loan_num"):
                                from crm import update_loan as _upd
                                _upd(ln["id"],
                                     share_id=item["share_id"],
                                     share_owner=item.get("owner", ""),
                                     share_owner_inbox=item.get("owner_inbox", ""),
                                     share_with=_json.dumps(item.get("shared_with", [])),
                                     share_version=item.get("version", 1))
                                break
                        dismiss_from_inbox(item["_file"])
                        st.rerun()
                with ib4:
                    if st.button("Dismiss", key=f"inbox_dismiss_{share_id}", use_container_width=True):
                        dismiss_from_inbox(item["_file"])
                        st.rerun()
                st.markdown('<div style="height:2px;border-bottom:1px solid #4a3a8a;"></div>',
                            unsafe_allow_html=True)

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
    if my_loans_only and my_name:
        loans = [l for l in loans
                 if l.get("assigned_to") == my_name
                 or l.get("created_by") == my_name]

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

        created_by = loan.get("created_by", "")
        assigned_to = loan.get("assigned_to", "")
        team_line = ""
        if created_by or assigned_to:
            parts = []
            if created_by:
                parts.append(f"➕ {created_by}")
            if assigned_to:
                parts.append(f"👤 {assigned_to}")
            team_line = f'<br><span style="font-size:11px;color:#a89ec9;">{" &nbsp;·&nbsp; ".join(parts)}</span>'

        st.markdown(
            f'<div class="loan-card" style="border-left: 4px solid {border_color};">'
            f'<span class="loan-num">#{loan.get("loan_num","—")}</span> &nbsp;'
            f'<span class="loan-name">{loan.get("borrower","—")}</span> &nbsp;'
            f'{_status_chip(status)}'
            f'{team_line}'
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
            n_col, r_col = st.columns([3, 2])
            with n_col:
                notes = st.text_input(
                    "Notes:", value=loan.get("notes", ""),
                    key=f"notes_{lid}", label_visibility="collapsed",
                    placeholder="Notes...",
                )
            with r_col:
                cur_assigned = loan.get("assigned_to", "")
                cur_idx = user_names.index(cur_assigned) if cur_assigned in user_names else 0
                new_assignee = st.selectbox(
                    "Assign:", user_names, index=cur_idx,
                    key=f"assign_{lid}", label_visibility="collapsed",
                )
            nc1, nc2, nc3 = st.columns([1, 1, 1])
            with nc1:
                if st.button("Save Notes", key=f"nsave_{lid}", use_container_width=True):
                    update_loan(lid, notes=notes)
                    st.rerun()
            with nc2:
                if st.button("Reassign", key=f"rassign_{lid}", use_container_width=True):
                    val = "" if new_assignee == "(Unassigned)" else new_assignee
                    update_loan(lid, assigned_to=val)
                    st.rerun()
            with nc3:
                if st.button("🗑️ Remove", key=f"del_{lid}", use_container_width=True):
                    delete_loan(lid)
                    st.rerun()

        # ── Share this loan ──────────────────────────────────────────────────
        from sharing import get_members, share_loan as _share_loan, send_update as _send_update
        team_members = get_members()
        team_names = [m["name"] for m in team_members]

        # Show "Send Update" if this loan was shared with us
        is_shared_loan = bool(loan.get("share_id"))
        share_key = f"share_open_{lid}"

        sh1, sh2 = st.columns([1, 6])
        with sh1:
            lbl = "📤 Send Update" if is_shared_loan else "🔗 Share"
            if team_names and st.button(lbl, key=f"sharebtn_{lid}", use_container_width=True):
                st.session_state[share_key] = not st.session_state.get(share_key, False)

        if st.session_state.get(share_key) and team_names:
            with st.container():
                if is_shared_loan:
                    # Send update back to owner + shared_with
                    st.markdown(
                        "<div style='font-size:13px;color:#cdd9e5;margin-bottom:6px;'>"
                        f"Send updated status for <b>#{loan.get('loan_num')}</b> back to "
                        f"<b>{loan.get('share_owner','owner')}</b> and shared teammates."
                        "</div>",
                        unsafe_allow_html=True,
                    )
                    if st.button("Send Update Now", key=f"sendupd_{lid}", type="primary"):
                        shared_meta = {
                            "share_id": loan.get("share_id"),
                            "loan_num": loan.get("loan_num", ""),
                            "borrower": loan.get("borrower", ""),
                            "owner": loan.get("share_owner", ""),
                            "owner_inbox": loan.get("share_owner_inbox", ""),
                            "shared_with": _json.loads(loan.get("share_with", "[]")),
                            "version": loan.get("share_version", 1),
                        }
                        updates = {
                            "status": loan.get("status"),
                            "missing_docs": loan.get("missing_docs", ""),
                            "notes": loan.get("notes", ""),
                            "due_date": loan.get("due_date", ""),
                        }
                        results = _send_update(shared_meta, my_name, updates)
                        ok = [k for k, v in results.items() if v == "ok"]
                        fail = [k for k, v in results.items() if v != "ok"]
                        if ok:
                            st.success(f"Sent to: {', '.join(ok)}")
                        if fail:
                            st.error(f"Failed: {', '.join(fail)}")
                        st.session_state[share_key] = False
                else:
                    # Share a new loan with selected teammates
                    st.markdown(
                        "<div style='font-size:13px;color:#cdd9e5;margin-bottom:6px;'>"
                        f"Share <b>#{loan.get('loan_num')} — {loan.get('borrower')}</b> with:</div>",
                        unsafe_allow_html=True,
                    )
                    sp1, sp2 = st.columns([3, 1])
                    with sp1:
                        selected_recipients = st.multiselect(
                            "Select teammates:",
                            options=team_names,
                            key=f"share_who_{lid}",
                            label_visibility="collapsed",
                        )
                    with sp2:
                        if st.button("Share Now", key=f"share_now_{lid}",
                                     type="primary", use_container_width=True):
                            if selected_recipients:
                                results = _share_loan(loan, selected_recipients, my_name)
                                ok = [k for k, v in results.items() if v == "ok"]
                                fail = {k: v for k, v in results.items() if v != "ok"}
                                if ok:
                                    st.success(f"✅ Shared with: {', '.join(ok)}")
                                for name, err in fail.items():
                                    st.error(f"❌ {name}: {err}")
                                st.session_state[share_key] = False
                            else:
                                st.warning("Pick at least one person to share with.")

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


def show_team_page():
    """Team setup: configure your inbox folder and add team members."""
    from sharing import (
        get_team_config, save_team_config, get_members,
        add_member, remove_member, set_my_inbox, test_inbox,
    )
    from db import ROLE_OPTIONS

    st.markdown("## 👥 My Team")
    st.caption(
        "Set your inbox folder so teammates can share loans directly with you. "
        "Add each person once — after that, sharing is one click."
    )

    config = get_team_config()

    # ── My Inbox Setup ──────────────────────────────────────────────────────
    st.markdown("### My Inbox Folder")
    st.markdown(
        "This is **your private drop folder**. When someone shares a loan with you, "
        "the app writes a file here. Give this path to anyone who wants to share with you."
    )

    ib1, ib2 = st.columns([4, 1])
    with ib1:
        my_inbox = st.text_input(
            "My Inbox Path",
            value=config.get("my_inbox", ""),
            placeholder=r"e.g.  C:\Users\YourName\GopherInbox  or  \\OFFICE-NAS\Shared\YourName",
            label_visibility="collapsed",
        )
    with ib2:
        if st.button("Test & Save", use_container_width=True, key="test_inbox_btn"):
            ok, msg = test_inbox(my_inbox)
            my_name = st.session_state.get("user_name", "")
            set_my_inbox(my_inbox, name=my_name)
            if ok:
                st.success(msg)
            else:
                st.error(f"Can't reach folder: {msg}")

    st.markdown(
        f"<div style='font-size:12px;color:#a89ec9;margin-top:4px;'>"
        f"📋 Share this path with teammates so they can drop files for you: "
        f"<code style='color:#b794f4;'>{config.get('my_inbox','(not set)')}</code>"
        f"</div>",
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # ── Add Team Member ─────────────────────────────────────────────────────
    st.markdown("### Add a Team Member")
    st.caption(
        "Add each person you work with. You'll need their inbox folder path — "
        "just ask them to open this page and copy their path."
    )

    with st.form("add_member_form"):
        am1, am2, am3 = st.columns([2, 2, 3])
        with am1:
            new_name = st.text_input("Their Name", placeholder="e.g. Jane Garcia")
        with am2:
            new_role = st.selectbox("Their Role", ROLE_OPTIONS)
        with am3:
            new_inbox = st.text_input(
                "Their Inbox Path",
                placeholder=r"e.g. C:\Users\Jane\GopherInbox  or  \\JANES-PC\GopherInbox",
            )
        submitted = st.form_submit_button("Add to Team", use_container_width=True)
        if submitted:
            if not new_name.strip() or not new_inbox.strip():
                st.error("Name and inbox path are both required.")
            else:
                ok, msg = test_inbox(new_inbox)
                add_member(new_name.strip(), new_role, new_inbox.strip())
                if ok:
                    st.success(f"✅ {new_name} added — inbox is reachable!")
                else:
                    st.warning(
                        f"⚠️ {new_name} added, but can't reach their inbox right now: {msg}. "
                        "You can still add them and share when the folder is accessible."
                    )
                st.rerun()

    st.markdown("---")

    # ── Current Team List ───────────────────────────────────────────────────
    members = get_members()
    st.markdown(f"### My Team &nbsp; <span style='font-size:13px;color:#a89ec9;'>({len(members)} people)</span>",
                unsafe_allow_html=True)

    if not members:
        st.info("No team members yet. Add your first teammate above.")
        return

    for m in members:
        with st.container():
            mc1, mc2, mc3, mc4 = st.columns([2, 2, 4, 1])
            with mc1:
                st.markdown(
                    f"<div style='font-weight:700;color:#f0f6fc;font-size:14px;'>{m['name']}</div>",
                    unsafe_allow_html=True,
                )
            with mc2:
                st.markdown(
                    f"<div style='color:#b794f4;font-size:13px;'>{m.get('role','')}</div>",
                    unsafe_allow_html=True,
                )
            with mc3:
                inbox_path = m.get("inbox", "")
                reachable = os.path.isdir(inbox_path) if inbox_path else False
                dot = "🟢" if reachable else "🔴"
                st.markdown(
                    f"<div style='font-size:12px;color:#a89ec9;'>{dot} "
                    f"<code style='color:#cdd9e5;'>{inbox_path or '(no path)'}</code></div>",
                    unsafe_allow_html=True,
                )
            with mc4:
                if st.button("Remove", key=f"rm_{m['name']}", use_container_width=True):
                    remove_member(m["name"])
                    st.rerun()
            st.markdown('<div style="height:4px;border-bottom:1px solid #4a3a8a;margin-bottom:4px;"></div>',
                        unsafe_allow_html=True)


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


def show_email_watch_page():
    """Email inbox watcher — setup, toggle, and matched attachment inbox."""
    import email_watch as ew

    st.markdown("## 📧 Email Watch")
    st.caption(
        "Watch your inbox for new PDF attachments. When one arrives, the app reads it, "
        "tries to match the borrower name to your pipeline, and asks what to do with it. "
        "100% local — your credentials never leave your computer."
    )

    cfg = ew.get_config()
    status = ew.get_status()

    # ── Status card ──────────────────────────────────────────────────────────
    if status["running"]:
        st.markdown(
            f'<div style="background:#152a1e;border-left:4px solid #27ae60;border-radius:8px;'
            f'padding:10px 16px;margin-bottom:16px;">'
            f'<span style="font-size:14px;font-weight:700;color:#a9dfbf;">🟢 Watching inbox</span>'
            f'<span style="font-size:12px;color:#7dcea0;margin-left:12px;">'
            f'Last check: {status["last_time"] or "—"} · {status["last_status"]}</span></div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<div style="background:#1e1645;border-left:4px solid #4a3a8a;border-radius:8px;'
            f'padding:10px 16px;margin-bottom:16px;">'
            f'<span style="font-size:14px;font-weight:700;color:#a89ec9;">⚫ Inbox watch is off</span>'
            + (f'<span style="font-size:12px;color:#6a56b8;margin-left:12px;">'
               f'Last check: {status["last_time"]} · {status["last_status"]}</span>'
               if status["last_time"] else "")
            + '</div>',
            unsafe_allow_html=True,
        )

    # ── Toggle ───────────────────────────────────────────────────────────────
    t1, t2 = st.columns([1, 4])
    with t1:
        if status["running"]:
            if st.button("⏹ Stop Watching", use_container_width=True, type="primary"):
                ew.stop()
                st.success("Inbox watch stopped.")
                st.rerun()
        else:
            if st.button("▶ Start Watching", use_container_width=True, type="primary"):
                try:
                    ew.start()
                    st.success("Inbox watch started — checking every "
                               f"{cfg.get('interval_minutes', 5)} minutes.")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Could not start: {exc}  ·  Set up your credentials below first.")

    st.markdown("---")

    # ── Pending matches ───────────────────────────────────────────────────────
    matches = ew.get_matches()
    if matches:
        st.markdown(f"### 📬 {len(matches)} New Attachment(s) — Waiting for Action")
        for i, m in enumerate(matches):
            conf  = m.get("confidence", 0)
            sugg  = m.get("suggestion", "unknown")
            bname = m.get("borrower") or "Unknown borrower"
            lnum  = m.get("loan_num", "")

            if sugg == "match":
                conf_color = "#27ae60"
                conf_label = f"✅ Matched — {bname} · Loan {lnum} ({conf}% confidence)"
            elif sugg == "possible":
                conf_color = "#f1c40f"
                conf_label = f"⚠️ Possible match — {bname} · Loan {lnum} ({conf}%)"
            else:
                conf_color = "#e74c3c"
                conf_label = "❓ No pipeline match found"

            with st.expander(f"📄 {m['filename']}  ·  {m.get('received', '')}  ·  {conf_label}", expanded=True):
                mc1, mc2 = st.columns([3, 1])
                with mc1:
                    st.markdown(
                        f'<div style="font-size:12px;color:#a89ec9;">From: {m["sender"]}</div>'
                        f'<div style="font-size:12px;color:#a89ec9;">Subject: {m["subject"]}</div>'
                        f'<div style="font-size:13px;font-weight:700;color:{conf_color};margin-top:6px;">'
                        f'{conf_label}</div>',
                        unsafe_allow_html=True,
                    )
                    folder = m.get("suggested_folder", "")
                    if folder:
                        st.markdown(
                            f'<div style="font-size:12px;color:#7c6ff7;margin-top:4px;">'
                            f'📁 Suggested folder: {folder}</div>',
                            unsafe_allow_html=True,
                        )

                with mc2:
                    if folder and os.path.isdir(folder):
                        if st.button("💾 Save to folder", key=f"ew_save_{i}", use_container_width=True, type="primary"):
                            import shutil
                            dest = os.path.join(folder, m["filename"])
                            shutil.copy2(m["file_path"], dest)
                            ew.dismiss(i)
                            st.success(f"Saved to {dest}")
                            st.rerun()
                    if st.button("Open in Reader", key=f"ew_read_{i}", use_container_width=True):
                        st.session_state.reader_open_file = m["file_path"]
                        st.session_state.page = "reader"
                        st.rerun()
                    if st.button("Dismiss", key=f"ew_dismiss_{i}", use_container_width=True):
                        ew.dismiss(i)
                        st.rerun()

        if st.button("Dismiss All", key="ew_dismiss_all"):
            ew.clear_all()
            st.rerun()

        st.markdown("---")

    # ── Incoming Queue — all files in the incoming/ folder ────────────────────
    import email_watch as ew
    _incoming_dir = os.path.join(os.path.dirname(__file__), "incoming")
    _inbox_files  = []
    if os.path.isdir(_incoming_dir):
        _inbox_files = [
            f for f in os.listdir(_incoming_dir)
            if f.lower().endswith(".pdf")
        ]

    _iq_label = f"📂 Incoming Queue — {len(_inbox_files)} file(s) waiting" if _inbox_files \
                else "📂 Incoming Queue — empty"
    with st.expander(_iq_label, expanded=bool(_inbox_files)):
        if not _inbox_files:
            st.markdown(
                '<span style="color:#a89ec9;font-size:13px;">No files in the incoming folder. '
                'Files appear here when Email Watch downloads attachments.</span>',
                unsafe_allow_html=True,
            )
        else:
            st.caption(
                "These files came from your email inbox. Review each one — "
                "**nothing moves until you click Yes.**"
            )
            from doc_verify import verify as _dv_q
            from crm import get_all_loans as _iq_loans
            _pipeline = {l.get("id"): l for l in _iq_loans()}

            for _qi, _qfname in enumerate(_inbox_files):
                _qfpath = os.path.join(_incoming_dir, _qfname)
                try:
                    with open(_qfpath, "rb") as _qf:
                        _qbytes = _qf.read()
                    _qv = _dv_q(_qbytes, _qfname)
                except Exception:
                    _qv = {"doc_type": "Document", "ok_list": [], "flags": ["Could not read file"],
                           "verdict": "check", "borrower": None, "loan_num": "",
                           "suggested_folder": "", "confidence": 0}

                _v_color = {"pass": "#27ae60", "review": "#f1c40f", "check": "#e74c3c"}.get(
                    _qv.get("verdict", "check"), "#e74c3c"
                )
                _v_icon  = {"pass": "✅", "review": "⚠️", "check": "🔍"}.get(
                    _qv.get("verdict", "check"), "🔍"
                )
                _bname = _qv.get("borrower") or "Unknown borrower"
                _lnum  = _qv.get("loan_num", "")
                _match_label = f" · {_bname} · Loan {_lnum}" if _qv.get("borrower") else " · No pipeline match"

                with st.container():
                    st.markdown(
                        f'<div style="background:#1e1645;border-left:3px solid {_v_color};'
                        f'border-radius:6px;padding:8px 12px;margin-bottom:6px;">'
                        f'<span style="font-weight:700;color:#f0f6fc;font-size:13px;">'
                        f'{_v_icon} {_qfname}</span>'
                        f'<span style="font-size:12px;color:#a89ec9;">{_match_label}</span><br>'
                        f'<span style="font-size:11px;color:#7c6ff7;">{_qv.get("doc_type","Document")} · '
                        f'{_qv.get("page_count",0)} pages · '
                        f'{_qv.get("days_old","?")}d old</span></div>',
                        unsafe_allow_html=True,
                    )
                    _qa, _qb, _qc, _qd = st.columns([3, 1, 1, 1])
                    with _qa:
                        for _ok in _qv.get("ok_list", []):
                            st.markdown(f'<span style="color:#27ae60;font-size:11px;">✓ {_ok}</span><br>',
                                        unsafe_allow_html=True)
                        for _fl in _qv.get("flags", []):
                            st.markdown(f'<span style="color:#e74c3c;font-size:11px;">⚑ {_fl}</span><br>',
                                        unsafe_allow_html=True)
                    _dest_folder = _qv.get("suggested_folder", "")
                    with _qb:
                        if _dest_folder and os.path.isdir(_dest_folder):
                            if st.button("✅ Yes — Save", key=f"iq_yes_{_qi}",
                                         use_container_width=True, type="primary"):
                                import shutil as _shu
                                _dest = os.path.join(_dest_folder, _qfname)
                                _shu.move(_qfpath, _dest)
                                st.success(f"Moved to {_dest}")
                                st.rerun()
                        else:
                            _manual = st.text_input("Save to:", key=f"iq_path_{_qi}",
                                                    placeholder=r"C:\Loans\Smith",
                                                    label_visibility="collapsed")
                            if _manual and st.button("✅ Yes", key=f"iq_yes_m_{_qi}",
                                                     use_container_width=True, type="primary"):
                                import shutil as _shu
                                os.makedirs(_manual, exist_ok=True)
                                _shu.move(_qfpath, os.path.join(_manual, _qfname))
                                st.success("Moved.")
                                st.rerun()
                    with _qc:
                        if st.button("📂 Read", key=f"iq_read_{_qi}", use_container_width=True):
                            st.session_state.reader_open_file = _qfpath
                            st.session_state.page = "reader"
                            st.rerun()
                    with _qd:
                        if st.button("❌ No", key=f"iq_no_{_qi}", use_container_width=True):
                            try:
                                os.remove(_qfpath)
                            except Exception:
                                pass
                            st.rerun()

    # ── Credentials setup ─────────────────────────────────────────────────────
    with st.expander("⚙️ Email Credentials" + (" (configured)" if cfg else " (not set up)"), expanded=not cfg):
        st.markdown(
            '<div style="background:#3d3015;border-left:3px solid #f1c40f;border-radius:6px;'
            'padding:8px 14px;margin-bottom:12px;font-size:12px;color:#f9e79f;">'
            '⚠️ <b>Gmail users:</b> You must use an App Password, not your real password.<br>'
            'Go to: <b>myaccount.google.com → Security → 2-Step Verification → App Passwords</b><br>'
            'Select "Mail" + "Windows Computer" → copy the 16-character code → paste below.</div>',
            unsafe_allow_html=True,
        )

        provider = st.selectbox(
            "Email provider",
            list(ew.PROVIDERS.keys()),
            index=list(ew.PROVIDERS.keys()).index(cfg.get("provider", "Gmail"))
            if cfg.get("provider") in ew.PROVIDERS else 0,
            key="ew_provider",
        )
        email_addr = st.text_input(
            "Your email address",
            value=cfg.get("email", ""),
            placeholder="you@gmail.com",
            key="ew_email",
        )
        password = st.text_input(
            "App password (not your real password)",
            value=cfg.get("password", ""),
            type="password",
            placeholder="xxxx xxxx xxxx xxxx",
            key="ew_pass",
        )
        if provider == "Custom":
            custom_host = st.text_input(
                "IMAP server hostname",
                value=cfg.get("host", ""),
                placeholder="imap.yourprovider.com",
                key="ew_host",
            )
        else:
            custom_host = ""

        iv1, iv2 = st.columns(2)
        with iv1:
            interval = st.select_slider(
                "Check every",
                options=[2, 5, 10, 15, 30],
                value=cfg.get("interval_minutes", 5),
                format_func=lambda x: f"{x} min",
                key="ew_interval",
            )
        with iv2:
            since_hours = st.select_slider(
                "Only look back",
                options=[0, 1, 2, 3, 6, 12, 24],
                value=cfg.get("since_hours", 1),
                format_func=lambda x: "All unread" if x == 0 else f"Last {x}h",
                key="ew_since",
            )

        if st.button("💾 Save Credentials", key="ew_save_creds", type="primary"):
            if email_addr and password:
                ew.save_config(email_addr, password, provider, custom_host, interval, since_hours)
                st.success("Credentials saved. Click ▶ Start Watching to begin.")
                st.rerun()
            else:
                st.error("Enter both email address and app password.")

    # ── How it works ─────────────────────────────────────────────────────────
    with st.expander("ℹ️ How Email Watch works"):
        st.markdown("""
**What it does:**
- Checks your inbox every N minutes (runs in the background — you can use the rest of the app normally)
- Looks for **unread emails with PDF attachments**
- Downloads each PDF to the `incoming/` folder in this app's directory
- Reads the first 3 pages of the PDF to extract borrower names
- Fuzzy-matches those names against every loan in your Pipeline
- Shows a notification card here and in the sidebar

**Privacy:**
- Your credentials are saved locally in `email_config.json` in the app folder
- The app connects to your IMAP server, downloads attachments, then disconnects
- Nothing is sent anywhere — reads only, no cloud

**Toggle:**
- On: background thread checks every N minutes, then sleeps
- Off: thread stops within a few seconds — no more peeking

**Borrower matching confidence:**
- 🟢 80%+ = high confidence match (name found in PDF text)
- 🟡 50–79% = possible match (partial name found)
- 🔴 Below 50% = no match — file saved to `incoming/` folder, you decide
        """)


# --- Ollama Settings Page ---
def show_ollama_page():
    import ollama_client as _oc

    st.title("🤖 Ollama — Local AI Enhancement")
    st.caption("Optional. Connects to a locally running Ollama instance for smarter document analysis. 100% offline.")

    cfg = _oc.get_config()

    # ── Status card ──────────────────────────────────────────────────────────
    ok, msg = _oc.ping(cfg.get("endpoint", _oc.DEFAULT_ENDPOINT))
    if cfg.get("enabled"):
        if ok:
            st.success(f"🟣 Ollama is running · {cfg.get('endpoint')} · model: {cfg.get('model')}")
        else:
            st.error(f"🔴 Ollama enabled but unreachable — {msg}")
            st.info("Make sure Ollama is running: open a terminal and run `ollama serve`")
    else:
        st.info("⚫ Ollama is disabled. Enable it below to activate AI-enhanced features.")

    st.markdown("---")

    # ── Settings form ────────────────────────────────────────────────────────
    with st.form("ollama_settings_form"):
        enabled = st.toggle("Enable Ollama", value=bool(cfg.get("enabled")), key="oc_enabled")
        endpoint = st.text_input("Ollama endpoint", value=cfg.get("endpoint", _oc.DEFAULT_ENDPOINT),
                                 key="oc_endpoint",
                                 help="Default: http://localhost:11434")

        # Model: try to list from server, fall back to text input
        available_models = _oc.list_models(endpoint) if ok else []
        current_model = cfg.get("model", _oc.DEFAULT_MODEL)
        if available_models:
            if current_model not in available_models:
                available_models.insert(0, current_model)
            model = st.selectbox("Model", available_models,
                                 index=available_models.index(current_model),
                                 key="oc_model")
        else:
            model = st.text_input("Model name", value=current_model, key="oc_model_txt",
                                  help="e.g. llama3.2 · Run: ollama pull llama3.2")

        save_btn = st.form_submit_button("💾 Save Settings", type="primary")

    if save_btn:
        _oc.save_config(enabled, endpoint, model if available_models else st.session_state.get("oc_model_txt", model))
        st.success("Settings saved.")
        st.rerun()

    # ── Quick setup guide ────────────────────────────────────────────────────
    with st.expander("📖 How to set up Ollama (one-time)"):
        st.markdown("""
**Step 1 — Install Ollama**
Download from [ollama.com](https://ollama.com) and run the installer. It adds a system tray icon.

**Step 2 — Pull a model** (in your terminal)
```
ollama pull llama3.2
```
`llama3.2` is fast and works well. For more accuracy try `mistral` or `llama3.1`.

**Step 3 — Start the server** (if not auto-started)
```
ollama serve
```

**Step 4 — Enable here**
Toggle "Enable Ollama" above and click Save.

---
**What Ollama enhances:**
- 🤖 **Draft with Ollama** — richer, context-aware document request emails
- 🤖 **Enhance conditions** — catches conditions the script might miss
- 🤖 **Interpret guidelines** — explains what a guideline means in plain English
- 🤖 **Summarize doc** — quick overview of any uploaded document

All processing stays on your machine. No internet. No API key.
        """)

    # ── Recent processing log ─────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 📋 Recent Processing Log")
    st.caption("Shows which mode was used for each analysis (script-only vs Ollama-enhanced).")

    log_lines = _oc.get_recent_log(40)
    if log_lines:
        log_c1, log_c2 = st.columns([5, 1])
        with log_c2:
            if st.button("🗑 Clear Log", key="oc_clear_log"):
                _oc.clear_log()
                st.rerun()
        log_text = "\n".join(reversed(log_lines))
        st.code(log_text, language=None)
    else:
        st.info("No processing log yet — scan a document or draft an email to see entries here.")


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
        elif page == "team":
            show_team_page()
        elif page == "email_watch":
            show_email_watch_page()
        elif page == "ollama":
            show_ollama_page()
        elif page == "history":
            show_history()
        elif page == "reader":
            show_reader()
        else:
            show_dashboard()


if __name__ == "__main__":
    main()
