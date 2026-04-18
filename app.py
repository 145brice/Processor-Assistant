"""
Processor Assistant - Mortgage Document Processing App
Main Streamlit application.
"""

import os
import streamlit as st

# --- Page Config ---
st.set_page_config(
    page_title="Processor Assistant",
    page_icon="—",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- No-cache headers (so CSS/JS edits take effect on reload without F12) ---
st.markdown("""
<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
<meta http-equiv="Pragma" content="no-cache">
<meta http-equiv="Expires" content="0">
""", unsafe_allow_html=True)

# --- Custom CSS ---
st.markdown(r"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600&display=swap');
:root {
    --bg-page: #111111; --bg-white: #1a1a1a; --bg-subtle: #242424;
    --accent: #39FF14; --accent-dark: #32d410; --accent-light: rgba(57, 255, 20, 0.1);
    --green: #39FF14; --green-bg: rgba(57, 255, 20, 0.1); --green-border: rgba(57, 255, 20, 0.3);
    --red: #ef4444; --red-bg: rgba(239, 68, 68, 0.1); --red-border: rgba(239, 68, 68, 0.3);
    --amber: #f59e0b; --amber-bg: rgba(245, 158, 11, 0.1); --amber-border: rgba(245, 158, 11, 0.3);
    --purple: #a78bfa; --purple-bg: rgba(167, 139, 250, 0.1); --purple-border: rgba(167, 139, 250, 0.3);
    --pink: #f472b6; --pink-bg: rgba(244, 114, 182, 0.1); --pink-border: rgba(244, 114, 182, 0.3);
    --gold: #fbbf24; --gold-bg: rgba(251, 191, 36, 0.1);
    --slate-900: #ffffff; --slate-700: #e5e7eb; --slate-600: #9ca3af;
    --slate-500: #6b7280; --slate-400: #6b7280; --slate-300: #374151;
    --slate-200: rgba(255, 255, 255, 0.05); --slate-100: rgba(255, 255, 255, 0.03);
    --radius-sm: 6px; --radius-md: 12px;
    --shadow-card: 0 1px 3px rgba(0,0,0,0.3);
    --shadow-hover: 0 4px 12px rgba(0,0,0,0.4);
    --shadow-lg: 0 10px 30px rgba(0,0,0,0.5);
    --neon-glow: 0 0 20px rgba(57, 255, 20, 0.15), 0 0 60px rgba(57, 255, 20, 0.05);
    --neon-glow-lg: 0 0 30px rgba(57, 255, 20, 0.25), 0 0 80px rgba(57, 255, 20, 0.1);
}
html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
.stApp { background: linear-gradient(160deg, #1a1a1a 0%, #111111 60%, #161616 100%) !important; }
.stApp::before {
    content: ''; position: fixed; top: 0; left: 0; right: 0; bottom: 0;
    background-image: radial-gradient(circle, rgba(57, 255, 20, 0.03) 1px, transparent 1px);
    background-size: 32px 32px; pointer-events: none; z-index: 0;
}
[data-testid="stAppViewContainer"] > div:first-child { background: transparent !important; }
#MainMenu, footer { visibility: hidden; height: 0; }
/* Header must stay visible so sidebar reopen arrow is reachable */
header, [data-testid="stHeader"] { background: transparent !important; visibility: visible !important; display: flex !important; height: auto !important; min-height: 40px !important; z-index: 999999 !important; }
header [data-testid="stDecoration"], header [data-testid="stStatusWidget"] { display: none !important; }
/* Sidebar is permanent — hide all collapse/expand controls so users can't hide it */
[data-testid="stSidebarCollapsedControl"],
[data-testid="stSidebarHeader"],
[data-testid="stSidebarHeader"] *,
[data-testid="stSidebar"] [data-testid="stBaseButton-headerNoPadding"],
[data-testid="stSidebar"] button[kind="headerNoPadding"],
[data-testid="stSidebar"] [data-testid="baseButton-headerNoPadding"],
[data-testid="stSidebar"] [aria-label*="collapse" i],
[data-testid="stSidebar"] [aria-label*="close" i],
[data-testid="stSidebar"] [aria-label*="sidebar" i],
header button:not([kind]):not([aria-label*="menu" i]):not([aria-label*="theme" i]) {
    display: none !important;
    visibility: hidden !important;
    width: 0 !important; height: 0 !important;
    pointer-events: none !important;
    opacity: 0 !important;
}
/* Force sidebar to stay open regardless of collapse state */
[data-testid="stSidebar"][aria-expanded="false"] {
    transform: translateX(0) !important;
    margin-left: 0 !important;
    visibility: visible !important;
}
.stDeployButton { display: none; }
/* Keep native sidebar collapse/expand toggle visible so users can reopen the sidebar */
[data-testid="stSidebar"] { background: linear-gradient(180deg, #222222 0%, #181818 100%) !important; border-right: 1px solid rgba(255,255,255,0.1) !important; }
[data-testid="stSidebar"] > div:first-child { padding: 0.75rem 1rem 1rem 1rem !important; }
[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] { padding-top: 0.5rem !important; margin-top: 0 !important; }
[data-testid="stSidebar"] .block-container { padding-top: 0.75rem !important; }
[data-testid="stSidebar"] button, [data-testid="stSidebar"] button[kind], [data-testid="stSidebar"] [data-testid*="baseButton"] { background: rgba(255,255,255,0.07) !important; border: 1px solid rgba(255,255,255,0.1) !important; color: #c0c0c0 !important; border-radius: var(--radius-sm) !important; font-size: 13px !important; font-weight: 500 !important; text-align: left !important; padding: 8px 12px !important; margin-bottom: 3px !important; width: 100% !important; box-shadow: none !important; transition: all 0.2s ease !important; height: auto !important; min-height: 36px !important; opacity: 1 !important; display: block !important; visibility: visible !important; }
[data-testid="stSidebar"] button p, [data-testid="stSidebar"] button span, [data-testid="stSidebar"] button div { background: transparent !important; color: #c0c0c0 !important; }
[data-testid="stSidebar"] button[kind="primary"] { background: rgba(57,255,20,0.08) !important; border: 1px solid var(--accent) !important; color: var(--accent) !important; font-weight: 600 !important; box-shadow: 0 0 8px rgba(57,255,20,0.18) !important; }
[data-testid="stSidebar"] button[kind="primary"] p, [data-testid="stSidebar"] button[kind="primary"] span, [data-testid="stSidebar"] button[kind="primary"] div { color: var(--accent) !important; font-weight: 600 !important; background: transparent !important; }
[data-testid="stSidebar"] button[kind="primary"]:hover { background: rgba(57,255,20,0.14) !important; border-color: var(--accent) !important; color: var(--accent) !important; box-shadow: 0 0 14px rgba(57,255,20,0.35) !important; }
[data-testid="stSidebar"] button[kind="primary"]:focus, [data-testid="stSidebar"] button[kind="primary"]:active { background: rgba(57,255,20,0.08) !important; color: var(--accent) !important; border-color: var(--accent) !important; }
[data-testid="stSidebar"] button:hover { background: rgba(57,255,20,0.12) !important; border-color: rgba(57,255,20,0.35) !important; color: var(--accent) !important; outline: none !important; box-shadow: none !important; }
[data-testid="stSidebar"] button:focus, [data-testid="stSidebar"] button:focus-visible, [data-testid="stSidebar"] button:active, [data-testid="stSidebar"] button[data-focused="true"] { background: rgba(255,255,255,0.07) !important; border-color: rgba(255,255,255,0.1) !important; color: #c0c0c0 !important; outline: none !important; box-shadow: none !important; }
[data-testid="stSidebar"] button:focus p, [data-testid="stSidebar"] button:focus-visible p, [data-testid="stSidebar"] button:active p { color: #c0c0c0 !important; background: transparent !important; }
button { text-align: left !important; justify-content: flex-start !important; }
button * { text-align: left !important; }
button p { text-align: left !important; width: 100% !important; }
button > div { justify-content: flex-start !important; text-align: left !important; }
.block-container { padding: 1.5rem 2rem 3rem 2rem !important; max-width: 1200px !important; }
h1 { font-size: 24px !important; font-weight: 800 !important; color: var(--slate-900) !important; }
h2, [data-testid="stMarkdownContainer"] h2, .main h2, .block-container h2 { font-size: 42px !important; font-weight: 800 !important; color: var(--accent) !important; padding: 8px 0 8px 14px !important; border-left: 4px solid var(--accent) !important; text-shadow: 0 0 16px rgba(57,255,20,0.5) !important; margin-bottom: 14px !important; line-height: 1.2 !important; }
h2 span, [data-testid="stMarkdownContainer"] h2 span { font-size: inherit !important; color: var(--accent) !important; font-weight: inherit !important; }
h3 { font-size: 15px !important; font-weight: 600 !important; color: var(--slate-700) !important; }
p, li { color: var(--slate-600) !important; font-size: 13px !important; }
label { color: var(--slate-700) !important; font-size: 13px !important; font-weight: 500 !important; }
[data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] li, [data-testid="stMarkdownContainer"] span { color: var(--slate-600) !important; font-size: 13px !important; }
[data-testid="stMarkdownContainer"] strong { color: var(--slate-900) !important; font-weight: 600 !important; }
button[kind="primary"] { background: rgba(57,255,20,0.08) !important; color: var(--accent) !important; border: 1px solid var(--accent) !important; border-radius: var(--radius-sm) !important; font-weight: 700 !important; font-size: 13px !important; height: 36px !important; box-shadow: 0 0 10px rgba(57, 255, 20, 0.18) !important; transition: all 0.25s ease !important; }
button[kind="primary"]:hover { background: rgba(57,255,20,0.15) !important; color: var(--accent) !important; border-color: var(--accent) !important; box-shadow: 0 0 18px rgba(57, 255, 20, 0.4) !important; transform: translateY(-1px) !important; }
button[kind="primary"] p { color: var(--accent) !important; font-weight: 700 !important; }
button[kind="secondary"] { background: linear-gradient(135deg, #2a2a2a 0%, #222222 100%) !important; color: #c0c0c0 !important; border: 1px solid rgba(255,255,255,0.15) !important; border-radius: var(--radius-sm) !important; font-weight: 500 !important; font-size: 12px !important; height: 34px !important; box-shadow: 0 1px 3px rgba(0,0,0,0.4) !important; }
button[kind="secondary"]:hover { border-color: var(--accent) !important; color: var(--accent) !important; background: var(--accent-light) !important; box-shadow: var(--neon-glow) !important; }
button[kind="secondary"] p { color: var(--slate-600) !important; }
button[kind="secondary"]:hover p { color: var(--accent) !important; }
[data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea, [data-testid="stSelectbox"] > div > div, [data-testid="stNumberInput"] input { background: var(--bg-subtle) !important; border: 1px solid var(--slate-300) !important; border-radius: var(--radius-sm) !important; color: var(--slate-900) !important; font-size: 13px !important; }
[data-testid="stTextInput"] input:focus, [data-testid="stTextArea"] textarea:focus { border-color: var(--accent) !important; box-shadow: 0 0 0 3px rgba(57, 255, 20, 0.1) !important; }
[data-testid="stFileUploader"] { background: rgba(255,255,255,0.02) !important; border: 1.5px dashed rgba(57,255,20,0.3) !important; border-radius: 14px !important; padding: 8px !important; transition: all 0.18s ease-in-out !important; }
[data-testid="stFileUploader"]:hover { border-color: rgba(57,255,20,0.6) !important; background: rgba(57,255,20,0.04) !important; box-shadow: 0 0 24px rgba(57,255,20,0.12) !important; }
[data-testid="stFileUploader"] section { background: transparent !important; }
[data-testid="stFileUploader"] button { background: rgba(57,255,20,0.08) !important; border: 1px solid rgba(57,255,20,0.3) !important; color: #39FF14 !important; }
[data-testid="stFileUploader"] small, [data-testid="stFileUploader"] span, [data-testid="stFileUploader"] p { color: #6b7280 !important; }
[data-testid="stFileUploaderFile"] { background: rgba(255,255,255,0.03) !important; border: 1px solid rgba(255,255,255,0.08) !important; }
[data-testid="stFileUploaderFile"] span, [data-testid="stFileUploaderFile"] p { color: #9ca3af !important; }
[data-testid="stFileUploaderFileName"] { color: #e5e7eb !important; font-weight: 600 !important; }
[data-testid="stExpander"] { background: var(--bg-white) !important; border: 1px solid var(--slate-200) !important; border-radius: var(--radius-sm) !important; margin-bottom: 4px !important; box-shadow: none !important; }
[data-testid="stExpander"]:hover { border-color: rgba(255,255,255,0.2) !important; box-shadow: none !important; transform: none !important; }
[data-testid="stExpander"] summary { font-weight: 600 !important; color: var(--slate-900) !important; font-size: 13px !important; padding: 10px 14px !important; }
[data-testid="stExpander"] summary:hover { color: var(--accent) !important; background: var(--accent-light) !important; }
[data-testid="stAlert"][data-type="warning"], .stAlert[kind="warning"] { background: var(--amber-bg) !important; color: var(--amber) !important; border: 1px solid var(--amber-border) !important; }
[data-testid="stAlert"][data-type="error"], .stAlert[kind="error"] { background: var(--red-bg) !important; color: var(--red) !important; border: 1px solid var(--red-border) !important; }
[data-testid="stAlert"][data-type="success"], .stAlert[kind="success"] { background: var(--green-bg) !important; color: var(--green) !important; border: 1px solid var(--green-border) !important; }
[data-testid="stAlert"][data-type="info"], .stAlert[kind="info"] { background: var(--accent-light) !important; color: var(--accent) !important; border: 1px solid var(--green-border) !important; }
hr { border-color: var(--slate-200) !important; margin: 12px 0 !important; }
[data-testid="stTabs"] [role="tab"] { font-size: 13px !important; font-weight: 500 !important; color: var(--slate-500) !important; }
[data-testid="stTabs"] [role="tab"][aria-selected="true"] { color: var(--accent) !important; border-bottom: 2px solid var(--accent) !important; font-weight: 700 !important; }
[data-testid="stProgress"] > div > div { background: var(--accent) !important; }
[data-testid="stProgress"] { background: var(--slate-300) !important; }
[data-testid="stVerticalBlockBorderWrapper"] { background: var(--bg-white) !important; border: 1px solid var(--slate-200) !important; border-radius: var(--radius-sm) !important; box-shadow: none !important; }
[data-testid="stVerticalBlockBorderWrapper"]:hover { border-color: rgba(255,255,255,0.2) !important; box-shadow: none !important; transform: none !important; }
[data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"] { background: transparent !important; border: none !important; box-shadow: none !important; }
[data-testid="stSidebar"] button > div, [data-testid="stSidebar"] button > div > div, [data-testid="stSidebar"] [data-testid="baseButton-secondary"] { background: transparent !important; }
[data-testid="stSidebar"] [data-testid="baseButton-secondary"]:hover { background: rgba(57,255,20,0.12) !important; }
[data-baseweb="popover"] ul, [data-baseweb="menu"] { background: var(--bg-white) !important; border: 1px solid var(--slate-300) !important; box-shadow: var(--shadow-hover) !important; }
[data-baseweb="popover"] li, [data-baseweb="menu"] li { background: var(--bg-white) !important; color: var(--slate-900) !important; }
[data-baseweb="popover"] li:hover, [data-baseweb="menu"] li:hover { background: var(--accent-light) !important; color: var(--accent) !important; }
[data-baseweb="select"] > div { background: var(--bg-subtle) !important; border-color: var(--slate-300) !important; color: var(--slate-900) !important; }
[data-testid="stToggle"] > label > div[data-checked="true"] { background: var(--accent) !important; }
[data-testid="stHorizontalBlock"] { gap: 0.3rem !important; }
[data-testid="stHorizontalBlock"] > div > div { margin-bottom: 2px !important; }
[data-testid="stVerticalBlock"] { gap: 6px !important; }
[data-testid="stMultiSelect"] > div { background: var(--bg-subtle) !important; border: 1px solid var(--slate-300) !important; }
[data-testid="stMultiSelect"] span[data-baseweb="tag"] { background: var(--accent-light) !important; color: var(--accent) !important; border: 1px solid var(--green-border) !important; }
[data-testid="stMarkdownContainer"] table { width: 100% !important; border-collapse: collapse !important; background: var(--bg-white) !important; border: 1px solid var(--slate-200) !important; box-shadow: var(--shadow-card) !important; }
[data-testid="stMarkdownContainer"] thead tr { background: var(--bg-subtle) !important; }
[data-testid="stMarkdownContainer"] th { color: var(--slate-700) !important; font-size: 11px !important; font-weight: 600 !important; padding: 8px 12px !important; text-transform: uppercase !important; border-bottom: 2px solid var(--slate-300) !important; }
[data-testid="stMarkdownContainer"] td { color: var(--slate-900) !important; font-size: 13px !important; padding: 6px 12px !important; border-bottom: 1px solid var(--slate-200) !important; }
[data-testid="stMarkdownContainer"] tr:hover td { background: var(--accent-light) !important; }
.progress-nav { display: flex; gap: 3px; background: var(--bg-subtle); border-radius: var(--radius-md); padding: 4px; margin-bottom: 14px; border: 1px solid var(--slate-200); box-shadow: var(--shadow-card); }
.pn-step { flex: 1; min-width: 70px; text-align: center; padding: 6px; border-radius: var(--radius-sm); font-size: 10px; font-weight: 500; text-decoration: none; color: var(--slate-500); }
.pn-step.done { background: var(--green-bg); color: var(--green); border: 1px solid var(--green-border); font-weight: 600 !important; }
.pn-step.active { background: var(--accent-light); color: var(--accent); border: 1px solid var(--accent); font-weight: 600 !important; box-shadow: 0 0 10px rgba(57, 255, 20, 0.15); }
.pn-step.pending { background: transparent; color: var(--slate-500); }
.pn-num { display: block; font-size: 12px; font-weight: 600; margin-bottom: 1px; }
.badge { display: inline-block; padding: 2px 10px; border-radius: 9999px; font-size: 11px; font-weight: 600; }
.badge-borrower { background: var(--accent-light); color: var(--accent); border: 1px solid var(--green-border); }
.badge-title { background: var(--purple-bg); color: var(--purple); border: 1px solid var(--purple-border); }
.badge-underwriter { background: var(--amber-bg); color: var(--amber); border: 1px solid var(--amber-border); }
.badge-insurance { background: var(--green-bg); color: var(--green); border: 1px solid var(--green-border); }
.badge-closer { background: var(--gold-bg); color: var(--gold); border: 1px solid rgba(251, 191, 36, 0.3); }
.badge-jr { background: var(--pink-bg); color: var(--pink); border: 1px solid var(--pink-border); }
.badge-manager { background: var(--accent-light); color: var(--accent); border: 1px solid var(--green-border); }
.badge-appraiser { background: var(--green-bg); color: var(--green); border: 1px solid var(--green-border); }
.badge-default { background: var(--slate-100); color: var(--slate-600); border: 1px solid var(--slate-200); }
.status-chip { display: inline-block; padding: 3px 10px; border-radius: 9999px; font-size: 11px; font-weight: 600; }
.status-pending { background: var(--red-bg); color: var(--red); border: 1px solid var(--red-border); }
.status-requested { background: var(--amber-bg); color: var(--amber); border: 1px solid var(--amber-border); }
.status-cleared { background: var(--green-bg); color: var(--green); border: 1px solid var(--green-border); }
.status-overdue { background: var(--slate-100); color: var(--slate-600); border: 1px solid var(--slate-300); }
.status-closed { background: var(--slate-100); color: var(--slate-500); border: 1px solid var(--slate-200); }
.loan-card { background: var(--bg-white); border: 1px solid var(--slate-200); border-radius: var(--radius-md); padding: 6px 12px; margin: 0 0 4px 0; box-shadow: var(--shadow-card); line-height: 1.3; transition: transform 0.3s ease, box-shadow 0.3s ease, border-color 0.3s ease !important; }
.loan-card:hover { border-color: var(--accent) !important; background: var(--accent-light) !important; box-shadow: var(--neon-glow) !important; transform: translateY(-2px) !important; }
.loan-num { font-size: 13px; font-weight: 700; color: var(--accent); font-family: 'JetBrains Mono', monospace; }
.loan-name { font-size: 13px; color: var(--slate-900); font-weight: 600; }
.loan-due { font-size: 11px; color: var(--slate-500); }
.loan-missing { font-size: 11px; color: var(--red); font-weight: 500; }
.stat-card { text-align: left; padding: 10px 14px; border-radius: var(--radius-md); background: var(--bg-white); border: 1px solid var(--slate-200); box-shadow: var(--shadow-card); transition: transform 0.3s ease, box-shadow 0.3s ease, border-color 0.3s ease !important; }
.stat-card:hover { border-color: var(--accent) !important; box-shadow: var(--neon-glow) !important; transform: translateY(-2px) !important; }
.stat-num { font-size: 20px; font-weight: 700; color: var(--accent); }
.stat-label { font-size: 10px; color: var(--slate-500); font-weight: 600; text-transform: uppercase; letter-spacing: 0.4px; }
.login-card { max-width: 360px; margin: 0 auto; background: var(--bg-white); border: 1px solid var(--slate-200); border-radius: 16px; padding: 36px 32px 28px; box-shadow: 0 0 30px rgba(57, 255, 20, 0.1), 0 4px 24px rgba(0,0,0,0.4); }
.login-title { font-size: 22px; font-weight: 800; color: var(--slate-900); text-align: center; letter-spacing: -0.4px; }
.login-sub { font-size: 12px; color: var(--slate-500); text-align: center; margin-bottom: 20px; }
.login-page-wrap { max-width: 360px; margin: 0 auto; padding: 0 0 40px 0; }
.login-sandbox-btn button { background: rgba(57,255,20,0.08) !important; color: var(--accent) !important; border: 1px solid var(--accent) !important; font-weight: 700 !important; font-size: 13px !important; border-radius: 12px !important; height: 44px !important; min-height: 44px !important; box-shadow: 0 0 14px rgba(57, 255, 20, 0.25) !important; transition: all 0.25s ease !important; }
.login-sandbox-btn button:hover { box-shadow: 0 0 30px rgba(57, 255, 20, 0.4) !important; transform: translateY(-2px) !important; }
.login-sandbox-btn button p { color: #000 !important; font-weight: 700 !important; }
.login-divider { display:flex;align-items:center;gap:10px;margin:18px 0 14px; }
.login-divider span { font-size:11px;color:var(--slate-500);white-space:nowrap; }
.login-divider hr { flex:1;border:none;border-top:1px solid var(--slate-200); }
[data-testid="stToast"], div[data-testid="stToast"] > div { background: var(--bg-white) !important; color: var(--slate-900) !important; border: 1px solid var(--slate-300) !important; }
div[data-baseweb="popover"], ul[data-testid="stSelectboxVirtualDropdown"] { background: var(--bg-white) !important; border: 1px solid var(--slate-300) !important; }
[data-baseweb="tooltip"] { background: #1a1a1a !important; color: #c0c0c0 !important; border: 1px solid rgba(255,255,255,0.15) !important; box-shadow: none !important; }
[data-baseweb="tooltip"] * { background: transparent !important; color: #c0c0c0 !important; }
div[data-baseweb="popover"] li, ul[data-testid="stSelectboxVirtualDropdown"] li { color: var(--slate-900) !important; }
div[data-baseweb="popover"] li:hover, ul[data-testid="stSelectboxVirtualDropdown"] li:hover { background: var(--accent-light) !important; }
[data-testid="stCaptionContainer"] p { color: var(--slate-500) !important; }
.glow-text { text-shadow: 0 0 40px rgba(57, 255, 20, 0.3); }
/* Pipeline: flat compact cards */
.pipeline-scroll button { height: 28px !important; min-height: 28px !important; font-size: 12px !important; font-weight: 600 !important; padding: 0 8px !important; border-radius: 3px !important; background: rgba(255,255,255,0.05) !important; border: 1px solid rgba(255,255,255,0.1) !important; color: #e5e7eb !important; box-shadow: none !important; transform: none !important; }
.pipeline-scroll button:hover { background: rgba(255,255,255,0.1) !important; border-color: rgba(255,255,255,0.25) !important; color: #ffffff !important; transform: none !important; box-shadow: none !important; }
.pipeline-scroll button p { color: inherit !important; font-size: 12px !important; font-weight: 600 !important; }
/* Primary (Open) button inside pipeline — neon-green, more prominent */
.pipeline-scroll button[kind="primary"], button[kind="primary"][data-testid*="open_"] {
    background: rgba(57,255,20,0.08) !important;
    border: 1px solid var(--accent) !important;
    color: var(--accent) !important;
    font-weight: 800 !important;
    font-size: 13px !important;
    height: 34px !important;
    min-height: 34px !important;
    letter-spacing: 0.5px !important;
    box-shadow: 0 0 10px rgba(57,255,20,0.2) !important;
}
.pipeline-scroll button[kind="primary"]:hover, button[kind="primary"][data-testid*="open_"]:hover {
    background: rgba(57,255,20,0.16) !important;
    box-shadow: 0 0 16px rgba(57,255,20,0.45) !important;
    color: var(--accent) !important;
}
.pipeline-scroll button[kind="primary"] p { color: var(--accent) !important; font-weight: 800 !important; font-size: 13px !important; }
/* Hoverable contact chip tooltip */
.pa-tip { position: relative; cursor: help; display: inline-block; }
.pa-tip-box { visibility: hidden; opacity: 0; position: absolute; bottom: 125%; left: 0; z-index: 9999;
    background: #1a1a1a; border: 1px solid rgba(57,255,20,0.35); border-radius: 8px;
    padding: 8px 10px; min-width: 200px; max-width: 320px;
    box-shadow: 0 6px 24px rgba(0,0,0,0.6); transition: opacity 0.12s ease-in-out;
    white-space: normal; pointer-events: none; }
.pa-tip:hover .pa-tip-box { visibility: visible; opacity: 1; }
/* Scan results: tight like pipeline cards */
.scan-scroll button { height: 26px !important; min-height: 26px !important; font-size: 11px !important; font-weight: 600 !important; padding: 0 7px !important; border-radius: 3px !important; background: rgba(255,255,255,0.05) !important; border: 1px solid rgba(255,255,255,0.1) !important; color: #e5e7eb !important; box-shadow: none !important; transform: none !important; }
.scan-scroll button:hover { background: rgba(255,255,255,0.1) !important; border-color: rgba(255,255,255,0.25) !important; color: #ffffff !important; }
.scan-scroll button p { color: inherit !important; font-size: 11px !important; font-weight: 600 !important; margin: 0 !important; }
.scan-scroll [data-testid="stCheckbox"] label { font-size: 11px !important; font-weight: 700 !important; color: #39FF14 !important; }
.scan-scroll [data-testid="stCheckbox"] { padding-top: 2px !important; }
.scan-scroll [data-baseweb="select"] > div { min-height: 26px !important; height: 26px !important; font-size: 11px !important; }
.scan-scroll [data-baseweb="select"] * { font-size: 11px !important; }
.scan-scroll div[data-testid="stVerticalBlock"] { gap: 2px !important; }
.scan-scroll div[data-testid="stHorizontalBlock"] { gap: 4px !important; align-items: center !important; }
.scan-scroll .cond-row { display:flex; align-items:center; gap:6px; padding:3px 0; border-bottom:1px dashed rgba(255,255,255,0.06); }
.scan-scroll .cond-num { color:#39FF14; font-weight:800; font-size:11px; min-width:22px; }
.scan-scroll .cond-desc { color:#e5e7eb; font-size:12px; line-height:1.35; flex:1; }
.scan-scroll .pa-section { font-size:10px; font-weight:700; color:#9ca3af; text-transform:uppercase; letter-spacing:0.6px; margin:6px 0 2px 0; }
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

# ── Persist auth across browser refreshes ──────────────────────────────────
import json as _json_auth
_SESSION_FILE = os.path.join(os.path.dirname(__file__), ".session_cache.json")
_AUTH_KEYS = ["authenticated", "user_id", "user_email", "user_name", "user_role", "sandbox_mode", "page"]

def _save_session():
    try:
        _data = {k: st.session_state.get(k) for k in _AUTH_KEYS}
        with open(_SESSION_FILE, "w") as _f:
            _json_auth.dump(_data, _f)
    except Exception:
        pass

def _clear_session():
    try:
        if os.path.exists(_SESSION_FILE):
            os.remove(_SESSION_FILE)
    except Exception:
        pass

# Initialize defaults first
for key, val in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = val

# Restore from session file if not yet authenticated
if not st.session_state.get("authenticated"):
    try:
        if os.path.exists(_SESSION_FILE):
            with open(_SESSION_FILE) as _f:
                _cached = _json_auth.load(_f)
            if _cached.get("authenticated") and _cached.get("user_id"):
                for _k, _v in _cached.items():
                    st.session_state[_k] = _v
    except Exception:
        pass


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


def _render_condition(_c, _fkey, _party_options, _cond_statuses):
    """Render a single condition row with checkbox, status, and party selector.
    Returns (checked_bool, status_str, parties_list)."""
    _cnum = _c.get("num", "?")
    _cdesc = _c.get("desc", "—")
    _cparty = _c.get("party", "Borrower")
    _cstatus = _c.get("status", "Needed")

    _uid = f"{_fkey}_{_cnum}"

    # Three-column layout for each condition
    _cc1, _cc2, _cc3 = st.columns([1, 1.5, 2])
    with _cc1:
        _chk = st.checkbox(f"#{_cnum}", value=False, key=f"{_uid}_chk")
    with _cc2:
        _status_labels = list(_cond_statuses.keys())
        _status_idx = _status_labels.index(_cstatus) if _cstatus in _status_labels else 0
        _cstat = st.selectbox(
            "Status",
            _status_labels,
            index=_status_idx,
            key=f"{_uid}_stat",
            label_visibility="collapsed",
        )
    with _cc3:
        _cparties = st.multiselect(
            "Parties",
            _party_options,
            default=[_cparty] if _cparty in _party_options else [],
            key=f"{_uid}_party",
            label_visibility="collapsed",
        )

    # Show condition description
    st.markdown(
        f'<div style="font-size:12px;color:#ffffff;margin:-8px 0 8px 0;">'
        f'<b style="color:#39FF14;">#{_cnum}</b> {_cdesc}'
        f'<span style="color:#9ca3af;margin-left:8px;font-size:11px;">'
        f'{_cstat}</span></div>',
        unsafe_allow_html=True,
    )

    return (_chk, _cstat, _cparties)


def show_login_page():
    """Login / Signup page."""
    # Push content down and center it with a narrow column
    st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)
    _, center, _ = st.columns([1, 1.4, 1])

    with center:
        st.markdown('<div class="login-page-wrap">', unsafe_allow_html=True)

        # ── Branding ────────────────────────────────────────────────
        st.markdown("""
        <div style="text-align:center;margin-bottom:24px;">
          <div style="display:inline-flex;align-items:center;justify-content:center;
               width:48px;height:48px;background:linear-gradient(135deg,#39FF14,#32E012);
               border-radius:12px;margin-bottom:12px;">
            <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 21h8M12 17v4"/>
            </svg>
          </div>
          <div style="font-size:22px;font-weight:800;color:#ffffff;letter-spacing:-0.5px;line-height:1.1;">
            Processor Assistant
          </div>
          <div style="font-size:11px;color:#9ca3af;margin-top:5px;letter-spacing:0.3px;">
            OFFLINE MORTGAGE PROCESSING
          </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Sandbox button ───────────────────────────────────────────
        st.markdown('<div class="login-sandbox-btn">', unsafe_allow_html=True)
        if st.button("Try Sandbox  —  No Account Needed", type="primary", use_container_width=True):
            st.session_state.authenticated = True
            st.session_state.user_id = "sandbox"
            st.session_state.user_email = "sandbox@demo"
            st.session_state.user_name = "Sandbox User"
            st.session_state.user_role = "Processor"
            st.session_state.sandbox_mode = True
            st.session_state.page = "dashboard"
            _save_session()
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown(
            '<div style="text-align:center;font-size:10px;color:#9ca3af;margin-top:4px;margin-bottom:4px;">'
            'Full access · Nothing saved between sessions</div>',
            unsafe_allow_html=True
        )

        # ── Divider ──────────────────────────────────────────────────
        st.markdown("""
        <div class="login-divider">
          <hr/><span>or sign in with your account</span><hr/>
        </div>
        """, unsafe_allow_html=True)

        # ── Tabs: Login / Sign Up ─────────────────────────────────────
        tab_login, tab_signup = st.tabs(["Login", "Sign Up"])

        with tab_login:
            with st.form("login_form"):
                email = st.text_input("Email", placeholder="you@example.com")
                password = st.text_input("Password", type="password", placeholder="••••••••")
                submitted = st.form_submit_button("Sign In", use_container_width=True, type="primary")
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
                        _save_session()
                        st.rerun()
                    else:
                        st.error(result.get("error", "Login failed"))

        with tab_signup:
            with st.form("signup_form"):
                from db import ROLE_OPTIONS
                display_name = st.text_input("Full Name", placeholder="e.g. Maria Garcia", key="signup_name")
                role = st.selectbox("Role", ROLE_OPTIONS, key="signup_role")
                email = st.text_input("Email", placeholder="you@example.com", key="signup_email")
                password = st.text_input("Password", type="password", placeholder="Min 6 characters", key="signup_pass")
                confirm = st.text_input("Confirm Password", type="password", placeholder="Repeat password", key="signup_confirm")
                tos = st.checkbox(
                    "Documents are processed in memory only and never stored. "
                    "I have authorization to process any documents I upload."
                )
                submitted = st.form_submit_button("Create Account", use_container_width=True, type="primary")
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

        # ── Footer ───────────────────────────────────────────────────
        st.markdown("""
        <div style="text-align:center;margin-top:20px;font-size:10px;color:#d1d5db;">
          100% offline &nbsp;·&nbsp; No cloud &nbsp;·&nbsp; No API keys required
        </div>
        """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)




def show_sidebar():
    """Sidebar navigation."""
    with st.sidebar:
        user_name = st.session_state.get("user_name", "")
        user_role = st.session_state.get("user_role", "")
        is_sandbox = st.session_state.get("sandbox_mode", False)

        st.markdown(
            '<div style="padding:0 0 36px 0;margin-top:-4px;">'
            '<div style="font-size:18px;font-weight:800;color:var(--slate-900);letter-spacing:-0.3px;">'
            'Processor Assistant</div>'
            '<div style="font-size:10px;color:var(--slate-400);margin-top:2px;">Offline · Local</div>'
            '</div>',
            unsafe_allow_html=True,
        )

        # ── Who's logged in ──────────────────────────────────────────────────
        if is_sandbox:
            st.markdown(
                '<div style="font-size:11px;color:var(--slate-500);margin-bottom:10px;">'
                '* Sandbox Mode</div>',
                unsafe_allow_html=True,
            )
        elif user_name:
            role_color = {"Loan Officer": "var(--amber)", "Manager": "var(--accent)",
                          "Jr Underwriter": "var(--red)"}.get(user_role, "var(--accent)")
            st.markdown(
                f'<div style="font-size:12px;font-weight:700;color:var(--slate-900);'
                f'margin-bottom:2px;">{user_name}</div>'
                f'<div style="font-size:10px;color:{role_color};font-weight:600;'
                f'margin-bottom:10px;">{user_role}</div>',
                unsafe_allow_html=True,
            )

        _current_page = st.session_state.get("page", "dashboard")

        # ── Email Watch live stats for badge ─────────────────────────────────
        import email_watch as _ew
        _ew_status  = _ew.get_status()
        _ew_pending = _ew_status["pending_count"]
        _ew_running = _ew_status["running"]
        _ew_dot     = "●" if _ew_running else "○"
        _ew_badge   = f" ({_ew_pending})" if _ew_pending else ""

        _nav_items = [
            ("Scanner",  "dashboard", "⬡"),
            ("Pipeline", "pipeline",  "⬡"),
            ("Reader",   "reader",    "⬡"),
            ("Team",     "team",      "⬡"),
            ("AI",       "ollama",    "⬡"),
            ("Billing",  "billing",   "⬡"),
        ]
        if not is_sandbox:
            _nav_items.append(("History", "history", "⬡"))

        for _nav_label, _nav_page, _nav_icon in _nav_items:
            _active = _current_page == _nav_page
            _btn_label = ("● " + _nav_label) if _active else _nav_label
            if st.button(_btn_label, key=f"nav_{_nav_page}", use_container_width=True,
                         type=("primary" if _active else "secondary")):
                st.session_state.page = _nav_page
                _save_session()
                st.rerun()

        # ── Email Watch — top-level + sub-nav ────────────────────────────────
        _ew_pages   = ("email_watch", "email_watch_controls")
        _ew_active  = _current_page in _ew_pages
        _ew_top_lbl = f"{_ew_dot} Email Watch{_ew_badge}"
        if _ew_active:
            _ew_top_lbl = "● " + _ew_top_lbl
        if st.button(_ew_top_lbl, key="nav_email_watch_top", use_container_width=True,
                     type=("primary" if _ew_active else "secondary")):
            if _ew_active:
                st.session_state["ew_nav_open"] = not st.session_state.get("ew_nav_open", True)
            else:
                st.session_state["ew_nav_open"] = True
                st.session_state.page = "email_watch_controls"
                _save_session()
                st.rerun()
        _ew_open = _ew_active or st.session_state.get("ew_nav_open", False)
        if _ew_open:
            _ew_sub = [
                ("Controls", "email_watch_controls"),
                ("Results",  "email_watch"),
            ]
            for _sub_lbl, _sub_page in _ew_sub:
                _sub_active = _current_page == _sub_page
                _suffix = f"  ({_ew_pending})" if (_sub_page == "email_watch" and _ew_pending) else ""
                _c_gutter, _c_btn = st.columns([1, 8])
                with _c_btn:
                    if st.button(_sub_lbl + _suffix, key=f"nav_{_sub_page}", use_container_width=True,
                                 type=("primary" if _sub_active else "secondary")):
                        st.session_state.page = _sub_page
                        st.session_state["ew_nav_open"] = True
                        _save_session()
                        st.rerun()

        st.markdown("---")

        # ── AI status indicator ───────────────────────────────────────────────
        import ai_router as _ar
        _ar_status = _ar.get_status()
        _pref = _ar_status["preferred"]
        if _pref == "cloud" and _ar_status["cloud_enabled"]:
            _ai_lbl = f"Cloud · {_ar_status['cloud_provider'].title()}"
        elif _pref == "ollama" and _ar_status["ollama_enabled"]:
            _ai_lbl = f"Ollama · {_ar_status['ollama_model']}"
        elif _ar_status["cloud_enabled"]:
            _ai_lbl = f"Cloud (fallback)"
        elif _ar_status["ollama_enabled"]:
            _ai_lbl = f"Ollama (fallback)"
        else:
            _ai_lbl = "Script only"
        st.markdown(
            f'<div style="background:#1e1e1e;border:1px solid rgba(255,255,255,0.1);'
            f'border-radius:var(--radius-sm);padding:5px 10px;margin-bottom:8px;font-size:12px;'
            f'color:#9ca3af;">'
            f'AI · {_ai_lbl}</div>',
            unsafe_allow_html=True,
        )

        if st.button("Logout", use_container_width=True):
            _clear_session()
            for key in DEFAULTS:
                st.session_state[key] = DEFAULTS[key]
            st.rerun()


def show_dashboard():
    """Compact document scanning page — always auto-detect, additive scanning."""
    _BULK_DOC_TYPES = [
        "Approval Letter", "Closing Disclosure (CD)", "Loan Estimate (LE)",
        "1003 Application", "Purchase Contract", "Credit Report",
        "Bank Statement", "Change of Circumstance (COC)", "Broker Package (BP)",
        "Pay Stub", "W-2", "1099", "Tax Return", "Appraisal",
        "Title Commitment", "Hazard Insurance", "Mortgage Statement",
        "VA Certificate of Eligibility", "DD-214", "Government ID", "Unknown",
    ]

    # Session state for accumulated scan batches
    if "scan_batches" not in st.session_state:
        st.session_state.scan_batches = []

    _has_batches = bool(st.session_state.scan_batches)
    _has_upload = bool(st.session_state.get("dash_uploader"))

    # ── Header: hero when empty, compact when active ─────────────────
    if not _has_batches and not _has_upload:
        _loan_ct = 0
        try:
            from crm import get_all_loans as _gl_hero
            _loan_ct = len(_gl_hero())
        except Exception:
            pass
        _user = st.session_state.get("user_name", "") or "there"
        st.markdown(
            f"""
            <div style="margin:8px 0 18px 0;padding:22px 26px;
                 background:linear-gradient(135deg, rgba(57,255,20,0.06) 0%, rgba(57,255,20,0.015) 100%);
                 border:1px solid rgba(57,255,20,0.18);border-radius:14px;
                 box-shadow:0 4px 24px rgba(0,0,0,0.25);">
              <div style="display:flex;align-items:center;gap:14px;margin-bottom:6px;">
                <div style="width:42px;height:42px;border-radius:11px;
                     background:linear-gradient(135deg,#39FF14,#2ed410);
                     display:flex;align-items:center;justify-content:center;
                     box-shadow:0 0 16px rgba(57,255,20,0.4);">
                  <svg width="22" height="22" viewBox="0 0 24 24" fill="none"
                       stroke="#0a0a0a" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="3" y="4" width="18" height="16" rx="2"/>
                    <path d="M7 8h10M7 12h10M7 16h6"/>
                  </svg>
                </div>
                <div>
                  <div style="font-size:22px;font-weight:800;color:#ffffff;line-height:1.1;letter-spacing:-0.4px;">
                    Welcome back, {_user.split()[0] if _user else 'there'}.
                  </div>
                  <div style="font-size:13px;color:#9ca3af;margin-top:3px;">
                    Drop in any loan document — I'll auto-detect the type, pull conditions & contacts, and match it to your pipeline.
                  </div>
                </div>
              </div>
              <div style="display:flex;gap:18px;margin-top:14px;flex-wrap:wrap;">
                <div style="font-size:11px;color:#9ca3af;">
                  <span style="color:#39FF14;font-weight:700;">●</span>
                  Approval · CD · LE · 1003 · Purchase Contract · Bank Stmt · W-2 · Appraisal · Title · HOI · and more
                </div>
                <div style="font-size:11px;color:#9ca3af;margin-left:auto;">
                  <b style="color:#39FF14;">{_loan_ct}</b> loan{'s' if _loan_ct != 1 else ''} in pipeline
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div style="display:flex;align-items:center;gap:10px;margin:4px 0 10px 0;">'
            '<div style="width:26px;height:26px;border-radius:7px;'
            'background:linear-gradient(135deg,#39FF14,#2ed410);'
            'display:flex;align-items:center;justify-content:center;">'
            '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" '
            'stroke="#0a0a0a" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round">'
            '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M7 8h10M7 12h10M7 16h6"/>'
            '</svg></div>'
            '<div style="font-size:18px;font-weight:800;color:#ffffff;letter-spacing:-0.3px;">Scanner</div>'
            '</div>',
            unsafe_allow_html=True,
        )

    # ── File uploader (additive) ─────────────────────────────────────
    new_files = st.file_uploader(
        "Drop PDFs here — or click to browse" if not _has_upload else "Add more PDFs",
        type=["pdf"], accept_multiple_files=True,
        key="dash_uploader",
    )

    if new_files:
        import hashlib as _hashlib
        import re as _re
        import io as _io
        import pypdf as _pypdf
        from ai_engine import detect_doc_type as _detect, process_document as _proc

        # ── Helper: extract grouping fingerprint from PDF bytes ──────
        def _extract_fingerprint(pdf_bytes):
            """Pull account numbers, names, dates, page sequence from PDF text."""
            fp = {"account": None, "names": [], "period": None, "page_num": None, "page_total": None}
            try:
                _r = _pypdf.PdfReader(_io.BytesIO(pdf_bytes))
                # Read first 3 pages max for speed
                _text = ""
                for _pg in _r.pages[:3]:
                    try:
                        _text += (_pg.extract_text() or "") + "\n"
                    except Exception:
                        pass

                # Account number — digits/dashes, often masked with X or *
                _acct = _re.search(r'(?:account\s*(?:number|#|no\.?)[:\s]*)([\dX*\-]{6,20})', _text, _re.I)
                if not _acct:
                    _acct = _re.search(r'(?:Primary account number[:\s]*)([\d\-]{6,20})', _text, _re.I)
                if not _acct:
                    # Last 4 shown as "...1234" or "ending in 1234"
                    _acct = _re.search(r'ending\s+in\s+(\d{4})', _text, _re.I)
                if _acct:
                    fp["account"] = _re.sub(r'[\s]', '', _acct.group(1)).upper()

                # Names — ALL CAPS lines in first 40 lines (borrower name style)
                _lines = _text.split("\n")
                _skip = {"STATEMENT", "BANK", "ACCOUNT", "BALANCE", "SUMMARY", "PAGE",
                         "DATE", "PERIOD", "DEPOSITS", "WITHDRAWALS", "BEGINNING", "ENDING",
                         "DESCRIPTION", "AMOUNT", "TRANSACTION", "ACTIVITY", "CHECKING",
                         "SAVINGS", "TOTAL", "AVAILABLE", "INTEREST", "SERVICE", "FEE",
                         "ONLINE", "MEMBER", "FEDERAL", "CREDIT", "UNION", "FINANCIAL"}
                for _ln in _lines[:50]:
                    _ln = _ln.strip()
                    if (len(_ln) >= 4 and _ln.isupper()
                            and _re.match(r'^[A-Z][A-Z\s\-\.]+$', _ln)
                            and not any(w in _ln.split() for w in _skip)
                            and len(_ln.split()) <= 5):
                        fp["names"].append(_ln)

                # Statement period
                _period = _re.search(
                    r'(?:for\s+the\s+period|statement\s+period|period)[:\s]+(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})\s*(?:to|through|[-–])\s*(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})',
                    _text, _re.I
                )
                if _period:
                    fp["period"] = (_period.group(1), _period.group(2))

                # Page X of Y
                _pg_match = _re.search(r'page\s+(\d+)\s+of\s+(\d+)', _text, _re.I)
                if _pg_match:
                    fp["page_num"] = int(_pg_match.group(1))
                    fp["page_total"] = int(_pg_match.group(2))

            except Exception:
                pass
            return fp

        # ── Duplicate detection (MD5) ────────────────────────────────
        _file_hashes = {}
        _dupes = set()
        _file_bytes_cache = {}
        for _fi, _uf in enumerate(new_files):
            _fbytes = _uf.read()
            _uf.seek(0)
            _file_bytes_cache[_fi] = _fbytes
            _fhash = _hashlib.md5(_fbytes).hexdigest()
            if _fhash in _file_hashes:
                _dupes.add(_fi)
                _dupes.add(_file_hashes[_fhash])
            else:
                _file_hashes[_fhash] = _fi

        if _dupes:
            # Group dupe indices by hash to show which files are actually identical
            _hash_to_indices = {}
            for _fi, _fbytes in _file_bytes_cache.items():
                _fh = _hashlib.md5(_fbytes).hexdigest()
                _hash_to_indices.setdefault(_fh, []).append(_fi)
            for _fh, _fidxs in _hash_to_indices.items():
                if len(_fidxs) > 1:
                    _dupe_fnames = [new_files[i].name for i in _fidxs]
                    st.warning(f"Identical file uploaded {len(_fidxs)}x: {', '.join(_dupe_fnames)} — only the first will be scanned.")

        # ── Auto-detect + fingerprint every file ────────────────────
        # Order matters — first match wins. Most-specific tokens first so
        # ambiguous matches (e.g. "approval" containing nothing HOI-related)
        # aren't hijacked by generic keywords further down.
        _FILENAME_FALLBACKS = [
            (["approval", "commitment letter", "du findings", "desktop underwriter",
              "lpa findings", "aus findings", "du ", "lpa ", "conditional approval",
              "loan approval", "underwriting approval", "uw approval",
              "loan decision", "underwriting decision", "uw decision",
              "credit decision", "decision", "findings", "loan estimate approval",
              "conditions list", "loan conditions"], "Approval Letter"),
            (["coe", "certificate of eligibility", "cert of eligib"], "VA Certificate of Eligibility"),
            (["dd214", "dd-214", "dd 214", "discharge", "dd_214"], "DD-214"),
            (["license", "drivers license", "id card", "government id", "photo id", "passport", "id -", "- id", "_id"], "Government ID"),
            (["w2", "w-2", "wage and tax"], "W-2"),
            (["1099"], "1099"),
            (["1003", "urla", "loan application"], "1003 Application"),
            (["credit report", "tri merge", "trimerge", "credit_report"], "Credit Report"),
            (["appraisal"], "Appraisal"),
            (["bank statement", "bank_statement"], "Bank Statement"),
            (["purchase contract", "purchase agreement", "sales contract"], "Purchase Contract"),
            (["title commitment", "title insurance"], "Title Commitment"),
            (["mortgage statement", "loan statement"], "Mortgage Statement"),
            (["paystub", "pay stub", "paycheck", "pay check", "earnings statement"], "Pay Stub"),
            (["tax return", "1040", "tax transcript"], "Tax Return"),
            # HOI last + tightened keywords — "insurance dec" / "declarations"
            # alone are too broad (appear in many loan docs). Require real
            # HOI-instance tokens.
            (["hoi", "hazard insurance", "homeowner insurance", "home owner insurance",
              "insurance binder", "insurance policy", "hoi dec", "insurance dec page",
              "declarations page"], "Hazard Insurance"),
        ]

        def _filename_fallback(fname: str) -> str | None:
            fl = fname.lower().replace("_", " ").replace("-", " ")
            for keywords, doc_type in _FILENAME_FALLBACKS:
                if any(kw in fl for kw in keywords):
                    return doc_type
            return None

        _detections = []
        _fingerprints = []
        for _fi, _bf in enumerate(new_files):
            _fbytes = _file_bytes_cache[_fi]
            _det = _detect(_fbytes)
            # Fallback to filename-based detection for image PDFs with no text
            if _det["doc_type"] == "Unknown" or _det["confidence"] in ("None", "Low"):
                _fn_type = _filename_fallback(_bf.name)
                if _fn_type:
                    _det = {"doc_type": _fn_type, "confidence": "Filename", "signals": ["filename match"]}
            _detections.append({
                "name": _bf.name,
                "detected_type": _det["doc_type"],
                "confidence": _det["confidence"],
            })
            _fingerprints.append(_extract_fingerprint(_fbytes))

        # ── Page grouping: find files that belong together ───────────
        # STRICT RULE: only suggest merge when files are clearly pages of the
        # SAME statement — same period dates OR consecutive page X-of-Y numbering.
        # Different period dates = different months = NEVER merge, always separate.
        _groups = []  # list of sets of indices
        _assigned = set()

        def _same_period(a, b):
            """Both have a period and they match exactly."""
            return (a["period"] and b["period"] and a["period"] == b["period"])

        def _consecutive_pages(a, b):
            """Both report page X of Y with the same Y, and page numbers are sequential."""
            if (a["page_num"] and b["page_num"]
                    and a["page_total"] and b["page_total"]
                    and a["page_total"] == b["page_total"]):
                diff = abs(a["page_num"] - b["page_num"])
                return diff >= 1  # any page of the same doc
            return False

        def _different_periods(a, b):
            """Both have periods but they differ — definitely different months."""
            return (a["period"] and b["period"] and a["period"] != b["period"])

        def _fingerprints_match(i, j):
            a, b = _fingerprints[i], _fingerprints[j]

            # Never merge files from different statement periods
            if _different_periods(a, b):
                return False

            # Must share account number to even consider merging
            same_acct = (a["account"] and b["account"] and a["account"] == b["account"])
            # Or same doc type + shared borrower name (fallback if no acct extracted)
            same_type = _detections[i]["detected_type"] == _detections[j]["detected_type"]
            shared_name = bool(set(a["names"]) & set(b["names"]))

            if not (same_acct or (same_type and shared_name)):
                return False

            # Now require evidence they're pages of the same statement:
            # either page X of Y sequence, or matching period dates
            return _consecutive_pages(a, b) or _same_period(a, b)

        for _i in range(len(new_files)):
            if _i in _assigned:
                continue
            _grp = {_i}
            for _j in range(_i + 1, len(new_files)):
                if _j in _assigned:
                    continue
                if _fingerprints_match(_i, _j):
                    _grp.add(_j)
            if len(_grp) > 1:
                _groups.append(_grp)
                _assigned.update(_grp)


        # ── Pull approval conditions from already-scanned docs ──────
        # Look for any Approval Letter, DU Findings, or LP in prior batches
        _approval_bank_conds = []  # list of condition desc strings mentioning bank stmts
        _approval_source = None
        _approval_types = {"Approval Letter", "Broker Package (BP)"}
        for _pb in st.session_state.get("scan_batches", []):
            if _pb.get("type") in _approval_types:
                _raw_conds = (_pb.get("result") or {}).get("conditions", [])
                # conditions can be either list[dict] (newer) or list[str] /
                # a single multiline str (older / markdown-style). Normalize.
                if isinstance(_raw_conds, str):
                    _raw_conds = [ln.strip(" -•\t") for ln in _raw_conds.splitlines() if ln.strip()]
                for _c in _raw_conds:
                    if isinstance(_c, dict):
                        _desc = (_c.get("desc") or "").lower()
                        _desc_src = _c.get("desc", "")
                    else:
                        _desc = str(_c).lower()
                        _desc_src = str(_c)
                    if any(kw in _desc for kw in ["bank statement", "bank stmt", "checking", "savings",
                                                   "asset", "deposit", "60 day", "2 month", "statement"]):
                        _approval_bank_conds.append(_desc_src)
                if _approval_bank_conds:
                    _approval_source = _pb["file"]
                    break

        # ── Missing pages analysis per statement ─────────────────────
        # For each uploaded bank statement, check if page sequence has gaps
        _missing_page_notices = []
        _bank_indices = [i for i, d in enumerate(_detections) if d["detected_type"] == "Bank Statement" and i not in _dupes]
        for _bi in _bank_indices:
            _fp = _fingerprints[_bi]
            if _fp["page_total"] and _fp["page_num"]:
                # We have one page of a multi-page statement — check if others are present
                _total = _fp["page_total"]
                _present_pages = set()
                for _oi in _bank_indices:
                    _ofp = _fingerprints[_oi]
                    if (_ofp["account"] == _fp["account"] or
                            (set(_ofp["names"]) & set(_fp["names"]))):
                        if _ofp["page_num"]:
                            _present_pages.add(_ofp["page_num"])
                _missing = [p for p in range(1, _total + 1) if p not in _present_pages]
                if _missing:
                    _acct_label = f"acct #{_fp['account']}" if _fp["account"] else (
                        _fp["names"][0] if _fp["names"] else new_files[_bi].name)
                    _missing_page_notices.append((_acct_label, _missing, _total))

        # Deduplicate missing-page notices (same account shows up per-file)
        _seen_acct_notices = set()
        _deduped_missing = []
        for (_lbl, _miss, _tot) in _missing_page_notices:
            if _lbl not in _seen_acct_notices:
                _seen_acct_notices.add(_lbl)
                _deduped_missing.append((_lbl, _miss, _tot))

        # ── Show missing page warnings ────────────────────────────────
        if _deduped_missing:
            st.markdown("---")
            for (_lbl, _miss, _tot) in _deduped_missing:
                _miss_str = ", ".join(str(p) for p in _miss)
                st.markdown(
                    f'<div style="background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.3);border-radius:4px;'
                    f'padding:7px 12px;margin-bottom:6px;font-size:12px;color:#ef4444;">'
                    f'<b>Missing pages ({_lbl}):</b> '
                    f'Page(s) {_miss_str} of {_tot} not uploaded. Upload all pages before scanning.'
                    f'</div>',
                    unsafe_allow_html=True
                )

        # ── Show approval cross-reference ─────────────────────────────
        if _approval_bank_conds and _bank_indices:
            st.markdown("---")
            st.markdown(
                f'<div style="background:rgba(57,255,20,0.1);border:1px solid rgba(57,255,20,0.3);border-radius:4px;'
                f'padding:8px 12px;margin-bottom:4px;font-size:12px;color:#39FF14;">'
                f'<b>Approval cross-reference</b> — from <i>{_approval_source}</i>:'
                f'</div>',
                unsafe_allow_html=True
            )
            # For each uploaded bank statement, check if it satisfies each condition
            for _ac in _approval_bank_conds:
                _ac_lower = _ac.lower()
                # Try to detect how many months required
                _months_req = 1
                for _m in _re.findall(r'(\d+)\s*month', _ac_lower):
                    _months_req = max(_months_req, int(_m))
                # Count distinct periods in uploaded bank statements
                _uploaded_periods = set()
                for _bi in _bank_indices:
                    _fp = _fingerprints[_bi]
                    if _fp["period"]:
                        _uploaded_periods.add(_fp["period"])
                    elif _fp["account"]:
                        # no period detected — count as 1 unknown
                        _uploaded_periods.add(("unknown", _fp["account"]))
                _months_have = len(_uploaded_periods)
                _ok = _months_have >= _months_req
                _icon = "✓" if _ok else "✗"
                _color = "#39FF14" if _ok else "#ef4444"
                _bg = "rgba(57,255,20,0.1)" if _ok else "rgba(239,68,68,0.1)"
                _border = "rgba(57,255,20,0.3)" if _ok else "rgba(239,68,68,0.3)"
                _note = f"{_months_have} of {_months_req} month(s) uploaded" if not _ok else f"{_months_have} month(s) — OK"
                st.markdown(
                    f'<div style="background:{_bg};border:1px solid {_border};border-radius:3px;'
                    f'padding:5px 10px;margin-bottom:4px;font-size:11px;color:{_color};">'
                    f'<b>{_icon}</b> {_ac[:120]} <span style="opacity:0.7;">— {_note}</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )

        # ── Show grouping suggestions ────────────────────────────────
        # Per-file checkboxes so user picks exactly which files to merge
        _merge_selections = {}  # group_id -> set of indices to include in merge
        if _groups:
            st.markdown("---")
            st.markdown("**Page grouping detected** — select pages to merge:")
            for _gi, _grp in enumerate(_groups):
                _grp_type = _detections[sorted(_grp)[0]]["detected_type"]
                _rep_fp = _fingerprints[sorted(_grp)[0]]

                _match_reasons = []
                if _rep_fp["account"]:
                    _match_reasons.append(f"acct #{_rep_fp['account']}")
                if _rep_fp["period"]:
                    _match_reasons.append(f"{_rep_fp['period'][0]}–{_rep_fp['period'][1]}")
                elif _rep_fp["names"]:
                    _match_reasons.append(_rep_fp["names"][0])
                _reason_str = " · ".join(_match_reasons) if _match_reasons else _grp_type

                st.markdown(
                    f'<div style="font-size:12px;font-weight:700;color:#39FF14;margin-bottom:4px;">'
                    f'Group {_gi+1} — {_grp_type} <span style="font-weight:400;color:#9ca3af;">({_reason_str})</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )
                _selected = set()
                for _idx in sorted(_grp, key=lambda i: _fingerprints[i]["page_num"] or 999):
                    _fp = _fingerprints[_idx]
                    _pg_label = f"pg {_fp['page_num']} of {_fp['page_total']}" if _fp["page_num"] else ""
                    _period_label = f"{_fp['period'][0]}–{_fp['period'][1]}" if _fp["period"] else ""
                    _label_parts = [new_files[_idx].name]
                    if _pg_label: _label_parts.append(_pg_label)
                    if _period_label: _label_parts.append(_period_label)
                    _cb_label = "  ·  ".join(_label_parts)
                    _checked = st.checkbox(_cb_label, value=True, key=f"dash_merge_{_gi}_{_idx}")
                    if _checked:
                        _selected.add(_idx)
                _merge_selections[_gi] = _selected

                if len(_selected) >= 2:
                    st.caption(f"Will merge {len(_selected)} file(s) into one PDF before scanning.")
                elif len(_selected) == 1:
                    st.caption("Only 1 file selected — will scan individually.")
                else:
                    st.caption("No files selected — group will be skipped.")
            st.markdown("---")

        # ── File list with checkboxes, type dropdowns, delete ────────
        # Visible (non-dupe) indices
        _visible = [_di for _di, _det in enumerate(_detections) if _di not in _dupes]

        # Check all / Uncheck all / Delete selected controls
        _sel_c1, _sel_c2, _sel_c3 = st.columns([1, 1, 2])
        with _sel_c1:
            if st.button("✓ Check All", key="dash_check_all", use_container_width=True):
                for _vi in _visible:
                    st.session_state[f"dash_sel_{_vi}"] = True
                st.rerun()
        with _sel_c2:
            if st.button("✗ Uncheck All", key="dash_uncheck_all", use_container_width=True):
                for _vi in _visible:
                    st.session_state[f"dash_sel_{_vi}"] = False
                st.rerun()
        with _sel_c3:
            if st.button("🗑 Delete Selected", key="dash_del_selected", use_container_width=True):
                _to_remove = [_vi for _vi in _visible if not st.session_state.get(f"dash_sel_{_vi}", True)]
                # Remove from file_bytes_cache and detections by rebuilding sans removed
                _keep = [i for i in range(len(new_files)) if i not in _to_remove]
                # Clear session state for removed keys
                for _vi in _to_remove:
                    for _sfx in [f"dash_sel_{_vi}", f"dash_type_{_vi}", f"dash_merge_"]:
                        st.session_state.pop(f"dash_sel_{_vi}", None)
                        st.session_state.pop(f"dash_type_{_vi}", None)
                # Rerun will re-detect from remaining uploaded files
                st.rerun()

        _overrides = {}
        for _di, _det in enumerate(_detections):
            if _di in _dupes:
                continue  # skip dupes in the list
            _didx = _BULK_DOC_TYPES.index(_det["detected_type"]) if _det["detected_type"] in _BULK_DOC_TYPES else 0
            _chk_col, _c1, _c2, _c3 = st.columns([0.5, 3.5, 3, 1])
            with _chk_col:
                _is_checked = st.checkbox(
                    "", value=st.session_state.get(f"dash_sel_{_di}", True),
                    key=f"dash_sel_{_di}", label_visibility="collapsed"
                )
            with _c1:
                _color = "var(--slate-900)" if _is_checked else "var(--slate-500)"
                st.markdown(f'<div style="font-size:12px;color:{_color};padding-top:8px;">{_det["name"]}</div>', unsafe_allow_html=True)
            with _c2:
                _ov = st.selectbox("Type", _BULK_DOC_TYPES, index=_didx, key=f"dash_type_{_di}", label_visibility="collapsed")
                _overrides[_di] = _ov
            with _c3:
                st.markdown(f'<div style="font-size:11px;color:var(--slate-500);padding-top:8px;">{_det["confidence"]}</div>', unsafe_allow_html=True)

        # ── Scan button ────────────────────────────────────────────
        _checked_visible = [_vi for _vi in _visible if st.session_state.get(f"dash_sel_{_vi}", True)]
        if st.button(f"Scan ({len(_checked_visible)} selected)", key="dash_scan", type="primary", disabled=len(_checked_visible) == 0):
            # Build the actual list of (bytes, name, type) to scan,
            # merging groups where the user said yes
            _scan_queue = []  # list of (pdf_bytes, display_name, doc_type)

            _merged_indices = set()
            for _gi, _grp in enumerate(_groups):
                _selected = _merge_selections.get(_gi, set())
                if len(_selected) >= 2:
                    # Merge selected files in page order
                    _sorted_grp = sorted(
                        _selected,
                        key=lambda i: _fingerprints[i]["page_num"] or 999
                    )
                    _writer = _pypdf.PdfWriter()
                    for _idx in _sorted_grp:
                        try:
                            _r = _pypdf.PdfReader(_io.BytesIO(_file_bytes_cache[_idx]))
                            for _pg in _r.pages:
                                _writer.add_page(_pg)
                        except Exception:
                            pass
                    _merged_buf = _io.BytesIO()
                    _writer.write(_merged_buf)
                    _merged_bytes = _merged_buf.getvalue()
                    _merged_name = " + ".join(new_files[i].name for i in _sorted_grp)
                    _grp_type = _overrides.get(_sorted_grp[0], _detections[_sorted_grp[0]]["detected_type"])
                    _scan_queue.append((_merged_bytes, _merged_name, _grp_type))
                    _merged_indices.update(_selected)  # only mark selected as merged, not whole group

            # Add remaining non-merged non-dupe checked files
            for _bi, _bf in enumerate(new_files):
                if _bi in _merged_indices or _bi in _dupes:
                    continue
                if not st.session_state.get(f"dash_sel_{_bi}", True):
                    continue  # skip unchecked files
                _bf_type = _overrides.get(_bi, _detections[_bi]["detected_type"])
                _scan_queue.append((_file_bytes_cache[_bi], _bf.name, _bf_type))

            # Run scans
            from doc_verify import _match_borrower as _mb
            _sq_total = len(_scan_queue)
            _sq_progress = st.progress(0, text="Starting scan...")
            for _sq_i, (_sq_bytes, _sq_name, _sq_type) in enumerate(_scan_queue):
                _sq_progress.progress(
                    int((_sq_i / _sq_total) * 100),
                    text=f"Scanning {_sq_i + 1} of {_sq_total}: {_sq_name}..."
                )
                if _sq_type == "Unknown":
                    st.warning(f"{_sq_name}: Unknown type — override the dropdown to scan")
                    continue
                _result = _proc(_sq_bytes, _sq_type)
                if _result.get("success"):
                    # Auto-match to a pipeline loan
                    _raw_text = _result.get("raw_text", "") or _result.get("bank_raw_text", "") or ""
                    _borrower_hint = ""
                    _contacts = _result.get("contacts", {})
                    if isinstance(_contacts, dict):
                        for _cv in _contacts.values():
                            if isinstance(_cv, dict) and _cv.get("name"):
                                _borrower_hint = _cv["name"]; break
                    _loan_match = _mb(_raw_text, _sq_name, _borrower_hint)

                    _batch = st.session_state.scan_batches
                    _new_bidx = len(_batch)
                    _batch.append({
                        "file": _sq_name,
                        "type": _sq_type,
                        "result": _result,
                        "loan_match": _loan_match,
                    })
                    # Store PDF bytes keyed by batch index for later attachment
                    st.session_state[f"_scan_bytes_{_new_bidx}"] = _sq_bytes
                    st.session_state.scan_batches = _batch
                    if _result.get("image_only"):
                        st.warning(f"{_sq_name}: {_sq_type} — scanned image, logged without extraction")
                    else:
                        st.success(f"{_sq_name}: {_sq_type} ✓")
                else:
                    st.error(f"{_sq_name}: {_result.get('error', 'Failed')}")
            _sq_progress.progress(100, text=f"Done — {_sq_total} document(s) scanned")

    # ── Show completed scan results ───────────────────────────────────
    if st.session_state.scan_batches:
        from crm import get_all_loans as _gl, add_loan as _al, update_loan as _ul, log_activity as _la
        st.markdown("---")
        _rb1, _rb2, _rb3 = st.columns([2, 1, 1])
        with _rb1:
            st.markdown(f'<div style="font-size:13px;font-weight:700;padding-top:6px;">{len(st.session_state.scan_batches)} document(s) scanned</div>', unsafe_allow_html=True)
        with _rb2:
            if st.button("+ Upload More", key="dash_scan_more2", use_container_width=True):
                for _k in list(st.session_state.keys()):
                    if _k.startswith("dash_"):
                        del st.session_state[_k]
                st.rerun()
        with _rb3:
            if st.button("Clear All", key="dash_clear_all2", use_container_width=True):
                st.session_state.scan_batches = []
                for _k in list(st.session_state.keys()):
                    if _k.startswith("dash_"):
                        del st.session_state[_k]
                st.rerun()
        # ── Pagination ────────────────────────────────────────────────
        _PAGE_SIZE = 25
        _total_batches = len(st.session_state.scan_batches)
        _total_pages = max(1, (_total_batches + _PAGE_SIZE - 1) // _PAGE_SIZE)
        if "scan_page" not in st.session_state:
            st.session_state.scan_page = 0
        st.session_state.scan_page = min(st.session_state.scan_page, _total_pages - 1)

        if _total_pages > 1:
            _pg_cols = st.columns([1, 2, 1])
            with _pg_cols[0]:
                if st.button("← Prev", key="scan_pg_prev", disabled=st.session_state.scan_page == 0):
                    st.session_state.scan_page -= 1; st.rerun()
            with _pg_cols[1]:
                st.markdown(f'<div style="text-align:center;font-size:12px;color:#9ca3af;padding-top:8px;">Page {st.session_state.scan_page+1} of {_total_pages} ({_total_batches} docs)</div>', unsafe_allow_html=True)
            with _pg_cols[2]:
                if st.button("Next →", key="scan_pg_next", disabled=st.session_state.scan_page >= _total_pages - 1):
                    st.session_state.scan_page += 1; st.rerun()

        _page_start = st.session_state.scan_page * _PAGE_SIZE
        _page_end   = min(_page_start + _PAGE_SIZE, _total_batches)

        for _bidx, _batch in enumerate(st.session_state.scan_batches[_page_start:_page_end], start=_page_start):
            _r = _batch["result"]
            _raw_c = _r.get("conditions")
            if isinstance(_raw_c, list):
                _cond_count = len(_raw_c)
            elif isinstance(_raw_c, str):
                _cond_count = len([ln for ln in _raw_c.splitlines() if ln.strip()])
            else:
                _cond_count = 0
            _cont_count = len(_r.get("contacts", {})) if isinstance(_r.get("contacts"), dict) else 0
            _lm = _batch.get("loan_match") or {}
            _lm_suggestion = _lm.get("suggestion", "no_match")
            _lm_borrower = _lm.get("borrower", "")
            _lm_loan_num = _lm.get("loan_num", "")
            _lm_loan_id = _lm.get("loan_id")
            _lm_conf = _lm.get("confidence", 0)

            # Match badge for expander title
            if _lm_suggestion == "match":
                _match_badge = f" · Loan {_lm_loan_num} ({_lm_borrower})"
            elif _lm_suggestion == "possible":
                _match_badge = f" · Possible: {_lm_borrower}"
            else:
                _match_badge = " · No loan match"

            _del_col, _exp_col = st.columns([1, 11])
            with _del_col:
                if st.button("✕", key=f"ds_del_{_bidx}", help="Remove this scan result"):
                    st.session_state.scan_batches.pop(_bidx)
                    st.rerun()
            with _exp_col:
                _exp = st.expander(
                    f"✓ {_batch['file']} — {_batch['type']} ({_cond_count} cond){_match_badge}",
                    expanded=(_cond_count > 0)
                )
            with _exp:
                # ── Loan match action row ──────────────────────────────
                if _lm_suggestion == "match":
                    st.markdown(
                        f'<div style="background:rgba(57,255,20,0.1);border:1px solid rgba(57,255,20,0.3);border-radius:4px;'
                        f'padding:6px 10px;margin-bottom:8px;font-size:12px;color:#39FF14;">'
                        f'<b>Matched:</b> Loan {_lm_loan_num} — {_lm_borrower} '
                        f'<span style="opacity:0.6;">({_lm_conf}% confidence)</span>'
                        f'</div>', unsafe_allow_html=True
                    )
                    _ma1, _ma2, _ma3 = st.columns([1, 1, 2])
                    with _ma1:
                        if st.button("Open Loan", key=f"ds_open_{_bidx}"):
                            st.session_state.detail_loan_id = _lm_loan_id
                            st.session_state.page = "loan_detail"
                            st.rerun()
                    with _ma2:
                        if st.button("Merge into Loan", key=f"ds_merge_{_bidx}"):
                            from crm import attach_document as _attach_doc
                            _existing_loan = next((l for l in _gl() if l.get("id") == _lm_loan_id), None)
                            if _existing_loan:
                                _existing_conds = _existing_loan.get("conditions", [])
                                _existing_contacts = _existing_loan.get("contacts", {})
                                _new_conds = _r.get("conditions", [])
                                _new_contacts = _r.get("contacts", {}) or {}
                                _upd = {}
                                _added = 0
                                # Merge conditions (approval letters, checklists, etc.)
                                for _nc in _new_conds:
                                    if not any(_nc.get("desc") == _ec.get("desc") for _ec in _existing_conds):
                                        _existing_conds.append(_nc); _added += 1
                                _upd["conditions"] = _existing_conds
                                # Merge contacts
                                _existing_contacts.update({k: v for k, v in _new_contacts.items() if v})
                                _upd["contacts"] = _existing_contacts
                                # Purchase contract extras — closing date, transaction data
                                if _batch["type"] == "Purchase Contract":
                                    _pcd = (_r.get("extracted_data") or {})
                                    _txn = _pcd.get("transaction", {})
                                    if _txn.get("closing_date") and not _existing_loan.get("closing_date"):
                                        _upd["closing_date"] = _txn["closing_date"]
                                        _upd["due_date"] = _txn["closing_date"]
                                    # Also merge listing/selling agents into contacts
                                    for _ak, _av in [("listing_agent", _pcd.get("listing_agent", {})),
                                                     ("selling_agent", _pcd.get("selling_agent", {})),
                                                     ("title", _pcd.get("title", {}))]:
                                        if _av and any(v for v in _av.values()):
                                            _existing_contacts[_ak] = _av
                                    _upd["contacts"] = _existing_contacts
                                    _msg = f"Purchase Contract merged — contacts & dates updated"
                                else:
                                    _msg = f"{_batch['type']} scanned — {_added} condition(s) merged"
                                _ul(_lm_loan_id, **_upd)
                                # Attach the PDF file to the loan
                                _pdf_bytes_for_attach = st.session_state.get(f"_scan_bytes_{_bidx}")
                                if _pdf_bytes_for_attach:
                                    _attach_doc(_lm_loan_id, _batch["file"], _batch["type"], _pdf_bytes_for_attach,
                                                extracted=_r.get("extracted_data"))
                                _la(_lm_loan_id, "upload", _msg, user=st.session_state.get("user_name", ""))
                                _toast_msg = f"Purchase Contract merged into Loan {_lm_loan_num}" if _batch["type"] == "Purchase Contract" else f"{_added} condition(s) merged into Loan {_lm_loan_num}"
                                st.toast(_toast_msg, icon="✅")
                elif _lm_suggestion == "possible":
                    st.markdown(
                        f'<div style="background:rgba(251,191,36,0.1);border:1px solid rgba(251,191,36,0.3);border-radius:4px;'
                        f'padding:6px 10px;margin-bottom:8px;font-size:12px;color:#fbbf24;">'
                        f'<b>Possible match:</b> {_lm_borrower} (Loan {_lm_loan_num}) — '
                        f'<span style="opacity:0.7;">{_lm_conf}% confidence, verify before merging</span>'
                        f'</div>', unsafe_allow_html=True
                    )
                    _pa1, _pa2 = st.columns([1, 1])
                    with _pa1:
                        if st.button("Open & Verify", key=f"ds_popen_{_bidx}"):
                            st.session_state.detail_loan_id = _lm_loan_id
                            st.session_state.page = "loan_detail"
                            st.rerun()
                    with _pa2:
                        if st.button("Start New Loan Instead", key=f"ds_pnew_{_bidx}"):
                            st.session_state[f"ds_start_new_{_bidx}"] = True
                            st.rerun()
                else:
                    # No match — offer to start a new loan pre-filled from scan
                    _extracted_borrower = ""
                    _contacts = _r.get("contacts", {})
                    if isinstance(_contacts, dict):
                        for _cv in _contacts.values():
                            if isinstance(_cv, dict) and _cv.get("name"):
                                _extracted_borrower = _cv["name"]; break
                    st.markdown(
                        f'<div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.1);border-radius:4px;'
                        f'padding:6px 10px;margin-bottom:8px;font-size:12px;color:#9ca3af;">'
                        f'<b>No pipeline match found.</b>'
                        + (f' Borrower extracted: <b>{_extracted_borrower}</b>' if _extracted_borrower else '')
                        + f'</div>', unsafe_allow_html=True
                    )
                    if st.button("+ Start New Loan from this Doc", key=f"ds_new_{_bidx}"):
                        st.session_state[f"ds_start_new_{_bidx}"] = True
                        st.rerun()

                # ── New loan form (shown when triggered) ──────────────
                if st.session_state.get(f"ds_start_new_{_bidx}"):
                    with st.form(key=f"ds_newloan_form_{_bidx}"):
                        st.markdown("**Start New Loan**")
                        # Pre-fill from contacts/1003 data in result
                        _pf_borrower = ""
                        _pf_loan_num = _r.get("loan_num", "") or ""
                        _pf_contacts = _r.get("contacts", {}) or {}
                        for _cv in _pf_contacts.values():
                            if isinstance(_cv, dict) and _cv.get("name"):
                                _pf_borrower = _cv["name"]; break
                        _nl_borrower = st.text_input("Borrower Name", value=_pf_borrower, key=f"ds_nl_b_{_bidx}")
                        _nl_loannum = st.text_input("Loan Number", value=_pf_loan_num, key=f"ds_nl_n_{_bidx}")
                        _nl_closing = st.text_input("Closing Date (MM/DD/YYYY)", key=f"ds_nl_c_{_bidx}")
                        _nl_submit = st.form_submit_button("Create Loan", type="primary")
                        if _nl_submit and _nl_borrower:
                            _new_lid = _al(
                                borrower=_nl_borrower,
                                loan_num=_nl_loannum or "TBD",
                                closing_date=_nl_closing or "",
                                conditions=_r.get("conditions", []),
                                contacts=_pf_contacts,
                                created_by=st.session_state.get("user_name", ""),
                            )
                            _la(_new_lid, "created", f"Loan created from scanned {_batch['type']}",
                                user=st.session_state.get("user_name", ""))
                            st.toast(f"Loan created for {_nl_borrower}", icon="✅")
                            st.session_state.pop(f"ds_start_new_{_bidx}", None)
                            st.rerun()

                # ── Conditions (interactive, compact) ──────────────────
                if _cond_count:
                    st.markdown('<div class="scan-scroll">', unsafe_allow_html=True)
                    st.markdown('<div class="pa-section">Conditions</div>', unsafe_allow_html=True)
                    _PARTY_OPTS_SCAN = [
                        "Borrower", "Co-Borrower", "Title", "Realtor", "Seller",
                        "Underwriter", "Jr Underwriter", "Loan Officer", "Closer",
                        "Insurance", "Appraiser", "Employer", "Manager",
                    ]
                    _COND_STATS_SCAN = ["Needed", "Requested", "Important", "Ready to Clear", "Cleared"]

                    def _infer_party(_desc: str) -> str:
                        _d = (_desc or "").lower()
                        if any(k in _d for k in ["insurance", "hoi", "hazard", "flood"]): return "Insurance"
                        if any(k in _d for k in ["title", "lien", "payoff", "survey"]):  return "Title"
                        if any(k in _d for k in ["appraisal", "appraiser", "value"]):    return "Appraiser"
                        if any(k in _d for k in ["voe", "employer", "employment"]):      return "Employer"
                        if any(k in _d for k in ["purchase contract", "realtor", "agent"]): return "Realtor"
                        if "seller" in _d:                                               return "Seller"
                        if any(k in _d for k in ["closer", "cd ", "closing disclosure"]):return "Closer"
                        return "Borrower"

                    _scan_fkey = f"scan_{_bidx}"
                    _raw_conds = _r.get("conditions", []) or []
                    if isinstance(_raw_conds, str):
                        _raw_conds = [ln.strip(" -•\t") for ln in _raw_conds.splitlines() if ln.strip()]
                    _norm_conds = []
                    for _i, _c in enumerate(_raw_conds):
                        _cc = dict(_c) if isinstance(_c, dict) else {"desc": str(_c)}
                        _cc.setdefault("num", str(_i + 1))
                        _cc["desc"] = _cc.get("desc") or _cc.get("description") or "—"
                        if not _cc.get("party"):
                            _cc["party"] = _infer_party(_cc["desc"])
                        _cc.setdefault("status", "Needed")
                        _norm_conds.append(_cc)

                    for _c in _norm_conds:
                        _uid = f"{_scan_fkey}_{_c['num']}"
                        # Single tight row: [✓] #N desc [status] [parties] [📧] [📁] [📖]
                        _r1, _r2, _r3, _r4, _r5, _r6, _r7 = st.columns([0.5, 4, 1.2, 1.6, 0.5, 0.5, 0.5])
                        with _r1:
                            _chk = st.checkbox("", value=False, key=f"{_uid}_chk",
                                               label_visibility="collapsed")
                        with _r2:
                            st.markdown(
                                f'<div style="font-size:12px;line-height:1.3;padding-top:3px;">'
                                f'<b style="color:#39FF14;">#{_c["num"]}</b> '
                                f'<span style="color:#e5e7eb;">{_c["desc"][:110]}</span></div>',
                                unsafe_allow_html=True,
                            )
                        with _r3:
                            _sidx = _COND_STATS_SCAN.index(_c["status"]) if _c["status"] in _COND_STATS_SCAN else 0
                            _cstat = st.selectbox("s", _COND_STATS_SCAN, index=_sidx,
                                                  key=f"{_uid}_stat", label_visibility="collapsed")
                        with _r4:
                            _cparties = st.multiselect("p", _PARTY_OPTS_SCAN,
                                                       default=[_c["party"]] if _c["party"] in _PARTY_OPTS_SCAN else [],
                                                       key=f"{_uid}_party", label_visibility="collapsed")
                        with _r5:
                            if st.button("📧", key=f"{_uid}_email", help="Draft email"):
                                st.session_state[f"{_uid}_email_open"] = True
                        with _r6:
                            _fd = not (_lm_suggestion == "match" and _lm_loan_id)
                            if st.button("📁", key=f"{_uid}_fetch", disabled=_fd,
                                         help="Match to loan first" if _fd else "Fetch from folder"):
                                try:
                                    from pathlib import Path as _P
                                    from folder_manager import fetch_for_condition as _ffc
                                    _ml = next((l for l in _gl() if l.get("id") == _lm_loan_id), None)
                                    _fp = (_ml or {}).get("folder_path", "")
                                    if _fp:
                                        st.session_state[f"{_uid}_fetch_hits"] = _ffc(_P(_fp), int(_c["num"]))
                                    else:
                                        st.session_state[f"{_uid}_fetch_hits"] = []
                                        st.toast("No folder path on loan", icon="⚠️")
                                except Exception as _e:
                                    st.toast(f"Fetch failed: {_e}", icon="⚠️")
                        with _r7:
                            if st.button("📖", key=f"{_uid}_guide", help="Check vs. Fannie/Freddie guidelines"):
                                st.session_state[f"{_uid}_guide_open"] = True
                                st.session_state.pop(f"{_uid}_guide_results", None)

                        # ── Email drafter panel (toggled by 📧) ──
                        if st.session_state.get(f"{_uid}_email_open"):
                            _ec1, _ec2, _ec3 = st.columns([1.5, 1, 0.5])
                            with _ec1:
                                _p_choice = st.selectbox(
                                    "To", _PARTY_OPTS_SCAN,
                                    index=_PARTY_OPTS_SCAN.index(_cparties[0]) if _cparties and _cparties[0] in _PARTY_OPTS_SCAN else (
                                        _PARTY_OPTS_SCAN.index(_c["party"]) if _c["party"] in _PARTY_OPTS_SCAN else 0
                                    ),
                                    key=f"{_uid}_email_to", label_visibility="collapsed",
                                )
                            with _ec2:
                                _lang = st.selectbox(
                                    "Language", ["English", "Spanish"],
                                    key=f"{_uid}_email_lang", label_visibility="collapsed",
                                )
                            with _ec3:
                                if st.button("✕", key=f"{_uid}_email_close", help="Close"):
                                    for _k in (f"{_uid}_email_open", f"{_uid}_email_body"):
                                        st.session_state.pop(_k, None)
                                    st.rerun()
                            try:
                                from ai_engine import draft_email as _draft
                                _ebody = _draft(f"- #{_c['num']}: {_c['desc']}", _p_choice, _lang)
                            except Exception as _e:
                                _ebody = f"(Draft failed: {_e})"
                            st.code(_ebody, language=None)
                        _hits = st.session_state.get(f"{_uid}_fetch_hits")
                        if _hits is not None:
                            if _hits:
                                _lines = " · ".join(
                                    f"`{(_h.get('file') or _h.get('path') or '?')}`"
                                    for _h in _hits[:5]
                                )
                                st.markdown(
                                    f'<div style="font-size:11px;color:#9ca3af;padding:2px 0 4px 32px;">{_lines}</div>',
                                    unsafe_allow_html=True,
                                )
                            else:
                                st.markdown(
                                    '<div style="font-size:11px;color:#6b7280;padding:2px 0 4px 32px;">No matching docs.</div>',
                                    unsafe_allow_html=True,
                                )

                        # ── Guidelines panel (toggled by 📖) ──
                        if st.session_state.get(f"{_uid}_guide_open"):
                            _gc1, _gc2 = st.columns([9, 0.5])
                            with _gc2:
                                if st.button("✕", key=f"{_uid}_guide_close", help="Close"):
                                    for _k in (f"{_uid}_guide_open", f"{_uid}_guide_results"):
                                        st.session_state.pop(_k, None)
                                    st.rerun()
                            _gres = st.session_state.get(f"{_uid}_guide_results")
                            if _gres is None:
                                with st.spinner("Searching Fannie Mae & Freddie Mac…"):
                                    try:
                                        from guidelines import check_conditions_against_guidelines as _cag
                                        _out = _cag([{"num": _c["num"], "desc": _c["desc"]}])
                                        if isinstance(_out, dict) and _out.get("error"):
                                            _gres = {"error": _out["error"]}
                                        else:
                                            _gres = _out.get(_c["num"], {}).get("guidelines", [])
                                    except Exception as _e:
                                        _gres = {"error": f"{_e}"}
                                    st.session_state[f"{_uid}_guide_results"] = _gres
                            if isinstance(_gres, dict) and _gres.get("error"):
                                st.markdown(
                                    f'<div style="font-size:11px;color:#fbbf24;padding:4px 8px;'
                                    f'background:rgba(251,191,36,0.08);border:1px solid rgba(251,191,36,0.25);'
                                    f'border-radius:6px;margin:4px 0 4px 32px;">⚠️ {_gres["error"]}</div>',
                                    unsafe_allow_html=True,
                                )
                            elif isinstance(_gres, list) and _gres:
                                for _gm in _gres[:4]:
                                    _src = _gm.get("source", "")
                                    _sec = _gm.get("section", "")
                                    _pg  = _gm.get("page", "")
                                    _sc  = _gm.get("score", 0)
                                    _ex  = (_gm.get("excerpt", "") or "").replace("\n", " ")[:360]
                                    _sec_part = f" · <b>{_sec}</b>" if _sec else ""
                                    st.markdown(
                                        f'<div style="font-size:11px;color:#e5e7eb;padding:6px 10px;margin:3px 0 3px 32px;'
                                        f'background:rgba(57,255,20,0.05);border-left:2px solid rgba(57,255,20,0.45);'
                                        f'border-radius:4px;">'
                                        f'<span style="color:#39FF14;font-weight:700;">{_src}</span>'
                                        f'{_sec_part}'
                                        f' <span style="color:#9ca3af;">p.{_pg} · {_sc}% match</span><br/>'
                                        f'<span style="color:#cbd5e1;font-size:10.5px;">{_ex}…</span>'
                                        f'</div>',
                                        unsafe_allow_html=True,
                                    )
                            elif isinstance(_gres, list):
                                st.markdown(
                                    '<div style="font-size:11px;color:#6b7280;padding:4px 0 4px 32px;">'
                                    'No relevant guideline sections found.</div>',
                                    unsafe_allow_html=True,
                                )
                    st.markdown('</div>', unsafe_allow_html=True)
                if _cont_count:
                    _cchips = []
                    for _k, _v in _r.get("contacts", {}).items():
                        if not isinstance(_v, dict):
                            continue
                        _name = _v.get("name", "") or _v.get("company", "")
                        _parts = [p for p in [_name, _v.get("phone", ""), _v.get("email", "")] if p]
                        if _parts:
                            _cchips.append(
                                f'<span style="display:inline-block;font-size:11px;'
                                f'background:rgba(57,255,20,0.08);border:1px solid rgba(57,255,20,0.2);'
                                f'border-radius:10px;padding:2px 8px;margin:2px 4px 2px 0;color:#e5e7eb;">'
                                f'<b style="color:#39FF14;">{_k.replace("_"," ").title()}</b> · '
                                f'{" · ".join(_parts)}</span>'
                            )
                    if _cchips:
                        st.markdown('<div class="pa-section" style="margin-top:8px;">Contacts</div>', unsafe_allow_html=True)
                        st.markdown("".join(_cchips), unsafe_allow_html=True)

                # ── Purchase Contract extended fields ──────────────────
                if _batch.get("type") == "Purchase Contract":
                    _txn = (_r.get("extracted_data") or {}).get("transaction", {})
                    _la_info = (_r.get("extracted_data") or {}).get("listing_agent", {})
                    _sa_info = (_r.get("extracted_data") or {}).get("selling_agent", {})
                    _title_info = (_r.get("extracted_data") or {}).get("title", {})
                    _rows = []
                    if _txn.get("date_signed"):        _rows.append(("Date Signed", _txn["date_signed"]))
                    if _txn.get("obligation_date"):    _rows.append(("Obligation/Approval Date", _txn["obligation_date"]))
                    if _txn.get("closing_date"):       _rows.append(("Closing Date", _txn["closing_date"]))
                    if _txn.get("seller_concessions"): _rows.append(("Seller Concessions", _txn["seller_concessions"]))
                    if _txn.get("earnest_money"):      _rows.append(("Earnest Money", f"${_txn['earnest_money']}"))
                    if _txn.get("down_payment"):       _rows.append(("Down Payment", f"${_txn['down_payment']}"))
                    if _la_info.get("name"):
                        _la_str = _la_info["name"]
                        if _la_info.get("brokerage"): _la_str += f" · {_la_info['brokerage']}"
                        if _la_info.get("phone"):     _la_str += f" · {_la_info['phone']}"
                        if _la_info.get("email"):     _la_str += f" · {_la_info['email']}"
                        _rows.append(("Listing Agent", _la_str))
                    if _sa_info.get("name"):
                        _sa_str = _sa_info["name"]
                        if _sa_info.get("brokerage"): _sa_str += f" · {_sa_info['brokerage']}"
                        if _sa_info.get("phone"):     _sa_str += f" · {_sa_info['phone']}"
                        if _sa_info.get("email"):     _sa_str += f" · {_sa_info['email']}"
                        _rows.append(("Selling Agent", _sa_str))
                    if _title_info.get("company"):
                        _tc_str = _title_info["company"]
                        if _title_info.get("contact"): _tc_str += f" · {_title_info['contact']}"
                        if _title_info.get("phone"):   _tc_str += f" · {_title_info['phone']}"
                        if _title_info.get("email"):   _tc_str += f" · {_title_info['email']}"
                        _rows.append(("Title Company", _tc_str))
                    if _rows:
                        st.markdown("**Purchase Contract Details**")
                        for _lbl, _val in _rows:
                            st.markdown(f"- **{_lbl}**: {_val}")

                # ── 1003 Application extended fields ───────────────────
                if _batch.get("type") == "1003 Application":
                    _app = (_r.get("extracted_data") or {})
                    _bor  = _app.get("borrower", {}) or {}
                    _cobor = _app.get("co_borrower", {}) or {}
                    _emp  = _app.get("employment", {}) or {}
                    _cemp = _app.get("co_employment", {}) or {}
                    _loan_info = _app.get("loan", {}) or {}

                    def _mask_ssn(ssn):
                        if not ssn: return None
                        import re as _re
                        digits = _re.sub(r'\D', '', str(ssn))
                        last4 = digits[-4:] if len(digits) >= 4 else digits
                        return last4

                    def _ssn_html(ssn):
                        last4 = _mask_ssn(ssn)
                        if not last4: return "—"
                        return (
                            f'<span style="filter:blur(3px);color:#9ca3af;user-select:none;">***-**-</span>'
                            f'<span style="color:#e5e7eb;">{last4}</span>'
                        )

                    _sections = []

                    # Borrower section
                    _bor_rows = []
                    if _bor.get("name"):   _bor_rows.append(("Name", f"<b>{_bor['name']}</b>", False))
                    if _bor.get("ssn"):    _bor_rows.append(("SSN", _ssn_html(_bor["ssn"]), True))
                    if _bor.get("dob"):    _bor_rows.append(("Date of Birth", _bor["dob"], False))
                    if _bor.get("phone"):  _bor_rows.append(("Phone", _bor["phone"], False))
                    if _bor.get("email"):  _bor_rows.append(("Email", _bor["email"], False))
                    if _bor.get("present_address"): _bor_rows.append(("Present Address", _bor["present_address"], False))
                    if _bor.get("previous_address"): _bor_rows.append(("Previous Address", _bor["previous_address"], False))
                    if _bor_rows:
                        _sections.append(("Borrower", _bor_rows))

                    # Co-Borrower section
                    _cobor_rows = []
                    if _cobor.get("name"):  _cobor_rows.append(("Name", f"<b>{_cobor['name']}</b>", False))
                    if _cobor.get("ssn"):   _cobor_rows.append(("SSN", _ssn_html(_cobor["ssn"]), True))
                    if _cobor.get("dob"):   _cobor_rows.append(("Date of Birth", _cobor["dob"], False))
                    if _cobor.get("phone"): _cobor_rows.append(("Phone", _cobor["phone"], False))
                    if _cobor.get("email"): _cobor_rows.append(("Email", _cobor["email"], False))
                    if _cobor.get("present_address"): _cobor_rows.append(("Present Address", _cobor["present_address"], False))
                    if _cobor_rows:
                        _sections.append(("Co-Borrower", _cobor_rows))

                    # Employment section
                    _emp_rows = []
                    if _emp.get("employer"):   _emp_rows.append(("Employer", _emp["employer"], False))
                    if _emp.get("employer_phone"):  _emp_rows.append(("Employer Phone", _emp["employer_phone"], False))
                    if _emp.get("position"):        _emp_rows.append(("Position/Title", _emp["position"], False))
                    if _emp.get("years_on_job"):    _emp_rows.append(("Years on Job", _emp["years_on_job"], False))
                    if _emp.get("years_in_field"):  _emp_rows.append(("Years in Field", _emp["years_in_field"], False))
                    if _emp.get("base_monthly_income"): _emp_rows.append(("Base Monthly Income", f"${_emp['base_monthly_income']}", False))
                    if _emp_rows:
                        _sections.append(("Employment", _emp_rows))

                    # Co-Borrower Employment
                    _cemp_rows = []
                    if _cemp.get("employer"):   _cemp_rows.append(("Employer", _cemp["employer"], False))
                    if _cemp.get("employer_phone"):      _cemp_rows.append(("Employer Phone", _cemp["employer_phone"], False))
                    if _cemp.get("position"):            _cemp_rows.append(("Position/Title", _cemp["position"], False))
                    if _cemp.get("years_on_job"):        _cemp_rows.append(("Years on Job", _cemp["years_on_job"], False))
                    if _cemp.get("base_monthly_income"): _cemp_rows.append(("Base Monthly Income", f"${_cemp['base_monthly_income']}", False))
                    if _cemp_rows:
                        _sections.append(("Co-Borrower Employment", _cemp_rows))

                    # Loan / Property section
                    _loan_rows = []
                    if _loan_info.get("amount"):       _loan_rows.append(("Loan Amount", f"${_loan_info['amount']}", False))
                    if _loan_info.get("purpose"):      _loan_rows.append(("Loan Purpose", _loan_info["purpose"], False))
                    if _loan_info.get("term"):         _loan_rows.append(("Loan Term", _loan_info["term"], False))
                    if _loan_info.get("interest_rate"):   _loan_rows.append(("Interest Rate", _loan_info["interest_rate"], False))
                    if _loan_info.get("property_address"): _loan_rows.append(("Property Address", _loan_info["property_address"], False))
                    if _loan_info.get("property_value"):  _loan_rows.append(("Property Value", f"${_loan_info['property_value']}", False))
                    if _loan_info.get("property_use"):    _loan_rows.append(("Property Use", _loan_info["property_use"], False))
                    if _loan_rows:
                        _sections.append(("Loan & Property", _loan_rows))

                    if _sections:
                        st.markdown("**1003 Application Data**")
                        for _sec_title, _sec_rows in _sections:
                            _rows_html = ""
                            for _lbl, _val, _is_html in _sec_rows:
                                _rows_html += (
                                    f'<tr><td style="color:#9ca3af;padding:2px 12px 2px 0;white-space:nowrap;font-size:12px;">{_lbl}</td>'
                                    f'<td style="color:#e5e7eb;padding:2px 0;font-size:12px;">{_val}</td></tr>'
                                )
                            st.markdown(
                                f'<div style="margin-bottom:10px;">'
                                f'<div style="font-size:11px;font-weight:700;color:#39FF14;letter-spacing:0.08em;text-transform:uppercase;margin-bottom:4px;">{_sec_title}</div>'
                                f'<table style="border-collapse:collapse;width:100%;">{_rows_html}</table>'
                                f'</div>',
                                unsafe_allow_html=True
                            )

                # ── W-2 extended fields + income calc ──────────────────
                if _batch.get("type") == "W-2":
                    _w2d = (_r.get("extracted_data") or {})
                    _w2_recs = _w2d.get("w2_records", [])
                    _w2_calc = _w2d.get("income_calc", {})

                    def _fmt_money(val):
                        try:
                            return f"${float(val):,.2f}"
                        except Exception:
                            return str(val) if val else "—"

                    def _w2_ssn_html(ssn):
                        if not ssn: return "—"
                        import re as _re2
                        digits = _re2.sub(r'\D', '', str(ssn))
                        last4 = digits[-4:] if len(digits) >= 4 else digits
                        return (
                            f'<span style="filter:blur(3px);color:#9ca3af;user-select:none;">***-**-</span>'
                            f'<span style="color:#e5e7eb;">{last4}</span>'
                        )

                    if _w2_recs:
                        st.markdown("**W-2 Details**")
                        for _wi, _wr in enumerate(_w2_recs):
                            _yr = _wr.get("year") or f"W-2 #{_wi+1}"
                            _rows_h = ""
                            if _wr.get("employee_name"): _rows_h += f'<tr><td style="color:#9ca3af;padding:2px 12px 2px 0;font-size:12px;white-space:nowrap;">Employee</td><td style="color:#e5e7eb;font-size:12px;"><b>{_wr["employee_name"]}</b></td></tr>'
                            if _wr.get("employee_ssn"):  _rows_h += f'<tr><td style="color:#9ca3af;padding:2px 12px 2px 0;font-size:12px;white-space:nowrap;">SSN</td><td style="color:#e5e7eb;font-size:12px;">{_w2_ssn_html(_wr["employee_ssn"])}</td></tr>'
                            if _wr.get("employer_name"): _rows_h += f'<tr><td style="color:#9ca3af;padding:2px 12px 2px 0;font-size:12px;white-space:nowrap;">Employer</td><td style="color:#e5e7eb;font-size:12px;">{_wr["employer_name"]}</td></tr>'
                            if _wr.get("employer_ein"):  _rows_h += f'<tr><td style="color:#9ca3af;padding:2px 12px 2px 0;font-size:12px;white-space:nowrap;">EIN</td><td style="color:#e5e7eb;font-size:12px;">{_wr["employer_ein"]}</td></tr>'
                            if _wr.get("box1_wages"):    _rows_h += f'<tr><td style="color:#9ca3af;padding:2px 12px 2px 0;font-size:12px;white-space:nowrap;">Box 1 — Wages</td><td style="color:#39FF14;font-size:12px;font-weight:700;">{_fmt_money(_wr["box1_wages"])}</td></tr>'
                            if _wr.get("box2_fed_tax"):  _rows_h += f'<tr><td style="color:#9ca3af;padding:2px 12px 2px 0;font-size:12px;white-space:nowrap;">Box 2 — Fed Tax W/H</td><td style="color:#e5e7eb;font-size:12px;">{_fmt_money(_wr["box2_fed_tax"])}</td></tr>'
                            if _wr.get("box3_ss_wages"): _rows_h += f'<tr><td style="color:#9ca3af;padding:2px 12px 2px 0;font-size:12px;white-space:nowrap;">Box 3 — SS Wages</td><td style="color:#e5e7eb;font-size:12px;">{_fmt_money(_wr["box3_ss_wages"])}</td></tr>'
                            if _wr.get("box5_medicare_wages"): _rows_h += f'<tr><td style="color:#9ca3af;padding:2px 12px 2px 0;font-size:12px;white-space:nowrap;">Box 5 — Medicare Wages</td><td style="color:#e5e7eb;font-size:12px;">{_fmt_money(_wr["box5_medicare_wages"])}</td></tr>'
                            if _wr.get("state"):         _rows_h += f'<tr><td style="color:#9ca3af;padding:2px 12px 2px 0;font-size:12px;white-space:nowrap;">State</td><td style="color:#e5e7eb;font-size:12px;">{_wr["state"]}</td></tr>'
                            if _wr.get("state_wages"):   _rows_h += f'<tr><td style="color:#9ca3af;padding:2px 12px 2px 0;font-size:12px;white-space:nowrap;">State Wages</td><td style="color:#e5e7eb;font-size:12px;">{_fmt_money(_wr["state_wages"])}</td></tr>'
                            if _wr.get("box12"):         _rows_h += f'<tr><td style="color:#9ca3af;padding:2px 12px 2px 0;font-size:12px;white-space:nowrap;">Box 12</td><td style="color:#e5e7eb;font-size:12px;">{_wr["box12"]}</td></tr>'
                            if _wr.get("box14"):         _rows_h += f'<tr><td style="color:#9ca3af;padding:2px 12px 2px 0;font-size:12px;white-space:nowrap;">Box 14 — Other</td><td style="color:#e5e7eb;font-size:12px;">{_wr["box14"]}</td></tr>'
                            st.markdown(
                                f'<div style="margin-bottom:10px;">'
                                f'<div style="font-size:11px;font-weight:700;color:#39FF14;letter-spacing:0.08em;text-transform:uppercase;margin-bottom:4px;">Tax Year {_yr}</div>'
                                f'<table style="border-collapse:collapse;width:100%;">{_rows_h}</table>'
                                f'</div>',
                                unsafe_allow_html=True
                            )

                    # Income Calculation box
                    if _w2_calc:
                        _ic = _w2_calc
                        _method = _ic.get("method", "")
                        _ic_rows = ""
                        if "year1" in _ic and "year1_wages" in _ic:
                            _ic_rows += f'<tr><td style="color:#9ca3af;padding:3px 16px 3px 0;font-size:12px;">{_ic["year1"]} Wages</td><td style="color:#e5e7eb;font-size:12px;text-align:right;">{_fmt_money(_ic["year1_wages"])}</td></tr>'
                        if "year2" in _ic and "year2_wages" in _ic:
                            _ic_rows += f'<tr><td style="color:#9ca3af;padding:3px 16px 3px 0;font-size:12px;">{_ic["year2"]} Wages</td><td style="color:#e5e7eb;font-size:12px;text-align:right;">{_fmt_money(_ic["year2_wages"])}</td></tr>'
                        if _ic.get("two_year_avg"):
                            _ic_rows += f'<tr style="border-top:1px solid rgba(255,255,255,0.1);"><td style="color:#9ca3af;padding:3px 16px 3px 0;font-size:12px;">2-Year Average</td><td style="color:#e5e7eb;font-size:12px;text-align:right;">{_fmt_money(_ic["two_year_avg"])}</td></tr>'
                        if _ic.get("monthly_avg"):
                            _ic_rows += f'<tr><td style="color:#39FF14;padding:3px 16px 3px 0;font-size:13px;font-weight:700;">Monthly Income</td><td style="color:#39FF14;font-size:13px;font-weight:700;text-align:right;">{_fmt_money(_ic["monthly_avg"])}</td></tr>'
                        st.markdown(
                            f'<div style="background:rgba(57,255,20,0.06);border:1px solid rgba(57,255,20,0.25);border-radius:6px;padding:10px 14px;margin-top:8px;">'
                            f'<div style="font-size:11px;font-weight:700;color:#39FF14;letter-spacing:0.08em;text-transform:uppercase;margin-bottom:6px;">Income Calculation ({_method})</div>'
                            f'<table style="border-collapse:collapse;width:100%;">{_ic_rows}</table>'
                            f'</div>',
                            unsafe_allow_html=True
                        )

                # ── Credit Report display ───────────────────────────────
                if _batch.get("type") == "Credit Report":
                    _cr = (_r.get("extracted_data") or {})
                    _cr_bor = _cr.get("borrower", {}) or {}
                    _cr_scores = _cr.get("scores", {}) or {}
                    _cr_mid = _cr.get("middle_score")
                    _cr_mid_bur = _cr.get("middle_bureau", "")
                    _cr_derog = _cr.get("derogatory", [])
                    _cr_coll  = _cr.get("collections", [])
                    _cr_pub   = _cr.get("public_records", [])
                    _cr_inq   = _cr.get("inquiry_count", 0)
                    _cr_past_due = _cr.get("total_past_due", 0)

                    def _cr_ssn_html(ssn):
                        if not ssn: return "—"
                        import re as _re3
                        digits = _re3.sub(r'\D', '', str(ssn))
                        last4 = digits[-4:] if len(digits) >= 4 else digits
                        return (f'<span style="filter:blur(3px);color:#9ca3af;user-select:none;">***-**-</span>'
                                f'<span style="color:#e5e7eb;">{last4}</span>')

                    st.markdown("**Credit Report**")

                    # Personal info
                    _pi_rows = ""
                    if _cr_bor.get("name"):    _pi_rows += f'<tr><td style="color:#9ca3af;padding:2px 12px 2px 0;font-size:12px;white-space:nowrap;">Name</td><td style="color:#e5e7eb;font-size:12px;"><b>{_cr_bor["name"]}</b></td></tr>'
                    if _cr_bor.get("ssn"):     _pi_rows += f'<tr><td style="color:#9ca3af;padding:2px 12px 2px 0;font-size:12px;white-space:nowrap;">SSN</td><td style="font-size:12px;">{_cr_ssn_html(_cr_bor["ssn"])}</td></tr>'
                    if _cr_bor.get("dob"):     _pi_rows += f'<tr><td style="color:#9ca3af;padding:2px 12px 2px 0;font-size:12px;white-space:nowrap;">DOB</td><td style="color:#e5e7eb;font-size:12px;">{_cr_bor["dob"]}</td></tr>'
                    if _cr_bor.get("address"): _pi_rows += f'<tr><td style="color:#9ca3af;padding:2px 12px 2px 0;font-size:12px;white-space:nowrap;">Address</td><td style="color:#e5e7eb;font-size:12px;">{_cr_bor["address"]}</td></tr>'
                    if _cr_bor.get("employer"):_pi_rows += f'<tr><td style="color:#9ca3af;padding:2px 12px 2px 0;font-size:12px;white-space:nowrap;">Employer</td><td style="color:#e5e7eb;font-size:12px;">{_cr_bor["employer"]}</td></tr>'
                    if _pi_rows:
                        st.markdown(
                            f'<div style="margin-bottom:10px;">'
                            f'<div style="font-size:11px;font-weight:700;color:#39FF14;letter-spacing:0.08em;text-transform:uppercase;margin-bottom:4px;">Borrower</div>'
                            f'<table style="border-collapse:collapse;width:100%;">{_pi_rows}</table>'
                            f'</div>', unsafe_allow_html=True
                        )

                    # Scores — all 3 + middle highlighted (sort: low, MID, high so middle is center)
                    if _cr_scores:
                        _score_html = '<div style="display:flex;gap:12px;flex-wrap:wrap;margin-bottom:10px;">'
                        _sorted_scores = sorted(_cr_scores.items(), key=lambda x: x[1])
                        # Reorder: [lowest, middle, highest] → display as [lowest, middle, highest]
                        for _bur, _scr in _sorted_scores:
                            _is_mid = (_bur == _cr_mid_bur and _scr == _cr_mid)
                            _bg = "rgba(57,255,20,0.15)" if _is_mid else "rgba(255,255,255,0.05)"
                            _border = "rgba(57,255,20,0.5)" if _is_mid else "rgba(255,255,255,0.12)"
                            _badge = '<div style="font-size:9px;color:#39FF14;font-weight:700;letter-spacing:0.1em;">MIDDLE</div>' if _is_mid else ''
                            _score_color = "#39FF14" if _is_mid else ("#ef4444" if _scr < 620 else ("#f59e0b" if _scr < 680 else "#e5e7eb"))
                            _score_html += (
                                f'<div style="background:{_bg};border:1px solid {_border};border-radius:8px;'
                                f'padding:8px 14px;text-align:center;min-width:90px;">'
                                f'{_badge}'
                                f'<div style="font-size:22px;font-weight:700;color:{_score_color};">{_scr}</div>'
                                f'<div style="font-size:10px;color:#9ca3af;">{_bur}</div>'
                                f'</div>'
                            )
                        _score_html += '</div>'
                        st.markdown(_score_html, unsafe_allow_html=True)

                    # Derogatory / collections / public records
                    if _cr_derog or _cr_coll or _cr_pub:
                        _flag_html = '<div style="margin-bottom:10px;">'
                        _flag_html += '<div style="font-size:11px;font-weight:700;color:#ef4444;letter-spacing:0.08em;text-transform:uppercase;margin-bottom:6px;">Derogatory / Past Due</div>'
                        for _d in (_cr_coll + _cr_derog + _cr_pub)[:8]:
                            _flag_html += f'<div style="font-size:11px;color:#fca5a5;padding:2px 0;border-left:2px solid #ef4444;padding-left:8px;margin-bottom:3px;">{_d[:100]}</div>'
                        _flag_html += '</div>'
                        st.markdown(_flag_html, unsafe_allow_html=True)
                    else:
                        st.markdown('<div style="font-size:12px;color:#39FF14;margin-bottom:8px;">✓ No derogatory items detected</div>', unsafe_allow_html=True)

                    # Summary row
                    _sum_parts = []
                    if _cr_inq:   _sum_parts.append(f"{_cr_inq} inquir{'y' if _cr_inq==1 else 'ies'}")
                    if _cr_past_due > 0: _sum_parts.append(f"Past due: ${_cr_past_due:,.2f}")
                    if _sum_parts:
                        st.caption(" · ".join(_sum_parts))

                # ── 1099 display ────────────────────────────────────────
                if _batch.get("type") == "1099":
                    _tf = (_r.get("extracted_data") or {})

                    def _1099_ssn_html(ssn):
                        if not ssn: return "—"
                        import re as _re4
                        digits = _re4.sub(r'\D', '', str(ssn))
                        last4 = digits[-4:] if len(digits) >= 4 else digits
                        return (f'<span style="filter:blur(3px);color:#9ca3af;user-select:none;">***-**-</span>'
                                f'<span style="color:#e5e7eb;">{last4}</span>')

                    def _fmt_m(val):
                        try: return f"${float(val):,.2f}"
                        except: return str(val) if val else "—"

                    st.markdown("**1099 Details**")
                    _rows_h = ""
                    if _tf.get("form_type"):     _rows_h += f'<tr><td style="color:#9ca3af;padding:2px 12px 2px 0;font-size:12px;white-space:nowrap;">Form</td><td style="color:#e5e7eb;font-size:12px;font-weight:700;">{_tf["form_type"]} — Tax Year {_tf.get("year","")}</td></tr>'
                    if _tf.get("recipient_name"):_rows_h += f'<tr><td style="color:#9ca3af;padding:2px 12px 2px 0;font-size:12px;white-space:nowrap;">Recipient</td><td style="color:#e5e7eb;font-size:12px;"><b>{_tf["recipient_name"]}</b></td></tr>'
                    if _tf.get("recipient_ssn"): _rows_h += f'<tr><td style="color:#9ca3af;padding:2px 12px 2px 0;font-size:12px;white-space:nowrap;">SSN</td><td style="font-size:12px;">{_1099_ssn_html(_tf["recipient_ssn"])}</td></tr>'
                    if _tf.get("payer_name"):    _rows_h += f'<tr><td style="color:#9ca3af;padding:2px 12px 2px 0;font-size:12px;white-space:nowrap;">Payer</td><td style="color:#e5e7eb;font-size:12px;">{_tf["payer_name"]}</td></tr>'
                    if _tf.get("payer_tin"):     _rows_h += f'<tr><td style="color:#9ca3af;padding:2px 12px 2px 0;font-size:12px;white-space:nowrap;">Payer TIN</td><td style="color:#e5e7eb;font-size:12px;">{_tf["payer_tin"]}</td></tr>'
                    if _tf.get("box1"):          _rows_h += f'<tr><td style="color:#9ca3af;padding:2px 12px 2px 0;font-size:12px;white-space:nowrap;">Box 1 Income</td><td style="color:#39FF14;font-size:12px;font-weight:700;">{_fmt_m(_tf["box1"])}</td></tr>'
                    if _tf.get("box2"):          _rows_h += f'<tr><td style="color:#9ca3af;padding:2px 12px 2px 0;font-size:12px;white-space:nowrap;">Box 2</td><td style="color:#e5e7eb;font-size:12px;">{_fmt_m(_tf["box2"])}</td></tr>'
                    if _tf.get("box4_fed_tax"):  _rows_h += f'<tr><td style="color:#9ca3af;padding:2px 12px 2px 0;font-size:12px;white-space:nowrap;">Fed Tax W/H</td><td style="color:#e5e7eb;font-size:12px;">{_fmt_m(_tf["box4_fed_tax"])}</td></tr>'
                    if _rows_h:
                        st.markdown(f'<table style="border-collapse:collapse;width:100%;margin-bottom:8px;">{_rows_h}</table>', unsafe_allow_html=True)

                    # Income calc box
                    if _tf.get("annual_income", 0) > 0:
                        st.markdown(
                            f'<div style="background:rgba(57,255,20,0.06);border:1px solid rgba(57,255,20,0.25);border-radius:6px;padding:10px 14px;">'
                            f'<div style="font-size:11px;font-weight:700;color:#39FF14;letter-spacing:0.08em;text-transform:uppercase;margin-bottom:4px;">Income (annual ÷ 12)</div>'
                            f'<table style="border-collapse:collapse;width:100%;">'
                            f'<tr><td style="color:#9ca3af;padding:3px 16px 3px 0;font-size:12px;">Annual</td><td style="color:#e5e7eb;font-size:12px;text-align:right;">{_fmt_m(_tf["annual_income"])}</td></tr>'
                            f'<tr><td style="color:#39FF14;padding:3px 16px 3px 0;font-size:13px;font-weight:700;">Monthly</td><td style="color:#39FF14;font-size:13px;font-weight:700;text-align:right;">{_fmt_m(_tf["monthly_income"])}</td></tr>'
                            f'</table>'
                            f'</div>', unsafe_allow_html=True
                        )

                # ── Mortgage Statement display ──────────────────────────
                if _batch.get("type") == "Mortgage Statement":
                    _ms = (_r.get("extracted_data") or {})
                    def _fmt_ms(v):
                        try: return f"${float(v.replace(',','')):,.2f}" if v else "—"
                        except: return v or "—"
                    _ms_rows = [
                        ("Servicer",          _ms.get("servicer")),
                        ("Borrower",          _ms.get("borrower")),
                        ("Loan Number",       _ms.get("loan_number")),
                        ("Property Address",  _ms.get("property_address")),
                        ("Principal Balance", _fmt_ms(_ms.get("principal_balance",""))),
                        ("Escrow Balance",    _fmt_ms(_ms.get("escrow_balance",""))),
                        ("Payment Amount",    _fmt_ms(_ms.get("payment_amount",""))),
                        ("Due Date",          _ms.get("due_date")),
                        ("Interest Rate",     _ms.get("interest_rate")),
                        ("Maturity Date",     _ms.get("maturity_date")),
                        ("YTD Interest Paid", _fmt_ms(_ms.get("ytd_interest_paid",""))),
                    ]
                    _ms_html = "".join(
                        f'<tr><td style="color:#9ca3af;padding:2px 12px 2px 0;font-size:12px;white-space:nowrap;">{l}</td>'
                        f'<td style="color:#e5e7eb;font-size:12px;">{v}</td></tr>'
                        for l, v in _ms_rows if v and v != "—"
                    )
                    if _ms_html:
                        st.markdown("**Mortgage Statement**")
                        st.markdown(f'<table style="border-collapse:collapse;width:100%;">{_ms_html}</table>', unsafe_allow_html=True)

                # ── Image-only stub (scanned PDF, no text layer) ──────────
                if _r.get("image_only"):
                    _img_labels = {
                        "VA Certificate of Eligibility": ("VA Certificate of Eligibility", "Document received and logged. This is a scanned image — fields cannot be auto-extracted. Verify manually and attach to loan file."),
                        "DD-214": ("DD-214 — Certificate of Release", "Document received and logged. This is a scanned image — fields cannot be auto-extracted. Verify discharge status and service dates manually."),
                        "Hazard Insurance": ("Hazard Insurance / HOI Declarations", "Document received and logged. This is a scanned image — verify policy number, coverage amounts, and expiration date manually."),
                        "Government ID": ("Government ID", "Document received and logged. This is a scanned image — verify name, DOB, ID number, and expiration manually."),
                    }
                    _img_title, _img_msg = _img_labels.get(_batch.get("type"), ("Document", "Received and logged. Scanned image — manual review required."))
                    st.markdown(f"**{_img_title}**")
                    st.markdown(
                        f'<div style="background:rgba(245,158,11,0.08);border:1px solid rgba(245,158,11,0.3);'
                        f'border-radius:4px;padding:8px 12px;font-size:12px;color:#fbbf24;margin-top:4px;">'
                        f'📄 Scanned image PDF — text extraction not available in offline mode.<br>'
                        f'<span style="color:#9ca3af;">{_img_msg}</span></div>',
                        unsafe_allow_html=True
                    )

                # ── VA COE display ─────────────────────────────────────────
                if _batch.get("type") == "VA Certificate of Eligibility" and not _r.get("image_only"):
                    _coe = (_r.get("extracted_data") or {})
                    _coe_rows = [
                        ("Veteran Name",        _coe.get("veteran_name")),
                        ("Entitlement Amount",  f'${_coe["entitlement_amount"]}' if _coe.get("entitlement_amount") else None),
                        ("Entitlement Code",    _coe.get("entitlement_code")),
                        ("Remaining Entitlement",f'${_coe["remaining_entitlement"]}' if _coe.get("remaining_entitlement") else None),
                        ("Loan Guaranty",       _coe.get("loan_guaranty")),
                        ("Funding Fee Exempt",  "YES — Service-Connected Disability" if _coe.get("funding_fee_exempt") else None),
                        ("Funding Fee Info",    _coe.get("funding_fee_info")),
                        ("Issue Date",          _coe.get("issue_date")),
                        ("Service Number",      _coe.get("service_number")),
                    ]
                    _coe_html = "".join(
                        f'<tr><td style="color:#9ca3af;padding:2px 12px 2px 0;font-size:12px;white-space:nowrap;">{l}</td>'
                        f'<td style="color:#e5e7eb;font-size:12px;">{v}</td></tr>'
                        for l, v in _coe_rows if v
                    )
                    if _coe_html:
                        st.markdown("**VA Certificate of Eligibility**")
                        st.markdown(f'<table style="border-collapse:collapse;width:100%;">{_coe_html}</table>', unsafe_allow_html=True)
                    if _coe.get("funding_fee_exempt"):
                        st.markdown('<div style="background:rgba(57,255,20,0.08);border:1px solid rgba(57,255,20,0.3);border-radius:4px;padding:6px 10px;font-size:12px;color:#39FF14;margin-top:6px;">✓ Funding fee exemption noted</div>', unsafe_allow_html=True)

                # ── DD-214 display ─────────────────────────────────────────
                if _batch.get("type") == "DD-214" and not _r.get("image_only"):
                    _dd = (_r.get("extracted_data") or {})
                    def _dd_ssn_html(ssn):
                        if not ssn: return "—"
                        import re as _re5
                        digits = _re5.sub(r'\D', '', str(ssn))
                        last4 = digits[-4:] if len(digits) >= 4 else digits
                        return (f'<span style="filter:blur(3px);color:#9ca3af;user-select:none;">***-**-</span>'
                                f'<span style="color:#e5e7eb;">{last4}</span>')
                    _dd_rows_html = ""
                    if _dd.get("name"):              _dd_rows_html += f'<tr><td style="color:#9ca3af;padding:2px 12px 2px 0;font-size:12px;white-space:nowrap;">Name</td><td style="color:#e5e7eb;font-size:12px;"><b>{_dd["name"]}</b></td></tr>'
                    if _dd.get("ssn"):               _dd_rows_html += f'<tr><td style="color:#9ca3af;padding:2px 12px 2px 0;font-size:12px;white-space:nowrap;">SSN</td><td style="font-size:12px;">{_dd_ssn_html(_dd["ssn"])}</td></tr>'
                    if _dd.get("dob"):               _dd_rows_html += f'<tr><td style="color:#9ca3af;padding:2px 12px 2px 0;font-size:12px;white-space:nowrap;">DOB</td><td style="color:#e5e7eb;font-size:12px;">{_dd["dob"]}</td></tr>'
                    if _dd.get("branch"):            _dd_rows_html += f'<tr><td style="color:#9ca3af;padding:2px 12px 2px 0;font-size:12px;white-space:nowrap;">Branch</td><td style="color:#e5e7eb;font-size:12px;">{_dd["branch"]}</td></tr>'
                    if _dd.get("rank"):              _dd_rows_html += f'<tr><td style="color:#9ca3af;padding:2px 12px 2px 0;font-size:12px;white-space:nowrap;">Rank</td><td style="color:#e5e7eb;font-size:12px;">{_dd["rank"]}</td></tr>'
                    if _dd.get("entry_date"):        _dd_rows_html += f'<tr><td style="color:#9ca3af;padding:2px 12px 2px 0;font-size:12px;white-space:nowrap;">Entry Date</td><td style="color:#e5e7eb;font-size:12px;">{_dd["entry_date"]}</td></tr>'
                    if _dd.get("separation_date"):   _dd_rows_html += f'<tr><td style="color:#9ca3af;padding:2px 12px 2px 0;font-size:12px;white-space:nowrap;">Separation Date</td><td style="color:#e5e7eb;font-size:12px;">{_dd["separation_date"]}</td></tr>'
                    if _dd.get("character_of_discharge"): _dd_rows_html += f'<tr><td style="color:#9ca3af;padding:2px 12px 2px 0;font-size:12px;white-space:nowrap;">Character of Discharge</td><td style="color:#e5e7eb;font-size:12px;">{_dd["character_of_discharge"]}</td></tr>'
                    if _dd.get("total_service"):     _dd_rows_html += f'<tr><td style="color:#9ca3af;padding:2px 12px 2px 0;font-size:12px;white-space:nowrap;">Total Service</td><td style="color:#e5e7eb;font-size:12px;">{_dd["total_service"]}</td></tr>'
                    if _dd_rows_html:
                        st.markdown("**DD-214 — Certificate of Release**")
                        st.markdown(f'<table style="border-collapse:collapse;width:100%;">{_dd_rows_html}</table>', unsafe_allow_html=True)
                    if _dd.get("disability_noted"):
                        st.markdown('<div style="background:rgba(57,255,20,0.08);border:1px solid rgba(57,255,20,0.3);border-radius:4px;padding:6px 10px;font-size:12px;color:#39FF14;margin-top:6px;">✓ Service-connected disability noted — verify VA funding fee exemption</div>', unsafe_allow_html=True)

                # ── Government ID display ──────────────────────────────────
                if _batch.get("type") == "Government ID" and not _r.get("image_only"):
                    _gid = (_r.get("extracted_data") or {})
                    def _gid_ssn_html(ssn):
                        if not ssn: return None
                        import re as _re6
                        digits = _re6.sub(r'\D', '', str(ssn))
                        last4 = digits[-4:] if len(digits) >= 4 else digits
                        return (f'<span style="filter:blur(3px);color:#9ca3af;user-select:none;">***-**-</span>'
                                f'<span style="color:#e5e7eb;">{last4}</span>')
                    _gid_html = ""
                    if _gid.get("id_type"):  _gid_html += f'<tr><td style="color:#9ca3af;padding:2px 12px 2px 0;font-size:12px;white-space:nowrap;">ID Type</td><td style="color:#39FF14;font-size:12px;font-weight:700;">{_gid["id_type"]}</td></tr>'
                    if _gid.get("name"):     _gid_html += f'<tr><td style="color:#9ca3af;padding:2px 12px 2px 0;font-size:12px;white-space:nowrap;">Name</td><td style="color:#e5e7eb;font-size:12px;"><b>{_gid["name"]}</b></td></tr>'
                    if _gid.get("dob"):      _gid_html += f'<tr><td style="color:#9ca3af;padding:2px 12px 2px 0;font-size:12px;white-space:nowrap;">Date of Birth</td><td style="color:#e5e7eb;font-size:12px;">{_gid["dob"]}</td></tr>'
                    if _gid.get("expiry"):   _gid_html += f'<tr><td style="color:#9ca3af;padding:2px 12px 2px 0;font-size:12px;white-space:nowrap;">Expires</td><td style="color:#e5e7eb;font-size:12px;">{_gid["expiry"]}</td></tr>'
                    if _gid.get("issued"):   _gid_html += f'<tr><td style="color:#9ca3af;padding:2px 12px 2px 0;font-size:12px;white-space:nowrap;">Issued</td><td style="color:#e5e7eb;font-size:12px;">{_gid["issued"]}</td></tr>'
                    if _gid.get("id_number"):_gid_html += f'<tr><td style="color:#9ca3af;padding:2px 12px 2px 0;font-size:12px;white-space:nowrap;">ID Number</td><td style="color:#e5e7eb;font-size:12px;">{_gid["id_number"]}</td></tr>'
                    if _gid.get("state"):    _gid_html += f'<tr><td style="color:#9ca3af;padding:2px 12px 2px 0;font-size:12px;white-space:nowrap;">State</td><td style="color:#e5e7eb;font-size:12px;">{_gid["state"]}</td></tr>'
                    if _gid.get("address"):  _gid_html += f'<tr><td style="color:#9ca3af;padding:2px 12px 2px 0;font-size:12px;white-space:nowrap;">Address</td><td style="color:#e5e7eb;font-size:12px;">{_gid["address"]}</td></tr>'
                    if _gid.get("ssn"):
                        _ssn_disp = _gid_ssn_html(_gid["ssn"])
                        if _ssn_disp:
                            _gid_html += f'<tr><td style="color:#9ca3af;padding:2px 12px 2px 0;font-size:12px;white-space:nowrap;">SSN</td><td style="font-size:12px;">{_ssn_disp}</td></tr>'
                    if _gid_html:
                        st.markdown("**Government ID**")
                        st.markdown(f'<table style="border-collapse:collapse;width:100%;">{_gid_html}</table>', unsafe_allow_html=True)

                if _cond_count > 10:
                    st.caption(f"...and {_cond_count - 10} more conditions")



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
        '<span style="font-size:16px;font-weight:700;color:#ffffff;">My Pipeline</span>'
        '&nbsp;&nbsp;<span style="font-size:11px;color:#9ca3af;">Track loans by status</span>'
        '</div>',
        unsafe_allow_html=True,
    )

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
        _opts = ["All"] + STATUS_OPTIONS
        _default = st.session_state.get("pipeline_filter_val", "All")
        if _default not in _opts:
            _default = "All"
        filter_status = st.selectbox(
            "Status", _opts,
            index=_opts.index(_default),
            key="pipeline_filter",
        )
        st.session_state["pipeline_filter_val"] = filter_status
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
                '<span style="font-size:14px;font-weight:700;color:#ffffff;">Add New Loan</span>',
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
                        f'<div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.1);border-radius:8px;'
                        f'padding:10px;margin:6px 0;font-size:12px;color:#9ca3af;">'
                        f'<b style="color:#39FF14;">Scanned {len(_sc)} file(s):</b> '
                        f'{_ok} processed, {_skip} skipped<br>'
                        + "".join(
                            f'<span style="color:{"#39FF14" if s["status"]=="ok" else "#ef4444"};">'
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
                            f'<div style="background:#0a1a0a;border:1px solid rgba(57,255,20,0.2);border-radius:8px;'
                            f'padding:10px;margin:4px 0;font-size:12px;color:#39FF14;">'
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
                            f'<div style="background:#1a1500;border:1px solid rgba(251,191,36,0.2);border-radius:8px;'
                            f'padding:8px 12px;margin:4px 0;font-size:12px;color:#fbbf24;">'
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
                '<span style="font-size:12px;font-weight:700;color:#9ca3af;text-transform:uppercase;'
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
                    f'<div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.1);border-radius:8px;'
                    f'padding:8px 12px;margin:4px 0;font-size:12px;color:#9ca3af;">'
                    f'From bulk scan: <b style="color:#39FF14;">{len(_bf_conds)}</b> condition(s) '
                    f'and <b style="color:#39FF14;">{len(_bf_contacts)}</b> contact group(s) '
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
                        f"<div style='font-weight:700;color:#ffffff;'>"
                        f"#{item.get('loan_num','—')} &nbsp; {item.get('borrower','—')}</div>"
                        f"<div style='font-size:12px;color:#9ca3af;'>"
                        f"From: {item.get('last_updated_by','?')} &nbsp;·&nbsp; "
                        f"Updated: {item.get('last_updated','')[:10]}</div>",
                        unsafe_allow_html=True,
                    )
                with ib2:
                    shared_with_list = ", ".join(item.get("shared_with", []))
                    st.markdown(
                        f"<div style='font-size:12px;color:#d1d5db;'>"
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
                st.markdown('<div style="height:2px;border-bottom:1px solid rgba(255,255,255,0.1);"></div>',
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
        loans.sort(key=lambda l: str(l.get("closing_date") or l.get("due_date") or "9999"))
    elif sort_by == "Lock Expiry":
        loans.sort(key=lambda l: str(l.get("lock_expiry") or "9999"))
    elif sort_by == "Last Name":
        loans.sort(key=lambda l: _last_name(l.get("borrower") or ""))
    elif sort_by == "First Name":
        loans.sort(key=lambda l: _first_name(l.get("borrower") or ""))
    elif sort_by == "Loan #":
        loans.sort(key=lambda l: str(l.get("loan_num") or ""))
    elif sort_by == "Status":
        _status_order = {s: i for i, s in enumerate(STATUS_OPTIONS)}
        loans.sort(key=lambda l: _status_order.get(l.get("status"), 99))
    else:  # Newest (default — most recently created first)
        loans.sort(key=lambda l: l.get("id") or 0, reverse=True)

    if not loans:
        st.info("No loans in pipeline yet. Click **+Add Loan** to get started.")
        return

    # ── Stats row (inline) ────────────────────────────────────────────────
    all_loans = get_all_loans()
    counts = {s: sum(1 for l in all_loans if l["status"] == s) for s in STATUS_OPTIONS}
    _chip_tints = {
        "Pending":   ("#ef4444", "rgba(239,68,68,0.1)", "rgba(239,68,68,0.3)"),
        "Requested": ("#f59e0b", "rgba(245,158,11,0.1)", "rgba(245,158,11,0.3)"),
        "Cleared":   ("#39FF14", "rgba(57,255,20,0.1)", "rgba(57,255,20,0.3)"),
        "Overdue":   ("#9ca3af", "rgba(255,255,255,0.03)", "rgba(255,255,255,0.1)"),
        "Closed":    ("#9ca3af", "rgba(255,255,255,0.03)", "rgba(255,255,255,0.1)"),
    }
    # Status filter chips — real Streamlit buttons, stay in-tab
    _chip_labels = ["All"] + list(STATUS_OPTIONS)
    _chip_cols = st.columns(len(_chip_labels))
    for _i, _s in enumerate(_chip_labels):
        with _chip_cols[_i]:
            _n = len(all_loans) if _s == "All" else counts.get(_s, 0)
            _lbl = f"{_n}  {_s}"
            _active = (filter_status == _s)
            if st.button(_lbl, key=f"statchip_{_s}", type=("primary" if _active else "secondary"), use_container_width=True):
                st.session_state["pipeline_filter_val"] = _s
                st.session_state.pop("pipeline_filter", None)
                st.rerun()

    # ── Pipeline-wide progress bar ────────────────────────────────────────────
    _total_loans = len(all_loans)
    if _total_loans:
        _closed = counts.get("Cleared", 0) + counts.get("Closed", 0)
        _in_prog = counts.get("Requested", 0)
        _pipeline_pct = int((_closed / _total_loans) * 100)
        _pipeline_bar_html = (
            f'<div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.1);border-radius:2px;'
            f'padding:5px 8px;margin-bottom:6px;">'
            f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:3px;">'
            f'<span style="font-size:10px;font-weight:700;color:#ffffff;text-transform:uppercase;letter-spacing:0.4px;">Pipeline Progress</span>'
            f'<span style="font-size:10px;color:#9ca3af;">'
            f'{_closed} cleared&nbsp;·&nbsp;{_in_prog} in progress&nbsp;·&nbsp;{_total_loans} total</span>'
            f'</div>'
            f'<div style="background:rgba(255,255,255,0.1);border-radius:1px;height:6px;overflow:hidden;position:relative;">'
            f'<div style="background:#39FF14;width:{_pipeline_pct}%;height:100%;'
            f'position:absolute;left:0;"></div>'
            f'<div style="background:#f59e0b;'
            f'width:{int((_in_prog/_total_loans)*100)}%;height:100%;'
            f'position:absolute;left:{_pipeline_pct}%;"></div>'
            f'</div>'
            f'<div style="display:flex;gap:10px;margin-top:3px;">'
            f'<span style="font-size:9px;color:#39FF14;font-weight:600;">&#9632; Cleared {_pipeline_pct}%</span>'
            f'<span style="font-size:9px;color:#f59e0b;font-weight:600;">&#9632; In Progress {int((_in_prog/_total_loans)*100)}%</span>'
            f'<span style="font-size:9px;color:#ef4444;font-weight:600;">&#9632; Pending/Overdue {100 - _pipeline_pct - int((_in_prog/_total_loans)*100)}%</span>'
            f'</div>'
            f'</div>'
        )
        st.markdown(_pipeline_bar_html, unsafe_allow_html=True)

    # ── Loan rows (scrollable container ~33vh) ───────────────────────────────
    st.markdown('<div class="pipeline-scroll">', unsafe_allow_html=True)
    for loan in loans:
        lid = loan.get("id")
        status = loan.get("status", "Pending")
        status_css = status.lower()
        emoji = STATUS_EMOJI.get(status, "")

        # Color left-border by status
        border_colors = {
            "Pending":   "#ef4444",
            "Requested": "#f59e0b",
            "Cleared":   "#39FF14",
            "Overdue":   "#9ca3af",
            "Closed":    "#6b7280",
        }
        border_color = border_colors.get(status, "rgba(255,255,255,0.2)")

        created_by = loan.get("created_by", "")
        assigned_to = loan.get("assigned_to", "")
        team_line = ""
        if created_by or assigned_to:
            parts = []
            if created_by:
                parts.append(f"+{created_by}")
            if assigned_to:
                parts.append(f"{assigned_to}")
            team_line = f'<div style="font-size:9px;color:#9ca3af;margin-top:0px;">{" · ".join(parts)}</div>'

        # Lock expiry badge
        _lock_exp = loan.get("lock_expiry", "")
        _lock_badge = ""
        if _lock_exp:
            try:
                from datetime import date as _dt_date, datetime as _dt_datetime
                _lock_d = _dt_datetime.strptime(_lock_exp, "%Y-%m-%d").date()
                _lock_days = (_lock_d - _dt_date.today()).days
                if _lock_days < 0:
                    _lock_clr, _lock_lbl = "#ef4444", f"LOCK EXPIRED ({abs(_lock_days)}d ago)"
                elif _lock_days <= 7:
                    _lock_clr, _lock_lbl = "#ef4444", f"Lock expires in {_lock_days}d"
                elif _lock_days <= 14:
                    _lock_clr, _lock_lbl = "#f59e0b", f"Lock {_lock_days}d"
                else:
                    _lock_clr, _lock_lbl = "#39FF14", f"Lock {_lock_exp}"
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
            _bar_color = "#39FF14"
        elif _pct >= 40:
            _bar_color = "#f59e0b"
        else:
            _bar_color = "#ef4444"

        # ── Inline badges ────────────────────────────────────────────
        _inline_badges = ""
        if _lock_badge:
            _inline_badges += f"&nbsp;{_lock_badge}"
        if _missing_txt and _missing_txt != "None":
            _inline_badges += (
                f'&nbsp;<span style="background:rgba(245,158,11,0.1);color:#f59e0b;padding:1px 5px;'
                f'border-radius:3px;font-size:9px;font-weight:500;border:1px solid rgba(245,158,11,0.3);">'
                f'Missing</span>'
            )

        # ── Contact chips ────────────────────────────────────────────
        _contacts_data = loan.get("contacts", {})
        _contact_chips = []
        _contact_label_map = {
            "seller": "Seller", "listing_agent": "L.Agent", "selling_agent": "B.Agent",
            "title": "Title", "insurance": "HOI",
        }
        for _ck in ["seller", "listing_agent", "selling_agent", "title", "insurance"]:
            _cv = _contacts_data.get(_ck)
            if not _cv or not isinstance(_cv, dict):
                continue
            _cname = _cv.get("name") or _cv.get("company") or _cv.get("contact") or ""
            if not _cname:
                continue
            _clabel = _contact_label_map.get(_ck, _ck)
            _cphone = _cv.get("phone", "")
            _cemail = _cv.get("email", "")
            _ccompany = _cv.get("company", "") if _cv.get("name") else ""
            _tip_rows = []
            if _ccompany:
                _tip_rows.append(f'<div style="color:#9ca3af;font-size:11px;">{_ccompany}</div>')
            if _cphone:
                _tip_rows.append(f'<div style="color:#d1d5db;font-size:12px;">📞 {_cphone}</div>')
            if _cemail:
                _tip_rows.append(f'<div style="color:#d1d5db;font-size:12px;">✉️ {_cemail}</div>')
            _tip_html = "".join(_tip_rows) if _tip_rows else '<div style="color:#9ca3af;font-size:11px;">No contact details</div>'
            _tooltip = (
                f'<span class="pa-tip-box">'
                f'<div style="color:#39FF14;font-size:10px;font-weight:700;text-transform:uppercase;margin-bottom:4px;">{_clabel}</div>'
                f'<div style="color:#ffffff;font-size:13px;font-weight:600;margin-bottom:4px;">{_cname}</div>'
                f'{_tip_html}'
                f'</span>'
            )
            _contact_chips.append(
                f'<span class="pa-tip"><span style="color:#6b7280;">{_clabel}:</span> {_cname}{_tooltip}</span>'
            )
        _contacts_line = ""
        if _contact_chips:
            _contacts_line = (
                f'<div style="font-size:9px;color:#9ca3af;margin-top:2px;margin-bottom:8px;">'
                + " · ".join(_contact_chips) + '</div>'
            )

        _loan_num = loan.get('loan_num', '—')
        _borrower = loan.get('borrower', '—')
        _status_clr = border_color

        # ── Delete query param handling ──────────────────────────────
        _del_key = f"confirm_del_{lid}"
        _del_open = st.session_state.get(_del_key)
        _qp = st.query_params
        _qp_del = _qp.get("del", "")
        if isinstance(_qp_del, list):
            _qp_del = _qp_del[0] if _qp_del else ""
        if _qp_del == str(lid):
            st.session_state[_del_key] = True
            st.query_params.clear()
            st.rerun()
        _qp_confirm = _qp.get("confirm_del", "")
        if isinstance(_qp_confirm, list):
            _qp_confirm = _qp_confirm[0] if _qp_confirm else ""
        if _qp_confirm == str(lid):
            log_activity(lid, "removed", "Loan moved to Trash", user=my_name)
            delete_loan(lid)
            st.session_state.pop(_del_key, None)
            st.query_params.clear()
            st.toast("Moved to Trash", icon="🗑️")
            st.rerun()
        _qp_cancel = _qp.get("cancel_del", "")
        if isinstance(_qp_cancel, list):
            _qp_cancel = _qp_cancel[0] if _qp_cancel else ""
        if _qp_cancel == str(lid):
            st.session_state.pop(_del_key, None)
            st.query_params.clear()
            st.rerun()

        # ── Remove link ──────────────────────────────────────────────
        if _del_open:
            _remove_html = (
                f'<a href="?confirm_del={lid}" style="color:#ef4444;font-size:9px;font-weight:600;'
                f'text-decoration:none;margin-left:6px;">Confirm?</a>'
                f'<a href="?cancel_del={lid}" style="color:#6b7280;font-size:9px;'
                f'text-decoration:none;margin-left:4px;">Cancel</a>'
            )
        else:
            _remove_html = (
                f'<a href="?del={lid}" style="color:#ef4444;font-size:9px;font-weight:500;'
                f'text-decoration:none;opacity:0.6;">x</a>'
            )

        # ── Single compact row (all HTML) ────────────────────────────
        st.markdown(
            f'<div style="border-left:3px solid {_status_clr};padding:4px 8px;margin-bottom:1px;">'
            f'<div style="display:flex;align-items:center;gap:6px;flex-wrap:nowrap;">'
            f'<span style="font-size:11px;font-weight:700;color:#fff;white-space:nowrap;">#{_loan_num}</span>'
            f'<span style="font-size:11px;color:#d1d5db;">{_borrower}</span>'
            f'<span style="font-size:9px;color:{_status_clr};font-weight:600;">{emoji}{status}</span>'
            f'{_inline_badges}'
            f'<span style="font-size:8px;color:#6b7280;margin-left:auto;white-space:nowrap;">'
            f'{_closing_dt} · {_lock_dt if _lock_dt else "—"}</span>'
            f'<div style="width:40px;background:rgba(255,255,255,0.08);height:2px;border-radius:1px;">'
            f'<div style="background:{_bar_color};width:{_pct}%;height:100%;"></div></div>'
            f'<span style="font-size:8px;color:{_bar_color};font-weight:700;">{_pct}%</span>'
            f'{_remove_html}'
            f'</div>'
            + (_contacts_line if _contacts_line else '')
            + f'</div>',
            unsafe_allow_html=True,
        )

        # ── Compact action row: Open | Status | Assign ───────────────
        ac1, ac2, ac3 = st.columns([1.3, 1.5, 2])
        with ac1:
            if st.button(f"▸ OPEN", key=f"open_{lid}", type="primary", use_container_width=True):
                st.session_state.detail_loan_id = lid
                st.session_state.page = "loan_detail"
                st.rerun()
        with ac2:
            _new_status = st.selectbox(
                "Status", STATUS_OPTIONS, index=STATUS_OPTIONS.index(status) if status in STATUS_OPTIONS else 0,
                key=f"st_{lid}", label_visibility="collapsed",
            )
            if _new_status != status:
                set_status(lid, _new_status)
                log_activity(lid, "status", f"Status → {_new_status}", user=my_name)
                st.rerun()
        with ac3:
            cur_assigned = loan.get("assigned_to", "")
            cur_display = cur_assigned if cur_assigned in user_names else "(Unassigned)"
            cur_idx = user_names.index(cur_display)
            new_assignee = st.selectbox(
                "Assign", user_names, index=cur_idx,
                key=f"assign_{lid}", label_visibility="collapsed",
            )
            _new_val = "" if new_assignee == "(Unassigned)" else new_assignee
            if _new_val != cur_assigned:
                update_loan(lid, assigned_to=_new_val)
                log_activity(lid, "reassign", f"Reassigned to {new_assignee}", user=my_name)
                st.rerun()

        # ── HOI / Title quick-generate + copyable contacts ───────────────────
        _docs_key = f"docs_open_{lid}"
        _docs_open = st.session_state.get(_docs_key, False)
        _docs_lbl = f"📄 Docs & Contacts  {'▲' if _docs_open else '▼'}"
        if st.button(_docs_lbl, key=f"docsbtn_{lid}", use_container_width=True):
            st.session_state[_docs_key] = not _docs_open
            st.rerun()

        if st.session_state.get(_docs_key):
            _pl_contacts = loan.get("contacts", {}) or {}
            _hoi_col, _title_col = st.columns(2)

            # ── HOI side ────────────────────────────────────────────────
            with _hoi_col:
                if st.button("Generate HOI", key=f"pl_gen_hoi_{lid}", use_container_width=True):
                    try:
                        from template_filler import fill_template, build_context, OUTPUT_ROOT
                        import os as _os, re as _re
                        _ctx = build_context(loan)
                        _safe = _re.sub(r"[^A-Za-z0-9_-]+", "_", _ctx["borrower_name"])[:40]
                        _out = _os.path.join(OUTPUT_ROOT, str(lid), f"HOI Request_{_safe}.docx")
                        fill_template("HOI Request.docx", _ctx, _out)
                        log_activity(lid, "generated", "HOI Request generated", user=my_name)
                        st.session_state[f"_pl_hoi_path_{lid}"] = _out
                        st.toast("HOI Request generated", icon="✅")
                        st.rerun()
                    except Exception as _e:
                        st.error(f"HOI gen failed: {_e}")
                _p_hoi = st.session_state.get(f"_pl_hoi_path_{lid}")
                if _p_hoi:
                    try:
                        with open(_p_hoi, "rb") as _fh:
                            st.download_button(
                                "⬇ Download HOI",
                                _fh.read(),
                                file_name=_p_hoi.split(chr(92))[-1] if chr(92) in _p_hoi else _p_hoi.split("/")[-1],
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                key=f"pl_dl_hoi_{lid}",
                                use_container_width=True,
                            )
                    except FileNotFoundError:
                        pass
                _rc = _pl_contacts.get("insurance") or {}
                _name = _rc.get("contact") or _rc.get("name") or _rc.get("company") or ""
                _phone, _email = _rc.get("phone", ""), _rc.get("email", "")
                st.markdown(
                    '<div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.1);'
                    'border-radius:8px;padding:8px;margin-top:6px;">'
                    '<div style="font-size:10px;color:#39FF14;font-weight:700;'
                    'text-transform:uppercase;margin-bottom:4px;">HOI / Insurance</div>'
                    + (f'<div style="color:#ffffff;font-size:12px;font-weight:600;">{_name}</div>' if _name else '')
                    + ('' if (_name or _phone or _email) else '<span style="color:#9ca3af;font-size:11px;">Not set</span>')
                    + '</div>',
                    unsafe_allow_html=True,
                )
                if _phone:
                    st.code(_phone, language=None)
                if _email:
                    st.code(_email, language=None)

            # ── Title side ──────────────────────────────────────────────
            with _title_col:
                if st.button("Generate Title", key=f"pl_gen_title_{lid}", use_container_width=True):
                    try:
                        from template_filler import fill_template, build_context, OUTPUT_ROOT
                        import os as _os, re as _re
                        _ctx = build_context(loan)
                        _safe = _re.sub(r"[^A-Za-z0-9_-]+", "_", _ctx["borrower_name"])[:40]
                        _out = _os.path.join(OUTPUT_ROOT, str(lid), f"Title Request_{_safe}.docx")
                        fill_template("Title Request copy.docx", _ctx, _out)
                        log_activity(lid, "generated", "Title Request generated", user=my_name)
                        st.session_state[f"_pl_title_path_{lid}"] = _out
                        st.toast("Title Request generated", icon="✅")
                        st.rerun()
                    except Exception as _e:
                        st.error(f"Title gen failed: {_e}")
                _p_ttl = st.session_state.get(f"_pl_title_path_{lid}")
                if _p_ttl:
                    try:
                        with open(_p_ttl, "rb") as _fh:
                            st.download_button(
                                "⬇ Download Title",
                                _fh.read(),
                                file_name=_p_ttl.split(chr(92))[-1] if chr(92) in _p_ttl else _p_ttl.split("/")[-1],
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                key=f"pl_dl_title_{lid}",
                                use_container_width=True,
                            )
                    except FileNotFoundError:
                        pass
                _rc = _pl_contacts.get("title") or {}
                _name = _rc.get("contact") or _rc.get("name") or _rc.get("company") or ""
                _phone, _email = _rc.get("phone", ""), _rc.get("email", "")
                st.markdown(
                    '<div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.1);'
                    'border-radius:8px;padding:8px;margin-top:6px;">'
                    '<div style="font-size:10px;color:#39FF14;font-weight:700;'
                    'text-transform:uppercase;margin-bottom:4px;">Title Company</div>'
                    + (f'<div style="color:#ffffff;font-size:12px;font-weight:600;">{_name}</div>' if _name else '')
                    + ('' if (_name or _phone or _email) else '<span style="color:#9ca3af;font-size:11px;">Not set</span>')
                    + '</div>',
                    unsafe_allow_html=True,
                )
                if _phone:
                    st.code(_phone, language=None)
                if _email:
                    st.code(_email, language=None)

        # ── Share this loan ──────────────────────────────────────────────────
        from sharing import get_members, share_loan as _share_loan, send_update as _send_update
        team_members = get_members()
        team_names = [m["name"] for m in team_members]

        # Show "Send Update" if this loan was shared with us
        is_shared_loan = bool(loan.get("share_id"))
        share_key = f"share_open_{lid}"

        sh1 = st.columns(1)[0]
        with sh1:
            lbl = "Export Update" if is_shared_loan else "Share"
            if team_names and st.button(lbl, key=f"sharebtn_{lid}", use_container_width=True):
                st.session_state[share_key] = not st.session_state.get(share_key, False)

        if st.session_state.get(share_key) and team_names:
            with st.container():
                if is_shared_loan:
                    # Send update back to owner + shared_with
                    st.markdown(
                        "<div style='font-size:13px;color:#d1d5db;margin-bottom:6px;'>"
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
                        "<div style='font-size:13px;color:#d1d5db;margin-bottom:6px;'>"
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

        st.markdown('<div style="height:2px;border-bottom:1px solid rgba(255,255,255,0.05);margin:2px 0;"></div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

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
                st.toast(f"Retention set to {_new_ret}", icon="✅")
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
                        _exp_tag = f'<span style="color:#ef4444;font-size:10px;font-weight:600;">deletes in {max(0,_exp_days)}d</span>'
                    else:
                        _exp_tag = f'<span style="color:#9ca3af;font-size:10px;">deletes in {_exp_days}d</span>'
                else:
                    _exp_tag = '<span style="color:#9ca3af;font-size:10px;">kept forever</span>'

                tc1, tc2, tc3 = st.columns([4, 1, 1])
                with tc1:
                    st.markdown(
                        f'<span style="font-weight:700;color:#39FF14;">#{tl.get("loan_num", "—")}</span>'
                        f' &nbsp;{tl.get("borrower", "—")}'
                        f' &nbsp;<span style="color:#9ca3af;font-size:10px;">removed {tl.get("deleted_on", "?")}</span>'
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
    # Sync picked folder into widget key before rendering
    _rf = st.session_state.get("reader_folder", "")
    if _rf and "reader_folder_input" not in st.session_state:
        st.session_state["reader_folder_input"] = _rf

    col1, col2, col3 = st.columns([4, 1, 1])
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
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Pick Folder", use_container_width=True, key="reader_pick_btn"):
            import tkinter as _tk
            from tkinter import filedialog as _fd
            _root = _tk.Tk()
            _root.withdraw()
            _root.attributes("-topmost", True)
            _picked = _fd.askdirectory(title="Select a folder to read")
            _root.destroy()
            if _picked and os.path.isdir(_picked):
                st.session_state["reader_folder"] = _picked
                folder_path = _picked
                browse_btn = True
                st.rerun()
            else:
                st.toast("No folder selected")

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

        _IMG_EXT = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tif", ".tiff", ".webp"}
        if open_file["ext"] == ".pdf":
            _show_pdf_reader(open_file["path"], search_term)
        elif open_file["ext"] in {".txt", ".csv"}:
            _show_text_reader(open_file["path"], search_term)
        elif open_file["ext"] in _IMG_EXT:
            try:
                st.image(open_file["path"], use_container_width=True)
            except Exception as _e:
                st.error(f"Could not display image: {_e}")
            with open(open_file["path"], "rb") as _ifh:
                st.download_button(
                    f"⬇ Download {open_file['name']}",
                    _ifh.read(),
                    file_name=open_file["name"],
                    mime=f"image/{open_file['ext'].lstrip('.')}",
                    key=f"img_dl_{open_file['name']}",
                )
        else:
            # Offer download for office docs / unknown types
            try:
                with open(open_file["path"], "rb") as _ofh:
                    st.info("This file type can't be rendered inline — download it below.")
                    st.download_button(
                        f"⬇ Download {open_file['name']}",
                        _ofh.read(),
                        file_name=open_file["name"],
                        key=f"other_dl_{open_file['name']}",
                    )
            except Exception as _e:
                st.error(f"Could not open file: {_e}")


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
        f"<div style='font-size:12px;color:#9ca3af;margin-top:4px;'>"
        f"Share this path with teammates so they can drop files for you: "
        f"<code style='color:#39FF14;'>{config.get('my_inbox','(not set)')}</code>"
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
    st.markdown(f"### My Team &nbsp; <span style='font-size:13px;color:#9ca3af;'>({len(members)} people)</span>",
                unsafe_allow_html=True)

    if not members:
        st.info("No team members yet. Add your first teammate above.")
        return

    for m in members:
        with st.container():
            mc1, mc2, mc3, mc4 = st.columns([2, 2, 4, 1])
            with mc1:
                st.markdown(
                    f"<div style='font-weight:700;color:#ffffff;font-size:14px;'>{m['name']}</div>",
                    unsafe_allow_html=True,
                )
            with mc2:
                st.markdown(
                    f"<div style='color:#39FF14;font-size:13px;'>{m.get('role','')}</div>",
                    unsafe_allow_html=True,
                )
            with mc3:
                inbox_path = m.get("inbox", "")
                reachable = os.path.isdir(inbox_path) if inbox_path else False
                dot = "●" if reachable else "●"
                st.markdown(
                    f"<div style='font-size:12px;color:#9ca3af;'>{dot} "
                    f"<code style='color:#d1d5db;'>{inbox_path or '(no path)'}</code></div>",
                    unsafe_allow_html=True,
                )
            with mc4:
                if st.button("Remove", key=f"rm_{m['name']}", use_container_width=True):
                    remove_member(m["name"])
                    st.rerun()
            st.markdown('<div style="height:4px;border-bottom:1px solid rgba(255,255,255,0.05);margin-bottom:4px;"></div>',
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


def show_email_watch_controls_page():
    """Email Watch — Controls: status, start/stop, credentials, settings."""
    import email_watch as ew

    st.markdown("## Email Watch · Controls")
    st.caption(
        "Watch your inbox for new attachments. Runs in the background — "
        "you can use Scanner or Pipeline normally while it checks."
    )

    cfg = ew.get_config()
    status = ew.get_status()

    # ── Status card ──────────────────────────────────────────────────────────
    if status["running"]:
        st.markdown(
            f'<div style="background:rgba(57,255,20,0.05);border-left:4px solid #39FF14;border-radius:8px;'
            f'padding:10px 16px;margin-bottom:16px;">'
            f'<span style="font-size:14px;font-weight:700;color:#a9dfbf;">● Watching inbox</span>'
            f'<span style="font-size:12px;color:#7dcea0;margin-left:12px;">'
            f'Last check: {status["last_time"] or "—"} · {status["last_status"]}</span></div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<div style="background:rgba(255,255,255,0.1);border-left:4px solid rgba(255,255,255,0.05);border-radius:8px;'
            f'padding:10px 16px;margin-bottom:16px;">'
            f'<span style="font-size:14px;font-weight:700;color:#9ca3af;">● Inbox watch is off</span>'
            + (f'<span style="font-size:12px;color:#d1d5db;margin-left:12px;">'
               f'Last check: {status["last_time"]} · {status["last_status"]}</span>'
               if status["last_time"] else "")
            + '</div>',
            unsafe_allow_html=True,
        )

    # ── Toggle ───────────────────────────────────────────────────────────────
    t1, t2, t3 = st.columns([1, 1, 3])
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
    with t2:
        if st.button("🔄 Check Now", use_container_width=True,
                     help="Run one check immediately without waiting for interval"):
            with st.spinner("Checking inbox…"):
                _found, _msg = ew.check_now()
            if _msg.startswith("Error"):
                st.error(_msg)
            elif _found:
                st.success(f"Found {_found} new PDF(s) — see below.")
            else:
                st.info(_msg)
            st.rerun()

    # ── Credentials setup ─────────────────────────────────────────────────────
    with st.expander("⚙️ Email Credentials" + (" (configured)" if cfg else " (not set up)"), expanded=not cfg):
        st.markdown(
            '<div style="background:rgba(251,191,36,0.05);border-left:3px solid #fbbf24;border-radius:6px;'
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


def show_email_watch_page():
    """Email Watch — Results: pending matches and incoming queue."""
    import email_watch as ew

    _ew_status  = ew.get_status()
    _ew_pending = _ew_status["pending_count"]
    _ew_running = _ew_status["running"]

    # compact status strip + Controls shortcut
    _dot   = "●" if _ew_running else "○"
    _state = f"Watching · last check {_ew_status['last_time'] or '—'}" if _ew_running else "Watch is off"
    _rs1, _rs2 = st.columns([5, 1])
    with _rs1:
        st.markdown(
            f'<div style="background:#1e1e1e;border-left:3px solid '
            f'{"#39FF14" if _ew_running else "rgba(255,255,255,0.15)"};border-radius:6px;'
            f'padding:6px 14px;font-size:12px;color:#9ca3af;">'
            f'{_dot} {_state} · <b style="color:#fff">{_ew_pending} attachment(s) waiting</b></div>',
            unsafe_allow_html=True,
        )
    with _rs2:
        if st.button("⚙️ Controls", key="ew_goto_controls", use_container_width=True):
            st.session_state.page = "email_watch_controls"
            st.session_state["ew_nav_open"] = True
            st.rerun()

    st.markdown("## Email Watch · Results")

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
                conf_color = "#39FF14"
                conf_label = f"✓ Matched — {bname} · Loan {lnum} ({conf}% confidence)"
            elif sugg == "possible":
                conf_color = "#fbbf24"
                conf_label = f"⚠️ Possible match — {bname} · Loan {lnum} ({conf}%)"
            else:
                conf_color = "#ef4444"
                conf_label = "? No pipeline match found"

            with st.expander(f"{m['filename']}  ·  {m.get('received', '')}  ·  {conf_label}", expanded=True):
                mc1, mc2 = st.columns([3, 1])
                with mc1:
                    st.markdown(
                        f'<div style="font-size:12px;color:#9ca3af;">From: {m["sender"]}</div>'
                        f'<div style="font-size:12px;color:#9ca3af;">Subject: {m["subject"]}</div>'
                        f'<div style="font-size:13px;font-weight:700;color:{conf_color};margin-top:6px;">'
                        f'{conf_label}</div>',
                        unsafe_allow_html=True,
                    )
                    folder = m.get("suggested_folder", "")
                    if folder:
                        st.markdown(
                            f'<div style="font-size:12px;color:#39FF14;margin-top:4px;">'
                            f'Suggested folder: {folder}</div>',
                            unsafe_allow_html=True,
                        )

                    _fp = m.get("file_path", "")
                    _fname_low = (m.get("filename") or "").lower()
                    _IMG_EXT = (".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tif", ".tiff", ".webp")
                    _can_preview = _fp and os.path.exists(_fp) and _fname_low.endswith(
                        _IMG_EXT + (".pdf", ".txt", ".csv")
                    )

                with mc2:
                    if _can_preview:
                        _icon = "🖼️" if _fname_low.endswith(_IMG_EXT) else ("📄" if _fname_low.endswith(".pdf") else "📋")
                        if st.button(f"{_icon} Preview", key=f"ew_preview_{i}", use_container_width=True):
                            _toggle = f"ew_preview_open_{i}"
                            st.session_state[_toggle] = not st.session_state.get(_toggle, False)
                    if folder and os.path.isdir(folder):
                        if st.button("Save to folder", key=f"ew_save_{i}", use_container_width=True, type="primary"):
                            import shutil
                            dest = os.path.join(folder, m["filename"])
                            shutil.copy2(m["file_path"], dest)
                            ew.dismiss(i)
                            st.success(f"Saved to {dest}")
                            st.rerun()
                    # Direct download — works for every file type
                    try:
                        with open(m["file_path"], "rb") as _dfh:
                            st.download_button(
                                "⬇ Download", _dfh.read(),
                                file_name=m["filename"],
                                key=f"ew_dl_{i}", use_container_width=True,
                            )
                    except Exception:
                        pass
                    if st.button("Open in Reader", key=f"ew_read_{i}", use_container_width=True):
                        import os as _os_ew
                        _fp2 = m["file_path"]
                        _fname = m.get("filename") or _os_ew.path.basename(_fp2)
                        _ext = _os_ew.path.splitext(_fname)[1].lower()
                        st.session_state.reader_open_file = {
                            "name": _fname, "path": _fp2, "rel": _fname,
                            "ext": _ext, "size_kb": 0,
                        }
                        st.session_state["reader_page"] = 1
                        st.session_state.page = "reader"
                        st.rerun()
                    if st.button("Dismiss", key=f"ew_dismiss_{i}", use_container_width=True):
                        ew.dismiss(i)
                        st.rerun()

                # ── Preview panel (below columns, full width) ──────────
                if _can_preview and st.session_state.get(f"ew_preview_open_{i}", False):
                    try:
                        if _fname_low.endswith(_IMG_EXT):
                            st.image(_fp, use_container_width=True)
                        elif _fname_low.endswith(".pdf"):
                            import base64 as _b64
                            with open(_fp, "rb") as _pfh:
                                _b64data = _b64.b64encode(_pfh.read()).decode("utf-8")
                            st.markdown(
                                f'<iframe src="data:application/pdf;base64,{_b64data}" '
                                f'width="100%" height="500" style="border:1px solid rgba(255,255,255,0.1);'
                                f'border-radius:6px;"></iframe>',
                                unsafe_allow_html=True,
                            )
                        elif _fname_low.endswith((".txt", ".csv")):
                            with open(_fp, "r", encoding="utf-8", errors="replace") as _tfh:
                                st.code(_tfh.read()[:3000], language=None)
                    except Exception as _pe:
                        st.caption(f"_(Preview failed: {_pe})_")

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
                '<span style="color:#9ca3af;font-size:13px;">No files in the incoming folder. '
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

                _v_color = {"pass": "#39FF14", "review": "#fbbf24", "check": "#ef4444"}.get(
                    _qv.get("verdict", "check"), "#ef4444"
                )
                _v_icon  = {"pass": "✓", "review": "△", "check": "?"}.get(
                    _qv.get("verdict", "check"), "Search"
                )
                _bname = _qv.get("borrower") or "Unknown borrower"
                _lnum  = _qv.get("loan_num", "")
                _match_label = f" · {_bname} · Loan {_lnum}" if _qv.get("borrower") else " · No pipeline match"

                with st.container():
                    st.markdown(
                        f'<div style="background:rgba(255,255,255,0.1);border-left:3px solid {_v_color};'
                        f'border-radius:6px;padding:8px 12px;margin-bottom:6px;">'
                        f'<span style="font-weight:700;color:#ffffff;font-size:13px;">'
                        f'{_v_icon} {_qfname}</span>'
                        f'<span style="font-size:12px;color:#9ca3af;">{_match_label}</span><br>'
                        f'<span style="font-size:11px;color:#39FF14;">{_qv.get("doc_type","Document")} · '
                        f'{_qv.get("page_count",0)} pages · '
                        f'{_qv.get("days_old","?")}d old</span></div>',
                        unsafe_allow_html=True,
                    )
                    _qa, _qb, _qc, _qd = st.columns([3, 1, 1, 1])
                    with _qa:
                        for _ok in _qv.get("ok_list", []):
                            st.markdown(f'<span style="color:#39FF14;font-size:11px;">✓ {_ok}</span><br>',
                                        unsafe_allow_html=True)
                        for _fl in _qv.get("flags", []):
                            st.markdown(f'<span style="color:#ef4444;font-size:11px;">⚑ {_fl}</span><br>',
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

    st.caption("Go to **Email Watch → Controls** to start/stop watching or update credentials.")


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
    bar_color = "#39FF14" if pct < 80 else ("#f59e0b" if pct < 100 else "#ef4444")
    st.markdown(
        f'<div style="background:rgba(255,255,255,0.1);border-radius:8px;padding:12px 16px;margin:8px 0 16px;">'
        f'<div style="font-size:13px;color:#d1d5db;margin-bottom:6px;">'
        f'Quota: {usage["scans"]} / {usage["included"]} scans used ({pct}%)</div>'
        f'<div style="background:rgba(255,255,255,0.03);border-radius:4px;height:10px;">'
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
                f'<span style="font-size:13px;color:#d1d5db;width:220px;">{dtype or "Unknown"}</span>'
                f'<div style="flex:1;background:rgba(255,255,255,0.03);border-radius:4px;height:8px;">'
                f'<div style="background:#39FF14;width:{pct_dt}%;height:8px;border-radius:4px;"></div></div>'
                f'<span style="font-size:13px;color:#d1d5db;width:40px;text-align:right;">{count}</span>'
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
            st.markdown(f'<div style="font-size:13px;color:#9ca3af;">· {n}</div>',
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
    _ld_bar_color = "#39FF14" if _ld_pct >= 75 else ("#f59e0b" if _ld_pct >= 40 else "#ef4444")

    st.markdown(
        f'<div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.1);border-left:3px solid {border_color};'
        f'border-radius:3px;padding:12px 14px;margin:4px 0;">'
        f'<div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:8px;">'
        f'<span style="font-size:16px;font-weight:700;color:#39FF14;">#{loan.get("loan_num","—")}</span>'
        f'<span style="font-size:15px;font-weight:600;color:#ffffff;">{loan.get("borrower","—")}</span>'
        f'<span class="status-chip status-{status.lower()}" style="font-size:13px;">'
        f'<span style="color:{border_color};font-size:10px;">●</span> {status}</span>'
        f'</div>'
        f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:3px;">'
        f'<span style="font-size:11px;color:#9ca3af;">{_ld_label}</span>'
        f'<span style="font-size:12px;font-weight:700;color:{_ld_bar_color};">{_ld_pct}% to close</span>'
        f'</div>'
        f'<div style="background:rgba(255,255,255,0.1);border-radius:2px;height:8px;overflow:hidden;">'
        f'<div style="background:{_ld_bar_color};width:{_ld_pct}%;height:100%;border-radius:2px;"></div>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Key Dates ─────────────────────────────────────────────────────────
    st.markdown(
        '<span style="font-size:13px;font-weight:700;color:#39FF14;text-transform:uppercase;'
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
                return f'<span style="color:#ef4444;font-weight:700;"> ({abs(diff)}d ago)</span>'
            elif diff == 0:
                return '<span style="color:#ef4444;font-weight:700;"> (TODAY)</span>'
            elif diff <= 7:
                return f'<span style="color:#f59e0b;font-weight:700;"> ({diff}d left)</span>'
            else:
                return f'<span style="color:#9ca3af;"> ({diff}d)</span>'
        except Exception:
            return ""

    d1, d2, d3, d4, d5 = st.columns(5)
    with d1:
        st.markdown(
            f'<div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.1);border-radius:8px;padding:10px;">'
            f'<div style="font-size:10px;color:#39FF14;font-weight:700;text-transform:uppercase;">Closing Date</div>'
            f'<div style="font-size:16px;font-weight:700;color:#ffffff;margin-top:4px;">'
            f'{_closing or "Not set"}{_days_away(_closing)}</div></div>',
            unsafe_allow_html=True,
        )
    with d2:
        st.markdown(
            f'<div style="background:#2d2200;border:1px solid #5a4400;border-radius:8px;padding:10px;">'
            f'<div style="font-size:10px;color:#fbbf24;font-weight:700;text-transform:uppercase;">Lock Expiration</div>'
            f'<div style="font-size:16px;font-weight:700;color:#ffffff;margin-top:4px;">'
            f'{_lock or "Not set"}{_days_away(_lock)}</div></div>',
            unsafe_allow_html=True,
        )
    with d3:
        st.markdown(
            f'<div style="background:#1a2d1a;border:1px solid #2d5a2d;border-radius:8px;padding:10px;">'
            f'<div style="font-size:10px;color:#9ca3af;font-weight:700;text-transform:uppercase;">Commitment Exp.</div>'
            f'<div style="font-size:16px;font-weight:700;color:#ffffff;margin-top:4px;">'
            f'{_commitment or "Not set"}{_days_away(_commitment)}</div></div>',
            unsafe_allow_html=True,
        )
    with d4:
        st.markdown(
            f'<div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.1);border-radius:8px;padding:10px;">'
            f'<div style="font-size:10px;color:#9ca3af;font-weight:700;text-transform:uppercase;">Created</div>'
            f'<div style="font-size:14px;color:#ffffff;margin-top:4px;">{_created or "—"}</div></div>',
            unsafe_allow_html=True,
        )
    with d5:
        st.markdown(
            f'<div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.1);border-radius:8px;padding:10px;">'
            f'<div style="font-size:10px;color:#9ca3af;font-weight:700;text-transform:uppercase;">Last Updated</div>'
            f'<div style="font-size:14px;color:#ffffff;margin-top:4px;">{_updated or "—"}</div></div>',
            unsafe_allow_html=True,
        )

    # ── Loan Details ──────────────────────────────────────────────────────
    st.markdown(
        '<span style="font-size:13px;font-weight:700;color:#39FF14;text-transform:uppercase;'
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
            f'<tr><td style="padding:4px 12px 4px 0;color:#9ca3af;font-size:12px;font-weight:600;'
            f'white-space:nowrap;vertical-align:top;">{k}</td>'
            f'<td style="padding:4px 0;color:#ffffff;font-size:13px;">{v}</td></tr>'
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
            f'<tr><td style="padding:4px 12px 4px 0;color:#9ca3af;font-size:12px;font-weight:600;'
            f'white-space:nowrap;vertical-align:top;">{k}</td>'
            f'<td style="padding:4px 0;color:#ffffff;font-size:13px;">{v}</td></tr>'
            for k, v in _fields_right
        )
        st.markdown(
            f'<table style="border-collapse:collapse;">{_rows_html2}</table>',
            unsafe_allow_html=True,
        )

    # ── Missing Docs ──────────────────────────────────────────────────────
    _missing = loan.get("missing_docs", "")
    st.markdown(
        '<span style="font-size:13px;font-weight:700;color:#39FF14;text-transform:uppercase;'
        'letter-spacing:0.5px;margin-top:12px;display:inline-block;">Missing Documents</span>',
        unsafe_allow_html=True,
    )
    if _missing:
        _docs = [d.strip() for d in _missing.split(",") if d.strip()]
        _doc_html = "".join(
            f'<div style="display:flex;align-items:center;gap:6px;margin-bottom:3px;">'
            f'<span style="color:#ef4444;">●</span>'
            f'<span style="color:#ffb86c;font-size:13px;">{d}</span></div>'
            for d in _docs
        )
        st.markdown(_doc_html, unsafe_allow_html=True)
    else:
        st.markdown(
            '<span style="color:#39FF14;font-size:13px;">All documents received</span>',
            unsafe_allow_html=True,
        )

    # ── Generate Templates (HOI + Title Request) ────────────────────────────
    st.markdown(
        '<span style="font-size:13px;font-weight:700;color:#39FF14;text-transform:uppercase;'
        'letter-spacing:0.5px;margin-top:12px;display:inline-block;">Generate Documents</span>',
        unsafe_allow_html=True,
    )
    _gen_c1, _gen_c2 = st.columns(2)
    with _gen_c1:
        if st.button("📄 Generate HOI Request", key=f"gen_hoi_{lid}", use_container_width=True):
            try:
                from template_filler import fill_template, build_context, OUTPUT_ROOT
                import os as _os, re as _re
                _ctx = build_context(loan)
                _safe = _re.sub(r"[^A-Za-z0-9_-]+", "_", _ctx["borrower_name"])[:40]
                _out = _os.path.join(OUTPUT_ROOT, str(lid), f"HOI Request_{_safe}.docx")
                fill_template("HOI Request.docx", _ctx, _out)
                log_activity(lid, "generated", f"HOI Request generated", user=my_name)
                st.session_state[f"_gen_hoi_path_{lid}"] = _out
                st.toast("HOI Request generated", icon="✅")
                st.rerun()
            except Exception as _e:
                st.error(f"Generation failed: {_e}")
    with _gen_c2:
        if st.button("📄 Generate Title Request", key=f"gen_title_{lid}", use_container_width=True):
            try:
                from template_filler import fill_template, build_context, OUTPUT_ROOT
                import os as _os, re as _re
                _ctx = build_context(loan)
                _safe = _re.sub(r"[^A-Za-z0-9_-]+", "_", _ctx["borrower_name"])[:40]
                _out = _os.path.join(OUTPUT_ROOT, str(lid), f"Title Request_{_safe}.docx")
                fill_template("Title Request copy.docx", _ctx, _out)
                log_activity(lid, "generated", f"Title Request generated", user=my_name)
                st.session_state[f"_gen_title_path_{lid}"] = _out
                st.toast("Title Request generated", icon="✅")
                st.rerun()
            except Exception as _e:
                st.error(f"Generation failed: {_e}")

    # Download buttons for freshly generated docs
    for _lbl, _skey in [("HOI Request", f"_gen_hoi_path_{lid}"), ("Title Request", f"_gen_title_path_{lid}")]:
        _p = st.session_state.get(_skey)
        if _p:
            try:
                with open(_p, "rb") as _fh:
                    st.download_button(
                        f"⬇ Download {_lbl} ({_p.split(chr(92))[-1] if chr(92) in _p else _p.split('/')[-1]})",
                        _fh.read(),
                        file_name=_p.split(chr(92))[-1] if chr(92) in _p else _p.split("/")[-1],
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        key=f"dl_{_skey}",
                        use_container_width=True,
                    )
            except FileNotFoundError:
                pass

    # ── Quick-copy Title & HOI contacts ─────────────────────────────────────
    _qc_contacts = loan.get("contacts", {}) or {}
    st.markdown(
        '<span style="font-size:13px;font-weight:700;color:#39FF14;text-transform:uppercase;'
        'letter-spacing:0.5px;margin-top:12px;display:inline-block;">Title &amp; HOI Contact — Copy</span>',
        unsafe_allow_html=True,
    )
    _qc_c1, _qc_c2 = st.columns(2)
    for _col, _role_key, _role_label in [
        (_qc_c1, "title", "Title"),
        (_qc_c2, "insurance", "HOI / Insurance"),
    ]:
        with _col:
            _rc = _qc_contacts.get(_role_key) or {}
            _name = _rc.get("contact") or _rc.get("name") or _rc.get("company") or ""
            _phone = _rc.get("phone", "")
            _email = _rc.get("email", "")
            st.markdown(
                f'<div style="font-size:10px;color:#39FF14;font-weight:700;'
                f'text-transform:uppercase;margin-bottom:4px;">{_role_label}</div>',
                unsafe_allow_html=True,
            )
            if not (_name or _phone or _email):
                st.markdown(
                    '<span style="color:#9ca3af;font-size:12px;">Not set</span>',
                    unsafe_allow_html=True,
                )
                continue
            if _name:
                st.markdown(
                    f'<div style="color:#d1d5db;font-size:13px;font-weight:600;margin-bottom:2px;">{_name}</div>',
                    unsafe_allow_html=True,
                )
            if _phone:
                st.code(_phone, language=None)
            if _email:
                st.code(_email, language=None)

    # ── Open Conditions (interactive — checkbox, status, parties, email) ────
    _conditions = loan.get("conditions", [])
    st.markdown(
        '<span style="font-size:13px;font-weight:700;color:#39FF14;text-transform:uppercase;'
        'letter-spacing:0.5px;margin-top:12px;display:inline-block;">Open Conditions</span>',
        unsafe_allow_html=True,
    )

    PARTY_OPTIONS_LD = [
        "Borrower", "Co-Borrower", "Title", "Realtor", "Seller",
        "Underwriter", "Jr Underwriter", "Loan Officer", "Closer",
        "Insurance", "Appraiser", "Manager",
    ]
    COND_STATUSES_LD = {
        "Needed":         {"label": "Needed",         "emoji": "●"},
        "Requested":      {"label": "Requested",      "emoji": "●"},
        "Important":      {"label": "Important",      "emoji": "●"},
        "Ready to Clear": {"label": "Ready to Clear", "emoji": "●"},
        "Cleared":        {"label": "Cleared",        "emoji": "✓"},
    }

    _ld_fkey = f"ld_{lid}"

    if _conditions:
        _ld_checked = []
        for _c in _conditions:
            _c["desc"] = _c.get("desc", _c.get("description", "—"))
            if "num" not in _c:
                _c["num"] = str(_conditions.index(_c) + 1)
            if "party" not in _c:
                _c["party"] = "Borrower"
            _chk, _cstat, _cparties = _render_condition(_c, _ld_fkey, PARTY_OPTIONS_LD, COND_STATUSES_LD)
            if _chk:
                _ld_checked.append({**_c, "party": _cparties[0] if _cparties else _c["party"], "all_parties": _cparties})

            # ── Per-condition 📖 Guidelines check ──
            _ld_uid = f"{_ld_fkey}_{_c['num']}"
            _gb1, _gb2 = st.columns([0.5, 9.5])
            with _gb1:
                if st.button("📖", key=f"{_ld_uid}_guide", help="Check vs. Fannie/Freddie guidelines"):
                    st.session_state[f"{_ld_uid}_guide_open"] = True
                    st.session_state.pop(f"{_ld_uid}_guide_results", None)
            if st.session_state.get(f"{_ld_uid}_guide_open"):
                _gc1, _gc2 = st.columns([9, 0.5])
                with _gc2:
                    if st.button("✕", key=f"{_ld_uid}_guide_close"):
                        for _k in (f"{_ld_uid}_guide_open", f"{_ld_uid}_guide_results"):
                            st.session_state.pop(_k, None)
                        st.rerun()
                _gres = st.session_state.get(f"{_ld_uid}_guide_results")
                if _gres is None:
                    with st.spinner("Searching Fannie Mae & Freddie Mac…"):
                        try:
                            from guidelines import check_conditions_against_guidelines as _cag_ld
                            _out = _cag_ld([{"num": _c["num"], "desc": _c["desc"]}])
                            if isinstance(_out, dict) and _out.get("error"):
                                _gres = {"error": _out["error"]}
                            else:
                                _gres = _out.get(_c["num"], {}).get("guidelines", [])
                        except Exception as _e:
                            _gres = {"error": f"{_e}"}
                        st.session_state[f"{_ld_uid}_guide_results"] = _gres
                if isinstance(_gres, dict) and _gres.get("error"):
                    st.markdown(
                        f'<div style="font-size:11px;color:#fbbf24;padding:4px 8px;'
                        f'background:rgba(251,191,36,0.08);border:1px solid rgba(251,191,36,0.25);'
                        f'border-radius:6px;margin:4px 0 4px 32px;">⚠️ {_gres["error"]}</div>',
                        unsafe_allow_html=True,
                    )
                elif isinstance(_gres, list) and _gres:
                    for _gm in _gres[:4]:
                        _src = _gm.get("source", "")
                        _sec = _gm.get("section", "")
                        _pg  = _gm.get("page", "")
                        _sc  = _gm.get("score", 0)
                        _ex  = (_gm.get("excerpt", "") or "").replace("\n", " ")[:360]
                        _sec_part = f" · <b>{_sec}</b>" if _sec else ""
                        st.markdown(
                            f'<div style="font-size:11px;color:#e5e7eb;padding:6px 10px;margin:3px 0 3px 32px;'
                            f'background:rgba(57,255,20,0.05);border-left:2px solid rgba(57,255,20,0.45);'
                            f'border-radius:4px;">'
                            f'<span style="color:#39FF14;font-weight:700;">{_src}</span>'
                            f'{_sec_part}'
                            f' <span style="color:#9ca3af;">p.{_pg} · {_sc}% match</span><br/>'
                            f'<span style="color:#cbd5e1;font-size:10.5px;">{_ex}…</span>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )
                elif isinstance(_gres, list):
                    st.markdown(
                        '<div style="font-size:11px;color:#6b7280;padding:4px 0 4px 32px;">'
                        'No relevant guideline sections found.</div>',
                        unsafe_allow_html=True,
                    )

        # ── Email Draft — below conditions, auto-populate from stored contacts ──
        st.markdown(
            '<span style="font-size:13px;font-weight:700;color:#39FF14;text-transform:uppercase;'
            'letter-spacing:0.5px;margin:10px 0 4px 0;display:inline-block;">Draft Email</span>',
            unsafe_allow_html=True,
        )

        # Build party list from stored contacts first, then fallback to PARTY_OPTIONS
        _stored_contacts = loan.get("contacts", {})
        _contact_party_map = {}  # display label -> contact info dict
        _party_display_labels = {
            "borrower": "Borrower", "co_borrower": "Co-Borrower", "buyer": "Borrower",
            "seller": "Seller", "listing_agent": "Listing Agent", "selling_agent": "Selling Agent",
            "title": "Title", "employer": "Employer",
        }
        for _ck, _cv in _stored_contacts.items():
            if not _cv or not isinstance(_cv, dict):
                continue
            _clabel = _party_display_labels.get(_ck, _ck.replace("_", " ").title())
            _cname = _cv.get("name") or _cv.get("company") or ""
            _cemail = _cv.get("email", "")
            _display = f"{_clabel}{f' — {_cname}' if _cname else ''}{f' ({_cemail})' if _cemail else ''}"
            _contact_party_map[_display] = _cv

        _party_choices = list(_contact_party_map.keys()) if _contact_party_map else PARTY_OPTIONS_LD

        # Pre-select parties from checked conditions
        _checked_parties = []
        for _cc in _ld_checked:
            for _cp in _cc.get("all_parties", [_cc["party"]]):
                if _cp not in _checked_parties:
                    _checked_parties.append(_cp)

        _em_c1, _em_c2, _em_c3 = st.columns([2, 2, 1])
        with _em_c1:
            _ld_recipient = st.selectbox(
                "Send to", _party_choices,
                key=f"ld_recip_{lid}", label_visibility="visible"
            )
        with _em_c2:
            _ld_lang = st.selectbox(
                "Language", ["English", "Spanish"],
                key=f"ld_lang_{lid}", label_visibility="visible"
            )
        with _em_c3:
            if _ld_checked:
                st.markdown(
                    f'<div style="padding-top:26px;font-size:11px;color:#39FF14;font-weight:600;">'
                    f'✓ {len(_ld_checked)} checked</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    '<div style="padding-top:26px;font-size:10px;color:#9ca3af;">check above</div>',
                    unsafe_allow_html=True,
                )

        _ld_d1, _ld_d2 = st.columns([1, 1])
        with _ld_d1:
            _ld_draft_btn = st.button("Draft Email", key=f"ld_draft_{lid}",
                                      type="primary", use_container_width=True)
        with _ld_d2:
            _ld_ai_btn = st.button("Draft with AI", key=f"ld_ai_draft_{lid}",
                                   use_container_width=True)

        if _ld_draft_btn:
            from ai_engine import draft_email as _de
            # Get recipient name/email from stored contact if available
            _recip_contact = _contact_party_map.get(_ld_recipient, {})
            _recip_label = _recip_contact.get("name") or _ld_recipient.split("—")[0].strip()
            if _ld_checked:
                _cond_lines = [f"- Condition #{c['num']}: {c['desc']}" for c in _ld_checked]
            else:
                _cond_lines = [f"- Condition #{c['num']}: {c['desc']}" for c in _conditions[:10]]
            _email_out = _de("\n".join(_cond_lines), _recip_label, _ld_lang)
            # Auto-fill To: if we have a stored email
            _recip_email = _recip_contact.get("email", "")
            if _recip_email:
                st.markdown(
                    f'<div style="font-size:11px;color:#9ca3af;margin-bottom:4px;">To: <b>{_recip_email}</b></div>',
                    unsafe_allow_html=True,
                )
            st.container(border=True).markdown(_email_out)

        if _ld_ai_btn:
            import ai_router as _ld_ar
            _ld_backend = _ld_ar.get_preferred_backend()
            if _ld_backend == "script":
                st.warning("AI backend not configured. Go to AI Settings.")
            else:
                _conds_for_ai = _ld_checked if _ld_checked else _conditions[:10]
                with st.spinner("Drafting with AI…"):
                    _ld_ai_text, _ld_ai_log = _ld_ar.draft_email_enhanced(
                        _conds_for_ai, _ld_recipient.split("—")[0].strip(), _ld_lang
                    )
                if _ld_ai_text:
                    st.container(border=True).markdown(_ld_ai_text)
    else:
        st.markdown(
            '<span style="color:#9ca3af;font-size:12px;">No conditions attached to this loan yet. '
            'Upload and scan a document to extract conditions.</span>',
            unsafe_allow_html=True,
        )

    # ── Parties & Contacts ───────────────────────────────────────────────
    _contacts = loan.get("contacts", {})
    st.markdown(
        '<span style="font-size:13px;font-weight:700;color:#39FF14;text-transform:uppercase;'
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
            _detail_str = " &nbsp;·&nbsp; ".join(_detail_parts) if _detail_parts else '<span style="color:#9ca3af;">No details</span>'
            _contact_html += (
                f'<div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.1);border-radius:8px;padding:10px;">'
                f'<div style="font-size:10px;color:#39FF14;font-weight:700;text-transform:uppercase;margin-bottom:4px;">{_clabel}</div>'
                f'<div style="color:#ffffff;font-size:13px;font-weight:600;">{_cname or "—"}</div>'
                f'<div style="color:#9ca3af;font-size:11px;margin-top:3px;">{_detail_str}</div>'
                f'</div>'
            )
        _contact_html += '</div>'
        st.markdown(_contact_html, unsafe_allow_html=True)
    else:
        st.markdown(
            '<span style="color:#9ca3af;font-size:12px;">No contact information attached. '
            'Upload a Purchase Contract or 1003 to populate parties.</span>',
            unsafe_allow_html=True,
        )

    # ── Scan & Attach Document ───────────────────────────────────────────
    st.markdown(
        '<span style="font-size:13px;font-weight:700;color:#39FF14;text-transform:uppercase;'
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

                _pc_rows = [
                    f'Buyer: {_pc_buyer.get("name","—")}',
                    f'Seller: {_pc_seller.get("name","—")}',
                    f'Price: ${_pc_txn.get("purchase_price","—")}',
                    f'Close: {_pc_txn.get("closing_date","—")}',
                ]
                if _pc_txn.get("date_signed"):
                    _pc_rows.append(f'Date Signed: {_pc_txn["date_signed"]}')
                if _pc_txn.get("obligation_date"):
                    _pc_rows.append(f'Obligation Date: {_pc_txn["obligation_date"]}')
                if _pc_txn.get("seller_concessions"):
                    _pc_rows.append(f'Seller Concessions: {_pc_txn["seller_concessions"]}')
                if _pc_la.get("name"):
                    _la_str = f'Listing Agent: {_pc_la["name"]}'
                    if _pc_la.get("brokerage"): _la_str += f' · {_pc_la["brokerage"]}'
                    if _pc_la.get("phone"):     _la_str += f' · {_pc_la["phone"]}'
                    if _pc_la.get("email"):     _la_str += f' · {_pc_la["email"]}'
                    _pc_rows.append(_la_str)
                if _pc_sa.get("name"):
                    _sa_str = f'Selling Agent: {_pc_sa["name"]}'
                    if _pc_sa.get("brokerage"): _sa_str += f' · {_pc_sa["brokerage"]}'
                    if _pc_sa.get("phone"):     _sa_str += f' · {_pc_sa["phone"]}'
                    if _pc_sa.get("email"):     _sa_str += f' · {_pc_sa["email"]}'
                    _pc_rows.append(_sa_str)
                if _pc_title.get("company"):
                    _tc_str = f'Title: {_pc_title["company"]}'
                    if _pc_title.get("contact"): _tc_str += f' · {_pc_title["contact"]}'
                    if _pc_title.get("phone"):   _tc_str += f' · {_pc_title["phone"]}'
                    _pc_rows.append(_tc_str)
                st.markdown(
                    '<div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.1);border-radius:8px;'
                    'padding:10px;margin:8px 0;font-size:12px;color:#9ca3af;">'
                    '<b style="color:#39FF14;">Purchase Contract found:</b><br>'
                    + '<br>'.join(_pc_rows) +
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
                    st.toast("Contacts merged into loan", icon="✅")
                    st.rerun()

            # ── 1003 Application → merge contacts ──
            elif _sr_dtype == "1003 Application" and _sr.get("extracted_data"):
                _app = _sr["extracted_data"]
                _app_b = _app.get("borrower", {})
                _app_cb = _app.get("co_borrower", {})
                _app_emp = _app.get("employment", {})

                st.markdown(
                    '<div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.1);border-radius:8px;'
                    'padding:10px;margin:8px 0;font-size:12px;color:#9ca3af;">'
                    '<b style="color:#39FF14;">1003 Application found:</b><br>'
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
                    st.toast("Contacts merged into loan", icon="✅")
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
                        f'<div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.1);border-radius:8px;'
                        f'padding:10px;margin:8px 0;font-size:12px;color:#9ca3af;">'
                        f'<b style="color:#39FF14;">{_sr_dtype} scanned:</b> '
                        f'{len(_new_conds)} condition(s) found</div>',
                        unsafe_allow_html=True,
                    )
                    # Preview the conditions
                    for _nc in _new_conds:
                        st.markdown(
                            f'<span style="color:#fbbf24;font-size:12px;">●</span> '
                            f'<span style="color:#ffffff;font-size:12px;">{_nc["desc"]}</span> '
                            f'<span style="color:#9ca3af;font-size:11px;">— {_nc["party"]}</span>',
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
                        st.toast(f"{_added} condition(s) merged", icon="✅")
                        st.rerun()
                else:
                    st.info("No conditions extracted from this document.")

            # ── Bank Statement → show rules ──
            elif _sr.get("bank_rules"):
                st.markdown(
                    f'<div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.1);border-radius:8px;'
                    f'padding:10px;margin:8px 0;font-size:12px;color:#9ca3af;">'
                    f'<b style="color:#39FF14;">Bank Statement Analysis:</b></div>',
                    unsafe_allow_html=True,
                )
                st.markdown(_sr["bank_rules"])
                log_activity(lid, "upload", "Bank Statement scanned and reviewed", user=my_name)

    # ── Approval Fetch ────────────────────────────────────────────────────
    st.markdown(
        '<span style="font-size:13px;font-weight:700;color:#39FF14;text-transform:uppercase;'
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
                f'<div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.1);border-radius:8px;'
                f'padding:10px;margin:8px 0;">'
                f'<div style="display:flex;justify-content:space-between;align-items:center;">'
                f'<div>'
                f'<span style="color:#39FF14;font-weight:700;font-size:13px;">Approval Letter Scanned</span><br>'
                f'<span style="color:#9ca3af;font-size:12px;">Borrower: <b style="color:#ffffff;">'
                f'{_af_borrower or "Unknown"}</b> · '
                f'{_af_data["cond_count"]} condition(s) extracted · '
                f'{_af_data["text_length"]:,} chars'
                f'{" · Commitment: <b style=color:#9ca3af;>" + _af_data.get("commitment_date","") + "</b>" if _af_data.get("commitment_date") else ""}'
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
                            f'<div class="stat-card"><div class="stat-num" style="color:#ffffff;">'
                            f'{len(_af_conds)}</div>'
                            f'<div class="stat-label">Total Conditions</div></div>',
                            unsafe_allow_html=True,
                        )
                    with _s2:
                        st.markdown(
                            f'<div class="stat-card"><div class="stat-num" style="color:#39FF14;">'
                            f'{len(_af_found)}</div>'
                            f'<div class="stat-label">✓ Documents Found</div></div>',
                            unsafe_allow_html=True,
                        )
                    with _s3:
                        st.markdown(
                            f'<div class="stat-card"><div class="stat-num" style="color:#ef4444;">'
                            f'{len(_af_missing)}</div>'
                            f'<div class="stat-label">✗ Still Missing</div></div>',
                            unsafe_allow_html=True,
                        )

                    # Found conditions
                    if _af_found:
                        st.markdown(
                            '<div style="font-size:13px;font-weight:700;color:#39FF14;'
                            'margin:12px 0 6px 0;">FOUND — Documents located in folder</div>',
                            unsafe_allow_html=True,
                        )
                        for _c, _matches in _af_found:
                            _best = _matches[0]
                            _conf_color = "#39FF14" if _best["score"] >= 70 else (
                                "#fbbf24" if _best["score"] >= 50 else "#f59e0b"
                            )
                            st.markdown(
                                f'<div style="display:flex;gap:10px;align-items:flex-start;'
                                f'background:rgba(57,255,20,0.05);border-left:3px solid #39FF14;'
                                f'border-radius:6px;padding:8px 12px;margin-bottom:4px;">'
                                f'<span style="color:#39FF14;font-weight:700;font-size:12px;min-width:20px;">✓</span>'
                                f'<div style="flex:1;">'
                                f'<span style="color:#ffffff;font-size:13px;font-weight:600;">'
                                f'#{_c["num"]} {_c["desc"][:80]}</span><br>'
                                f'<span style="color:#9ca3af;font-size:11px;">{_best["file_name"]}'
                                f' &nbsp;·&nbsp; <span style="color:{_conf_color};">{_best["score"]}% match</span>'
                                f' &nbsp;·&nbsp; {_best["match_type"]}</span>'
                                + (f'<br><span style="color:#9ca3af;font-size:11px;font-style:italic;">'
                                   f'{_best["snippet"][:120]}</span>' if _best.get("snippet") else "")
                                + (f'<br><span style="color:#9ca3af;font-size:10px;">'
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
                            '<div style="font-size:13px;font-weight:700;color:#ef4444;'
                            'margin:12px 0 6px 0;">MISSING — No matching documents found</div>',
                            unsafe_allow_html=True,
                        )
                        for _c in _af_missing:
                            st.markdown(
                                f'<div style="display:flex;gap:10px;align-items:flex-start;'
                                f'background:rgba(239,68,68,0.05);border-left:3px solid #ef4444;'
                                f'border-radius:6px;padding:8px 12px;margin-bottom:4px;">'
                                f'<span style="color:#ef4444;font-weight:700;font-size:12px;min-width:20px;">✗</span>'
                                f'<div style="flex:1;">'
                                f'<span style="color:#ffffff;font-size:13px;font-weight:600;">'
                                f'#{_c["num"]} {_c["desc"][:80]}</span>'
                                f'</div>'
                                f'<span style="background:#9ca3af;color:#fff;font-size:10px;'
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
                            st.toast(f"{_added} conditions merged into loan", icon="✅")
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
                            st.toast(f"{_added} conditions merged", icon="✅")
                            st.rerun()

                elif _af_scan_res and _af_scan_res.get("error"):
                    st.error(_af_scan_res["error"])

    # ── Notes ─────────────────────────────────────────────────────────────
    st.markdown(
        '<span style="font-size:13px;font-weight:700;color:#39FF14;text-transform:uppercase;'
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
        st.toast("Notes saved", icon="✅")
        st.rerun()

    # ── Quick Actions ─────────────────────────────────────────────────────
    st.markdown(
        '<span style="font-size:13px;font-weight:700;color:#39FF14;text-transform:uppercase;'
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
        '<span style="font-size:13px;font-weight:700;color:#39FF14;text-transform:uppercase;'
        'letter-spacing:0.5px;margin-top:16px;display:inline-block;">Activity Log</span>',
        unsafe_allow_html=True,
    )
    activity = get_activity(lid)
    if not activity:
        st.markdown(
            '<span style="color:#9ca3af;font-size:12px;">No activity recorded yet. '
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
            _user_tag = f'<span style="color:#39FF14;font-weight:600;">{_user}</span> · ' if _user else ""
            st.markdown(
                f'<div style="display:flex;gap:10px;padding:4px 0;border-bottom:1px solid rgba(255,255,255,0.05);">'
                f'<span style="font-size:14px;min-width:20px;">{_icon}</span>'
                f'<div>'
                f'<span style="color:#ffffff;font-size:12px;">{_detail}</span><br>'
                f'<span style="color:#9ca3af;font-size:10px;">{_user_tag}{_ts}</span>'
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
        elif page == "email_watch_controls":
            show_email_watch_controls_page()
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
