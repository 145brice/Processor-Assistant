"""
Pipeline Manager - Mortgage Document Processing App
Main Streamlit application.
"""

import os
import streamlit as st

# --- Page Config ---
st.set_page_config(
    page_title="Pipeline Manager",
    page_icon="—",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Custom CSS ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* ── Global reset & base ──────────────────────────────────────── */
html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}
.stApp {
    background: #d5d7da;
}

/* ── Hide Streamlit chrome ────────────────────────────────────── */
#MainMenu, footer, header { visibility: hidden; height: 0; }
.stDeployButton { display: none; }

/* ── Sidebar ──────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: #fafafa !important;
    border-right: 1px solid #888 !important;
}
[data-testid="stSidebar"] > div:first-child {
    padding: 1rem 0.75rem;
}

/* Sidebar nav buttons */
[data-testid="stSidebar"] button[kind="secondary"],
[data-testid="stSidebar"] button {
    background: transparent !important;
    border: 1px solid transparent !important;
    color: #374151 !important;
    border-radius: 4px !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    text-align: left !important;
    justify-content: flex-start !important;
    padding: 6px 10px !important;
    margin-bottom: 1px !important;
    transition: background 0.15s !important;
    width: 100% !important;
    box-shadow: none !important;
}
[data-testid="stSidebar"] button[kind="secondary"]:hover,
[data-testid="stSidebar"] button:hover {
    background: #e8e8e8 !important;
    border-color: transparent !important;
    color: #111 !important;
    box-shadow: none !important;
    transform: none !important;
}
/* Force all sidebar button inner content left */
[data-testid="stSidebar"] button p,
[data-testid="stSidebar"] button span,
[data-testid="stSidebar"] button div {
    text-align: left !important;
    justify-content: flex-start !important;
}

/* Global: force ALL buttons left-aligned */
button {
    text-align: left !important;
    justify-content: flex-start !important;
}
button * {
    text-align: left !important;
}
button p {
    text-align: left !important;
    width: 100% !important;
}
/* Streamlit button inner flex container */
button > div {
    justify-content: flex-start !important;
    text-align: left !important;
}
button > div > p {
    text-align: left !important;
}

/* Sidebar toggle */
[data-testid="stSidebar"] [data-testid="stToggle"] label {
    font-size: 13px !important;
    color: #4b5563 !important;
    font-weight: 500 !important;
}

/* ── Main content area ────────────────────────────────────────── */
.block-container {
    padding: 1rem 1.5rem 2rem 1.5rem !important;
    max-width: 1100px !important;
}

/* Page headings */
h1 { font-size: 20px !important; font-weight: 700 !important; color: #111 !important; letter-spacing: -0.3px; margin-bottom: 0.25rem !important; }
h2 { font-size: 16px !important; font-weight: 600 !important; color: #111 !important; }
h3 { font-size: 14px !important; font-weight: 600 !important; color: #222 !important; }
p, li { color: #333 !important; font-size: 13px !important; font-weight: 400 !important; }
label { color: #222 !important; font-size: 13px !important; font-weight: 500 !important; }

/* Markdown text inside the app */
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li,
[data-testid="stMarkdownContainer"] span {
    color: #374151 !important;
    font-size: 13px !important;
}
[data-testid="stMarkdownContainer"] strong {
    color: #111 !important;
    font-weight: 600 !important;
}

/* Checkbox labels */
[data-testid="stCheckbox"] label p {
    color: #374151 !important;
    font-size: 13px !important;
    font-weight: 500 !important;
}

/* Selectbox selected value text */
[data-testid="stSelectbox"] > div > div > div {
    color: #111 !important;
    font-size: 13px !important;
    font-weight: 500 !important;
}

/* Radio / number input labels */
[data-testid="stNumberInput"] label,
[data-testid="stDateInput"] label,
[data-testid="stTextArea"] label {
    color: #374151 !important;
    font-size: 13px !important;
    font-weight: 500 !important;
}

/* ── Buttons ──────────────────────────────────────────────────── */
button[kind="primary"] {
    background: #3b82f6 !important;
    color: #fff !important;
    border: 1px solid #2563eb !important;
    border-radius: 4px !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    padding: 0 16px !important;
    height: 34px !important;
    box-shadow: none !important;
    transition: background 0.15s !important;
}
button[kind="primary"]:hover {
    background: #2563eb !important;
    box-shadow: none !important;
    transform: none !important;
}
button[kind="secondary"] {
    background: #fff !important;
    color: #374151 !important;
    border: 1px solid #888 !important;
    border-radius: 4px !important;
    font-weight: 500 !important;
    font-size: 13px !important;
    height: 34px !important;
    transition: background 0.15s !important;
    box-shadow: none !important;
}
button[kind="secondary"]:hover {
    border-color: #9ca3af !important;
    color: #111 !important;
    background: #f9fafb !important;
    box-shadow: none !important;
    transform: none !important;
}

/* ── Inputs & selects ─────────────────────────────────────────── */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea,
[data-testid="stSelectbox"] > div > div,
[data-testid="stNumberInput"] input {
    background: #fff !important;
    border: 1px solid #888 !important;
    border-radius: 3px !important;
    color: #111 !important;
    font-size: 13px !important;
    font-family: 'Inter', sans-serif !important;
    box-shadow: none !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {
    border-color: #2563eb !important;
    box-shadow: 0 0 0 2px rgba(37,99,235,0.12) !important;
}

/* ── File uploader ────────────────────────────────────────────── */
[data-testid="stFileUploader"] {
    background: #fff !important;
    border: 1px dashed #888 !important;
    border-radius: 4px !important;
    padding: 14px !important;
    transition: border-color 0.15s !important;
}
[data-testid="stFileUploader"]:hover {
    border-color: #999 !important;
    background: #fff !important;
}
[data-testid="stFileUploader"] label {
    color: #333 !important;
}
/* Uploaded file chip */
[data-testid="stFileUploaderFile"] {
    background: #f7f7f7 !important;
    border: 1px solid #888 !important;
    border-radius: 3px !important;
    color: #374151 !important;
}
[data-testid="stFileUploaderFile"] span,
[data-testid="stFileUploaderFile"] small,
[data-testid="stFileUploaderFile"] p {
    color: #374151 !important;
    font-weight: 500 !important;
}
[data-testid="stFileUploaderFileName"] {
    color: #111 !important;
    font-weight: 600 !important;
}
[data-testid="stFileUploaderFileData"] {
    color: #444 !important;
}

/* ── Form submit buttons (Add to Team, Save, etc.) ────────────── */
[data-testid="stForm"] [data-testid="stBaseButton-secondaryFormSubmit"],
[data-testid="stForm"] button[kind="primaryFormSubmit"],
[data-testid="stForm"] button[kind="secondaryFormSubmit"] {
    background: #fff !important;
    border: 1px solid #888 !important;
    color: #374151 !important;
    font-weight: 500 !important;
    border-radius: 4px !important;
    box-shadow: none !important;
}
[data-testid="stForm"] button[kind="primaryFormSubmit"]:hover,
[data-testid="stForm"] button[kind="secondaryFormSubmit"]:hover {
    background: #f5f5f5 !important;
    border-color: #999 !important;
    color: #111 !important;
}

/* ── Expanders ────────────────────────────────────────────────── */
[data-testid="stExpander"] {
    background: #fff !important;
    border: 1px solid #888 !important;
    border-radius: 4px !important;
    margin-bottom: 3px !important;
    box-shadow: none !important;
}
[data-testid="stExpander"] summary {
    font-weight: 600 !important;
    color: #111 !important;
    font-size: 13px !important;
    padding: 6px 10px !important;
    min-height: 0 !important;
    line-height: 1.4 !important;
}
[data-testid="stExpander"] summary:hover {
    color: #111 !important;
    background: #f5f5f5 !important;
    border-radius: 4px !important;
}
/* Compact the expanded content area */
[data-testid="stExpander"] > div[data-testid="stExpanderDetails"] {
    padding: 6px 10px 10px 10px !important;
}

/* ── Info / warning / error boxes ────────────────────────────── */
[data-testid="stAlert"] {
    border-radius: 3px !important;
    border-width: 1px !important;
    font-size: 13px !important;
}

/* ── Dividers ─────────────────────────────────────────────────── */
hr { border-color: #888 !important; margin: 10px 0 !important; }

/* ── Tabs ─────────────────────────────────────────────────────── */
[data-testid="stTabs"] [role="tab"] {
    font-size: 13px !important;
    font-weight: 500 !important;
    color: #444 !important;
    border-radius: 0 !important;
    padding: 6px 14px !important;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    color: #111 !important;
    border-bottom: 2px solid #333 !important;
    background: transparent !important;
}

/* ── Checkbox ─────────────────────────────────────────────────── */
[data-testid="stCheckbox"] label {
    font-size: 13px !important;
    color: #374151 !important;
}

/* ── Caption / small text ─────────────────────────────────────── */
[data-testid="stCaptionContainer"] p,
.stCaption { color: #777 !important; font-size: 11px !important; font-weight: 500 !important; }

/* ── Progress bar ─────────────────────────────────────────────── */
[data-testid="stProgress"] > div > div {
    background: #2563eb !important;
    border-radius: 2px !important;
}
[data-testid="stProgress"] {
    background: #e0e0e0 !important;
    border-radius: 2px !important;
}

/* ── Containers (bordered) ────────────────────────────────────── */
[data-testid="stVerticalBlockBorderWrapper"] {
    background: #fff !important;
    border: 1px solid #888 !important;
    border-radius: 4px !important;
    padding: 12px !important;
    box-shadow: none !important;
}

/* ── Selectbox dropdown ───────────────────────────────────────── */
[data-testid="stSelectbox"] svg { color: #333 !important; }

/* Dropdown popup list */
[data-baseweb="popover"] ul,
[data-baseweb="menu"] {
    background: #fff !important;
    border: 1px solid #888 !important;
    border-radius: 3px !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08) !important;
}
[data-baseweb="popover"] li,
[data-baseweb="menu"] li {
    background: #fff !important;
    color: #111 !important;
    font-size: 13px !important;
    font-weight: 500 !important;
}
[data-baseweb="popover"] li:hover,
[data-baseweb="menu"] li:hover {
    background: #f5f5f5 !important;
    color: #111 !important;
}
[data-baseweb="select"] > div {
    background: #fff !important;
    border-color: #888 !important;
    color: #111 !important;
}

/* ── Toggle ───────────────────────────────────────────────────── */
[data-testid="stToggle"] > label > div[data-checked="true"] {
    background: #2563eb !important;
}

/* ── Condition status buttons (inside expander) ──────────────── */
div[data-testid="stHorizontalBlock"] button[kind="secondary"] {
    font-size: 12px !important;
    font-weight: 600 !important;
    padding: 3px 6px !important;
    height: 28px !important;
    border-radius: 3px !important;
}

/* ── Multiselect ──────────────────────────────────────────────── */
[data-testid="stMultiSelect"] > div {
    background: #fff !important;
    border: 1px solid #888 !important;
    border-radius: 3px !important;
}
[data-testid="stMultiSelect"] span[data-baseweb="tag"] {
    background: #f0f0f0 !important;
    color: #374151 !important;
    border: 1px solid #888 !important;
    border-radius: 3px !important;
    font-size: 12px !important;
    font-weight: 500 !important;
}
[data-testid="stMultiSelect"] input {
    color: #111 !important;
    background: transparent !important;
    border: none !important;
}

/* ── Markdown tables (conditions output) ─────────────────────── */
[data-testid="stMarkdownContainer"] table {
    width: 100% !important;
    border-collapse: collapse !important;
    background: #fff !important;
    border-radius: 0 !important;
    overflow: hidden !important;
    font-size: 13px !important;
    box-shadow: none !important;
    border: 1px solid #888 !important;
}
[data-testid="stMarkdownContainer"] thead tr {
    background: #f7f7f7 !important;
}
[data-testid="stMarkdownContainer"] th {
    color: #374151 !important;
    font-size: 11px !important;
    font-weight: 600 !important;
    padding: 6px 10px !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
    border-bottom: 1px solid #888 !important;
}
[data-testid="stMarkdownContainer"] td {
    color: #111 !important;
    font-size: 13px !important;
    font-weight: 400 !important;
    padding: 5px 10px !important;
    border-bottom: 1px solid #888 !important;
}
[data-testid="stMarkdownContainer"] tr:hover td {
    background: #f7f7f7 !important;
    color: #111 !important;
}

/* ── Progress nav bar ─────────────────────────────────────────── */
.progress-nav {
    display: flex;
    gap: 2px;
    background: #f7f7f7;
    border-radius: 3px;
    padding: 3px;
    margin-bottom: 12px;
    border: 1px solid #888;
    box-shadow: none;
    position: sticky;
    top: 0;
    z-index: 999;
    flex-wrap: wrap;
}
.pn-step {
    flex: 1;
    min-width: 70px;
    text-align: center;
    padding: 5px 4px;
    border-radius: 3px;
    font-size: 10px;
    font-weight: 500;
    text-decoration: none;
    transition: background 0.15s;
    line-height: 1.3;
    color: #5c6370;
}
.pn-step.done    { background: #e8f5e9; color: #2e7d32; border: 1px solid #c8e6c9; }
.pn-step.active  { background: #e3f2fd; color: #1565c0; border: 1px solid #bbdefb; }
.pn-step.pending { background: transparent; color: #333; }
.pn-step:hover   { background: #eee; color: #333; }
.pn-num { display: block; font-size: 12px; font-weight: 600; margin-bottom: 1px; }
.section-anchor  { display: block; position: relative; top: -100px; visibility: hidden; }

/* ── Party / condition badges ─────────────────────────────────── */
.badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 3px;
    font-size: 11px;
    font-weight: 500;
    margin: 1px 2px;
    letter-spacing: 0.2px;
}
.badge-borrower    { background: #e3f2fd; color: #1565c0; border: 1px solid #bbdefb; }
.badge-title       { background: #f3e5f5; color: #6a1b9a; border: 1px solid #e1bee7; }
.badge-underwriter { background: #fff3e0; color: #e65100; border: 1px solid #ffcc80; }
.badge-insurance   { background: #e8f5e9; color: #2e7d32; border: 1px solid #c8e6c9; }
.badge-closer      { background: #fffde7; color: #f57f17; border: 1px solid #fff59d; }
.badge-jr          { background: #fce4ec; color: #c2185b; border: 1px solid #f8bbd0; }
.badge-manager     { background: #e3f2fd; color: #1565c0; border: 1px solid #bbdefb; }
.badge-appraiser   { background: #e8f5e9; color: #2e7d32; border: 1px solid #c8e6c9; }
.badge-default     { background: #f5f5f5; color: #333; border: 1px solid #888; }

/* ── Pipeline status chips ────────────────────────────────────── */
.status-chip {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 3px;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.2px;
}
.status-pending   { background: #ffebee; color: #c62828; border: 1px solid #ef9a9a; }
.status-requested { background: #fff3e0; color: #e65100; border: 1px solid #ffcc80; }
.status-cleared   { background: #e8f5e9; color: #2e7d32; border: 1px solid #c8e6c9; }
.status-overdue   { background: #f5f5f5; color: #333; border: 1px solid #888; }
.status-closed    { background: #f5f5f5; color: #333; border: 1px solid #888; }

/* ── Loan pipeline cards ──────────────────────────────────────── */
.loan-card {
    background: #fff;
    border: 1px solid #888;
    border-radius: 3px;
    padding: 8px 12px;
    margin: 0 0 2px 0;
    transition: background 0.15s;
    line-height: 1.4;
    box-shadow: none;
}
.loan-card:hover {
    border-color: #bbb;
    background: #f7f7f7;
    box-shadow: none;
    transform: none;
}
.loan-num   { font-size: 13px; font-weight: 700; color: #1565c0; font-family: 'Inter', monospace; }
.loan-name  { font-size: 13px; color: #111; font-weight: 600; }
.loan-due   { font-size: 11px; color: #5c6370; font-weight: 400; }
.loan-missing { font-size: 11px; color: #c62828; font-weight: 500; }

/* ── Stat cards (pipeline counts — inline chips now) ─────────── */
.stat-card {
    text-align: left;
    padding: 6px 8px;
    border-radius: 3px;
    background: #fff;
    border: 1px solid #888;
    box-shadow: none;
}
.stat-num  { font-size: 18px; font-weight: 700; color: #111; line-height: 1; }
.stat-label { font-size: 10px; color: #5c6370; margin-top: 2px; font-weight: 500; text-transform: uppercase; letter-spacing: 0.3px; }

/* ── Login card ───────────────────────────────────────────────── */
.login-card {
    max-width: 400px;
    margin: 40px auto 0 auto;
    background: #fff;
    border: 1px solid #888;
    border-radius: 4px;
    padding: 28px 24px;
    box-shadow: none;
}
.login-title {
    font-size: 18px;
    font-weight: 700;
    color: #111;
    text-align: center;
    margin-bottom: 4px;
}
.login-sub {
    font-size: 12px;
    color: #5c6370;
    text-align: center;
    margin-bottom: 20px;
}

/* ── Subtle layout tightening ────────────────────────────────── */
[data-testid="stHorizontalBlock"] { gap: 0.4rem; }

/* ── Toasts, alerts, and popups ──────────────────────────────── */
[data-testid="stToast"],
div[data-testid="stToast"] > div {
    background: #fff !important;
    color: #111 !important;
    border: 1px solid #888 !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08) !important;
    border-radius: 3px !important;
}
[data-testid="stToast"] p,
[data-testid="stToast"] span {
    color: #111 !important;
}
div[data-testid="stAlert"],
div[role="alert"],
div[data-baseweb="notification"] {
    background: #fff !important;
    color: #111 !important;
    border-color: #888 !important;
    border-radius: 3px !important;
}
div[data-baseweb="notification"] div {
    color: #111 !important;
}
/* st.warning */
div[data-testid="stAlert"][data-type="warning"],
div.stAlert[kind="warning"] {
    background: #fffbeb !important;
    border-left-color: #f59e0b !important;
    color: #92400e !important;
}
/* st.error */
div[data-testid="stAlert"][data-type="error"],
div.stAlert[kind="error"] {
    background: #fef2f2 !important;
    border-left-color: #ef4444 !important;
    color: #991b1b !important;
}
/* st.success */
div[data-testid="stAlert"][data-type="success"],
div.stAlert[kind="success"] {
    background: #ecfdf5 !important;
    border-left-color: #10b981 !important;
    color: #065f46 !important;
}
/* st.info */
div[data-testid="stAlert"][data-type="info"],
div.stAlert[kind="info"] {
    background: #eff6ff !important;
    border-left-color: #3b82f6 !important;
    color: #1e40af !important;
}
/* Ensure text inside all alert types is readable */
div[data-testid="stAlert"] p,
div[data-testid="stAlert"] span,
div[data-testid="stAlert"] div,
div[role="alert"] p,
div[role="alert"] span {
    color: inherit !important;
}
/* Popover, dropdown menus, tooltips */
div[data-baseweb="popover"],
div[data-baseweb="tooltip"],
ul[data-testid="stSelectboxVirtualDropdown"] {
    background: #fff !important;
    border: 1px solid #888 !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08) !important;
    border-radius: 3px !important;
}
div[data-baseweb="popover"] li,
ul[data-testid="stSelectboxVirtualDropdown"] li {
    color: #111827 !important;
    background: #ffffff !important;
}
div[data-baseweb="popover"] li:hover,
ul[data-testid="stSelectboxVirtualDropdown"] li:hover {
    background: #f3f4f6 !important;
}
/* Expander headers */
div[data-testid="stExpander"] summary {
    color: #111827 !important;
}
/* Caption text */
div[data-testid="stCaptionContainer"] p {
    color: #6b7280 !important;
}
</style>
""", unsafe_allow_html=True)

# --- Session State Defaults ---
DEFAULTS = {
    "page": "pipeline",
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
      <div style="font-size:36px; margin-bottom:6px;">—</div>
      <div style="font-size:28px; font-weight:800; color:#222222; letter-spacing:-0.5px;">
        Pipeline Manager
      </div>
      <div style="font-size:13px; color:#484f58; margin-top:4px;">
        Offline Mortgage Processing &nbsp;·&nbsp; No cloud &nbsp;·&nbsp; No API keys
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    _, sb_col, _ = st.columns([1, 1, 1])
    with sb_col:
        if st.button("* Try Sandbox — No Account Needed", type="primary", use_container_width=True):
            st.session_state.authenticated = True
            st.session_state.user_id = "sandbox"
            st.session_state.user_email = "sandbox@demo"
            st.session_state.user_name = "Sandbox User"
            st.session_state.user_role = "Processor"
            st.session_state.sandbox_mode = True
            st.session_state.page = "pipeline"
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
                    st.session_state.page = "pipeline"
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
          <div style="font-size:20px; font-weight:800; color:#222222; letter-spacing:-0.3px;">
            Pipeline Manager
          </div>
          <div style="font-size:11px; color:#5c6370; margin-top:4px;">Offline · Local · No cloud</div>
        </div>
        """, unsafe_allow_html=True)

        # ── Who's logged in ──────────────────────────────────────────────────
        if is_sandbox:
            st.markdown(
                '<div style="background:#ffffff;border:1px solid #888;border-radius:8px;'
                'padding:8px 12px;margin-bottom:12px;">'
                '<span style="font-size:12px;color:#5c6370;">* Sandbox Mode</span></div>',
                unsafe_allow_html=True,
            )
        elif user_name:
            role_color = {"Loan Officer": "#e67e22", "Manager": "#2980b9",
                          "Jr Underwriter": "#c0392b"}.get(user_role, "#2563eb")
            st.markdown(
                f'<div style="background:#ffffff;border:1px solid #888;border-radius:8px;'
                f'padding:8px 12px;margin-bottom:12px;">'
                f'<div style="font-size:13px;font-weight:700;color:#111111;">{user_name}</div>'
                f'<div style="font-size:11px;color:{role_color};font-weight:600;">{user_role}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

        st.markdown("---")

        if st.button("Document Scanner", use_container_width=True):
            st.session_state.page = "dashboard"
            st.rerun()
        if st.button("Files️ My Pipeline", use_container_width=True):
            st.session_state.page = "pipeline"
            st.rerun()
        if st.button("Document Reader", use_container_width=True):
            st.session_state.page = "reader"
            st.rerun()
        if st.button("My Team", use_container_width=True):
            st.session_state.page = "team"
            st.rerun()
        if st.button("Email Email Watch", use_container_width=True):
            st.session_state.page = "email_watch"
            st.rerun()
        if st.button("AI Settings", use_container_width=True):
            st.session_state.page = "ollama"
            st.rerun()
        if st.button("$ Usage & Billing", use_container_width=True):
            st.session_state.page = "billing"
            st.rerun()
        if not is_sandbox:
            if st.button("My History", use_container_width=True):
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
            _dot = "●"
            _label = f"Watching · {_ew_last}"
        else:
            _dot = "●"
            _label = "Inbox watch off"
        _badge = f' <span style="background:#2563eb;color:#fff;font-size:10px;border-radius:8px;padding:1px 6px;">{_ew_pending}</span>' if _ew_pending else ""
        st.markdown(
            f'<div style="background:#ffffff;border:1px solid #888;border-radius:8px;'
            f'padding:7px 10px;margin-bottom:4px;cursor:default;">'
            f'<span style="font-size:12px;color:#333333;">{_dot} {_label}{_badge}</span></div>',
            unsafe_allow_html=True,
        )

        # ── AI status indicator ───────────────────────────────────────────────
        import ai_router as _ar
        _ar_status = _ar.get_status()
        _pref = _ar_status["preferred"]
        if _pref == "cloud" and _ar_status["cloud_enabled"]:
            _ai_dot   = "Cloud️"
            _ai_label = f"Cloud AI · {_ar_status['cloud_provider'].title()}"
        elif _pref == "ollama" and _ar_status["ollama_enabled"]:
            _ai_dot   = "●"
            _ai_label = f"Ollama · {_ar_status['ollama_model']}"
        elif _ar_status["cloud_enabled"]:
            _ai_dot   = "Cloud️"
            _ai_label = f"Cloud AI (fallback) · {_ar_status['cloud_provider'].title()}"
        elif _ar_status["ollama_enabled"]:
            _ai_dot   = "●"
            _ai_label = f"Ollama (fallback) · {_ar_status['ollama_model']}"
        else:
            _ai_dot, _ai_label = "●", "AI — script only"
        st.markdown(
            f'<div style="background:#ffffff;border:1px solid #888;border-radius:8px;'
            f'padding:7px 10px;margin-bottom:8px;cursor:default;">'
            f'<span style="font-size:12px;color:#333333;">{_ai_dot} {_ai_label}</span></div>',
            unsafe_allow_html=True,
        )

        st.markdown("---")
        if st.button("Logout", use_container_width=True):
            for key in DEFAULTS:
                st.session_state[key] = DEFAULTS[key]
            st.rerun()


def show_dashboard():
    """Main document scanning page."""
    st.markdown("## Document Scanner")

    # === QUICK DOC VERIFY — drop any PDF, get instant check ===
    import email_watch as _ew_mod
    _ew_pending = _ew_mod.get_status()["pending_count"]
    _qv_label   = f"Import Quick Verify  ({_ew_pending} from inbox waiting)" if _ew_pending else "Import Quick Verify — drop any PDF for instant check"

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
                vcard_bg, vcard_bdr, vcard_icon = "#152a1e", "#27ae60", "✓"
                vcard_title = "Looks good — ready for review"
            elif verdict == "review":
                vcard_bg, vcard_bdr, vcard_icon = "#2d2808", "#f1c40f", "△"
                vcard_title = "Probably fine — double-check flagged items"
            else:
                vcard_bg, vcard_bdr, vcard_icon = "#3d1515", "#e74c3c", "Search"
                vcard_title = "Needs attention before saving"

            st.markdown(
                f'<div style="background:{vcard_bg};border-left:4px solid {vcard_bdr};'
                f'border-radius:8px;padding:12px 16px;margin:12px 0;">'
                f'<div style="font-size:15px;font-weight:700;color:#111111;">'
                f'{vcard_icon} {result["doc_type"]} · {vcard_title}</div>'
                f'<div style="font-size:12px;color:#5c6370;margin-top:4px;">{qv_file.name}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

            vc1, vc2 = st.columns(2)
            with vc1:
                st.markdown("**✓ Passed**")
                for ok in result["ok_list"]:
                    st.markdown(
                        f'<div style="display:flex;gap:8px;margin-bottom:3px;">'
                        f'<span style="color:#27ae60;">✓</span>'
                        f'<span style="color:#333333;font-size:13px;">{ok}</span></div>',
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
                        '<span style="color:#5c6370;font-size:13px;">No flags — all clear</span>',
                        unsafe_allow_html=True,
                    )

            # ── Action row ───────────────────────────────────────────────────
            st.markdown("---")
            folder = result.get("suggested_folder", "")
            borrower = result.get("borrower", "")
            loan_num = result.get("loan_num", "")

            if borrower:
                st.markdown(
                    f'<div style="background:#ffffff;border:1px solid #888;border-radius:8px;'
                    f'padding:10px 14px;margin-bottom:10px;">'
                    f'<span style="font-size:13px;color:#333333;">Pipeline match: </span>'
                    f'<span style="font-size:14px;font-weight:700;color:#111111;">{borrower}</span>'
                    f'<span style="font-size:12px;color:#2563eb;margin-left:8px;">Loan {loan_num}</span>'
                    f'<span style="font-size:12px;color:#5c6370;margin-left:8px;">'
                    f'{result["confidence"]}% confidence</span></div>',
                    unsafe_allow_html=True,
                )

            act1, act2, act3, act4 = st.columns(4)
            with act1:
                if folder and os.path.isdir(folder):
                    if st.button("Save to folder", key="qv_save", type="primary", use_container_width=True):
                        import shutil
                        dest = os.path.join(folder, qv_file.name)
                        with open(dest, "wb") as _f:
                            _f.write(qv_bytes)
                        st.success(f"Saved to {dest} — marked Pending Review in pipeline.")
                else:
                    save_path = st.text_input("Save to folder:", placeholder=r"C:\Loans\Smith", key="qv_savepath")
                    if save_path and st.button("Save here", key="qv_save_manual", use_container_width=True):
                        os.makedirs(save_path, exist_ok=True)
                        dest = os.path.join(save_path, qv_file.name)
                        with open(dest, "wb") as _f:
                            _f.write(qv_bytes)
                        st.success(f"Saved to {dest}")
            with act2:
                if st.button("Scan this doc", key="qv_scan", use_container_width=True):
                    st.session_state["qv_promote"] = qv_bytes
                    st.session_state["qv_promote_name"] = qv_file.name
                    st.rerun()
            with act3:
                if st.button("Open in Reader", key="qv_reader", use_container_width=True):
                    st.session_state.reader_open_file = None
                    st.session_state.page = "reader"
                    st.rerun()
            with act4:
                pass   # space

        # ── Email Watch inbox inside Verify tab ──────────────────────────────
        ew_matches = _ew_mod.get_matches()
        if ew_matches:
            st.markdown("---")
            st.markdown(f"### Email Inbox — {len(ew_matches)} attachment(s) waiting")
            for ei, em in enumerate(ew_matches):
                v_icon = {"pass": "✓", "review": "△", "check": "?"}.get(em.get("verdict", "check"), "·")
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
                            if st.button("Save", key=f"ew_qv_save_{ei}", use_container_width=True, type="primary"):
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

    # ── Mode toggle: Manual Label vs Bulk Auto-Detect ─────────────────────
    _mode_c1, _mode_c2 = st.columns([1, 3])
    with _mode_c1:
        _bulk_mode = st.toggle("Bulk Auto-Detect", key="bulk_mode_toggle",
                               help="Auto-detect document types for all uploaded files")
    with _mode_c2:
        if _bulk_mode:
            st.caption("Auto-detect reads the first 2 pages of each PDF to classify the document type. "
                       "You can override any detection before scanning.")
        else:
            st.caption("Manual mode — select the document type for each file individually.")

    # ══════════════════════════════════════════════════════════════════════
    # BULK AUTO-DETECT MODE
    # ══════════════════════════════════════════════════════════════════════
    if _bulk_mode:
        from ai_engine import detect_doc_type as _detect, process_document as _bulk_proc

        _BULK_DOC_TYPES = [
            "Approval Letter", "Closing Disclosure (CD)", "Loan Estimate (LE)",
            "1003 Application", "Purchase Contract", "Credit Report",
            "Bank Statement", "Change of Circumstance (COC)", "Broker Package (BP)",
            "Pay Stub", "W-2", "Tax Return", "Appraisal",
            "Title Commitment", "Hazard Insurance", "Unknown",
        ]

        # Auto-detect on first load or when files change
        _detect_key = "bulk_detect_results"
        _file_sig = "|".join(f.name for f in uploaded_files)
        if (st.session_state.get("bulk_file_sig") != _file_sig
                or _detect_key not in st.session_state):
            with st.spinner(f"Auto-detecting {len(uploaded_files)} document(s)..."):
                _detections = []
                for _bf in uploaded_files:
                    _bf_bytes = _bf.read()
                    _bf.seek(0)
                    _det = _detect(_bf_bytes)
                    _detections.append({
                        "name": _bf.name,
                        "detected_type": _det["doc_type"],
                        "confidence": _det["confidence"],
                        "score": _det.get("score", 0),
                        "signals": _det.get("signals", []),
                    })
                st.session_state[_detect_key] = _detections
                st.session_state["bulk_file_sig"] = _file_sig

        _detections = st.session_state[_detect_key]

        # ── Classification summary ─────────────────────────────────────
        _conf_colors = {"High": "#27ae60", "Medium": "#f1c40f", "Low": "#e67e22", "None": "#e74c3c"}
        _conf_icons = {"High": "✓", "Medium": "●", "Low": "●", "None": "?"}

        st.markdown(
            '<div style="font-size:13px;font-weight:700;color:#2563eb;text-transform:uppercase;'
            'letter-spacing:0.5px;margin:12px 0 8px 0;">Document Classification</div>',
            unsafe_allow_html=True,
        )

        # Header row
        st.markdown(
            '<div style="display:grid;grid-template-columns:3fr 2fr 1fr 2fr;gap:8px;'
            'padding:6px 12px;font-size:11px;font-weight:700;color:#5c6370;'
            'text-transform:uppercase;border-bottom:1px solid #888;">'
            '<span>File</span><span>Detected Type</span>'
            '<span>Confidence</span><span>Override</span></div>',
            unsafe_allow_html=True,
        )

        # Per-file row with override dropdown
        _overrides = {}
        for _di, _det in enumerate(_detections):
            _det_conf = _det["confidence"]
            _det_color = _conf_colors.get(_det_conf, "#8b949e")
            _det_icon = _conf_icons.get(_det_conf, "●")
            _signals_str = ", ".join(_det["signals"][:2]) if _det["signals"] else "no strong signals"

            _rc1, _rc2, _rc3, _rc4 = st.columns([3, 2, 1, 2])
            with _rc1:
                st.markdown(
                    f'<div style="font-size:12px;font-weight:600;color:#111111;padding-top:8px;">'
                    f'{_det["name"]}</div>'
                    f'<div style="font-size:10px;color:#5c6370;font-style:italic;">{_signals_str}</div>',
                    unsafe_allow_html=True,
                )
            with _rc2:
                st.markdown(
                    f'<div style="font-size:13px;font-weight:600;color:#111111;padding-top:8px;">'
                    f'{_det["detected_type"]}</div>',
                    unsafe_allow_html=True,
                )
            with _rc3:
                st.markdown(
                    f'<div style="padding-top:8px;">'
                    f'<span style="color:{_det_color};font-weight:700;font-size:12px;">'
                    f'{_det_icon} {_det_conf}</span></div>',
                    unsafe_allow_html=True,
                )
            with _rc4:
                # Default to detected type; let user override
                _det_idx = 0
                if _det["detected_type"] in _BULK_DOC_TYPES:
                    _det_idx = _BULK_DOC_TYPES.index(_det["detected_type"])
                _override = st.selectbox(
                    "Type", _BULK_DOC_TYPES, index=_det_idx,
                    key=f"bulk_override_{_di}",
                    label_visibility="collapsed",
                )
                _overrides[_di] = _override

        st.markdown("---")

        # ── Scan All button ────────────────────────────────────────────
        _scan_c1, _scan_c2 = st.columns([1, 1])
        with _scan_c1:
            _scan_all = st.button("Scan All Documents", key="bulk_scan_all",
                                  type="primary", use_container_width=True)
        with _scan_c2:
            _scan_to_loan = st.checkbox(
                "Auto-merge results into a loan",
                key="bulk_auto_merge",
                help="If checked, conditions and contacts from all scanned docs "
                     "will be merged into a selected loan.",
            )

        if _scan_to_loan:
            from crm import get_all_loans as _bulk_get_loans
            _bulk_loans = _bulk_get_loans()
            _loan_opts = ["(New Loan)"] + [
                f'{l.get("loan_num","—")} — {l.get("borrower","—")}'
                for l in _bulk_loans
            ]
            _target_loan = st.selectbox("Target loan:", _loan_opts,
                                        key="bulk_target_loan")

        _bulk_results_key = "bulk_scan_results"

        if _scan_all:
            _all_results = []
            _total = len(uploaded_files)
            _progress = st.progress(0, text="Starting bulk scan...")

            for _bi, _bf in enumerate(uploaded_files):
                _bf_type = _overrides.get(_bi, _detections[_bi]["detected_type"])
                if _bf_type == "Unknown":
                    _all_results.append({
                        "name": _bf.name,
                        "doc_type": "Unknown",
                        "success": False,
                        "error": "Document type unknown — skipped. Override the type to scan.",
                    })
                    continue

                _progress.progress(
                    int((_bi / _total) * 100),
                    text=f"Scanning {_bf.name} as {_bf_type}..."
                )
                _bf_bytes = _bf.read()
                _bf.seek(0)
                _bf_result = _bulk_proc(_bf_bytes, _bf_type)
                _bf_result["name"] = _bf.name
                _bf_result["doc_type"] = _bf_type
                _all_results.append(_bf_result)

            _progress.progress(100, text=f"Done — {_total} document(s) processed")
            st.session_state[_bulk_results_key] = _all_results
            st.rerun()

        # ── Display bulk results ───────────────────────────────────────
        _bulk_results = st.session_state.get(_bulk_results_key)
        if _bulk_results:
            st.markdown(
                '<div style="font-size:13px;font-weight:700;color:#2563eb;text-transform:uppercase;'
                'letter-spacing:0.5px;margin:12px 0 8px 0;">Scan Results</div>',
                unsafe_allow_html=True,
            )

            _success_count = sum(1 for r in _bulk_results if r.get("success"))
            _fail_count = len(_bulk_results) - _success_count

            # All conditions and contacts collected across all docs
            _all_conds = []
            _all_contacts = {}
            _all_closing = ""

            _rs1, _rs2, _rs3 = st.columns(3)
            with _rs1:
                st.markdown(
                    f'<div class="stat-card"><div class="stat-num" style="color:#111111;">'
                    f'{len(_bulk_results)}</div>'
                    f'<div class="stat-label">Documents Scanned</div></div>',
                    unsafe_allow_html=True,
                )
            with _rs2:
                st.markdown(
                    f'<div class="stat-card"><div class="stat-num" style="color:#27ae60;">'
                    f'{_success_count}</div>'
                    f'<div class="stat-label">✓ Successful</div></div>',
                    unsafe_allow_html=True,
                )
            with _rs3:
                st.markdown(
                    f'<div class="stat-card"><div class="stat-num" style="color:#e74c3c;">'
                    f'{_fail_count}</div>'
                    f'<div class="stat-label">✗ Failed / Skipped</div></div>',
                    unsafe_allow_html=True,
                )

            for _br in _bulk_results:
                _br_name = _br.get("name", "?")
                _br_dtype = _br.get("doc_type", "Unknown")
                _br_ok = _br.get("success", False)

                if not _br_ok:
                    st.markdown(
                        f'<div style="display:flex;gap:10px;align-items:center;'
                        f'background:#3d1515;border-left:3px solid #e74c3c;'
                        f'border-radius:6px;padding:8px 12px;margin-bottom:4px;">'
                        f'<span style="color:#e74c3c;font-weight:700;">✗</span>'
                        f'<span style="color:#111111;font-size:13px;font-weight:600;">'
                        f'{_br_name}</span>'
                        f'<span style="color:#e8b4b4;font-size:12px;">'
                        f'{_br_dtype} — {_br.get("error","scan failed")}</span>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                    continue

                # Process results based on doc type
                _br_summary_parts = []

                # Conditions
                _br_cond_text = _br.get("conditions", "")
                _br_conds = []
                if _br_cond_text:
                    for _cl in _br_cond_text.split("\n"):
                        _cl = _cl.strip()
                        if (_cl.startswith("|") and not _cl.startswith("| #")
                                and not _cl.startswith("|--") and not _cl.startswith("|-")):
                            _cells = [c.strip() for c in _cl.split("|") if c.strip()]
                            if len(_cells) >= 4:
                                _br_conds.append({
                                    "num": _cells[0], "desc": _cells[1],
                                    "party": _cells[2], "status": _cells[3],
                                })
                    if _br_conds:
                        _br_summary_parts.append(f"{len(_br_conds)} condition(s)")
                        _all_conds.extend(_br_conds)

                # Contacts (Purchase Contract / 1003)
                _br_data = _br.get("extracted_data")
                if _br_data and _br_dtype == "Purchase Contract":
                    _pc_names = []
                    for _k in ["buyer", "seller", "listing_agent", "selling_agent", "title"]:
                        _v = _br_data.get(_k, {})
                        _n = _v.get("name") or _v.get("company") or ""
                        if _n:
                            _pc_names.append(f"{_k}: {_n}")
                        if any(str(vv).strip() for vv in _v.values()):
                            _all_contacts[_k] = _v
                    _txn = _br_data.get("transaction", {})
                    if _txn.get("closing_date"):
                        _all_closing = _txn["closing_date"]
                    if _pc_names:
                        _br_summary_parts.append(", ".join(_pc_names[:3]))

                if _br_data and _br_dtype == "1003 Application":
                    _app_b = _br_data.get("borrower", {})
                    _app_cb = _br_data.get("co_borrower", {})
                    _app_emp = _br_data.get("employment", {})
                    for _k, _v in [("borrower", _app_b), ("co_borrower", _app_cb), ("employer", _app_emp)]:
                        if any(str(vv).strip() for vv in _v.values()):
                            _all_contacts[_k] = _v
                    if _app_b.get("name"):
                        _br_summary_parts.append(f"borrower: {_app_b['name']}")

                # Bank rules
                if _br.get("bank_rules"):
                    _br_summary_parts.append("bank analysis complete")

                _br_chars = _br.get("text_length", 0)
                _summary_str = " · ".join(_br_summary_parts) if _br_summary_parts else f"{_br_chars:,} chars extracted"

                with st.expander(f"✓ {_br_name} — {_br_dtype}", expanded=False):
                    st.markdown(
                        f'<div style="font-size:12px;color:#5c6370;margin-bottom:8px;">'
                        f'{_summary_str} · {_br_chars:,} chars</div>',
                        unsafe_allow_html=True,
                    )
                    # Show conditions if any
                    if _br_conds:
                        for _bc in _br_conds:
                            st.markdown(
                                f'<span style="color:#f1c40f;font-size:12px;">●</span> '
                                f'<span style="color:#111111;font-size:12px;">#{_bc["num"]} {_bc["desc"][:80]}</span> '
                                f'<span style="color:#5c6370;font-size:11px;">— {_bc["party"]}</span>',
                                unsafe_allow_html=True,
                            )
                    # Show bank rules if any
                    if _br.get("bank_rules"):
                        _br_raw = _br["bank_rules"].strip().split("\n")
                        for _rx in _br_raw:
                            _ptx = _rx.split("|")
                            _tgx = _ptx[0] if _ptx else ""
                            if _tgx == "SUMMARY":
                                st.markdown(
                                    f'<div style="font-size:12px;color:#333333;padding:4px 0;">'
                                    f'✓ {_ptx[1]} Passed · {_ptx[2]} Flagged · '
                                    f'⚠️ {_ptx[3]} Missing · ℹ️ {_ptx[4]} Info</div>',
                                    unsafe_allow_html=True,
                                )
                            elif _tgx == "FLAG":
                                st.markdown(
                                    f'<div style="background:#3d1515;border-left:2px solid #e74c3c;'
                                    f'border-radius:4px;padding:4px 8px;margin-bottom:2px;'
                                    f'font-size:11px;color:#111111;">'
                                    f'{_ptx[2] if len(_ptx)>2 else ""} — '
                                    f'{_ptx[3] if len(_ptx)>3 else ""}</div>',
                                    unsafe_allow_html=True,
                                )
                    # Show contacts preview if any
                    if _br_data:
                        st.markdown(
                            f'<div style="font-size:11px;color:#5c6370;margin-top:4px;">'
                            f'Extracted data: {", ".join(k for k,v in _br_data.items() if v)}</div>',
                            unsafe_allow_html=True,
                        )

            # ── Merge into loan ────────────────────────────────────────
            if _all_conds or _all_contacts:
                st.markdown("---")
                st.markdown(
                    f'<div style="background:#ffffff;border:1px solid #888;border-radius:8px;'
                    f'padding:10px;margin:8px 0;font-size:12px;color:#5c6370;">'
                    f'<b style="color:#2563eb;">Bulk scan totals:</b> '
                    f'{len(_all_conds)} condition(s) · '
                    f'{len(_all_contacts)} contact group(s)'
                    + (f' · closing date: {_all_closing}' if _all_closing else "")
                    + f'</div>',
                    unsafe_allow_html=True,
                )

                _merge_target = st.session_state.get("bulk_target_loan", "(New Loan)")
                if st.button("✓ Merge all into loan", key="bulk_merge_btn",
                             type="primary", use_container_width=True):
                    from crm import get_all_loans as _bm_loans, add_loan as _bm_add, update_loan as _bm_update
                    from crm import get_loan as _bm_get, log_activity as _bm_log

                    if _merge_target == "(New Loan)":
                        # Create a new loan from the bulk data
                        _borrow_name = (_all_contacts.get("buyer", {}).get("name")
                                        or _all_contacts.get("borrower", {}).get("name")
                                        or "Bulk Upload")
                        _bm_add(
                            loan_num=f"BULK-{_borrow_name[:8]}",
                            borrower=_borrow_name,
                            status="Pending",
                            due_date=_all_closing or "",
                            missing_docs="",
                            folder_path="",
                            closing_date=_all_closing or "",
                            conditions=_all_conds,
                            contacts=_all_contacts,
                        )
                        st.toast(f"New loan created for {_borrow_name}", icon="✓")
                    else:
                        # Merge into existing loan
                        _loans_list = _bm_loans()
                        _target_idx = [
                            f'{l.get("loan_num","—")} — {l.get("borrower","—")}'
                            for l in _loans_list
                        ].index(_merge_target) if _merge_target in [
                            f'{l.get("loan_num","—")} — {l.get("borrower","—")}'
                            for l in _loans_list
                        ] else -1
                        if _target_idx >= 0:
                            _target_id = _loans_list[_target_idx].get("id")
                            _target_loan_data = _bm_get(_target_id)
                            if _target_loan_data:
                                # Merge conditions (deduplicate)
                                _existing_conds = list(_target_loan_data.get("conditions", []))
                                _existing_descs = {c.get("desc", "").lower().strip() for c in _existing_conds}
                                _added = 0
                                for _nc in _all_conds:
                                    if _nc["desc"].lower().strip() not in _existing_descs:
                                        _nc_copy = dict(_nc)
                                        _nc_copy["num"] = str(len(_existing_conds) + 1)
                                        _existing_conds.append(_nc_copy)
                                        _added += 1
                                # Merge contacts
                                _existing_contacts = dict(_target_loan_data.get("contacts", {}))
                                for _ck, _cv in _all_contacts.items():
                                    if any(str(v).strip() for v in _cv.values()):
                                        _existing_contacts[_ck] = _cv
                                _upd = {"conditions": _existing_conds, "contacts": _existing_contacts}
                                if _all_closing and not _target_loan_data.get("closing_date"):
                                    _upd["closing_date"] = _all_closing
                                    _upd["due_date"] = _all_closing
                                _bm_update(_target_id, **_upd)
                                _bm_log(_target_id, "upload",
                                    f"Bulk scan — {_added} condition(s), "
                                    f"{len(_all_contacts)} contact group(s) merged",
                                    user=st.session_state.get("user_name", ""))
                                st.toast(f"Merged into {_merge_target}", icon="✓")

                    st.session_state.pop(_bulk_results_key, None)
                    st.rerun()

            if st.button("Remove️ Clear bulk results", key="bulk_clear_results"):
                st.session_state.pop(_bulk_results_key, None)
                st.rerun()

        return  # End of bulk mode — don't fall through to manual mode

    # ══════════════════════════════════════════════════════════════════════
    # MANUAL LABEL MODE (existing behavior)
    # ══════════════════════════════════════════════════════════════════════
    for file_idx, uploaded_file in enumerate(uploaded_files):
        fkey = f"{uploaded_file.name}_{file_idx}"
        with st.expander(f"{uploaded_file.name}", expanded=True):
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
                    "Scan Document",
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
                            import billing as _bill
                            save_result(
                                st.session_state.user_id, doc_type,
                                result["conditions"], result.get("risks", ""),
                                result.get("bank_rules", ""),
                            )
                            _bill.log_scan(st.session_state.user_id, doc_type)
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

                    st.markdown("## Bank Statement Analysis")
                    st.caption("Offline pattern scan — manual review always recommended.")

                    # ── Account Summary Card ───────────────────────────────
                    _bf = result.get("bank_fields", {})
                    if _bf:
                        _names = ", ".join(_bf.get("holder_names") or []) or "—"
                        _acct  = _bf.get("account_number") or "—"
                        _inst  = _bf.get("institution") or "—"
                        _month = _bf.get("statement_month") or ""
                        _period = ""
                        if _bf.get("period_start") and _bf.get("period_end"):
                            _period = f'{_bf["period_start"]} – {_bf["period_end"]}'
                        elif _month:
                            _period = _month
                        _beg  = f'${_bf["beginning_balance"]}' if _bf.get("beginning_balance") else "—"
                        _end  = f'${_bf["ending_balance"]}' if _bf.get("ending_balance") else "—"
                        _low  = f'${_bf["lowest_balance"]}' if _bf.get("lowest_balance") else "—"
                        _dep  = f'${_bf["deposits_total"]}' if _bf.get("deposits_total") else "—"
                        _wd   = f'${_bf["withdrawals_total"]}' if _bf.get("withdrawals_total") else "—"

                        st.markdown(
                            f'<div style="background:#fff;border:1px solid #888;border-radius:3px;'
                            f'padding:12px 16px;margin-bottom:14px;">'
                            f'<div style="font-size:12px;font-weight:700;color:#2563eb;'
                            f'text-transform:uppercase;letter-spacing:0.5px;margin-bottom:10px;">'
                            f'Account Summary</div>'
                            f'<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:8px;">'
                            # row 1
                            f'<div><div style="font-size:11px;color:#5c6370;">Account Holder(s)</div>'
                            f'<div style="font-size:13px;font-weight:600;color:#111;">{_names}</div></div>'
                            f'<div><div style="font-size:11px;color:#5c6370;">Account Number</div>'
                            f'<div style="font-size:13px;font-weight:600;color:#111;">{_acct}</div></div>'
                            f'<div><div style="font-size:11px;color:#5c6370;">Institution</div>'
                            f'<div style="font-size:13px;font-weight:600;color:#111;">{_inst}</div></div>'
                            # row 2
                            f'<div><div style="font-size:11px;color:#5c6370;">Statement Period</div>'
                            f'<div style="font-size:13px;font-weight:600;color:#111;">{_period or "—"}</div></div>'
                            f'<div><div style="font-size:11px;color:#5c6370;">Beginning Balance</div>'
                            f'<div style="font-size:13px;font-weight:600;color:#111;">{_beg}</div></div>'
                            f'<div><div style="font-size:11px;color:#5c6370;">Ending Balance</div>'
                            f'<div style="font-size:13px;font-weight:600;color:#111;">{_end}</div></div>'
                            # row 3
                            f'<div><div style="font-size:11px;color:#5c6370;">Lowest Balance</div>'
                            f'<div style="font-size:13px;font-weight:600;color:#111;">{_low}</div></div>'
                            f'<div><div style="font-size:11px;color:#5c6370;">Total Deposits</div>'
                            f'<div style="font-size:13px;font-weight:600;color:#27ae60;">{_dep}</div></div>'
                            f'<div><div style="font-size:11px;color:#5c6370;">Total Withdrawals</div>'
                            f'<div style="font-size:13px;font-weight:600;color:#c0392b;">{_wd}</div></div>'
                            f'</div></div>',
                            unsafe_allow_html=True,
                        )

                    # ── Approval Cross-Reference ───────────────────────────
                    from ai_engine import cross_reference_approval as _xref
                    _xref_key = f"xref_notes_{fkey}"
                    _xref_notes = st.text_area(
                        "Approval Condition Notes (paste to cross-reference against statement)",
                        key=_xref_key,
                        height=90,
                        placeholder="e.g. Source $4,500 deposit 01/15 from ABC Company. Verify $1,200 payment to Chase Auto.",
                        label_visibility="visible",
                    )
                    if _xref_notes.strip() and result.get("bank_raw_text"):
                        _xref_results = _xref(result["bank_raw_text"], _xref_notes)
                        if _xref_results:
                            st.markdown(
                                '<div style="font-size:12px;font-weight:700;color:#2563eb;'
                                'text-transform:uppercase;letter-spacing:0.5px;margin:10px 0 6px 0;">'
                                'Cross-Reference Results</div>',
                                unsafe_allow_html=True,
                            )
                            for _xr in _xref_results:
                                _xr_bg  = "#152a1e" if _xr["found"] else "#3d1515"
                                _xr_col = "#27ae60" if _xr["found"] else "#e74c3c"
                                _xr_lbl = "✓ Found" if _xr["found"] else "✗ Not Found"
                                _xr_icon = "amount" if _xr["type"] == "amount" else "name"
                                st.markdown(
                                    f'<div style="display:flex;gap:10px;align-items:center;'
                                    f'background:{_xr_bg};border-left:3px solid {_xr_col};'
                                    f'border-radius:3px;padding:6px 12px;margin-bottom:3px;">'
                                    f'<span style="color:{_xr_col};font-weight:700;font-size:12px;min-width:72px;">{_xr_lbl}</span>'
                                    f'<span style="color:#5c6370;font-size:11px;min-width:44px;">[{_xr_icon}]</span>'
                                    f'<span style="color:#111;font-size:13px;font-weight:600;">{_xr["query"]}</span>'
                                    f'</div>',
                                    unsafe_allow_html=True,
                                )
                    st.markdown("---")

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
                                    f'<div class="stat-label">✓ Passed</div></div>',
                                    unsafe_allow_html=True,
                                )
                            with sc2:
                                st.markdown(
                                    f'<div class="stat-card"><div class="stat-num" style="color:#e74c3c;">{flag_c}</div>'
                                    f'<div class="stat-label">Flagged</div></div>',
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
                                f'<div style="font-size:13px;font-weight:700;color:#2563eb;'
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
                                f'<div><span style="color:#333333;font-size:13px;font-weight:600;">{label}</span>'
                                f'<br><span style="color:#5c6370;font-size:12px;">{msg}</span></div></div>',
                                unsafe_allow_html=True,
                            )

                        elif tag == "FLAG":
                            num, label, msg = parts[1], parts[2], parts[3] if len(parts) > 3 else ""
                            st.markdown(
                                f'<div style="display:flex;gap:10px;align-items:flex-start;'
                                f'background:#3d1515;border-left:3px solid #e74c3c;'
                                f'border-radius:6px;padding:7px 12px;margin-bottom:3px;">'
                                f'<span style="color:#e74c3c;font-weight:700;font-size:12px;min-width:20px;">Flag</span>'
                                f'<div><span style="color:#111111;font-size:13px;font-weight:700;">{label}</span>'
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
                                f'<div><span style="color:#111111;font-size:13px;font-weight:600;">{label}</span>'
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
                                f'<div><span style="color:#111111;font-size:13px;font-weight:600;">{label}</span>'
                                f'<br><span style="color:#a8c8e8;font-size:12px;">{msg}</span></div></div>',
                                unsafe_allow_html=True,
                            )

                        elif tag == "MANUAL":
                            num, label = parts[1], parts[2] if len(parts) > 2 else ""
                            st.markdown(
                                f'<div style="display:flex;gap:10px;align-items:center;'
                                f'background:#252040;border-left:3px solid #888;'
                                f'border-radius:6px;padding:6px 12px;margin-bottom:3px;">'
                                f'<span style="color:#d1d5db;font-size:12px;min-width:20px;">View</span>'
                                f'<span style="color:#5c6370;font-size:13px;">{label}</span>'
                                f'</div>',
                                unsafe_allow_html=True,
                            )

                    # ── Fetch & Analyze from Folder ──────────────────────────
                    st.markdown("---")
                    st.markdown("### Fetch & Analyze Bank Statements from Folder")
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
                            "Search", key=f"bs_search_{fkey}",
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
                            f"<div style='font-size:13px;color:#5c6370;margin-bottom:8px;'>"
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
                                    f'<div style="font-weight:600;color:#111111;font-size:13px;">'
                                    f'{hit["file_name"]}</div>'
                                    f'<div style="font-size:11px;color:#5c6370;">'
                                    f'{hit["snippet"][:120]}...</div>',
                                    unsafe_allow_html=True,
                                )
                            with hc2:
                                st.markdown(
                                    f'<div style="font-size:12px;color:{conf_color};font-weight:700;">'
                                    f'{conf_label} confidence ({hit["score"]}%)</div>'
                                    f'<div style="font-size:11px;color:#5c6370;">{hit["reason"]}</div>',
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
                                        f"color:#2563eb;margin:10px 0 6px 0;'>"
                                        f"Analysis: {hit['file_name']}</div>",
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
                                                (_s1, _ok2, "#27ae60", "✓ Passed"),
                                                (_s2, _fl2, "#e74c3c", "Flagged"),
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
                                                f'<div style="font-size:12px;font-weight:700;color:#2563eb;'
                                                f'margin:10px 0 4px 0;text-transform:uppercase;">'
                                                f'{_pts[1] if len(_pts)>1 else ""}</div>',
                                                unsafe_allow_html=True,
                                            )
                                        elif _tag in ("OK", "FLAG", "MISSING", "INFO", "MANUAL"):
                                            _lbl2 = _pts[2] if len(_pts) > 2 else ""
                                            _msg2 = _pts[3] if len(_pts) > 3 else ""
                                            _styles = {
                                                "OK":     ("#152a1e", "#27ae60", "✓"),
                                                "FLAG":   ("#3d1515", "#e74c3c", "Flag"),
                                                "MISSING":("#3d3015", "#f1c40f", "⚠"),
                                                "INFO":   ("#1a2a3d", "#5dade2", "ℹ"),
                                                "MANUAL": ("#252040", "#d1d5db", "View"),
                                            }
                                            _bg, _bdr, _ico = _styles.get(
                                                _tag, ("#252040", "#d1d5db", "·")
                                            )
                                            st.markdown(
                                                f'<div style="display:flex;gap:8px;'
                                                f'background:{_bg};border-left:3px solid {_bdr};'
                                                f'border-radius:5px;padding:5px 10px;margin-bottom:2px;">'
                                                f'<span style="color:{_bdr};min-width:18px;">{_ico}</span>'
                                                f'<div><span style="color:#111111;font-size:12px;'
                                                f'font-weight:600;">{_lbl2}</span>'
                                                + (f'<br><span style="color:#5c6370;font-size:11px;">{_msg2}</span>' if _msg2 else "")
                                                + f'</div></div>',
                                                unsafe_allow_html=True,
                                            )

                    # ── Fraud Check (bank statements) ───────────────────────
                    st.markdown("---")
                    fc_key = f"fraud_on_{fkey}"
                    fc_col1, fc_col2 = st.columns([1, 4])
                    with fc_col1:
                        fraud_on = st.toggle("Fraud Check", key=fc_key, value=False)
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
                            f'<div style="font-size:14px;font-weight:700;color:#111111;">'
                            f'{_fc_result["summary"]}</div></div>',
                            unsafe_allow_html=True,
                        )
                        if _fc_flags:
                            for _ffl in _fc_flags:
                                _ffl_clr = {"high": "#f5b7b1", "medium": "#fdebd0"}.get(
                                    _ffl["severity"], "#333333"
                                )
                                st.markdown(
                                    f'<div style="display:flex;gap:8px;margin-bottom:4px;">'
                                    f'<span style="color:#e74c3c;font-size:14px;">⚑</span>'
                                    f'<div><span style="color:#111111;font-size:13px;font-weight:600;">'
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

                    st.markdown("## 1003 Application — Extracted Fields")
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
                            '✓ All required fields found.</div>',
                            unsafe_allow_html=True,
                        )

                    _nf = '<i style="color:#d1d5db;">not found</i>'

                    def _field(label, value, editable_key=None):
                        dot = '<span style="color:#27ae60;font-weight:700;">●</span>' if value else \
                              '<span style="color:#e74c3c;font-weight:700;">●</span>'
                        disp = value if value else _nf
                        st.markdown(
                            f'<div style="display:flex;gap:8px;align-items:baseline;margin-bottom:2px;">'
                            f'{dot}<span style="color:#5c6370;font-size:12px;min-width:140px;">{label}</span>'
                            f'<span style="color:#111111;font-size:13px;font-weight:600;">{disp}</span></div>',
                            unsafe_allow_html=True,
                        )

                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.markdown("**Borrower**")
                        _field("Name", b.get("name"))
                        _field("SSN", b.get("ssn"))
                        _field("Date of Birth", b.get("dob"))
                        _field("Phone", b.get("phone"))
                        _field("Email", b.get("email"))
                        _field("Present Address", b.get("present_address"))
                        _field("Previous Address", b.get("previous_address"))
                        st.markdown("---")
                        st.markdown("**— Employment**")
                        _field("Employer", emp.get("employer"))
                        _field("Position / Title", emp.get("position"))
                        _field("Employer Phone", emp.get("employer_phone"))
                        _field("Years on Job", emp.get("years_on_job"))
                        _field("Years in Field", emp.get("years_in_field"))
                        _field("Base Monthly Income", emp.get("base_monthly_income"))

                    with col_b:
                        st.markdown("**Co-Borrower**")
                        _field("Name", cb.get("name"))
                        _field("SSN", cb.get("ssn"))
                        _field("Employer", cb.get("employer"))
                        st.markdown("---")
                        st.markdown("**Home Loan / Property**")
                        _field("Loan Amount", loan.get("amount"))
                        _field("Loan Purpose", loan.get("purpose"))
                        _field("Term", loan.get("term"))
                        _field("Interest Rate", loan.get("interest_rate"))
                        _field("Property Address", loan.get("property_address"))
                        _field("Property Value", loan.get("property_value"))
                        _field("Property Use", loan.get("property_use"))

                    st.markdown("---")
                    pp_col1, pp_col2 = st.columns([2, 1])
                    with pp_col1:
                        st.caption("Push to Pipeline to create a tracked loan from this 1003.")
                    with pp_col2:
                        if st.button("+Push to Pipeline", key=f"push1003_{fkey}", use_container_width=True, type="primary"):
                            from crm import add_loan
                            _1003_contacts = {
                                "borrower": {"name": b.get("name",""), "phone": b.get("phone",""), "email": b.get("email",""), "address": b.get("present_address","")},
                                "co_borrower": {"name": cb.get("name",""), "phone": cb.get("phone",""), "email": cb.get("email","")},
                                "employer": {"name": emp.get("employer",""), "phone": emp.get("employer_phone",""), "position": emp.get("position","")},
                            }
                            add_loan(
                                loan_num=f"1003-{b.get('name', 'Unknown')[:8]}",
                                borrower=b.get("name", "Unknown"),
                                status="Pending",
                                due_date="",
                                missing_docs=", ".join(missing) if missing else "",
                                folder_path="",
                                contacts=_1003_contacts,
                            )
                            st.success(f"✓ Added {b.get('name', 'borrower')} to pipeline.")
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

                    st.markdown("## Purchase Contract — Extracted Fields")
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
                            '✓ All required fields found.</div>',
                            unsafe_allow_html=True,
                        )

                    _nf2 = '<i style="color:#d1d5db;">not found</i>'

                    def _cfield(label, value):
                        dot = '<span style="color:#27ae60;font-weight:700;">●</span>' if value else \
                              '<span style="color:#e74c3c;font-weight:700;">●</span>'
                        disp = value if value else _nf2
                        st.markdown(
                            f'<div style="display:flex;gap:8px;align-items:baseline;margin-bottom:2px;">'
                            f'{dot}<span style="color:#5c6370;font-size:12px;min-width:140px;">{label}</span>'
                            f'<span style="color:#111111;font-size:13px;font-weight:600;">{disp}</span></div>',
                            unsafe_allow_html=True,
                        )

                    pc1, pc2, pc3 = st.columns(3)
                    with pc1:
                        st.markdown("**— Parties**")
                        _cfield("Buyer", buyer.get("name"))
                        _cfield("Buyer Phone", buyer.get("phone"))
                        _cfield("Buyer Email", buyer.get("email"))
                        _cfield("Seller", seller.get("name"))
                        _cfield("Seller Phone", seller.get("phone"))
                        st.markdown("---")
                        st.markdown("**Home Property**")
                        _cfield("Address", prop.get("address"))

                    with pc2:
                        st.markdown("**Transaction**")
                        _cfield("Purchase Price", txn.get("purchase_price"))
                        _cfield("Closing Date", txn.get("closing_date"))
                        _cfield("Earnest Money", txn.get("earnest_money"))
                        _cfield("Down Payment", txn.get("down_payment"))
                        _cfield("Seller Concessions", txn.get("seller_concessions"))
                        st.markdown("---")
                        st.markdown("**Title Company**")
                        _cfield("Company", title.get("company"))
                        _cfield("Contact", title.get("contact"))
                        _cfield("Phone", title.get("phone"))

                    with pc3:
                        st.markdown("**Listing Agent**")
                        _cfield("Name", la.get("name"))
                        _cfield("Brokerage", la.get("brokerage"))
                        _cfield("Phone", la.get("phone"))
                        _cfield("Email", la.get("email"))
                        st.markdown("---")
                        st.markdown("**— Selling / Buyer's Agent**")
                        _cfield("Name", sa.get("name"))
                        _cfield("Brokerage", sa.get("brokerage"))
                        _cfield("Phone", sa.get("phone"))
                        _cfield("Email", sa.get("email"))

                    st.markdown("---")
                    st.markdown("**Contingencies**")
                    conc1, conc2, conc3 = st.columns(3)
                    with conc1:
                        _cfield("Inspection", cont.get("inspection"))
                    with conc2:
                        _cfield("Appraisal", cont.get("appraisal"))
                    with conc3:
                        _cfield("Financing", cont.get("financing"))

                    if addendums:
                        st.markdown("**Attach Addendums / Riders**")
                        for add in addendums:
                            st.markdown(
                                f'<div style="color:#333333;font-size:12px;margin-left:12px;">• {add}</div>',
                                unsafe_allow_html=True,
                            )

                    # ── AI re-extraction for unusual / unfamiliar contract forms ──
                    _missing_key_fields = not buyer.get("name") or not txn.get("purchase_price") or not prop.get("address")
                    _ai_key = f"pc_ai_data_{fkey}"
                    _raw_text = result.get("raw_text", "")

                    if _raw_text:
                        import ai_router as _air
                        _ai_status = _air.get_status()
                        _ai_available = _ai_status["cloud_enabled"] or _ai_status["ollama_enabled"]

                        if _ai_available:
                            _ai_hint = " (recommended — some fields appear missing)" if _missing_key_fields else ""
                            with st.expander(f"AI Extract — handles any state form{_ai_hint}", expanded=_missing_key_fields):
                                st.caption(
                                    "Regex extraction works well for standard contracts but may miss fields on "
                                    "unusual forms (MN STAR, WI WB, TX TREC, CA CAR, custom builder contracts). "
                                    "AI extraction reads the whole document and finds fields regardless of layout."
                                )
                                if st.button("Run AI Extraction", key=f"pc_ai_btn_{fkey}", type="primary"):
                                    with st.spinner("AI reading contract..."):
                                        _ai_data, _ai_log = _air.extract_purchase_contract_ai(_raw_text)
                                    if _ai_data:
                                        # Merge: AI fills blanks, doesn't overwrite confirmed regex values
                                        def _merge(regex_d, ai_d):
                                            if not isinstance(regex_d, dict) or not isinstance(ai_d, dict):
                                                return regex_d or ai_d
                                            out = dict(regex_d)
                                            for k, v in ai_d.items():
                                                if k not in out or not out[k]:
                                                    out[k] = v
                                            return out

                                        merged = {
                                            "buyer":         _merge(data.get("buyer", {}), _ai_data.get("buyer", {})),
                                            "seller":        _merge(data.get("seller", {}), _ai_data.get("seller", {})),
                                            "property":      _merge(data.get("property", {}), _ai_data.get("property", {})),
                                            "transaction":   _merge(data.get("transaction", {}), _ai_data.get("transaction", {})),
                                            "listing_agent": _merge(data.get("listing_agent", {}), _ai_data.get("listing_agent", {})),
                                            "selling_agent": _merge(data.get("selling_agent", {}), _ai_data.get("selling_agent", {})),
                                            "title":         _merge(data.get("title", {}), _ai_data.get("title", {})),
                                            "contingencies": _merge(data.get("contingencies", {}), _ai_data.get("contingencies", {})),
                                            "addendums":     data.get("addendums") or _ai_data.get("addendums", []),
                                            "missing_required": [],
                                        }
                                        st.session_state[_ai_key] = merged
                                        st.session_state.scan_results["extracted_data"] = merged
                                        st.success(f"✓ AI extraction complete. ({_ai_log})")
                                        st.rerun()
                                    else:
                                        st.warning(f"AI returned no data. ({_ai_log})")

                        elif _missing_key_fields:
                            st.info("Enable Cloud AI or Ollama in **AI Settings** to extract fields from unusual contract forms automatically.")

                    # ── Manual correction expander ──────────────────────────────
                    with st.expander("✏️ Correct fields manually", expanded=False):
                        st.caption("Edit any fields the scanner got wrong, then push to pipeline.")
                        _ec1, _ec2 = st.columns(2)
                        with _ec1:
                            _e_buyer  = st.text_input("Buyer Name",     value=buyer.get("name", ""),           key=f"e_buyer_{fkey}")
                            _e_seller = st.text_input("Seller Name",    value=seller.get("name", ""),          key=f"e_seller_{fkey}")
                            _e_addr   = st.text_input("Property Address", value=prop.get("address", ""),       key=f"e_addr_{fkey}")
                        with _ec2:
                            _e_price  = st.text_input("Purchase Price", value=txn.get("purchase_price", ""),   key=f"e_price_{fkey}")
                            _e_close  = st.text_input("Closing Date",   value=txn.get("closing_date", ""),     key=f"e_close_{fkey}")
                            _e_earn   = st.text_input("Earnest Money",  value=txn.get("earnest_money", ""),    key=f"e_earn_{fkey}")
                        if st.button("Apply Corrections", key=f"apply_corrections_{fkey}"):
                            _corrected = dict(data)
                            _corrected["buyer"]       = dict(buyer,   name=_e_buyer)
                            _corrected["seller"]      = dict(seller,  name=_e_seller)
                            _corrected["property"]    = dict(prop,    address=_e_addr)
                            _corrected["transaction"] = dict(txn,
                                purchase_price=_e_price,
                                closing_date=_e_close,
                                earnest_money=_e_earn,
                            )
                            st.session_state.scan_results["extracted_data"] = _corrected
                            st.success("✓ Corrections saved. Scroll up to see updated fields.")
                            st.rerun()

                    st.markdown("---")
                    act_c1, act_c2, act_c3 = st.columns(3)
                    with act_c1:
                        if st.button("+Push to Pipeline", key=f"pushpc_{fkey}", use_container_width=True, type="primary"):
                            from crm import add_loan
                            _pc_contacts = {
                                "buyer": {"name": buyer.get("name",""), "phone": buyer.get("phone",""), "email": buyer.get("email","")},
                                "seller": {"name": seller.get("name",""), "phone": seller.get("phone","")},
                                "listing_agent": {"name": la.get("name",""), "brokerage": la.get("brokerage",""), "phone": la.get("phone",""), "email": la.get("email","")},
                                "selling_agent": {"name": sa.get("name",""), "brokerage": sa.get("brokerage",""), "phone": sa.get("phone",""), "email": sa.get("email","")},
                                "title": {"company": title.get("company",""), "contact": title.get("contact",""), "phone": title.get("phone","")},
                            }
                            _pc_conditions = []
                            add_loan(
                                loan_num=f"PC-{buyer.get('name', 'Unknown')[:8]}",
                                borrower=buyer.get("name", "Unknown"),
                                status="Pending",
                                due_date=txn.get("closing_date", ""),
                                missing_docs=", ".join(missing) if missing else "",
                                folder_path="",
                                closing_date=txn.get("closing_date", ""),
                                conditions=_pc_conditions,
                                contacts=_pc_contacts,
                            )
                            st.success(f"✓ Added {buyer.get('name', 'buyer')} to pipeline.")
                    with act_c2:
                        if title.get("company") and st.button("Email️ Draft Title Email", key=f"titlemailpc_{fkey}", use_container_width=True):
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
                    "Needed":          {"emoji": "●", "color": "#f1c40f", "label": "Needed"},
                    "Requested":       {"emoji": "●", "color": "#e67e22", "label": "Requested"},
                    "Important":       {"emoji": "●", "color": "#e74c3c", "label": "Important"},
                    "Ready to Clear":  {"emoji": "●", "color": "#27ae60", "label": "Ready to Clear"},
                    "Cleared":         {"emoji": "●", "color": "#5dade2", "label": "Cleared"},
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
                                st.caption(f"{saved_notes}")

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
                                fetch_btn = st.button("Fetch from Folder",
                                    key=f"fetchbtn_{fkey}_{cnum}", use_container_width=True)
                            with fb:
                                guide_btn = st.button("Check Guidelines",
                                    key=f"guidebtn_{fkey}_{cnum}", use_container_width=True)
                            if fc:
                                with fc:
                                    bs_fetch_btn = st.button(
                                        "Bank Find & Analyze Bank Stmt",
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
                                                f'<div style="font-weight:600;color:#111111;font-size:12px;">'
                                                f'{_bht["file_name"]}</div>'
                                                f'<div style="font-size:11px;color:#5c6370;">'
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
                                                            f'<div style="font-size:12px;color:#333333;padding:4px 0;">'
                                                            f'✓ {_ox} Passed &nbsp; {_fx} Flagged &nbsp; '
                                                            f'⚠️ {_mx} Missing &nbsp; ℹ️ {_ix} Info</div>',
                                                            unsafe_allow_html=True,
                                                        )
                                                    elif _tgx == "FLAG":
                                                        st.markdown(
                                                            f'<div style="background:#3d1515;border-left:2px solid #e74c3c;'
                                                            f'border-radius:4px;padding:4px 8px;margin-bottom:2px;font-size:11px;color:#111111;">'
                                                            f'{_ptx[2] if len(_ptx)>2 else ""} — {_ptx[3] if len(_ptx)>3 else ""}</div>',
                                                            unsafe_allow_html=True,
                                                        )
                                                    elif _tgx == "MISSING":
                                                        st.markdown(
                                                            f'<div style="background:#3d3015;border-left:2px solid #f1c40f;'
                                                            f'border-radius:4px;padding:4px 8px;margin-bottom:2px;font-size:11px;color:#111111;">'
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
                                        dot = "●" if score >= 80 else ("●" if score >= 65 else "●")
                                        pages_str = f" | Pages: {', '.join(str(p) for p in m['matched_pages'])}" if m["matched_pages"] else ""
                                        st.markdown(f"{dot} **{m['file_name']}** — {m['match_type']} ({score}%){pages_str}")
                                        st.caption(f"Folder {m['file_path']}")
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
                                        dot = "●" if score >= 80 else ("●" if score >= 65 else "●")
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
                st.markdown("### Email️ Draft Email")
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
                            f'<div style="padding-top:8px; font-size:13px; color:#333333;">'
                            f'✓ {len(pre_selected)} condition(s) checked</div>',
                            unsafe_allow_html=True,
                        )
                    else:
                        st.caption("Check conditions below to include them")

                _draft_col1, _draft_col2 = st.columns([1, 1])
                with _draft_col1:
                    draft_clicked = st.button("Email️ Draft Email", key=f"draft_{fkey}",
                                              type="primary", use_container_width=True)
                with _draft_col2:
                    ai_draft_clicked = st.button("Draft with AI", key=f"odraft_{fkey}",
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

                if ai_draft_clicked:
                    import ai_router as _ar
                    backend = _ar.get_preferred_backend()
                    if backend == "script":
                        st.warning("AI is set to Script Only. Go to AI Settings to enable Cloud AI or Ollama.")
                    else:
                        conds_for_ai = pre_selected if pre_selected else []
                        _backend_label = "Cloud AI" if backend == "cloud" else "Ollama"
                        with st.spinner(f"Drafting with {_backend_label}…"):
                            _ai_text, _ai_log = _ar.draft_email_enhanced(
                                conds_for_ai, recipient, email_lang
                            )
                        if _ai_text:
                            st.container(border=True).markdown(_ai_text)
                            st.caption(f"AI draft · {_ai_log.split('|')[-1].strip() if '|' in _ai_log else ''}")
                        else:
                            st.info("AI didn't return a draft — check AI Settings to verify your backend is configured.")

                st.markdown("---")

                # ── Quick Copy + Export row ──────────────────────────────────
                _qc_label = "Quick Copy & Export"
                with st.expander(_qc_label, expanded=False):
                    # Build loan context from pipeline match
                    _loan_info = {}
                    try:
                        from crm import get_all_loans as _gcl
                        for _pl in _gcl():
                            _pf = _pl.get("folder_path", "")
                            _pn = _pl.get("loan_num", "")
                            if (_pf and result.get("text_length", 0) > 0) or True:
                                # Best match: look at borrower from structured result
                                _struct = result.get("extracted_data", {})
                                _bname = (_struct.get("borrower", {}).get("name", "") or
                                          _struct.get("buyer", {}).get("name", ""))
                                if _bname and _bname.lower() in _pl.get("borrower", "").lower():
                                    _loan_info = _pl
                                    break
                    except Exception:
                        pass

                    # Quick-copy code blocks for key fields
                    _struct = result.get("extracted_data", {})
                    if _struct:
                        _b = _struct.get("borrower", _struct.get("buyer", {}))
                        _copy_fields = [
                            ("Borrower Name",    _b.get("name", "")),
                            ("SSN",              _b.get("ssn", "")),
                            ("Property Address", (_struct.get("loan", _struct.get("property", {}))
                                                 .get("property_address",
                                                      _struct.get("property", {}).get("address", "")))),
                            ("Loan Amount",      _struct.get("loan", _struct.get("transaction", {}))
                                                 .get("amount",
                                                      _struct.get("transaction", {}).get("purchase_price", ""))),
                            ("Closing Date",     _struct.get("transaction", {}).get("closing_date", "")),
                        ]
                        _has_fields = any(v for _, v in _copy_fields)
                        if _has_fields:
                            st.markdown("**Copy key fields** (click the copy icon)")
                            _cf_cols = st.columns(min(len([f for f in _copy_fields if f[1]]), 3))
                            _ci = 0
                            for _lbl, _val in _copy_fields:
                                if _val:
                                    with _cf_cols[_ci % len(_cf_cols)]:
                                        st.caption(_lbl)
                                        st.code(_val, language=None)
                                    _ci += 1
                        st.markdown("---")

                    # Download buttons
                    _dl1, _dl2 = st.columns(2)
                    with _dl1:
                        _csv_bytes = None
                        try:
                            import export as _exp
                            _csv_bytes = _exp.conditions_to_csv(condition_rows, _loan_info)
                        except Exception:
                            pass
                        if _csv_bytes:
                            _csv_fname = f"conditions_{fkey}.csv"
                            st.download_button(
                                "⬇️ Download CSV",
                                data=_csv_bytes,
                                file_name=_csv_fname,
                                mime="text/csv",
                                use_container_width=True,
                                key=f"dl_csv_{fkey}",
                            )
                    with _dl2:
                        _html_bytes = None
                        try:
                            import export as _exp
                            _proc = st.session_state.get("user_name", "")
                            _snap_html = _exp.snapshot_html(
                                condition_rows, _loan_info, doc_type, _proc
                            )
                            _html_bytes = _snap_html.encode("utf-8")
                        except Exception:
                            pass
                        if _html_bytes:
                            _html_fname = f"snapshot_{fkey}.html"
                            st.download_button(
                                "Condition Snapshot (print-to-PDF)",
                                data=_html_bytes,
                                file_name=_html_fname,
                                mime="text/html",
                                use_container_width=True,
                                key=f"dl_snap_{fkey}",
                                help="Download → open in browser → Ctrl+P → Save as PDF",
                            )

                st.markdown("### Conditions")

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
                    with st.expander(f"● Cleared ({len(cleared_conds)})", expanded=False):
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
                    _fraud_on2 = st.toggle("Fraud Check", key=_fc2_key, value=False)
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
                        f'<div style="font-size:14px;font-weight:700;color:#111111;">'
                        f'{_fc2_result["summary"]}</div></div>',
                        unsafe_allow_html=True,
                    )
                    for _ffl2 in _fc2_result.get("flags", []):
                        _ffl2_clr = {"high": "#f5b7b1", "medium": "#fdebd0"}.get(
                            _ffl2["severity"], "#333333"
                        )
                        st.markdown(
                            f'<div style="display:flex;gap:8px;margin-bottom:4px;">'
                            f'<span style="color:#e74c3c;font-size:14px;">⚑</span>'
                            f'<div><span style="color:#111111;font-size:13px;font-weight:600;">'
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
        STATUS_OPTIONS, STATUS_EMOJI, STATUS_COLORS,
        get_trash, restore_loan, permanently_delete, empty_trash,
        get_retention_days, set_retention_days, RETENTION_OPTIONS,
        log_activity,
    )

    import json as _json

    st.markdown(
        '<div style="margin-bottom:2px;">'
        '<span style="font-size:16px;font-weight:700;color:#111;">My Pipeline</span>'
        '&nbsp;&nbsp;<span style="font-size:11px;color:#5c6370;">Track loans by status</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    # ── Closing Countdown & Lock Expiry Alert Bar ───────────────────────────
    try:
        from datetime import date as _cd_date, datetime as _cd_dt
        _cd_loans = get_all_loans()
        _cd_today = _cd_date.today()
        _urgents = []
        for _cdl in _cd_loans:
            if _cdl.get("status") in ("Cleared", "Closed"):
                continue
            _due = _cdl.get("closing_date") or _cdl.get("due_date", "")
            _lck = _cdl.get("lock_expiry", "")
            _cmt = _cdl.get("commitment_date", "")
            _bor = _cdl.get("borrower", "")
            _num = _cdl.get("loan_num", "")
            _lid = _cdl.get("id")
            if _due:
                try:
                    _due_d = _cd_dt.strptime(_due, "%Y-%m-%d").date()
                    _days  = (_due_d - _cd_today).days
                    if _days <= 10:
                        _urgents.append((_days, _num, _bor, "closing", _due, _lck, _cmt, _lid))
                except Exception:
                    pass
            if _lck:
                try:
                    _lck_d = _cd_dt.strptime(_lck, "%Y-%m-%d").date()
                    _ldays = (_lck_d - _cd_today).days
                    if _ldays <= 14:
                        _urgents.append((_ldays, _num, _bor, "lock", _due, _lck, _cmt, _lid))
                except Exception:
                    pass
            if _cmt:
                try:
                    _cmt_d = _cd_dt.strptime(_cmt, "%Y-%m-%d").date()
                    _cdays = (_cmt_d - _cd_today).days
                    if _cdays <= 14:
                        _urgents.append((_cdays, _num, _bor, "commitment", _due, _lck, _cmt, _lid))
                except Exception:
                    pass
        if _urgents:
            _urgents.sort(key=lambda x: x[0])
            # Deduplicate by loan ID — keep the most urgent entry per loan
            _seen_ids = set()
            _deduped = []
            for item in _urgents:
                _item_lid = item[7]
                if _item_lid not in _seen_ids:
                    _seen_ids.add(_item_lid)
                    _deduped.append(item)
            st.markdown(
                '<div style="margin-bottom:4px;">'
                '<span style="font-size:10px;color:#2563eb;font-weight:700;letter-spacing:0.5px;'
                'text-transform:uppercase;">Upcoming Deadlines</span></div>',
                unsafe_allow_html=True,
            )
            def _cal_svg(color):
                return (
                    f'<svg width="16" height="16" viewBox="0 0 16 16" fill="none" '
                    f'xmlns="http://www.w3.org/2000/svg" style="vertical-align:middle;margin-right:4px;">'
                    f'<rect x="1" y="3" width="14" height="12" rx="1.5" stroke="{color}" stroke-width="1.5" fill="none"/>'
                    f'<line x1="1" y1="7" x2="15" y2="7" stroke="{color}" stroke-width="1.5"/>'
                    f'<line x1="5" y1="1" x2="5" y2="5" stroke="{color}" stroke-width="1.5" stroke-linecap="round"/>'
                    f'<line x1="11" y1="1" x2="11" y2="5" stroke="{color}" stroke-width="1.5" stroke-linecap="round"/>'
                    f'<rect x="4" y="9" width="2.5" height="2.5" rx="0.5" fill="{color}"/>'
                    f'<rect x="6.75" y="9" width="2.5" height="2.5" rx="0.5" fill="{color}"/>'
                    f'</svg>'
                )

            for _days, _num, _bor, _kind, _closing, _lock, _commit, _ulid in _deduped[:6]:
                if _days < 0:
                    _label = f"EXPIRED {abs(_days)}d ago"
                    _color = "#c62828"
                    _bg    = "#ffebee"
                    _bdr   = "#ef9a9a"
                elif _days == 0:
                    _label = "DUE TODAY"
                    _color = "#c62828"
                    _bg    = "#ffebee"
                    _bdr   = "#ef9a9a"
                elif _days <= 3:
                    _label = f"{_days}d left"
                    _color = "#b71c1c"
                    _bg    = "#ffebee"
                    _bdr   = "#ef9a9a"
                elif _days <= 7:
                    _label = f"{_days}d left"
                    _color = "#e65100"
                    _bg    = "#fff3e0"
                    _bdr   = "#ffcc80"
                else:
                    _label = f"{_days}d left"
                    _color = "#2e7d32"
                    _bg    = "#e8f5e9"
                    _bdr   = "#c8e6c9"
                _close_display = _closing if _closing else "—"
                _lock_display  = _lock if _lock else "—"
                _row_col, _btn_col = st.columns([5, 1])
                with _row_col:
                    st.markdown(
                        f'<div style="background:{_bg};border:1px solid {_bdr};border-left:3px solid {_color};'
                        f'border-radius:3px;padding:5px 10px;margin-bottom:2px;display:flex;align-items:center;gap:6px;">'
                        f'{_cal_svg(_color)}'
                        f'<div>'
                        f'<span style="color:{_color};font-size:11px;font-weight:700;">{_label}</span>'
                        f'&nbsp;&nbsp;<span style="color:#374151;font-size:12px;font-weight:600;">#{_num} {_bor}</span>'
                        f'<br><span style="color:#5c6370;font-size:10px;">'
                        f'Close: {_close_display} &nbsp;·&nbsp; Lock: {_lock_display}</span>'
                        f'</div></div>',
                        unsafe_allow_html=True,
                    )
                with _btn_col:
                    if st.button("Open", key=f"urgent_{_kind}_{_ulid}", use_container_width=True):
                        st.session_state.detail_loan_id = _ulid
                        st.session_state.page = "loan_detail"
                        st.rerun()
    except Exception:
        pass

    from db import get_all_users
    all_users = get_all_users()
    user_names = ["(Unassigned)"] + [
        u.get("display_name") or u["email"] for u in all_users
    ]
    my_name = st.session_state.get("user_name", "")

    # ── Top action bar ──────────────────────────────────────────────────────
    tb1, tb2, tb3, tb4, tb5 = st.columns([1.5, 2, 2.5, 2, 1])
    with tb1:
        if st.button("+Add Loan", use_container_width=True, type="primary"):
            st.session_state.pipeline_add_open = not st.session_state.get("pipeline_add_open", False)
    with tb2:
        filter_status = st.selectbox(
            "Status", ["All"] + STATUS_OPTIONS,
            key="pipeline_filter",
        )
    with tb3:
        search_loan = st.text_input(
            "Search", placeholder="Loan # or borrower name",
            key="pipeline_search",
        )
    with tb4:
        sort_by = st.selectbox(
            "Sort by", [
                "Newest",
                "Closing Date",
                "Lock Expiry",
                "Last Name",
                "First Name",
                "Loan #",
                "Status",
            ],
            key="pipeline_sort",
        )
    with tb5:
        st.markdown('<div style="height:24px;"></div>', unsafe_allow_html=True)
        my_loans_only = st.checkbox("My loans", key="pipeline_myloans")

    # ── Add Loan form ────────────────────────────────────────────────────────
    if st.session_state.get("pipeline_add_open"):
        with st.container(border=True):
            st.markdown(
                '<span style="font-size:14px;font-weight:700;color:#111111;">Add New Loan</span>',
                unsafe_allow_html=True,
            )

            # ── Bulk Upload — auto-fill from documents ────────────────
            _add_bulk_key = "add_loan_bulk"
            with st.expander("Upload documents to auto-fill loan details", expanded=not st.session_state.get(_add_bulk_key)):
                _add_bulk_files = st.file_uploader(
                    "Drop your loan package — approval letter, purchase contract, 1003, etc.",
                    type=["pdf"], accept_multiple_files=True,
                    key="add_loan_bulk_upload",
                    label_visibility="collapsed",
                )

                if _add_bulk_files and st.button("Scan & Auto-Fill",
                                                  key="add_loan_bulk_scan",
                                                  type="primary", use_container_width=True):
                    from ai_engine import detect_doc_type as _ald, process_document as _alp
                    from ai_engine import extract_contacts as _alc
                    import re as _al_re

                    _al_progress = st.progress(0, text="Scanning documents...")
                    _al_total = len(_add_bulk_files)

                    _al_borrower = ""
                    _al_co_borrower = ""
                    _al_loan_num = ""
                    _al_closing = ""
                    _al_lock = ""
                    _al_commitment = ""
                    _al_conditions = []
                    _al_contacts = {}
                    _al_missing = []
                    _al_scanned = []

                    for _ai, _af in enumerate(_add_bulk_files):
                        _al_progress.progress(
                            int((_ai / _al_total) * 100),
                            text=f"Scanning {_af.name}..."
                        )
                        _af_bytes = _af.read()
                        _af.seek(0)

                        # Auto-detect type
                        _det = _ald(_af_bytes)
                        _dtype = _det["doc_type"]
                        if _dtype == "Unknown":
                            _al_scanned.append({"name": _af.name, "type": "Unknown", "status": "skipped"})
                            continue

                        # Process
                        _result = _alp(_af_bytes, _dtype)
                        if not _result.get("success"):
                            _al_scanned.append({"name": _af.name, "type": _dtype, "status": "failed"})
                            continue

                        _al_scanned.append({"name": _af.name, "type": _dtype, "status": "ok"})

                        # ── Pull from extracted_data FIRST (engine already parsed these) ──
                        _ext = _result.get("extracted_data")
                        if _ext and _dtype == "Purchase Contract":
                            for _k in ["buyer", "seller", "listing_agent", "selling_agent", "title"]:
                                _v = _ext.get(_k, {})
                                if any(str(vv).strip() for vv in _v.values()):
                                    _al_contacts[_k] = _v
                            _txn = _ext.get("transaction", {})
                            if _txn.get("closing_date") and not _al_closing:
                                _raw_cd = _txn["closing_date"]
                                # Normalize to YYYY-MM-DD
                                from datetime import datetime as _cd_dt
                                _cd_fmts = [
                                    "%B %d, %Y", "%B %d %Y", "%b %d, %Y", "%b %d %Y",
                                    "%m/%d/%Y", "%m-%d-%Y", "%m/%d/%y", "%m-%d-%y",
                                    "%m.%d.%Y", "%m.%d.%y", "%Y-%m-%d",
                                ]
                                for _cf in _cd_fmts:
                                    try:
                                        _al_closing = _cd_dt.strptime(_raw_cd.strip(), _cf).strftime("%Y-%m-%d")
                                        break
                                    except ValueError:
                                        continue
                                if not _al_closing:
                                    _al_closing = _raw_cd  # keep raw if no format matched
                            if _txn.get("purchase_price"):
                                _al_scanned[-1]["price"] = _txn["purchase_price"]
                            if not _al_borrower:
                                _al_borrower = (_ext.get("buyer", {}).get("name") or "")
                            if not _al_loan_num:
                                _al_loan_num = (_ext.get("transaction", {}).get("mls_number") or "")

                        if _ext and _dtype == "1003 Application":
                            for _k in ["borrower", "co_borrower", "employment"]:
                                _v = _ext.get(_k, {})
                                if any(str(vv).strip() for vv in _v.values()):
                                    _al_contacts[_k] = _v
                            if not _al_borrower:
                                _al_borrower = (_ext.get("borrower", {}).get("name") or "")
                            # 1003 often has loan number
                            if not _al_loan_num:
                                _al_loan_num = (_ext.get("loan_number") or _ext.get("Loan Number") or "")

                        # ── Regex mining on raw text for anything not already found ──
                        from pypdf import PdfReader as _AL_PR
                        import io as _al_io
                        try:
                            _al_reader = _AL_PR(_al_io.BytesIO(_af_bytes))
                            _al_text = "\n".join((p.extract_text() or "") for p in _al_reader.pages[:5])
                        except Exception:
                            _al_text = ""

                        if _al_text:
                            # ── Use extract_contacts() — same logic as the regular scanner ──
                            from ai_engine import extract_contacts as _ec_fn
                            _ec_result = _ec_fn(_al_text)
                            # Parse borrower from the markdown table row: | Name | Primary Borrower | ...
                            if not _al_borrower:
                                _ec_bor_m = _al_re.search(r'\|\s*([^|]+?)\s*\|\s*Primary Borrower\s*\|', _ec_result)
                                if _ec_bor_m:
                                    _ec_bor = _ec_bor_m.group(1).strip()
                                    if _ec_bor and _ec_bor != "Not found":
                                        _al_borrower = _ec_bor

                            # Parse loan number: - Loan Number: XXXXX
                            if not _al_loan_num:
                                _ec_ln_m = _al_re.search(r'-\s*Loan\s*Number\s*:\s*(.+)', _ec_result)
                                if _ec_ln_m:
                                    _ec_ln = _ec_ln_m.group(1).strip()
                                    if _ec_ln and _ec_ln != "Not found":
                                        _al_loan_num = _ec_ln

                            # Fallback: mine loan number with regex (relaxed — allow dashes, shorter numbers)
                            if not _al_loan_num:
                                for _lp in [
                                    r'(?i)loan\s*(?:#|number|num|no\.?)\s*[:\s]*([\d][\d\-]{4,}[\d])',
                                    r'(?i)case\s*(?:#|number|no\.?)\s*[:\s]*([\d][\d\-]{4,}[\d])',
                                    r'(?i)file\s*(?:#|number|no\.?)\s*[:\s]*([\d][\d\-]{4,}[\d])',
                                    r'(?i)(?:loan|ref|reference)\s*#?\s*[:\s]*([\d][\d\-]{4,}[\d])',
                                    r'(?i)fha\s*(?:case)?\s*#?\s*[:\s]*([\d][\d\-]{4,}[\d])',
                                ]:
                                    _m = _al_re.search(_lp, _al_text)
                                    if _m:
                                        _al_loan_num = _m.group(1).strip()
                                        break

                            # Mine closing date (relaxed — many formats)
                            if not _al_closing:
                                for _dp in [
                                    r'(?i)closing\s*date\s*[:\s]*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})',
                                    r'(?i)settlement\s*date\s*[:\s]*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})',
                                    r'(?i)close\s*(?:of\s*escrow|by|on)\s*[:\s]*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})',
                                    r'(?i)(?:est(?:imated)?\.?\s*)?close?\s*[:\s]*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})',
                                    r'(?i)(?:contract|target)\s*(?:close|closing)\s*[:\s]*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})',
                                ]:
                                    _m = _al_re.search(_dp, _al_text)
                                    if _m:
                                        _raw_date = _m.group(1)
                                        from datetime import datetime as _al_dt
                                        for _fmt in ["%m/%d/%Y", "%m-%d-%Y", "%m/%d/%y", "%m-%d-%y",
                                                     "%m.%d.%Y", "%m.%d.%y"]:
                                            try:
                                                _al_closing = _al_dt.strptime(_raw_date, _fmt).strftime("%Y-%m-%d")
                                                break
                                            except ValueError:
                                                continue
                                        if not _al_closing:
                                            _al_closing = _raw_date
                                        break

                            # Mine lock expiry (relaxed)
                            if not _al_lock:
                                for _lkp in [
                                    r'(?i)(?:lock|rate\s*lock)\s*(?:expir|expiration|expires?|exp)\s*[:\s]*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})',
                                    r'(?i)lock\s*(?:thru|through|until|to)\s*[:\s]*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})',
                                ]:
                                    _m = _al_re.search(_lkp, _al_text)
                                    if _m:
                                        _raw_lock = _m.group(1)
                                        from datetime import datetime as _al_dt2
                                        for _fmt in ["%m/%d/%Y", "%m-%d-%Y", "%m/%d/%y", "%m-%d-%y",
                                                     "%m.%d.%Y", "%m.%d.%y"]:
                                            try:
                                                _al_lock = _al_dt2.strptime(_raw_lock, _fmt).strftime("%Y-%m-%d")
                                                break
                                            except ValueError:
                                                continue
                                        if not _al_lock:
                                            _al_lock = _raw_lock
                                        break

                            # Mine commitment date (from approval/commitment letters)
                            if not _al_commitment:
                                for _cmp in [
                                    r'(?i)commitment\s*(?:expir(?:es?|ation)|expires?|exp)\s*[:\s]*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})',
                                    r'(?i)commitment\s*(?:date|valid\s*(?:thru|through|until))\s*[:\s]*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})',
                                    r'(?i)(?:this|the)\s*commitment\s*(?:expires?|is\s*valid)\s*(?:on|until|through|thru)\s*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})',
                                    r'(?i)commitment\s*(?:letter\s*)?(?:expir|valid)\s*[:\s]*([A-Za-z]+\s+\d{1,2},?\s+\d{4})',
                                    r'(?i)(?:approv(?:al|ed)\s*(?:letter\s*)?(?:expir|valid))\s*[:\s]*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})',
                                    r'(?i)(?:approv(?:al|ed)\s*(?:letter\s*)?(?:expir|valid))\s*[:\s]*([A-Za-z]+\s+\d{1,2},?\s+\d{4})',
                                ]:
                                    _m = _al_re.search(_cmp, _al_text)
                                    if _m:
                                        _raw_commit = _m.group(1)
                                        from datetime import datetime as _al_dt3
                                        for _fmt in ["%m/%d/%Y", "%m-%d-%Y", "%m/%d/%y", "%m-%d-%y",
                                                     "%m.%d.%Y", "%m.%d.%y",
                                                     "%B %d, %Y", "%B %d %Y", "%b %d, %Y", "%b %d %Y"]:
                                            try:
                                                _al_commitment = _al_dt3.strptime(_raw_commit.strip(), _fmt).strftime("%Y-%m-%d")
                                                break
                                            except ValueError:
                                                continue
                                        if not _al_commitment:
                                            _al_commitment = _raw_commit
                                        break

                        # Collect conditions
                        _cond_text = _result.get("conditions", "")
                        if _cond_text:
                            for _cl in _cond_text.split("\n"):
                                _cl = _cl.strip()
                                if (_cl.startswith("|") and not _cl.startswith("| #")
                                        and not _cl.startswith("|--") and not _cl.startswith("|-")):
                                    _cells = [c.strip() for c in _cl.split("|") if c.strip()]
                                    if len(_cells) >= 4:
                                        _al_conditions.append({
                                            "num": _cells[0], "desc": _cells[1],
                                            "party": _cells[2], "status": _cells[3],
                                        })

                    _al_progress.progress(100, text="Done!")

                    # Renumber conditions
                    for _ci, _c in enumerate(_al_conditions):
                        _c["num"] = str(_ci + 1)

                    # Store auto-filled data
                    st.session_state[_add_bulk_key] = {
                        "borrower": _al_borrower,
                        "loan_num": _al_loan_num,
                        "closing": _al_closing,
                        "lock": _al_lock,
                        "commitment": _al_commitment,
                        "conditions": _al_conditions,
                        "contacts": _al_contacts,
                        "scanned": _al_scanned,
                        "fresh": True,  # flag so prefill overwrites on next render
                    }
                    # Force-push into widget keys NOW before rerun
                    if _al_loan_num:
                        st.session_state["pl_new_num"] = _al_loan_num
                    if _al_borrower:
                        st.session_state["pl_new_borrower"] = _al_borrower
                    if _al_closing:
                        from datetime import datetime as _push_dt
                        _push_fmts = ["%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y", "%m/%d/%y",
                                      "%B %d, %Y", "%B %d %Y", "%b %d, %Y", "%b %d %Y",
                                      "%m.%d.%Y", "%m.%d.%y"]
                        for _pf in _push_fmts:
                            try:
                                st.session_state["pl_new_closing"] = _push_dt.strptime(_al_closing.strip(), _pf).date()
                                break
                            except ValueError:
                                continue
                    if _al_lock:
                        from datetime import datetime as _push_dt2
                        for _pf2 in ["%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y", "%m/%d/%y",
                                     "%B %d, %Y", "%B %d %Y", "%b %d, %Y", "%b %d %Y",
                                     "%m.%d.%Y", "%m.%d.%y"]:
                            try:
                                st.session_state["pl_new_lock"] = _push_dt2.strptime(_al_lock.strip(), _pf2).date()
                                break
                            except ValueError:
                                continue
                    if _al_commitment:
                        from datetime import datetime as _push_dt3
                        for _pf3 in ["%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y", "%m/%d/%y",
                                     "%B %d, %Y", "%B %d %Y", "%b %d, %Y", "%b %d %Y",
                                     "%m.%d.%Y", "%m.%d.%y"]:
                            try:
                                st.session_state["pl_new_commitment"] = _push_dt3.strptime(_al_commitment.strip(), _pf3).date()
                                break
                            except ValueError:
                                continue
                    st.rerun()

                # Show scan results summary
                _bulk_data = st.session_state.get(_add_bulk_key)
                if _bulk_data:
                    _sc = _bulk_data["scanned"]
                    _ok = sum(1 for s in _sc if s["status"] == "ok")
                    _skip = sum(1 for s in _sc if s["status"] != "ok")
                    st.markdown(
                        f'<div style="background:#ffffff;border:1px solid #888;border-radius:8px;'
                        f'padding:10px;margin:6px 0;font-size:12px;color:#5c6370;">'
                        f'<b style="color:#2563eb;">Scanned {len(_sc)} file(s):</b> '
                        f'{_ok} processed, {_skip} skipped<br>'
                        + "".join(
                            f'<span style="color:{"#27ae60" if s["status"]=="ok" else "#e74c3c"};">'
                            f'{"✓" if s["status"]=="ok" else "✗"}</span> '
                            f'{s["name"]} → {s["type"]}&nbsp;&nbsp;'
                            for s in _sc
                        )
                        + f'</div>',
                        unsafe_allow_html=True,
                    )
                    # Show what was extracted
                    _parts = []
                    if _bulk_data["borrower"]:
                        _parts.append(f'Borrower: <b>{_bulk_data["borrower"]}</b>')
                    if _bulk_data["loan_num"]:
                        _parts.append(f'Loan #: <b>{_bulk_data["loan_num"]}</b>')
                    if _bulk_data["closing"]:
                        _parts.append(f'Closing: <b>{_bulk_data["closing"]}</b>')
                    if _bulk_data["lock"]:
                        _parts.append(f'Lock: <b>{_bulk_data["lock"]}</b>')
                    if _bulk_data["conditions"]:
                        _parts.append(f'<b>{len(_bulk_data["conditions"])}</b> condition(s)')
                    if _bulk_data["contacts"]:
                        _parts.append(f'<b>{len(_bulk_data["contacts"])}</b> contact group(s)')
                    if _parts:
                        st.markdown(
                            f'<div style="background:#152a1e;border:1px solid #1a4a2a;border-radius:8px;'
                            f'padding:10px;margin:4px 0;font-size:12px;color:#a8d8a8;">'
                            f'✓ Auto-filled: {" &nbsp;·&nbsp; ".join(_parts)}'
                            f'</div>',
                            unsafe_allow_html=True,
                        )
                    # Show what was NOT found so user knows what to fill manually
                    _not_found = []
                    if not _bulk_data.get("borrower"):
                        _not_found.append("Borrower name")
                    if not _bulk_data.get("loan_num"):
                        _not_found.append("Loan #")
                    if not _bulk_data.get("closing"):
                        _not_found.append("Closing date")
                    if not _bulk_data.get("lock"):
                        _not_found.append("Lock expiry")
                    if _not_found:
                        st.markdown(
                            f'<div style="background:#3d2808;border:1px solid #5a4400;border-radius:8px;'
                            f'padding:8px 12px;margin:4px 0;font-size:12px;color:#f1c40f;">'
                            f'⚠️ Not found in documents: <b>{", ".join(_not_found)}</b> '
                            f'— fill these in manually below.</div>',
                            unsafe_allow_html=True,
                        )
                    if st.button("Remove️ Clear scan results", key="add_loan_bulk_clear"):
                        st.session_state.pop(_add_bulk_key, None)
                        for _k in ["pl_new_num", "pl_new_borrower", "pl_new_closing",
                                    "pl_new_lock"]:
                            st.session_state.pop(_k, None)
                        st.rerun()

            # ── Manual fields (pre-filled from bulk if available) ─────
            _bf = st.session_state.get(_add_bulk_key, {})

            # Force-push extracted values into widget keys
            # Always overwrite if fresh scan, otherwise only fill empty fields
            _is_fresh = _bf.get("fresh", False)
            if _bf:
                if _bf.get("loan_num") and (_is_fresh or not st.session_state.get("pl_new_num")):
                    st.session_state["pl_new_num"] = _bf["loan_num"]
                if _bf.get("borrower") and (_is_fresh or not st.session_state.get("pl_new_borrower")):
                    st.session_state["pl_new_borrower"] = _bf["borrower"]
                if _bf.get("closing") and _is_fresh:
                    try:
                        from datetime import datetime as _pf_dt
                        st.session_state["pl_new_closing"] = _pf_dt.strptime(_bf["closing"], "%Y-%m-%d").date()
                    except Exception:
                        pass
                if _bf.get("lock") and _is_fresh:
                    try:
                        from datetime import datetime as _pf_dt2
                        st.session_state["pl_new_lock"] = _pf_dt2.strptime(_bf["lock"], "%Y-%m-%d").date()
                    except Exception:
                        pass
                # Clear the fresh flag so we don't keep overwriting user edits
                if _is_fresh:
                    _bf["fresh"] = False
                    st.session_state[_add_bulk_key] = _bf

            st.markdown("---")
            st.markdown(
                '<span style="font-size:12px;font-weight:700;color:#5c6370;text-transform:uppercase;'
                'letter-spacing:0.5px;">Loan Details</span>',
                unsafe_allow_html=True,
            )

            f1, f2, f3, f4, f5 = st.columns(5)
            with f1:
                new_loan_num = st.text_input("Loan #", key="pl_new_num")
                new_borrower = st.text_input("Borrower", key="pl_new_borrower")
            with f2:
                new_status = st.selectbox("Status", STATUS_OPTIONS, key="pl_new_status")
                default_idx = user_names.index(my_name) if my_name in user_names else 0
                new_assigned = st.selectbox("Assign To", user_names, index=default_idx, key="pl_new_assigned")
            with f3:
                new_closing = st.date_input("Closing Date", key="pl_new_closing")
                new_lock = st.date_input("Lock Expires", key="pl_new_lock",
                                         help="Rate lock expiration date")
                new_commitment = st.date_input("Commitment Exp.", key="pl_new_commitment",
                                               help="Commitment / approval letter expiration date")
            with f4:
                new_missing = st.text_area("Missing Docs", key="pl_new_missing", height=68,
                                           placeholder="Comma separated")
                new_folder = st.text_input("Folder Path", key="pl_new_folder",
                                           placeholder=r"C:\Loans\SmithJ")
            with f5:
                st.markdown("")  # spacer

            # Show what will be saved from bulk scan
            _bf_conds = _bf.get("conditions", [])
            _bf_contacts = _bf.get("contacts", {})
            if _bf_conds or _bf_contacts:
                st.markdown(
                    f'<div style="background:#ffffff;border:1px solid #888;border-radius:8px;'
                    f'padding:8px 12px;margin:4px 0;font-size:12px;color:#5c6370;">'
                    f'From bulk scan: <b style="color:#2563eb;">{len(_bf_conds)}</b> condition(s) '
                    f'and <b style="color:#2563eb;">{len(_bf_contacts)}</b> contact group(s) '
                    f'will be attached to this loan on save.</div>',
                    unsafe_allow_html=True,
                )

            sa1, sa2, sa3, sa4 = st.columns(4)
            with sa1:
                if st.button("Save Loan", use_container_width=True, key="pl_save_btn", type="primary"):
                    if new_loan_num and new_borrower:
                        assigned_val = "" if new_assigned == "(Unassigned)" else new_assigned
                        lock_str = str(new_lock) if new_lock else ""
                        closing_str = str(new_closing) if new_closing else ""
                        commitment_str = str(new_commitment) if new_commitment else ""
                        _new = add_loan(
                            new_loan_num, new_borrower, new_status,
                            closing_str, new_missing, new_folder,
                            created_by=my_name,
                            assigned_to=assigned_val,
                            lock_expiry=lock_str,
                            closing_date=closing_str,
                            commitment_date=commitment_str,
                            conditions=_bf_conds,
                            contacts=_bf_contacts,
                        )
                        _cond_note = f", {len(_bf_conds)} conditions" if _bf_conds else ""
                        _cont_note = f", {len(_bf_contacts)} contact groups" if _bf_contacts else ""
                        log_activity(_new["id"], "created",
                            f"Loan created — {new_borrower} #{new_loan_num}{_cond_note}{_cont_note}",
                            user=my_name)
                        # Clean up session state
                        st.session_state.pipeline_add_open = False
                        st.session_state.pop(_add_bulk_key, None)
                        for _k in ["pl_new_num", "pl_new_borrower", "pl_new_closing",
                                    "pl_new_lock", "pl_new_commitment", "pl_new_status",
                                    "pl_new_assigned", "pl_new_missing", "pl_new_folder"]:
                            st.session_state.pop(_k, None)
                        st.rerun()
                    else:
                        st.error("Loan # and Borrower are required.")
            with sa2:
                if st.button("Cancel", key="pl_cancel_btn", use_container_width=True):
                    st.session_state.pipeline_add_open = False
                    st.session_state.pop(_add_bulk_key, None)
                    for _k in ["pl_new_num", "pl_new_borrower", "pl_new_closing",
                                "pl_new_lock", "pl_new_status", "pl_new_assigned",
                                "pl_new_missing", "pl_new_folder"]:
                        st.session_state.pop(_k, None)
                    st.rerun()

    # ── Inbox (incoming shared loans) ────────────────────────────────────────
    from sharing import scan_inbox, dismiss_from_inbox, inbox_count
    inbox_items = scan_inbox()
    if inbox_items:
        n = len(inbox_items)
        with st.expander(f"Inbox — {n} shared loan{'s' if n != 1 else ''} waiting", expanded=True):
            st.caption("Loans shared directly with you by teammates. Accept to add to your pipeline.")
            for item in inbox_items:
                ib1, ib2, ib3, ib4 = st.columns([3, 2, 1, 1])
                share_id = item.get("share_id", "?")
                with ib1:
                    st.markdown(
                        f"<div style='font-weight:700;color:#111111;'>"
                        f"#{item.get('loan_num','—')} &nbsp; {item.get('borrower','—')}</div>"
                        f"<div style='font-size:12px;color:#5c6370;'>"
                        f"From: {item.get('last_updated_by','?')} &nbsp;·&nbsp; "
                        f"Updated: {item.get('last_updated','')[:10]}</div>",
                        unsafe_allow_html=True,
                    )
                with ib2:
                    shared_with_list = ", ".join(item.get("shared_with", []))
                    st.markdown(
                        f"<div style='font-size:12px;color:#333333;'>"
                        f"Status: <b>{item.get('status','—')}</b><br>"
                        f"Shared with: {shared_with_list or 'you'}</div>",
                        unsafe_allow_html=True,
                    )
                with ib3:
                    if st.button("✓ Accept", key=f"inbox_accept_{share_id}", use_container_width=True):
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
                            lock_expiry=item.get("lock_expiry", ""),
                            closing_date=item.get("closing_date", ""),
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
                st.markdown('<div style="height:2px;border-bottom:1px solid #888;"></div>',
                            unsafe_allow_html=True)

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

    # ── Sort loans ─────────────────────────────────────────────────────────
    def _last_name(name):
        """Extract last name for sorting: 'Carlos & Diana Reyes' → 'reyes'."""
        parts = name.strip().split()
        return parts[-1].lower() if parts else ""

    def _first_name(name):
        """Extract first name for sorting: 'Carlos & Diana Reyes' → 'carlos'."""
        parts = name.strip().split()
        return parts[0].lower() if parts else ""

    if sort_by == "Closing Date":
        loans.sort(key=lambda l: l.get("closing_date") or l.get("due_date") or "9999")
    elif sort_by == "Lock Expiry":
        loans.sort(key=lambda l: l.get("lock_expiry") or "9999")
    elif sort_by == "Last Name":
        loans.sort(key=lambda l: _last_name(l.get("borrower", "")))
    elif sort_by == "First Name":
        loans.sort(key=lambda l: _first_name(l.get("borrower", "")))
    elif sort_by == "Loan #":
        loans.sort(key=lambda l: l.get("loan_num", ""))
    elif sort_by == "Status":
        _status_order = {s: i for i, s in enumerate(STATUS_OPTIONS)}
        loans.sort(key=lambda l: _status_order.get(l.get("status"), 99))
    else:  # Newest (default — most recently created first)
        loans.sort(key=lambda l: l.get("id", 0), reverse=True)

    if not loans:
        st.info("No loans in pipeline yet. Click **+Add Loan** to get started.")
        return

    # ── Stats row (inline) ────────────────────────────────────────────────
    all_loans = get_all_loans()
    counts = {s: sum(1 for l in all_loans if l["status"] == s) for s in STATUS_OPTIONS}
    _chip_tints = {
        "Pending":   ("#c62828", "#ffebee", "#ef9a9a"),
        "Requested": ("#e65100", "#fff3e0", "#ffcc80"),
        "Cleared":   ("#2e7d32", "#e8f5e9", "#c8e6c9"),
        "Overdue":   ("#333",    "#f5f5f5", "#ddd"),
        "Closed":    ("#333",    "#f5f5f5", "#ddd"),
    }
    _stat_chips = " ".join(
        f'<span style="background:{_chip_tints.get(s, ("#333","#f5f5f5","#ddd"))[1]};'
        f'border:1px solid {_chip_tints.get(s, ("#333","#f5f5f5","#ddd"))[2]};border-radius:3px;'
        f'padding:2px 8px;font-size:12px;font-weight:600;color:{_chip_tints.get(s, ("#333","#f5f5f5","#ddd"))[0]};'
        f'display:inline-block;margin-bottom:2px;">'
        f'{counts[s]} <span style="font-size:10px;'
        f'font-weight:500;text-transform:uppercase;letter-spacing:0.3px;">{s}</span></span>'
        for s in STATUS_OPTIONS
    )
    st.markdown(
        f'<div style="margin:4px 0 8px 0;">{_stat_chips}</div>',
        unsafe_allow_html=True,
    )

    # ── Pipeline-wide progress bar ────────────────────────────────────────────
    _total_loans = len(all_loans)
    if _total_loans:
        _closed = counts.get("Cleared", 0) + counts.get("Closed", 0)
        _in_prog = counts.get("Requested", 0)
        _pipeline_pct = int((_closed / _total_loans) * 100)
        _pipeline_bar_html = (
            f'<div style="background:#fff;border:1px solid #888;border-radius:3px;'
            f'padding:6px 10px;margin-bottom:8px;">'
            f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">'
            f'<span style="font-size:11px;font-weight:600;color:#374151;">Pipeline Progress</span>'
            f'<span style="font-size:11px;color:#5c6370;">'
            f'{_closed} cleared / closed &nbsp;·&nbsp; {_in_prog} in progress &nbsp;·&nbsp; {_total_loans} total</span>'
            f'</div>'
            f'<div style="background:#d5d7da;border-radius:2px;height:8px;overflow:hidden;position:relative;">'
            # cleared/closed portion (green)
            f'<div style="background:#2e7d32;width:{_pipeline_pct}%;height:100%;'
            f'border-radius:2px 0 0 2px;position:absolute;left:0;"></div>'
            # in-progress portion (orange) stacked after green
            f'<div style="background:#e65100;'
            f'width:{int((_in_prog/_total_loans)*100)}%;height:100%;'
            f'position:absolute;left:{_pipeline_pct}%;"></div>'
            f'</div>'
            f'<div style="display:flex;gap:12px;margin-top:4px;">'
            f'<span style="font-size:10px;color:#2e7d32;font-weight:600;">&#9632; Cleared/Closed {_pipeline_pct}%</span>'
            f'<span style="font-size:10px;color:#e65100;font-weight:600;">&#9632; In Progress {int((_in_prog/_total_loans)*100)}%</span>'
            f'<span style="font-size:10px;color:#c62828;font-weight:600;">&#9632; Pending/Overdue {100 - _pipeline_pct - int((_in_prog/_total_loans)*100)}%</span>'
            f'</div>'
            f'</div>'
        )
        st.markdown(_pipeline_bar_html, unsafe_allow_html=True)

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
                parts.append(f"+{created_by}")
            if assigned_to:
                parts.append(f"{assigned_to}")
            team_line = f'<div style="font-size:10px;color:#5c6370;margin-top:1px;">{" · ".join(parts)}</div>'

        # Lock expiry badge
        _lock_exp = loan.get("lock_expiry", "")
        _lock_badge = ""
        if _lock_exp:
            try:
                from datetime import date as _dt_date, datetime as _dt_datetime
                _lock_d = _dt_datetime.strptime(_lock_exp, "%Y-%m-%d").date()
                _lock_days = (_lock_d - _dt_date.today()).days
                if _lock_days < 0:
                    _lock_clr, _lock_lbl = "#e74c3c", f"LOCK EXPIRED ({abs(_lock_days)}d ago)"
                elif _lock_days <= 7:
                    _lock_clr, _lock_lbl = "#e74c3c", f"Lock expires in {_lock_days}d"
                elif _lock_days <= 14:
                    _lock_clr, _lock_lbl = "#f39c12", f"Lock {_lock_days}d"
                else:
                    _lock_clr, _lock_lbl = "#27ae60", f"Lock {_lock_exp}"
                _lock_badge = (
                    f'<span style="background:{_lock_clr};color:#fff;'
                    f'padding:1px 6px;border-radius:3px;font-size:10px;font-weight:500;">{_lock_lbl}</span>'
                )
            except Exception:
                pass

        _closing_dt = loan.get("closing_date") or loan.get("due_date") or "—"
        _lock_dt = loan.get("lock_expiry") or ""
        _dates_html = f'Closing: {_closing_dt}'
        _dates_html += f' &nbsp;·&nbsp; Lock: {_lock_dt if _lock_dt else "Not set"}'
        _missing_txt = loan.get("missing_docs", "") or "None"

        # ── Progress calculation ─────────────────────────────────────
        _conds = loan.get("conditions", [])
        if _conds:
            _total_c = len(_conds)
            _cleared_c = sum(1 for c in _conds if c.get("status") in ("Cleared", "Ready to Clear"))
            _pct = int((_cleared_c / _total_c) * 100) if _total_c else 0
            # Boost for Closed status
            if status == "Closed":
                _pct = 100
            _pct_label = f"{_cleared_c}/{_total_c} conditions cleared"
        else:
            # No conditions — use milestone-based progress
            _milestone_pct = {"Pending": 10, "Requested": 30, "Cleared": 75, "Overdue": 20, "Closed": 100}
            _pct = _milestone_pct.get(status, 10)
            # Bonus points for key fields being set
            if loan.get("closing_date") or loan.get("due_date"):
                _pct = min(_pct + 10, 100)
            if loan.get("lock_expiry"):
                _pct = min(_pct + 10, 100)
            if loan.get("folder_path"):
                _pct = min(_pct + 5, 100)
            if not (loan.get("missing_docs") or "").strip() or loan.get("missing_docs") == "None":
                _pct = min(_pct + 5, 100)
            _pct_label = f"{status}"

        # Progress bar color
        if _pct >= 75:
            _bar_color = "#2e7d32"
        elif _pct >= 40:
            _bar_color = "#e65100"
        else:
            _bar_color = "#c62828"

        _progress_html = (
            f'<div style="margin-top:4px;">'
            f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:2px;">'
            f'<span style="font-size:10px;color:#5c6370;font-weight:500;">{_pct_label}</span>'
            f'<span style="font-size:11px;color:{_bar_color};font-weight:700;">{_pct}%</span>'
            f'</div>'
            f'<div style="background:#d5d7da;border-radius:2px;height:6px;overflow:hidden;">'
            f'<div style="background:{_bar_color};width:{_pct}%;height:100%;border-radius:2px;'
            f'transition:width 0.3s;"></div>'
            f'</div>'
            f'</div>'
        )

        # Clickable loan card — opens detail view
        _card_label = f"#{loan.get('loan_num','—')}  ·  {loan.get('borrower','—')}  ·  {emoji} {status}"
        if st.button(_card_label, key=f"open_{lid}", use_container_width=True):
            st.session_state.detail_loan_id = lid
            st.session_state.page = "loan_detail"
            st.rerun()
        # Build status line with colored badges left-aligned
        _status_items = []
        if _lock_badge:
            _status_items.append(_lock_badge)
        if _missing_txt and _missing_txt != "None":
            _status_items.append(
                f'<span style="background:#fff3e0;color:#bf360c;padding:1px 6px;'
                f'border-radius:3px;font-size:10px;font-weight:500;border:1px solid #ffcc80;">'
                f'Missing: {_missing_txt}</span>'
            )
        _badges_row = ""
        if _status_items:
            _badges_row = (
                f'<div style="display:flex;gap:6px;flex-wrap:wrap;margin-top:3px;">'
                f'{"".join(_status_items)}</div>'
            )

        st.markdown(
            f'<div style="background:#fff;border-left:3px solid {border_color};'
            f'border-radius:0 0 3px 3px;padding:4px 10px;margin-top:-10px;margin-bottom:2px;'
            f'border:1px solid #888;border-left:3px solid {border_color};">'
            f'{team_line}'
            f'<div style="font-size:11px;color:#5c6370;font-weight:400;">Closing: {_closing_dt}'
            f' &nbsp;·&nbsp; Lock: {_lock_dt if _lock_dt else "Not set"}</div>'
            f'{_badges_row}'
            f'{_progress_html}'
            f'</div>',
            unsafe_allow_html=True,
        )

        # ── Action row: status buttons + folder ───────────────────────────
        ac1, ac2, ac3, ac4, ac5, ac6 = st.columns([1, 1, 1, 1, 1, 1])
        with ac1:
            if st.button("✓ Cleared", key=f"clr_{lid}", use_container_width=True):
                set_status(lid, "Cleared")
                log_activity(lid, "status", "Status changed to Cleared", user=my_name)
                st.rerun()
        with ac2:
            if st.button("Export Requested", key=f"req_{lid}", use_container_width=True):
                set_status(lid, "Requested")
                log_activity(lid, "status", "Status changed to Requested", user=my_name)
                st.rerun()
        with ac3:
            if st.button("⏰ Overdue", key=f"ovr_{lid}", use_container_width=True):
                set_status(lid, "Overdue")
                log_activity(lid, "status", "Status changed to Overdue", user=my_name)
                st.rerun()
        with ac4:
            folder = loan.get("folder_path", "")
            if folder and os.path.isdir(folder):
                if st.button("Folder", key=f"ofld_{lid}", use_container_width=True):
                    os.startfile(folder)
        with ac5:
            cur_assigned = loan.get("assigned_to", "")
            cur_display = cur_assigned if cur_assigned in user_names else "(Unassigned)"
            cur_idx = user_names.index(cur_display)
            new_assignee = st.selectbox(
                "Reassign", user_names, index=cur_idx,
                key=f"assign_{lid}", label_visibility="collapsed",
            )
            _new_val = "" if new_assignee == "(Unassigned)" else new_assignee
            if _new_val != cur_assigned:
                update_loan(lid, assigned_to=_new_val)
                log_activity(lid, "reassign", f"Reassigned to {new_assignee}", user=my_name)
                st.toast(f"Reassigned to {new_assignee}", icon="User")
                st.rerun()
        with ac6:
            _del_key = f"confirm_del_{lid}"
            if st.session_state.get(_del_key):
                if st.button("✗ Yes, remove", key=f"ydel_{lid}", type="primary", use_container_width=True):
                    log_activity(lid, "removed", "Loan moved to Removed", user=my_name)
                    delete_loan(lid)
                    st.session_state.pop(_del_key, None)
                    st.toast("Moved to Trash", icon="Remove️")
                    st.rerun()
                if st.button("↩ Cancel", key=f"ndel_{lid}", use_container_width=True):
                    st.session_state.pop(_del_key, None)
                    st.rerun()
            else:
                if st.button("Remove️ Remove", key=f"del_{lid}", use_container_width=True):
                    st.session_state[_del_key] = True
                    st.rerun()

        # ── Share this loan ──────────────────────────────────────────────────
        from sharing import get_members, share_loan as _share_loan, send_update as _send_update
        team_members = get_members()
        team_names = [m["name"] for m in team_members]

        # Show "Send Update" if this loan was shared with us
        is_shared_loan = bool(loan.get("share_id"))
        share_key = f"share_open_{lid}"

        sh1, sh2, sh3, sh4, sh5, sh6 = st.columns(6)
        with sh1:
            lbl = "Export Update" if is_shared_loan else "Share"
            if team_names and st.button(lbl, key=f"sharebtn_{lid}", use_container_width=True):
                st.session_state[share_key] = not st.session_state.get(share_key, False)

        if st.session_state.get(share_key) and team_names:
            with st.container():
                if is_shared_loan:
                    # Send update back to owner + shared_with
                    st.markdown(
                        "<div style='font-size:13px;color:#333333;margin-bottom:6px;'>"
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
                        "<div style='font-size:13px;color:#333333;margin-bottom:6px;'>"
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
                                    st.success(f"✓ Shared with: {', '.join(ok)}")
                                for name, err in fail.items():
                                    st.error(f"✗ {name}: {err}")
                                st.session_state[share_key] = False
                            else:
                                st.warning("Pick at least one person to share with.")

        st.markdown('<div style="height:2px;border-bottom:1px solid #888;margin:2px 0;"></div>', unsafe_allow_html=True)

    # ── Removed / Recover Section ────────────────────────────────────────────
    trash_items = get_trash()
    _cur_retention = get_retention_days()
    _ret_label = "Forever" if _cur_retention == 0 else f"{_cur_retention} days"
    _trash_label = f"Remove️ Removed ({len(trash_items)})" if trash_items else "Remove️ Removed"
    with st.expander(_trash_label, expanded=False):
        # Retention picker
        rt1, rt2, rt3 = st.columns([2, 2, 2])
        with rt1:
            _ret_options = list(RETENTION_OPTIONS.keys())
            _cur_idx = 0
            for i, (k, v) in enumerate(RETENTION_OPTIONS.items()):
                if v == _cur_retention:
                    _cur_idx = i
                    break
            _new_ret = st.selectbox(
                "Auto-delete after", _ret_options, index=_cur_idx,
                key="retention_picker",
            )
            _new_ret_days = RETENTION_OPTIONS[_new_ret]
            if _new_ret_days != _cur_retention:
                set_retention_days(_new_ret_days)
                st.toast(f"Retention set to {_new_ret}", icon="✓")
                st.rerun()
        with rt3:
            if trash_items and st.button("Remove️ Empty All", key="empty_trash", use_container_width=True):
                empty_trash()
                st.toast("All removed loans permanently deleted", icon="Remove️")
                st.rerun()

        if not trash_items:
            st.caption("No removed loans.")
        else:
            from datetime import date as _tr_date, datetime as _tr_dt
            for tl in trash_items:
                t_lid = tl.get("id", 0)
                _exp = tl.get("expires_on", "")
                if _exp:
                    _exp_days = (_tr_dt.strptime(_exp, "%Y-%m-%d").date() - _tr_date.today()).days
                    if _exp_days <= 3:
                        _exp_tag = f'<span style="color:#e74c3c;font-size:10px;font-weight:600;">deletes in {max(0,_exp_days)}d</span>'
                    else:
                        _exp_tag = f'<span style="color:#5c6370;font-size:10px;">deletes in {_exp_days}d</span>'
                else:
                    _exp_tag = '<span style="color:#5c6370;font-size:10px;">kept forever</span>'

                tc1, tc2, tc3 = st.columns([4, 1, 1])
                with tc1:
                    st.markdown(
                        f'<span style="font-weight:700;color:#2563eb;">#{tl.get("loan_num", "—")}</span>'
                        f' &nbsp;{tl.get("borrower", "—")}'
                        f' &nbsp;<span style="color:#5c6370;font-size:10px;">removed {tl.get("deleted_on", "?")}</span>'
                        f' &nbsp;{_exp_tag}',
                        unsafe_allow_html=True,
                    )
                with tc2:
                    if st.button("Reset️ Restore", key=f"restore_{t_lid}", use_container_width=True):
                        restore_loan(t_lid)
                        st.toast(f"Restored #{tl.get('loan_num', '')}", icon="Reset️")
                        st.rerun()
                with tc3:
                    if st.button("✗ Delete", key=f"permdel_{t_lid}", use_container_width=True):
                        permanently_delete(t_lid)
                        st.toast("Permanently deleted", icon="✗")
                        st.rerun()


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

    st.markdown("## My Team")
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
        f"<div style='font-size:12px;color:#5c6370;margin-top:4px;'>"
        f"Share this path with teammates so they can drop files for you: "
        f"<code style='color:#2563eb;'>{config.get('my_inbox','(not set)')}</code>"
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
                    st.success(f"✓ {new_name} added — inbox is reachable!")
                else:
                    st.warning(
                        f"⚠️ {new_name} added, but can't reach their inbox right now: {msg}. "
                        "You can still add them and share when the folder is accessible."
                    )
                st.rerun()

    st.markdown("---")

    # ── Current Team List ───────────────────────────────────────────────────
    members = get_members()
    st.markdown(f"### My Team &nbsp; <span style='font-size:13px;color:#5c6370;'>({len(members)} people)</span>",
                unsafe_allow_html=True)

    if not members:
        st.info("No team members yet. Add your first teammate above.")
        return

    for m in members:
        with st.container():
            mc1, mc2, mc3, mc4 = st.columns([2, 2, 4, 1])
            with mc1:
                st.markdown(
                    f"<div style='font-weight:700;color:#111111;font-size:14px;'>{m['name']}</div>",
                    unsafe_allow_html=True,
                )
            with mc2:
                st.markdown(
                    f"<div style='color:#2563eb;font-size:13px;'>{m.get('role','')}</div>",
                    unsafe_allow_html=True,
                )
            with mc3:
                inbox_path = m.get("inbox", "")
                reachable = os.path.isdir(inbox_path) if inbox_path else False
                dot = "●" if reachable else "●"
                st.markdown(
                    f"<div style='font-size:12px;color:#5c6370;'>{dot} "
                    f"<code style='color:#333333;'>{inbox_path or '(no path)'}</code></div>",
                    unsafe_allow_html=True,
                )
            with mc4:
                if st.button("Remove", key=f"rm_{m['name']}", use_container_width=True):
                    remove_member(m["name"])
                    st.rerun()
            st.markdown('<div style="height:4px;border-bottom:1px solid #888;margin-bottom:4px;"></div>',
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
        with st.expander(f"{entry['doc_type']} - {entry['created_at'][:10]}"):
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

    st.markdown("## Email Email Watch")
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
            f'<span style="font-size:14px;font-weight:700;color:#a9dfbf;">● Watching inbox</span>'
            f'<span style="font-size:12px;color:#7dcea0;margin-left:12px;">'
            f'Last check: {status["last_time"] or "—"} · {status["last_status"]}</span></div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<div style="background:#ffffff;border-left:4px solid #888;border-radius:8px;'
            f'padding:10px 16px;margin-bottom:16px;">'
            f'<span style="font-size:14px;font-weight:700;color:#5c6370;">● Inbox watch is off</span>'
            + (f'<span style="font-size:12px;color:#d1d5db;margin-left:12px;">'
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
        st.markdown(f"### {len(matches)} New Attachment(s) — Waiting for Action")
        for i, m in enumerate(matches):
            conf  = m.get("confidence", 0)
            sugg  = m.get("suggestion", "unknown")
            bname = m.get("borrower") or "Unknown borrower"
            lnum  = m.get("loan_num", "")

            if sugg == "match":
                conf_color = "#27ae60"
                conf_label = f"✓ Matched — {bname} · Loan {lnum} ({conf}% confidence)"
            elif sugg == "possible":
                conf_color = "#f1c40f"
                conf_label = f"⚠️ Possible match — {bname} · Loan {lnum} ({conf}%)"
            else:
                conf_color = "#e74c3c"
                conf_label = "? No pipeline match found"

            with st.expander(f"{m['filename']}  ·  {m.get('received', '')}  ·  {conf_label}", expanded=True):
                mc1, mc2 = st.columns([3, 1])
                with mc1:
                    st.markdown(
                        f'<div style="font-size:12px;color:#5c6370;">From: {m["sender"]}</div>'
                        f'<div style="font-size:12px;color:#5c6370;">Subject: {m["subject"]}</div>'
                        f'<div style="font-size:13px;font-weight:700;color:{conf_color};margin-top:6px;">'
                        f'{conf_label}</div>',
                        unsafe_allow_html=True,
                    )
                    folder = m.get("suggested_folder", "")
                    if folder:
                        st.markdown(
                            f'<div style="font-size:12px;color:#2563eb;margin-top:4px;">'
                            f'Folder Suggested folder: {folder}</div>',
                            unsafe_allow_html=True,
                        )

                with mc2:
                    if folder and os.path.isdir(folder):
                        if st.button("Save to folder", key=f"ew_save_{i}", use_container_width=True, type="primary"):
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

    _iq_label = f"Incoming Queue — {len(_inbox_files)} file(s) waiting" if _inbox_files \
                else "Incoming Queue — empty"
    with st.expander(_iq_label, expanded=bool(_inbox_files)):
        if not _inbox_files:
            st.markdown(
                '<span style="color:#5c6370;font-size:13px;">No files in the incoming folder. '
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
                _v_icon  = {"pass": "✓", "review": "△", "check": "?"}.get(
                    _qv.get("verdict", "check"), "Search"
                )
                _bname = _qv.get("borrower") or "Unknown borrower"
                _lnum  = _qv.get("loan_num", "")
                _match_label = f" · {_bname} · Loan {_lnum}" if _qv.get("borrower") else " · No pipeline match"

                with st.container():
                    st.markdown(
                        f'<div style="background:#ffffff;border-left:3px solid {_v_color};'
                        f'border-radius:6px;padding:8px 12px;margin-bottom:6px;">'
                        f'<span style="font-weight:700;color:#111111;font-size:13px;">'
                        f'{_v_icon} {_qfname}</span>'
                        f'<span style="font-size:12px;color:#5c6370;">{_match_label}</span><br>'
                        f'<span style="font-size:11px;color:#2563eb;">{_qv.get("doc_type","Document")} · '
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
                            if st.button("✓ Yes — Save", key=f"iq_yes_{_qi}",
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
                            if _manual and st.button("✓ Yes", key=f"iq_yes_m_{_qi}",
                                                     use_container_width=True, type="primary"):
                                import shutil as _shu
                                os.makedirs(_manual, exist_ok=True)
                                _shu.move(_qfpath, os.path.join(_manual, _qfname))
                                st.success("Moved.")
                                st.rerun()
                    with _qc:
                        if st.button("Read", key=f"iq_read_{_qi}", use_container_width=True):
                            st.session_state.reader_open_file = _qfpath
                            st.session_state.page = "reader"
                            st.rerun()
                    with _qd:
                        if st.button("✗ No", key=f"iq_no_{_qi}", use_container_width=True):
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

        if st.button("Save Credentials", key="ew_save_creds", type="primary"):
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
- ● 80%+ = high confidence match (name found in PDF text)
- ● 50–79% = possible match (partial name found)
- ● Below 50% = no match — file saved to `incoming/` folder, you decide
        """)


# --- AI Settings Page ---
def show_ollama_page():
    import ollama_client as _oc
    import cloud_client  as _cc
    import ai_router     as _ar

    st.title("AI Settings")
    st.caption("Choose your preferred AI backend for enhanced document analysis, condition extraction, and email drafting.")

    status = _ar.get_status()

    # ── Status overview ───────────────────────────────────────────────────────
    s1, s2, s3 = st.columns(3)
    with s1:
        if status["preferred"] == "cloud" and status["cloud_enabled"]:
            s1.success(f"Cloud️ Cloud AI · {status['cloud_provider'].title()} · {status['cloud_model']}")
        elif status["cloud_enabled"]:
            s1.info(f"Cloud️ Cloud AI ready · {status['cloud_provider'].title()}")
        else:
            s1.warning("Cloud️ Cloud AI — not configured")
    with s2:
        if status["preferred"] == "ollama" and status["ollama_enabled"]:
            s2.success(f"● Ollama · {status['ollama_model']}")
        elif status["ollama_enabled"]:
            s2.info(f"● Ollama ready · {status['ollama_model']}")
        else:
            s2.warning("● Ollama — disabled")
    with s3:
        preferred_label = {
            "cloud":  "Cloud️ Cloud AI (primary)",
            "ollama": "● Ollama (primary)",
            "script": "— Script only",
        }.get(status["preferred"], status["preferred"])
        s3.info(f"Active: {preferred_label}")

    st.markdown("---")

    # ── Backend preference ────────────────────────────────────────────────────
    st.markdown("### Preferred Backend")
    ar_cfg = _ar.get_config()

    pref_options = ["script", "ollama", "cloud"]
    pref_labels  = {
        "script": "— Script only — no AI (fastest, fully offline)",
        "ollama": "● Ollama first — local AI, falls back to Cloud if enabled",
        "cloud":  "Cloud️ Cloud AI first — Claude / OpenAI, falls back to Ollama if enabled",
    }
    current_pref = ar_cfg.get("preferred_backend", "script")
    new_pref = st.radio(
        "When you click 'Draft with AI' or any AI button:",
        pref_options,
        index=pref_options.index(current_pref),
        format_func=lambda x: pref_labels[x],
        key="ar_pref",
    )
    fallback_on = st.checkbox(
        "If preferred backend fails, try the other AI automatically",
        value=bool(ar_cfg.get("fallback_enabled", True)),
        key="ar_fallback",
    )
    if st.button("Save Backend Preference", key="ar_save", type="primary"):
        _ar.save_config(new_pref, fallback_on)
        st.success("Backend preference saved.")
        st.rerun()

    st.markdown("---")

    # ── Cloud AI settings ─────────────────────────────────────────────────────
    st.markdown("### Cloud️ Cloud AI (Claude / OpenAI)")
    st.caption("Requires an internet connection and API key. More powerful than local models.")

    cc_cfg = _cc.get_config()

    with st.form("cloud_settings_form"):
        cc_enabled  = st.toggle("Enable Cloud AI", value=bool(cc_cfg.get("enabled")), key="cc_enabled")
        cc_provider = st.selectbox(
            "Provider",
            ["claude", "openai"],
            index=0 if cc_cfg.get("provider", "claude") == "claude" else 1,
            format_func=lambda x: "Anthropic Claude" if x == "claude" else "OpenAI (GPT)",
            key="cc_provider",
        )
        _default_models = {
            "claude": ["claude-sonnet-4-6", "claude-haiku-4-5-20251001", "claude-opus-4-6"],
            "openai": ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"],
        }
        cc_model = st.selectbox(
            "Model",
            _default_models.get(cc_provider, ["claude-sonnet-4-6"]),
            index=0,
            key="cc_model",
        )
        cc_key = st.text_input(
            "API Key",
            value=cc_cfg.get("api_key", ""),
            type="password",
            key="cc_key",
            help="Claude: get from console.anthropic.com · OpenAI: platform.openai.com/api-keys",
        )
        cc_save = st.form_submit_button("Save Cloud Settings", type="primary")

    if cc_save:
        _cc.save_config(cc_enabled, cc_provider, cc_key, cc_model)
        st.success("Cloud AI settings saved.")
        st.rerun()

    if st.button("Test Cloud Connection", key="cc_test"):
        if not cc_cfg.get("api_key"):
            st.warning("Save an API key first.")
        else:
            with st.spinner("Testing…"):
                ok, msg = _cc.ping()
            if ok:
                st.success(f"✓ {msg}")
            else:
                st.error(f"✗ {msg}")

    with st.expander("Guide Getting an API key"):
        st.markdown("""
**Anthropic Claude** (recommended — same AI powering this assistant)
1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Create an account → API Keys → Create Key
3. Paste the key above and select a Claude model

**OpenAI (GPT)**
1. Go to [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. Create a key and paste it above

**Cost:** Claude Sonnet runs about $0.003 per document analysis.
`claude-haiku-4-5-20251001` is even cheaper for lighter tasks.
`gpt-4o-mini` is the most affordable OpenAI option.
        """)

    st.markdown("---")

    # ── Ollama settings ───────────────────────────────────────────────────────
    st.markdown("### ● Ollama (Local — 100% Offline)")
    st.caption("Runs entirely on your machine. No internet required. No API key. Slower but private.")

    oc_cfg = _oc.get_config()
    oc_ok, oc_msg = _oc.ping(oc_cfg.get("endpoint", _oc.DEFAULT_ENDPOINT))

    if oc_cfg.get("enabled"):
        if oc_ok:
            st.success(f"● Ollama running · {oc_cfg.get('endpoint')} · {oc_cfg.get('model')}")
        else:
            st.error(f"● Ollama enabled but unreachable — {oc_msg}")
            st.caption("Run `ollama serve` in a terminal to start it.")
    else:
        st.info("● Ollama disabled.")

    with st.form("ollama_settings_form"):
        oc_enabled  = st.toggle("Enable Ollama", value=bool(oc_cfg.get("enabled")), key="oc_enabled")
        oc_endpoint = st.text_input("Endpoint", value=oc_cfg.get("endpoint", _oc.DEFAULT_ENDPOINT),
                                    key="oc_endpoint", help="Default: http://localhost:11434")
        available_models = _oc.list_models(oc_endpoint) if oc_ok else []
        current_model    = oc_cfg.get("model", _oc.DEFAULT_MODEL)
        if available_models:
            if current_model not in available_models:
                available_models.insert(0, current_model)
            oc_model = st.selectbox("Model", available_models,
                                    index=available_models.index(current_model), key="oc_model")
        else:
            oc_model = st.text_input("Model name", value=current_model, key="oc_model_txt",
                                     help="e.g. llama3.2 · Run: ollama pull llama3.2")

        oc_save = st.form_submit_button("Save Ollama Settings", type="primary")

    if oc_save:
        _oc.save_config(oc_enabled, oc_endpoint,
                        oc_model if available_models else st.session_state.get("oc_model_txt", oc_model))
        st.success("Ollama settings saved.")
        st.rerun()

    with st.expander("Guide How to set up Ollama"):
        st.markdown("""
**Step 1** — Download and install Ollama from [ollama.com](https://ollama.com)

**Step 2** — Pull a model (run in terminal):
```
ollama pull llama3.2
```
Recommended: `llama3.2` (fast) · `mistral` (more thorough) · `llama3.1` (best quality)

**Step 3** — Start the server (if not auto-started):
```
ollama serve
```

**Step 4** — Enable above, paste the endpoint, and save.
        """)

    # ── Processing log ────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### Processing Log")
    st.caption("Every AI call is logged here — shows which backend handled each request.")

    oc_lines = _oc.get_recent_log(20)
    cc_lines = _cc.get_recent_log(20)
    all_lines = sorted(oc_lines + cc_lines, reverse=True)[:40]

    if all_lines:
        log_c1, log_c2 = st.columns([5, 1])
        with log_c2:
            if st.button("Clear All Logs", key="ai_clear_log"):
                _oc.clear_log()
                _cc.clear_log()
                st.rerun()
        st.code("\n".join(all_lines), language=None)
    else:
        st.info("No processing log yet — scan a document or draft an email to see entries here.")


# --- Billing & Usage Page ---
def show_billing_page():
    import billing as _bl

    uid  = st.session_state.get("user_id", "")
    role = st.session_state.get("user_role", "Processor")

    st.title("$ Usage & Billing")
    st.caption("Tracks document scans processed each month and calculates your monthly cost.")

    # ── Current month summary ─────────────────────────────────────────────────
    usage = _bl.get_usage(uid)
    month_label = _bl.format_month(usage["year_month"])

    st.markdown(f"### {month_label}")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Scans This Month", usage["scans"])
    col2.metric("Included in Plan", usage["included"])
    col3.metric("Overage Scans", usage["overage"],
                delta=f"+${usage['overage_cost']:.2f}" if usage["overage"] else None,
                delta_color="inverse")
    col4.metric("Monthly Total", f"${usage['total_cost']:.2f}",
                help=f"${_bl.MONTHLY_BASE:.0f} base + ${usage['overage_cost']:.2f} overage")

    # ── Usage bar ─────────────────────────────────────────────────────────────
    pct = usage["pct_used"]
    bar_color = "#27ae60" if pct < 80 else ("#f39c12" if pct < 100 else "#e74c3c")
    st.markdown(
        f'<div style="background:#ffffff;border-radius:8px;padding:12px 16px;margin:8px 0 16px;">'
        f'<div style="font-size:13px;color:#333333;margin-bottom:6px;">'
        f'Quota: {usage["scans"]} / {usage["included"]} scans used ({pct}%)</div>'
        f'<div style="background:#2d2060;border-radius:4px;height:10px;">'
        f'<div style="background:{bar_color};width:{min(pct,100)}%;height:10px;border-radius:4px;'
        f'transition:width 0.4s;"></div></div></div>',
        unsafe_allow_html=True,
    )

    # ── Breakdown by doc type ──────────────────────────────────────────────────
    if usage["by_doc_type"]:
        st.markdown("#### Scans by Document Type")
        rows = sorted(usage["by_doc_type"].items(), key=lambda x: -x[1])
        for dtype, count in rows:
            pct_dt = round(count / max(usage["scans"], 1) * 100)
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:4px;">'
                f'<span style="font-size:13px;color:#333333;width:220px;">{dtype or "Unknown"}</span>'
                f'<div style="flex:1;background:#2d2060;border-radius:4px;height:8px;">'
                f'<div style="background:#2563eb;width:{pct_dt}%;height:8px;border-radius:4px;"></div></div>'
                f'<span style="font-size:13px;color:#333333;width:40px;text-align:right;">{count}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

    # ── Billing note ──────────────────────────────────────────────────────────
    st.markdown("---")
    with st.expander("Add a billing note for this month"):
        note_text = st.text_input("Note (e.g. 'Batch of 5 rush closings')", key="billing_note")
        if st.button("Add Note", key="billing_add_note"):
            if note_text.strip():
                _bl.add_note(uid, note_text)
                st.success("Note saved.")
                st.rerun()
    notes = _bl.get_notes(uid)
    if notes:
        for n in notes:
            st.markdown(f'<div style="font-size:13px;color:#5c6370;">· {n}</div>',
                        unsafe_allow_html=True)

    # ── Monthly history ───────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### Monthly History")
    history = _bl.get_history(uid, months=6)
    if history:
        for h in history:
            c1, c2, c3 = st.columns([3, 2, 2])
            c1.markdown(f"**{_bl.format_month(h['year_month'])}**")
            c2.markdown(f"{h['scans']} scans"
                        + (f" · {h['overage']} overage" if h["overage"] else ""))
            c3.markdown(f"**${h['total_cost']:.2f}**")
    else:
        st.info("No billing history yet — scan a document to start tracking.")

    # ── Pricing reference ─────────────────────────────────────────────────────
    st.markdown("---")
    with st.expander("Plan Details"):
        st.markdown(f"""
| Item | Amount |
|------|--------|
| Monthly base | **${_bl.MONTHLY_BASE:.2f}** |
| Included scans | **{_bl.INCLUDED_FILES} / month** |
| Overage rate | **${_bl.OVERAGE_RATE:.2f} / scan** |
| Reset | 1st of each month (UTC) |

Scans include all document uploads processed through the Scanner.
        """)

    # ── Admin view (Manager role only) ────────────────────────────────────────
    if role == "Manager":
        st.markdown("---")
        st.markdown("### All Users — Current Month")
        all_usage = _bl.get_all_users_usage()
        if all_usage:
            for u in all_usage:
                ua1, ua2, ua3, ua4 = st.columns([3, 2, 2, 2])
                ua1.markdown(f"**{u['display_name'] or u['email']}** · {u['role']}")
                ua2.markdown(f"{u['scans']} scans")
                ua3.markdown(f"{u['overage']} overage" if u["overage"] else "—")
                ua4.markdown(f"**${u['total_cost']:.2f}**")
        else:
            st.info("No scan data for current month.")


# --- Loan Detail Page ---
def show_loan_detail():
    """Full detail view for a single loan — all info, activity, documents."""
    from crm import (
        get_loan, update_loan, set_status, delete_loan,
        STATUS_OPTIONS, STATUS_EMOJI, STATUS_COLORS,
        get_activity, log_activity,
    )
    from datetime import date as _ld_date, datetime as _ld_dt

    lid = st.session_state.get("detail_loan_id")
    if not lid:
        st.session_state.page = "pipeline"
        st.rerun()
        return

    loan = get_loan(lid)
    if not loan:
        st.warning("Loan not found — it may have been removed.")
        if st.button("← Back to Pipeline"):
            st.session_state.page = "pipeline"
            st.rerun()
        return

    my_name = st.session_state.get("user_name", "")
    status = loan.get("status", "Pending")
    border_color = STATUS_COLORS.get(status, "#444")

    # ── Back button ───────────────────────────────────────────────────────
    if st.button("← Back to Pipeline", key="back_to_pipeline"):
        st.session_state.page = "pipeline"
        st.rerun()

    # ── Header ────────────────────────────────────────────────────────────
    # Compute progress for detail view
    _ld_conds = loan.get("conditions", [])
    if _ld_conds:
        _ld_total = len(_ld_conds)
        _ld_cleared = sum(1 for c in _ld_conds if c.get("status") in ("Cleared", "Ready to Clear"))
        _ld_pct = int((_ld_cleared / _ld_total) * 100) if _ld_total else 0
        if status == "Closed": _ld_pct = 100
        _ld_label = f"{_ld_cleared} of {_ld_total} conditions cleared"
    else:
        _ld_pct = {"Pending": 10, "Requested": 35, "Cleared": 80, "Overdue": 20, "Closed": 100}.get(status, 10)
        if loan.get("closing_date"): _ld_pct = min(_ld_pct + 10, 100)
        if loan.get("lock_expiry"):  _ld_pct = min(_ld_pct + 10, 100)
        _ld_label = f"{status} — no conditions tracked yet"
    _ld_bar_color = "#2e7d32" if _ld_pct >= 75 else ("#e65100" if _ld_pct >= 40 else "#c62828")

    st.markdown(
        f'<div style="background:#fff;border:1px solid #888;border-left:3px solid {border_color};'
        f'border-radius:3px;padding:12px 14px;margin:4px 0;">'
        f'<div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:8px;">'
        f'<span style="font-size:16px;font-weight:700;color:#1565c0;">#{loan.get("loan_num","—")}</span>'
        f'<span style="font-size:15px;font-weight:600;color:#111;">{loan.get("borrower","—")}</span>'
        f'<span class="status-chip status-{status.lower()}" style="font-size:13px;">'
        f'<span style="color:{border_color};font-size:10px;">●</span> {status}</span>'
        f'</div>'
        f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:3px;">'
        f'<span style="font-size:11px;color:#5c6370;">{_ld_label}</span>'
        f'<span style="font-size:12px;font-weight:700;color:{_ld_bar_color};">{_ld_pct}% to close</span>'
        f'</div>'
        f'<div style="background:#d5d7da;border-radius:2px;height:8px;overflow:hidden;">'
        f'<div style="background:{_ld_bar_color};width:{_ld_pct}%;height:100%;border-radius:2px;"></div>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Key Dates ─────────────────────────────────────────────────────────
    st.markdown(
        '<span style="font-size:13px;font-weight:700;color:#2563eb;text-transform:uppercase;'
        'letter-spacing:0.5px;">Key Dates</span>',
        unsafe_allow_html=True,
    )
    _closing = loan.get("closing_date") or loan.get("due_date") or ""
    _lock = loan.get("lock_expiry") or ""
    _commitment = loan.get("commitment_date") or ""
    _created = loan.get("created") or ""
    _updated = loan.get("updated") or ""
    _today = _ld_date.today()

    def _days_away(d_str):
        if not d_str:
            return ""
        try:
            d = _ld_dt.strptime(d_str, "%Y-%m-%d").date()
            diff = (d - _today).days
            if diff < 0:
                return f'<span style="color:#e74c3c;font-weight:700;"> ({abs(diff)}d ago)</span>'
            elif diff == 0:
                return '<span style="color:#e74c3c;font-weight:700;"> (TODAY)</span>'
            elif diff <= 7:
                return f'<span style="color:#f39c12;font-weight:700;"> ({diff}d left)</span>'
            else:
                return f'<span style="color:#5c6370;"> ({diff}d)</span>'
        except Exception:
            return ""

    d1, d2, d3, d4, d5 = st.columns(5)
    with d1:
        st.markdown(
            f'<div style="background:#ffffff;border:1px solid #888;border-radius:8px;padding:10px;">'
            f'<div style="font-size:10px;color:#2563eb;font-weight:700;text-transform:uppercase;">Closing Date</div>'
            f'<div style="font-size:16px;font-weight:700;color:#111111;margin-top:4px;">'
            f'{_closing or "Not set"}{_days_away(_closing)}</div></div>',
            unsafe_allow_html=True,
        )
    with d2:
        st.markdown(
            f'<div style="background:#2d2200;border:1px solid #5a4400;border-radius:8px;padding:10px;">'
            f'<div style="font-size:10px;color:#f1c40f;font-weight:700;text-transform:uppercase;">Lock Expiration</div>'
            f'<div style="font-size:16px;font-weight:700;color:#111111;margin-top:4px;">'
            f'{_lock or "Not set"}{_days_away(_lock)}</div></div>',
            unsafe_allow_html=True,
        )
    with d3:
        st.markdown(
            f'<div style="background:#1a2d1a;border:1px solid #2d5a2d;border-radius:8px;padding:10px;">'
            f'<div style="font-size:10px;color:#7ee787;font-weight:700;text-transform:uppercase;">Commitment Exp.</div>'
            f'<div style="font-size:16px;font-weight:700;color:#111111;margin-top:4px;">'
            f'{_commitment or "Not set"}{_days_away(_commitment)}</div></div>',
            unsafe_allow_html=True,
        )
    with d4:
        st.markdown(
            f'<div style="background:#ffffff;border:1px solid #888;border-radius:8px;padding:10px;">'
            f'<div style="font-size:10px;color:#5c6370;font-weight:700;text-transform:uppercase;">Created</div>'
            f'<div style="font-size:14px;color:#111111;margin-top:4px;">{_created or "—"}</div></div>',
            unsafe_allow_html=True,
        )
    with d5:
        st.markdown(
            f'<div style="background:#ffffff;border:1px solid #888;border-radius:8px;padding:10px;">'
            f'<div style="font-size:10px;color:#5c6370;font-weight:700;text-transform:uppercase;">Last Updated</div>'
            f'<div style="font-size:14px;color:#111111;margin-top:4px;">{_updated or "—"}</div></div>',
            unsafe_allow_html=True,
        )

    # ── Loan Details ──────────────────────────────────────────────────────
    st.markdown(
        '<span style="font-size:13px;font-weight:700;color:#2563eb;text-transform:uppercase;'
        'letter-spacing:0.5px;margin-top:12px;display:inline-block;">Loan Details</span>',
        unsafe_allow_html=True,
    )
    ld1, ld2 = st.columns(2)
    with ld1:
        _fields_left = [
            ("Loan #", loan.get("loan_num", "—")),
            ("Borrower", loan.get("borrower", "—")),
            ("Status", f'{STATUS_EMOJI.get(status,"")}  {status}'),
            ("Created By", loan.get("created_by") or "—"),
            ("Assigned To", loan.get("assigned_to") or "Unassigned"),
        ]
        _rows_html = "".join(
            f'<tr><td style="padding:4px 12px 4px 0;color:#5c6370;font-size:12px;font-weight:600;'
            f'white-space:nowrap;vertical-align:top;">{k}</td>'
            f'<td style="padding:4px 0;color:#111111;font-size:13px;">{v}</td></tr>'
            for k, v in _fields_left
        )
        st.markdown(
            f'<table style="border-collapse:collapse;">{_rows_html}</table>',
            unsafe_allow_html=True,
        )
    with ld2:
        _fields_right = [
            ("Closing Date", _closing or "Not set"),
            ("Lock Expiry", _lock or "Not set"),
            ("Commitment Exp.", _commitment or "Not set"),
            ("Due Date", loan.get("due_date") or "—"),
            ("Folder", loan.get("folder_path") or "Not set"),
        ]
        _rows_html2 = "".join(
            f'<tr><td style="padding:4px 12px 4px 0;color:#5c6370;font-size:12px;font-weight:600;'
            f'white-space:nowrap;vertical-align:top;">{k}</td>'
            f'<td style="padding:4px 0;color:#111111;font-size:13px;">{v}</td></tr>'
            for k, v in _fields_right
        )
        st.markdown(
            f'<table style="border-collapse:collapse;">{_rows_html2}</table>',
            unsafe_allow_html=True,
        )

    # ── Missing Docs ──────────────────────────────────────────────────────
    _missing = loan.get("missing_docs", "")
    st.markdown(
        '<span style="font-size:13px;font-weight:700;color:#2563eb;text-transform:uppercase;'
        'letter-spacing:0.5px;margin-top:12px;display:inline-block;">Missing Documents</span>',
        unsafe_allow_html=True,
    )
    if _missing:
        _docs = [d.strip() for d in _missing.split(",") if d.strip()]
        _doc_html = "".join(
            f'<div style="display:flex;align-items:center;gap:6px;margin-bottom:3px;">'
            f'<span style="color:#e74c3c;">●</span>'
            f'<span style="color:#ffb86c;font-size:13px;">{d}</span></div>'
            for d in _docs
        )
        st.markdown(_doc_html, unsafe_allow_html=True)
    else:
        st.markdown(
            '<span style="color:#27ae60;font-size:13px;">All documents received</span>',
            unsafe_allow_html=True,
        )

    # ── Open Conditions ──────────────────────────────────────────────────
    _conditions = loan.get("conditions", [])
    st.markdown(
        '<span style="font-size:13px;font-weight:700;color:#2563eb;text-transform:uppercase;'
        'letter-spacing:0.5px;margin-top:12px;display:inline-block;">Open Conditions</span>',
        unsafe_allow_html=True,
    )
    if _conditions:
        _cond_status_colors = {
            "Needed": "#f1c40f", "Requested": "#e67e22", "Important": "#e74c3c",
            "Ready to Clear": "#27ae60", "Cleared": "#5dade2",
        }
        _cond_status_emoji = {
            "Needed": "●", "Requested": "●", "Important": "●",
            "Ready to Clear": "●", "Cleared": "●",
        }
        from crm import PARTY_COLORS as _PC
        _cond_rows_html = ""
        for _ci, _c in enumerate(_conditions):
            _c_desc = _c.get("desc", _c.get("description", "—"))
            _c_party = _c.get("party", "—")
            _c_status = _c.get("status", "Needed")
            _c_color = _cond_status_colors.get(_c_status, "#f1c40f")
            _c_emoji = _cond_status_emoji.get(_c_status, "●")
            _p_color = _PC.get(_c_party, "#6c757d")
            _cond_rows_html += (
                f'<div style="display:flex;align-items:center;gap:8px;padding:6px 0;'
                f'border-bottom:1px solid #888;">'
                f'<span style="min-width:18px;font-size:13px;">{_c_emoji}</span>'
                f'<span style="flex:1;color:#111111;font-size:13px;">{_c_desc}</span>'
                f'<span style="background:{_p_color};color:#fff;font-size:10px;font-weight:600;'
                f'padding:2px 8px;border-radius:10px;white-space:nowrap;">{_c_party}</span>'
                f'<span style="color:{_c_color};font-size:11px;font-weight:600;min-width:60px;'
                f'text-align:right;">{_c_status}</span>'
                f'</div>'
            )
        st.markdown(_cond_rows_html, unsafe_allow_html=True)
    else:
        st.markdown(
            '<span style="color:#5c6370;font-size:12px;">No conditions attached to this loan yet. '
            'Upload and scan a document to extract conditions.</span>',
            unsafe_allow_html=True,
        )

    # ── Parties & Contacts ───────────────────────────────────────────────
    _contacts = loan.get("contacts", {})
    st.markdown(
        '<span style="font-size:13px;font-weight:700;color:#2563eb;text-transform:uppercase;'
        'letter-spacing:0.5px;margin-top:12px;display:inline-block;">Parties &amp; Contacts</span>',
        unsafe_allow_html=True,
    )
    if _contacts:
        from crm import PARTY_COLORS as _PC2
        _party_labels = {
            "buyer": "Buyer / Borrower", "borrower": "Borrower", "co_borrower": "Co-Borrower",
            "seller": "Seller", "listing_agent": "Listing Agent", "selling_agent": "Selling Agent",
            "title": "Title Company", "employer": "Employer",
        }
        _contact_html = '<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">'
        for _ck, _cv in _contacts.items():
            if not _cv or not isinstance(_cv, dict):
                continue
            # Skip empty contacts (all values blank)
            if not any(str(v).strip() for v in _cv.values()):
                continue
            _clabel = _party_labels.get(_ck, _ck.replace("_", " ").title())
            _cname = _cv.get("name") or _cv.get("company") or _cv.get("contact") or ""
            _cphone = _cv.get("phone", "")
            _cemail = _cv.get("email", "")
            _cbrok = _cv.get("brokerage", "")
            _caddr = _cv.get("address", "")
            _cpos = _cv.get("position", "")
            _detail_parts = []
            if _cphone:
                _detail_parts.append(f'{_cphone}')
            if _cemail:
                _detail_parts.append(f'Email️ {_cemail}')
            if _cbrok:
                _detail_parts.append(f'{_cbrok}')
            if _cpos:
                _detail_parts.append(f'— {_cpos}')
            if _caddr:
                _detail_parts.append(f'{_caddr}')
            _detail_str = " &nbsp;·&nbsp; ".join(_detail_parts) if _detail_parts else '<span style="color:#6c757d;">No details</span>'
            _contact_html += (
                f'<div style="background:#ffffff;border:1px solid #888;border-radius:8px;padding:10px;">'
                f'<div style="font-size:10px;color:#2563eb;font-weight:700;text-transform:uppercase;margin-bottom:4px;">{_clabel}</div>'
                f'<div style="color:#111111;font-size:13px;font-weight:600;">{_cname or "—"}</div>'
                f'<div style="color:#5c6370;font-size:11px;margin-top:3px;">{_detail_str}</div>'
                f'</div>'
            )
        _contact_html += '</div>'
        st.markdown(_contact_html, unsafe_allow_html=True)
    else:
        st.markdown(
            '<span style="color:#5c6370;font-size:12px;">No contact information attached. '
            'Upload a Purchase Contract or 1003 to populate parties.</span>',
            unsafe_allow_html=True,
        )

    # ── Scan & Attach Document ───────────────────────────────────────────
    st.markdown(
        '<span style="font-size:13px;font-weight:700;color:#2563eb;text-transform:uppercase;'
        'letter-spacing:0.5px;margin-top:12px;display:inline-block;">Scan &amp; Attach Document</span>',
        unsafe_allow_html=True,
    )
    with st.expander("Upload a document to scan and populate loan data", expanded=False):
        _scan_doc_types = [
            "Approval Letter", "Closing Disclosure (CD)", "Loan Estimate (LE)",
            "1003 Application", "Purchase Contract", "Credit Report",
            "Bank Statement", "Change of Circumstance (COC)", "Broker Package (BP)",
        ]
        _sc1, _sc2 = st.columns([2, 1])
        with _sc1:
            _scan_file = st.file_uploader(
                "Upload PDF", type=["pdf"], key=f"detail_scan_file_{lid}",
                label_visibility="collapsed",
            )
        with _sc2:
            _scan_dtype = st.selectbox(
                "Document type", _scan_doc_types, key=f"detail_scan_dtype_{lid}",
                label_visibility="collapsed",
            )

        _scan_key = f"detail_scan_result_{lid}"
        if _scan_file and st.button("Scan & Attach", key=f"detail_scan_btn_{lid}",
                                     type="primary", use_container_width=True):
            with st.spinner(f"Scanning {_scan_dtype}..."):
                from ai_engine import process_document as _proc_doc
                _pdf_bytes = _scan_file.read()
                _scan_result = _proc_doc(_pdf_bytes, _scan_dtype)

            if not _scan_result.get("success"):
                st.error(_scan_result.get("error", "Scan failed — could not extract text from this PDF."))
            else:
                st.session_state[_scan_key] = _scan_result
                st.success(f"✓ Scanned {_scan_dtype} — {_scan_result.get('text_length', 0):,} chars extracted")

        # Process scan results if available
        if _scan_key in st.session_state and st.session_state[_scan_key]:
            _sr = st.session_state[_scan_key]
            _sr_dtype = _sr.get("doc_type", "")
            _merged_something = False

            # ── Purchase Contract → merge contacts + show extracted data ──
            if _sr_dtype == "Purchase Contract" and _sr.get("extracted_data"):
                _pcd = _sr["extracted_data"]
                _pc_buyer = _pcd.get("buyer", {})
                _pc_seller = _pcd.get("seller", {})
                _pc_la = _pcd.get("listing_agent", {})
                _pc_sa = _pcd.get("selling_agent", {})
                _pc_title = _pcd.get("title", {})
                _pc_txn = _pcd.get("transaction", {})

                st.markdown(
                    '<div style="background:#ffffff;border:1px solid #888;border-radius:8px;'
                    'padding:10px;margin:8px 0;font-size:12px;color:#5c6370;">'
                    '<b style="color:#2563eb;">Purchase Contract found:</b><br>'
                    f'Buyer: {_pc_buyer.get("name","—")} · Seller: {_pc_seller.get("name","—")}<br>'
                    f'Price: ${_pc_txn.get("purchase_price","—")} · Close: {_pc_txn.get("closing_date","—")}'
                    '</div>',
                    unsafe_allow_html=True,
                )

                if st.button("✓ Merge contacts into this loan", key=f"detail_merge_pc_{lid}",
                             use_container_width=True):
                    _new_contacts = dict(_contacts)  # existing contacts
                    _pc_map = {
                        "buyer": {"name": _pc_buyer.get("name",""), "phone": _pc_buyer.get("phone",""), "email": _pc_buyer.get("email","")},
                        "seller": {"name": _pc_seller.get("name",""), "phone": _pc_seller.get("phone","")},
                        "listing_agent": {"name": _pc_la.get("name",""), "brokerage": _pc_la.get("brokerage",""), "phone": _pc_la.get("phone",""), "email": _pc_la.get("email","")},
                        "selling_agent": {"name": _pc_sa.get("name",""), "brokerage": _pc_sa.get("brokerage",""), "phone": _pc_sa.get("phone",""), "email": _pc_sa.get("email","")},
                        "title": {"company": _pc_title.get("company",""), "contact": _pc_title.get("contact",""), "phone": _pc_title.get("phone","")},
                    }
                    for _pk, _pv in _pc_map.items():
                        if any(str(v).strip() for v in _pv.values()):
                            _new_contacts[_pk] = _pv
                    # Also update closing date if found and not already set
                    _upd = {"contacts": _new_contacts}
                    if _pc_txn.get("closing_date") and not _closing:
                        _upd["closing_date"] = _pc_txn["closing_date"]
                        _upd["due_date"] = _pc_txn["closing_date"]
                    update_loan(lid, **_upd)
                    log_activity(lid, "upload", f"Purchase Contract scanned — contacts merged", user=my_name)
                    st.session_state.pop(_scan_key, None)
                    st.toast("Contacts merged into loan", icon="✓")
                    st.rerun()

            # ── 1003 Application → merge contacts ──
            elif _sr_dtype == "1003 Application" and _sr.get("extracted_data"):
                _app = _sr["extracted_data"]
                _app_b = _app.get("borrower", {})
                _app_cb = _app.get("co_borrower", {})
                _app_emp = _app.get("employment", {})

                st.markdown(
                    '<div style="background:#ffffff;border:1px solid #888;border-radius:8px;'
                    'padding:10px;margin:8px 0;font-size:12px;color:#5c6370;">'
                    '<b style="color:#2563eb;">1003 Application found:</b><br>'
                    f'Borrower: {_app_b.get("name","—")} · Phone: {_app_b.get("phone","—")}<br>'
                    f'Employer: {_app_emp.get("employer","—")}'
                    '</div>',
                    unsafe_allow_html=True,
                )

                if st.button("✓ Merge contacts into this loan", key=f"detail_merge_1003_{lid}",
                             use_container_width=True):
                    _new_contacts = dict(_contacts)
                    _1003_map = {
                        "borrower": {"name": _app_b.get("name",""), "phone": _app_b.get("phone",""), "email": _app_b.get("email",""), "address": _app_b.get("present_address","")},
                        "co_borrower": {"name": _app_cb.get("name",""), "phone": _app_cb.get("phone",""), "email": _app_cb.get("email","")},
                        "employer": {"name": _app_emp.get("employer",""), "phone": _app_emp.get("employer_phone",""), "position": _app_emp.get("position","")},
                    }
                    for _pk, _pv in _1003_map.items():
                        if any(str(v).strip() for v in _pv.values()):
                            _new_contacts[_pk] = _pv
                    update_loan(lid, contacts=_new_contacts)
                    log_activity(lid, "upload", f"1003 Application scanned — contacts merged", user=my_name)
                    st.session_state.pop(_scan_key, None)
                    st.toast("Contacts merged into loan", icon="✓")
                    st.rerun()

            # ── All other doc types → merge conditions ──
            elif _sr.get("conditions"):
                _cond_text = _sr["conditions"]
                _new_conds = []
                for _cl in _cond_text.split("\n"):
                    _cl = _cl.strip()
                    if _cl.startswith("|") and not _cl.startswith("| #") and not _cl.startswith("|--") and not _cl.startswith("|-"):
                        _cells = [c.strip() for c in _cl.split("|") if c.strip()]
                        if len(_cells) >= 4:
                            _new_conds.append({
                                "num": _cells[0], "desc": _cells[1],
                                "party": _cells[2], "status": _cells[3],
                            })

                if _new_conds:
                    st.markdown(
                        f'<div style="background:#ffffff;border:1px solid #888;border-radius:8px;'
                        f'padding:10px;margin:8px 0;font-size:12px;color:#5c6370;">'
                        f'<b style="color:#2563eb;">{_sr_dtype} scanned:</b> '
                        f'{len(_new_conds)} condition(s) found</div>',
                        unsafe_allow_html=True,
                    )
                    # Preview the conditions
                    for _nc in _new_conds:
                        st.markdown(
                            f'<span style="color:#f1c40f;font-size:12px;">●</span> '
                            f'<span style="color:#111111;font-size:12px;">{_nc["desc"]}</span> '
                            f'<span style="color:#5c6370;font-size:11px;">— {_nc["party"]}</span>',
                            unsafe_allow_html=True,
                        )

                    if st.button("✓ Merge conditions into this loan", key=f"detail_merge_conds_{lid}",
                                 use_container_width=True):
                        _existing = list(_conditions)
                        _existing_descs = {c.get("desc", "").lower().strip() for c in _existing}
                        _added = 0
                        for _nc in _new_conds:
                            if _nc["desc"].lower().strip() not in _existing_descs:
                                _nc["num"] = str(len(_existing) + 1)
                                _existing.append(_nc)
                                _added += 1
                        update_loan(lid, conditions=_existing)
                        log_activity(lid, "upload", f"{_sr_dtype} scanned — {_added} condition(s) added", user=my_name)
                        st.session_state.pop(_scan_key, None)
                        st.toast(f"{_added} condition(s) merged", icon="✓")
                        st.rerun()
                else:
                    st.info("No conditions extracted from this document.")

            # ── Bank Statement → show rules ──
            elif _sr.get("bank_rules"):
                st.markdown(
                    f'<div style="background:#ffffff;border:1px solid #888;border-radius:8px;'
                    f'padding:10px;margin:8px 0;font-size:12px;color:#5c6370;">'
                    f'<b style="color:#2563eb;">Bank Statement Analysis:</b></div>',
                    unsafe_allow_html=True,
                )
                st.markdown(_sr["bank_rules"])
                log_activity(lid, "upload", "Bank Statement scanned and reviewed", user=my_name)

    # ── Approval Fetch ────────────────────────────────────────────────────
    st.markdown(
        '<span style="font-size:13px;font-weight:700;color:#2563eb;text-transform:uppercase;'
        'letter-spacing:0.5px;margin-top:12px;display:inline-block;">Approval Fetch</span>',
        unsafe_allow_html=True,
    )
    with st.expander("Upload approval letter → scan borrower folder → see what's found vs missing", expanded=False):
        import os as _af_os
        _af_key = f"approval_fetch_{lid}"

        # Step 1: Upload the approval letter
        _af_file = st.file_uploader(
            "Upload Approval Letter PDF", type=["pdf"],
            key=f"af_upload_{lid}", label_visibility="collapsed",
        )

        if _af_file and st.button("Scan Approval Letter", key=f"af_scan_btn_{lid}",
                                   type="primary", use_container_width=True):
            with st.spinner("Extracting conditions from approval letter..."):
                from ai_engine import process_document as _af_proc, extract_contacts as _af_contacts
                from pypdf import PdfReader as _AF_PR
                _af_bytes = _af_file.read()
                _af_result = _af_proc(_af_bytes, "Approval Letter")

                # Also extract borrower name from the raw text
                import io as _af_io
                _af_reader = _AF_PR(_af_io.BytesIO(_af_bytes))
                _af_text = "\n".join((p.extract_text() or "") for p in _af_reader.pages)
                import re as _af_re
                _af_borrower = ""
                for _bp in [
                    r'(?i)borrower\s*(?:name)?\s*[:\s]+([A-Z][a-zA-Z\-\']+\s+[A-Z][a-zA-Z\-\']+)',
                    r'(?i)applicant\s*[:\s]+([A-Z][a-zA-Z\-\']+\s+[A-Z][a-zA-Z\-\']+)',
                    r'(?i)prepared\s+for\s*[:\s]+([A-Z][a-zA-Z\-\']+\s+[A-Z][a-zA-Z\-\']+)',
                    r'(?i)loan\s+(?:for|to)\s*[:\s]+([A-Z][a-zA-Z\-\']+\s+[A-Z][a-zA-Z\-\']+)',
                    r'(?i)dear\s+([A-Z][a-zA-Z\-\']+\s+[A-Z][a-zA-Z\-\']+)',
                ]:
                    _m = _af_re.search(_bp, _af_text)
                    if _m:
                        _af_borrower = _m.group(1).strip()
                        break
                # Fallback: use the loan's borrower name
                if not _af_borrower:
                    _af_borrower = loan.get("borrower", "")

            if not _af_result.get("success"):
                st.error(_af_result.get("error", "Could not extract text from this PDF."))
            else:
                # Parse conditions from the result
                _af_conds = []
                _af_cond_text = _af_result.get("conditions", "")
                for _cl in _af_cond_text.split("\n"):
                    _cl = _cl.strip()
                    if _cl.startswith("|") and not _cl.startswith("| #") and not _cl.startswith("|--") and not _cl.startswith("|-"):
                        _cells = [c.strip() for c in _cl.split("|") if c.strip()]
                        if len(_cells) >= 4:
                            _af_conds.append({
                                "num": _cells[0], "desc": _cells[1],
                                "party": _cells[2], "status": _cells[3],
                            })

                # Extract commitment/approval expiration date
                _af_commit_date = ""
                for _cp in [
                    r'(?i)commitment\s*(?:expir(?:es?|ation)|exp)\s*[:\s]*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})',
                    r'(?i)commitment\s*(?:date|valid\s*(?:thru|through|until))\s*[:\s]*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})',
                    r'(?i)(?:this|the)\s*commitment\s*(?:expires?|is\s*valid)\s*(?:on|until|through|thru)\s*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})',
                    r'(?i)commitment\s*(?:letter\s*)?(?:expir|valid)\s*[:\s]*([A-Za-z]+\s+\d{1,2},?\s+\d{4})',
                    r'(?i)(?:approv(?:al|ed)\s*(?:letter\s*)?(?:expir|valid))\s*[:\s]*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})',
                    r'(?i)(?:approv(?:al|ed)\s*(?:letter\s*)?(?:expir|valid))\s*[:\s]*([A-Za-z]+\s+\d{1,2},?\s+\d{4})',
                ]:
                    _cm = _af_re.search(_cp, _af_text)
                    if _cm:
                        _raw_cm = _cm.group(1)
                        from datetime import datetime as _af_cdt
                        for _cfmt in ["%m/%d/%Y", "%m-%d-%Y", "%m/%d/%y", "%m-%d-%y",
                                      "%m.%d.%Y", "%m.%d.%y",
                                      "%B %d, %Y", "%B %d %Y", "%b %d, %Y", "%b %d %Y"]:
                            try:
                                _af_commit_date = _af_cdt.strptime(_raw_cm.strip(), _cfmt).strftime("%Y-%m-%d")
                                break
                            except ValueError:
                                continue
                        if not _af_commit_date:
                            _af_commit_date = _raw_cm
                        break

                # Auto-save commitment date to the loan if found
                if _af_commit_date and not loan.get("commitment_date"):
                    update_loan(lid, commitment_date=_af_commit_date)
                    log_activity(lid, "dates",
                        f"Commitment date auto-set to {_af_commit_date} from approval letter",
                        user=my_name)

                st.session_state[_af_key] = {
                    "borrower": _af_borrower,
                    "conditions": _af_conds,
                    "cond_count": len(_af_conds),
                    "text_length": _af_result.get("text_length", 0),
                    "commitment_date": _af_commit_date,
                    "scan_results": None,
                }
                st.rerun()

        # Show results if we have a scanned approval
        _af_data = st.session_state.get(_af_key)
        if _af_data:
            _af_conds = _af_data["conditions"]
            _af_borrower = _af_data["borrower"]

            st.markdown(
                f'<div style="background:#ffffff;border:1px solid #888;border-radius:8px;'
                f'padding:10px;margin:8px 0;">'
                f'<div style="display:flex;justify-content:space-between;align-items:center;">'
                f'<div>'
                f'<span style="color:#2563eb;font-weight:700;font-size:13px;">Approval Letter Scanned</span><br>'
                f'<span style="color:#5c6370;font-size:12px;">Borrower: <b style="color:#111111;">'
                f'{_af_borrower or "Unknown"}</b> · '
                f'{_af_data["cond_count"]} condition(s) extracted · '
                f'{_af_data["text_length"]:,} chars'
                f'{" · Commitment: <b style=color:#7ee787;>" + _af_data.get("commitment_date","") + "</b>" if _af_data.get("commitment_date") else ""}'
                f'</span>'
                f'</div>'
                f'</div></div>',
                unsafe_allow_html=True,
            )

            if not _af_conds:
                st.warning("No conditions were extracted from this approval letter. "
                           "The document may use an unrecognized format.")
            else:
                # Step 2: Folder path to scan
                _af_default_folder = loan.get("folder_path") or st.session_state.get("last_fetch_folder", "")
                _af_folder = st.text_input(
                    "Borrower folder to scan:",
                    value=_af_default_folder,
                    key=f"af_folder_{lid}",
                    placeholder=r"C:\Loans\SmithJohn",
                )

                _af_c1, _af_c2 = st.columns([1, 1])
                with _af_c1:
                    _af_search = st.button("Scan Folder Against Conditions",
                                           key=f"af_search_btn_{lid}",
                                           use_container_width=True, type="primary")
                with _af_c2:
                    if st.button("Remove️ Clear Approval", key=f"af_clear_{lid}",
                                 use_container_width=True):
                        st.session_state.pop(_af_key, None)
                        st.rerun()

                if _af_search and _af_folder:
                    st.session_state["last_fetch_folder"] = _af_folder
                    if not _af_os.path.isdir(_af_folder):
                        st.error(f"Folder not found: {_af_folder}")
                    else:
                        from folder_search import scan_folder as _af_scan
                        _af_prog = st.progress(0, text="Scanning folder...")
                        _af_scan_res = _af_scan(
                            _af_folder, _af_conds, threshold=50,
                            progress_callback=lambda p, m: _af_prog.progress(min(p, 100), text=m),
                        )
                        _af_data["scan_results"] = _af_scan_res
                        st.session_state[_af_key] = _af_data
                        st.rerun()

                # Step 3: Show the found vs missing dashboard
                _af_scan_res = _af_data.get("scan_results")
                if _af_scan_res and not _af_scan_res.get("error"):
                    _af_found = []
                    _af_missing = []
                    for _c in _af_conds:
                        _cnum = _c["num"]
                        _matches = _af_scan_res.get(_cnum, {}).get("matches", [])
                        if _matches:
                            _af_found.append((_c, _matches))
                        else:
                            _af_missing.append(_c)

                    # Summary cards
                    st.markdown("---")
                    _s1, _s2, _s3 = st.columns(3)
                    with _s1:
                        st.markdown(
                            f'<div class="stat-card"><div class="stat-num" style="color:#111111;">'
                            f'{len(_af_conds)}</div>'
                            f'<div class="stat-label">Total Conditions</div></div>',
                            unsafe_allow_html=True,
                        )
                    with _s2:
                        st.markdown(
                            f'<div class="stat-card"><div class="stat-num" style="color:#27ae60;">'
                            f'{len(_af_found)}</div>'
                            f'<div class="stat-label">✓ Documents Found</div></div>',
                            unsafe_allow_html=True,
                        )
                    with _s3:
                        st.markdown(
                            f'<div class="stat-card"><div class="stat-num" style="color:#e74c3c;">'
                            f'{len(_af_missing)}</div>'
                            f'<div class="stat-label">✗ Still Missing</div></div>',
                            unsafe_allow_html=True,
                        )

                    # Found conditions
                    if _af_found:
                        st.markdown(
                            '<div style="font-size:13px;font-weight:700;color:#27ae60;'
                            'margin:12px 0 6px 0;">FOUND — Documents located in folder</div>',
                            unsafe_allow_html=True,
                        )
                        for _c, _matches in _af_found:
                            _best = _matches[0]
                            _conf_color = "#27ae60" if _best["score"] >= 70 else (
                                "#f1c40f" if _best["score"] >= 50 else "#e67e22"
                            )
                            st.markdown(
                                f'<div style="display:flex;gap:10px;align-items:flex-start;'
                                f'background:#152a1e;border-left:3px solid #27ae60;'
                                f'border-radius:6px;padding:8px 12px;margin-bottom:4px;">'
                                f'<span style="color:#27ae60;font-weight:700;font-size:12px;min-width:20px;">✓</span>'
                                f'<div style="flex:1;">'
                                f'<span style="color:#111111;font-size:13px;font-weight:600;">'
                                f'#{_c["num"]} {_c["desc"][:80]}</span><br>'
                                f'<span style="color:#a8d8a8;font-size:11px;">{_best["file_name"]}'
                                f' &nbsp;·&nbsp; <span style="color:{_conf_color};">{_best["score"]}% match</span>'
                                f' &nbsp;·&nbsp; {_best["match_type"]}</span>'
                                + (f'<br><span style="color:#5c6370;font-size:11px;font-style:italic;">'
                                   f'{_best["snippet"][:120]}</span>' if _best.get("snippet") else "")
                                + (f'<br><span style="color:#5c6370;font-size:10px;">'
                                   f'+{len(_matches)-1} more file(s)</span>' if len(_matches) > 1 else "")
                                + f'</div>'
                                f'<span style="background:{_conf_color};color:#fff;font-size:10px;'
                                f'font-weight:600;padding:2px 8px;border-radius:10px;white-space:nowrap;">'
                                f'{_c["party"]}</span>'
                                f'</div>',
                                unsafe_allow_html=True,
                            )

                    # Missing conditions
                    if _af_missing:
                        st.markdown(
                            '<div style="font-size:13px;font-weight:700;color:#e74c3c;'
                            'margin:12px 0 6px 0;">MISSING — No matching documents found</div>',
                            unsafe_allow_html=True,
                        )
                        for _c in _af_missing:
                            st.markdown(
                                f'<div style="display:flex;gap:10px;align-items:flex-start;'
                                f'background:#3d1515;border-left:3px solid #e74c3c;'
                                f'border-radius:6px;padding:8px 12px;margin-bottom:4px;">'
                                f'<span style="color:#e74c3c;font-weight:700;font-size:12px;min-width:20px;">✗</span>'
                                f'<div style="flex:1;">'
                                f'<span style="color:#111111;font-size:13px;font-weight:600;">'
                                f'#{_c["num"]} {_c["desc"][:80]}</span>'
                                f'</div>'
                                f'<span style="background:#6c757d;color:#fff;font-size:10px;'
                                f'font-weight:600;padding:2px 8px;border-radius:10px;white-space:nowrap;">'
                                f'{_c["party"]}</span>'
                                f'</div>',
                                unsafe_allow_html=True,
                            )

                    # Merge button — push conditions + found/missing status into the loan
                    st.markdown("---")
                    _mc1, _mc2 = st.columns([1, 1])
                    with _mc1:
                        if st.button("✓ Merge conditions into this loan", key=f"af_merge_{lid}",
                                     use_container_width=True, type="primary"):
                            _existing = list(_conditions)
                            _existing_descs = {c.get("desc", "").lower().strip() for c in _existing}
                            _added = 0
                            for _c in _af_conds:
                                if _c["desc"].lower().strip() not in _existing_descs:
                                    _c_copy = dict(_c)
                                    _c_copy["num"] = str(len(_existing) + 1)
                                    # Mark found ones as "Ready to Clear"
                                    _found_nums = {c["num"] for c, _ in _af_found}
                                    if _c["num"] in _found_nums:
                                        _c_copy["status"] = "Ready to Clear"
                                    else:
                                        _c_copy["status"] = "Needed"
                                    _existing.append(_c_copy)
                                    _added += 1
                            # Update missing docs list from missing conditions
                            _miss_list = [c["desc"][:60] for c in _af_missing]
                            _miss_str = ", ".join(_miss_list) if _miss_list else ""
                            update_loan(lid, conditions=_existing, missing_docs=_miss_str)
                            log_activity(lid, "upload",
                                f"Approval letter scanned — {_added} condition(s) merged, "
                                f"{len(_af_found)} found, {len(_af_missing)} missing",
                                user=my_name)
                            st.session_state.pop(_af_key, None)
                            st.toast(f"{_added} conditions merged into loan", icon="✓")
                            st.rerun()
                    with _mc2:
                        if st.button("Merge conditions only (skip folder results)",
                                     key=f"af_merge_conds_only_{lid}",
                                     use_container_width=True):
                            _existing = list(_conditions)
                            _existing_descs = {c.get("desc", "").lower().strip() for c in _existing}
                            _added = 0
                            for _c in _af_conds:
                                if _c["desc"].lower().strip() not in _existing_descs:
                                    _c_copy = dict(_c)
                                    _c_copy["num"] = str(len(_existing) + 1)
                                    _existing.append(_c_copy)
                                    _added += 1
                            update_loan(lid, conditions=_existing)
                            log_activity(lid, "upload",
                                f"Approval letter scanned — {_added} condition(s) merged",
                                user=my_name)
                            st.session_state.pop(_af_key, None)
                            st.toast(f"{_added} conditions merged", icon="✓")
                            st.rerun()

                elif _af_scan_res and _af_scan_res.get("error"):
                    st.error(_af_scan_res["error"])

    # ── Notes ─────────────────────────────────────────────────────────────
    st.markdown(
        '<span style="font-size:13px;font-weight:700;color:#2563eb;text-transform:uppercase;'
        'letter-spacing:0.5px;margin-top:12px;display:inline-block;">Notes</span>',
        unsafe_allow_html=True,
    )
    _cur_notes = loan.get("notes", "")
    _new_notes = st.text_area("Notes", value=_cur_notes, key="detail_notes",
                              label_visibility="collapsed", height=80,
                              placeholder="Add notes about this loan...")
    if st.button("Save Notes", key="detail_save_notes"):
        update_loan(lid, notes=_new_notes)
        log_activity(lid, "note", f"Note updated: {_new_notes[:80]}", user=my_name)
        st.toast("Notes saved", icon="✓")
        st.rerun()

    # ── Quick Actions ─────────────────────────────────────────────────────
    st.markdown(
        '<span style="font-size:13px;font-weight:700;color:#2563eb;text-transform:uppercase;'
        'letter-spacing:0.5px;margin-top:12px;display:inline-block;">Quick Actions</span>',
        unsafe_allow_html=True,
    )
    qa1, qa2, qa3, qa3b, qa4, qa5 = st.columns(6)
    with qa1:
        _new_status = st.selectbox("Change Status", STATUS_OPTIONS,
                                   index=STATUS_OPTIONS.index(status) if status in STATUS_OPTIONS else 0,
                                   key="detail_status")
        if _new_status != status:
            set_status(lid, _new_status)
            log_activity(lid, "status", f"Status changed to {_new_status}", user=my_name)
            st.rerun()
    with qa2:
        from datetime import datetime as _qa_dt
        _cd_val = _qa_dt.strptime(_closing, "%Y-%m-%d").date() if _closing else None
        _new_cd = st.date_input("Closing", value=_cd_val, key="detail_closing")
        _new_cd_str = str(_new_cd) if _new_cd else ""
        if _new_cd_str and _new_cd_str != _closing:
            update_loan(lid, closing_date=_new_cd_str, due_date=_new_cd_str)
            log_activity(lid, "dates", f"Closing date changed to {_new_cd_str}", user=my_name)
            st.rerun()
    with qa3:
        _lk_val = _qa_dt.strptime(_lock, "%Y-%m-%d").date() if _lock else None
        _new_lk = st.date_input("Lock Expiry", value=_lk_val, key="detail_lock")
        _new_lk_str = str(_new_lk) if _new_lk else ""
        if _new_lk_str and _new_lk_str != _lock:
            update_loan(lid, lock_expiry=_new_lk_str)
            log_activity(lid, "dates", f"Lock expiry changed to {_new_lk_str}", user=my_name)
            st.rerun()
    with qa3b:
        _cm_val = _qa_dt.strptime(_commitment, "%Y-%m-%d").date() if _commitment else None
        _new_cm = st.date_input("Commitment", value=_cm_val, key="detail_commitment")
        _new_cm_str = str(_new_cm) if _new_cm else ""
        if _new_cm_str and _new_cm_str != _commitment:
            update_loan(lid, commitment_date=_new_cm_str)
            log_activity(lid, "dates", f"Commitment date changed to {_new_cm_str}", user=my_name)
            st.rerun()
    with qa4:
        _miss_edit = st.text_input("Missing Docs", value=_missing, key="detail_missing",
                                   placeholder="Comma separated")
        if _miss_edit != _missing:
            if st.button("Save Docs", key="detail_save_docs"):
                update_loan(lid, missing_docs=_miss_edit)
                log_activity(lid, "docs", f"Missing docs updated", user=my_name)
                st.rerun()
    with qa5:
        from db import get_all_users as _gau
        _all_u = _gau()
        _unames = ["(Unassigned)"] + [u.get("display_name") or u["email"] for u in _all_u]
        _cur_a = loan.get("assigned_to", "")
        _cur_disp = _cur_a if _cur_a in _unames else "(Unassigned)"
        _new_a = st.selectbox("Assigned To", _unames, index=_unames.index(_cur_disp),
                              key="detail_assign")
        _new_a_val = "" if _new_a == "(Unassigned)" else _new_a
        if _new_a_val != _cur_a:
            update_loan(lid, assigned_to=_new_a_val)
            log_activity(lid, "reassign", f"Reassigned to {_new_a}", user=my_name)
            st.rerun()

    # ── Activity Log ──────────────────────────────────────────────────────
    st.markdown(
        '<span style="font-size:13px;font-weight:700;color:#2563eb;text-transform:uppercase;'
        'letter-spacing:0.5px;margin-top:16px;display:inline-block;">Activity Log</span>',
        unsafe_allow_html=True,
    )
    activity = get_activity(lid)
    if not activity:
        st.markdown(
            '<span style="color:#5c6370;font-size:12px;">No activity recorded yet. '
            'Actions on this loan will appear here.</span>',
            unsafe_allow_html=True,
        )
    else:
        _act_icons = {
            "created": "+",
            "status": "→",
            "reassign": "User",
            "note": "·",
            "dates": "·",
            "removed": "Remove",
            "docs": "—",
            "upload": "Attach",
            "email": "Email",
            "share": "↗",
        }
        for entry in activity[:30]:
            _ts = entry.get("ts", "")[:16].replace("T", " ")
            _action = entry.get("action", "")
            _detail = entry.get("detail", "")
            _user = entry.get("user", "")
            _icon = _act_icons.get(_action, "●")
            _user_tag = f'<span style="color:#2563eb;font-weight:600;">{_user}</span> · ' if _user else ""
            st.markdown(
                f'<div style="display:flex;gap:10px;padding:4px 0;border-bottom:1px solid #888;">'
                f'<span style="font-size:14px;min-width:20px;">{_icon}</span>'
                f'<div>'
                f'<span style="color:#111111;font-size:12px;">{_detail}</span><br>'
                f'<span style="color:#5c6370;font-size:10px;">{_user_tag}{_ts}</span>'
                f'</div></div>',
                unsafe_allow_html=True,
            )


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
        elif page == "billing":
            show_billing_page()
        elif page == "history":
            show_history()
        elif page == "reader":
            show_reader()
        elif page == "loan_detail":
            show_loan_detail()
        else:
            show_dashboard()


if __name__ == "__main__":
    main()
