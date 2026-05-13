"""
Processor Assistant - Mortgage Document Processing App
Main Streamlit application.
"""

import os
import re
import time
import streamlit as st
from dotenv import load_dotenv

# Load .env from app dir and parent workspace for local runs
_APP_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(_APP_DIR, ".env"), override=False)
load_dotenv(os.path.join(os.path.dirname(_APP_DIR), ".env"), override=False)

# --- Page Config ---
st.set_page_config(
    page_title="Processor Assistant",
    page_icon="",
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
    /* Tax-Delinquencies design system: navy/blue, flat, BI-tool aesthetic */
    --bg-page: #0f1117; --bg-white: #1a1f2e; --bg-subtle: #161b2b;
    --accent: #2563eb; --accent-dark: #1d4ed8; --accent-light: rgba(59, 130, 246, 0.1);
    --green: #16a34a; --green-bg: #14532d; --green-border: rgba(34, 197, 94, 0.4);
    --red: #ef4444; --red-bg: #7f1d1d; --red-border: rgba(239, 68, 68, 0.4);
    --amber: #fcd34d; --amber-bg: #78350f; --amber-border: rgba(245, 158, 11, 0.4);
    --purple: #c7d2fe; --purple-bg: #1e1b4b; --purple-border: rgba(99, 102, 241, 0.4);
    --pink: #fed7aa; --pink-bg: #7c2d12; --pink-border: rgba(234, 88, 12, 0.4);
    --gold: #fcd34d; --gold-bg: rgba(251, 191, 36, 0.1);
    --slate-900: #ffffff; --slate-700: #e0e0e0; --slate-600: #94a3b8;
    --slate-500: #64748b; --slate-400: #64748b; --slate-300: #334155;
    --slate-200: #1e293b; --slate-100: #161b2b;
    --radius-sm: 6px; --radius-md: 10px;
    --shadow-card: none;
    --shadow-hover: 0 2px 6px rgba(0,0,0,0.3);
    --shadow-lg: 0 10px 30px rgba(0,0,0,0.5);
    --neon-glow: none;
    --neon-glow-lg: none;
    --pa-sidebar-w: 244px;
    --pa-main-gutter: 12px;
}
html, body, [class*="css"] { font-family: 'Segoe UI', Arial, sans-serif !important; }
.stApp { background: #0f1117 !important; }
.stApp::before {
    content: ''; position: fixed; top: 0; left: 0; right: 0; bottom: 0;
    background-image: radial-gradient(circle, rgba(59, 130, 246, 0.03) 1px, transparent 1px);
    background-size: 32px 32px; pointer-events: none; z-index: 0;
}
[data-testid="stAppViewContainer"] > div:first-child { background: transparent !important; }
#MainMenu, footer { visibility: hidden; height: 0; }
/* Hide ONLY the sidebar collapse/expand toggle controls keep nav buttons visible */
[data-testid="stSidebarCollapsedControl"],
[data-testid="stExpandSidebarButton"],
[data-testid="stSidebarHeader"] [data-testid="stBaseButton-headerNoPadding"],
[data-testid="stSidebarCollapseButton"] {
    display: none !important;
}
/* Sidebar always rendered as expanded override Streamlit's aria-expanded="false" hiding */
[data-testid="stSidebar"] {
    min-width: var(--pa-sidebar-w) !important;
    width: var(--pa-sidebar-w) !important;
    max-width: var(--pa-sidebar-w) !important;
    transform: none !important;
    margin-left: 0 !important;
    visibility: visible !important;
    position: relative !important;
}
/* Let Streamlit place main content; only add inner gutter to avoid edge touch */
[data-testid="stMain"] {
    min-width: 0 !important;
    margin-left: 0 !important;
    width: 100vw !important;
    max-width: 100% !important;
    padding-left: 0 !important;
    box-sizing: border-box !important;
    overflow-x: hidden !important;
    transition: none !important;
}
[data-testid="stAppViewContainer"]:has([data-testid="stSidebar"]) [data-testid="stMain"] {
    margin-left: 0 !important;
    width: 100% !important;
}
[data-testid="stMain"] section[data-testid="stMain"],
[data-testid="stMain"] > div[data-testid="stMainBlockContainer"],
[data-testid="stAppViewContainer"] > .main,
[data-testid="stAppViewContainer"] section.main {
    margin-left: 0 !important;
    width: 100% !important;
    max-width: 100% !important;
    padding-left: var(--pa-main-gutter) !important;
    padding-right: var(--pa-main-gutter) !important;
    box-sizing: border-box !important;
}
/* Force just the user-content visible leave header/content default so scrolling works */
[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
    visibility: visible !important;
    opacity: 1 !important;
}
/* Hide the empty header bar that creates the white strip */
[data-testid="stSidebarHeader"] {
    background: transparent !important;
    min-height: 0 !important;
    padding: 0 !important;
}
/* Hide Streamlit's top white app header bar entirely */
header[data-testid="stHeader"], [data-testid="stHeader"], .stAppHeader {
    background: transparent !important;
    height: 0 !important;
    min-height: 0 !important;
    visibility: hidden !important;
    display: none !important;
}
/* â”€â”€â”€ Custom sidebar toggle (DOM-injected button + body class) â”€â”€â”€ */
#pa-sidebar-toggle {
    position: fixed !important;
    top: 12px !important;
    left: 252px !important;
    z-index: 999999 !important;
    width: 44px !important;
    height: 36px !important;
    border-radius: 8px !important;
    background: #3b82f6 !important;
    color: #fff !important;
    border: 2px solid #000 !important;
    font-size: 18px !important;
    font-weight: 900 !important;
    cursor: pointer !important;
    box-shadow: 0 0 14px rgba(59,130,246,0.7), 0 2px 6px rgba(0,0,0,0.4) !important;
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    justify-content: center !important;
    transition: left 0.25s ease, height 0.2s ease !important;
    padding: 4px 0 !important;
    line-height: 1 !important;
}
#pa-sidebar-toggle:hover { background: #2563eb !important; }
body.pa-sidebar-hidden #pa-sidebar-toggle { left: 12px !important; height: 48px !important; }
body.pa-sidebar-hidden [data-testid="stSidebar"] {
    width: 0 !important;
    min-width: 0 !important;
    max-width: 0 !important;
    overflow: hidden !important;
    visibility: hidden !important;
}
body.pa-sidebar-hidden [data-testid="stMain"] {
    margin-left: 0 !important;
    padding-left: 0 !important;
    width: 100vw !important;
    max-width: 100% !important;
}
body.pa-sidebar-hidden [data-testid="stMain"] section[data-testid="stMain"],
body.pa-sidebar-hidden [data-testid="stMain"] > div[data-testid="stMainBlockContainer"] {
    margin-left: 0 !important;
    padding-left: var(--pa-main-gutter) !important;
    padding-right: var(--pa-main-gutter) !important;
    max-width: 100% !important;
}
[data-testid="stSidebar"] {
    transition: width 0.25s ease, min-width 0.25s ease, max-width 0.25s ease !important;
}
@media (max-width: 768px) {
    :root { --pa-sidebar-w: 200px; --pa-main-gutter: 10px; }
    #pa-sidebar-toggle { left: 208px !important; }
    body.pa-sidebar-hidden #pa-sidebar-toggle { left: 12px !important; }
}
@media (max-width: 480px) {
    :root { --pa-sidebar-w: 180px; --pa-main-gutter: 8px; }
    #pa-sidebar-toggle { left: 188px !important; }
    body.pa-sidebar-hidden #pa-sidebar-toggle { left: 12px !important; }
}

/* â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ Mobile responsiveness â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */

/* Tablet & phone: wider sidebar so nav text isn't cramped collapse via toggle for content room */
@media (max-width: 768px) {
    [data-testid="stSidebar"] {
        min-width: 200px !important;
        width: 200px !important;
        max-width: 200px !important;
        flex-shrink: 0 !important;
    }
    [data-testid="stSidebar"] button {
        font-size: 12px !important;
        padding: 6px 8px !important;
        word-break: break-word !important;
    }
    [data-testid="stAppViewContainer"] > .main,
    [data-testid="stAppViewContainer"] section.main {
        overflow-x: hidden !important;
    }
    .main > div, .block-container {
        padding: 0.75rem !important;
        max-width: 100% !important;
    }
    /* Make st.columns stack instead of squeezing into narrow strips */
    [data-testid="stHorizontalBlock"] {
        flex-direction: column !important;
        gap: 0.5rem !important;
    }
    [data-testid="stHorizontalBlock"] > [data-testid="column"] {
        width: 100% !important;
        flex: 1 1 100% !important;
        min-width: 0 !important;
    }
    /* Tables: horizontal scroll instead of overflow */
    [data-testid="stMarkdownContainer"] table {
        display: block !important;
        overflow-x: auto !important;
        white-space: nowrap !important;
        -webkit-overflow-scrolling: touch !important;
    }
    /* Buttons full-width on mobile so they don't get cramped */
    .stButton > button, .stDownloadButton > button, .stLinkButton > a {
        width: 100% !important;
    }
    /* Hero h2 too big on phones */
    h2, [data-testid="stMarkdownContainer"] h2, .main h2, .block-container h2 {
        font-size: 28px !important;
        padding: 6px 0 6px 10px !important;
    }
    h1 { font-size: 20px !important; }
}

/* Phone-only: even tighter narrower sidebar, smaller buttons */
@media (max-width: 480px) {
    [data-testid="stSidebar"] {
        min-width: 180px !important;
        width: 180px !important;
        max-width: 180px !important;
    }
    [data-testid="stSidebar"] button {
        font-size: 11px !important;
        padding: 5px 6px !important;
    }
    .block-container {
        padding: 0.5rem !important;
    }
    /* Date inputs and selectboxes full width, taller for touch */
    [data-testid="stDateInput"], [data-testid="stSelectbox"],
    [data-testid="stTextInput"], [data-testid="stTextArea"],
    [data-testid="stNumberInput"], [data-testid="stMultiSelect"] {
        width: 100% !important;
    }
    [data-testid="stDateInput"] input, [data-testid="stSelectbox"] > div > div,
    [data-testid="stTextInput"] input {
        min-height: 40px !important;  /* finger-friendly tap target */
        font-size: 14px !important;
    }
    /* Stat cards: stack vertically with breathing room */
    .stat-card { padding: 12px 14px !important; margin-bottom: 6px !important; }
    .stat-num { font-size: 22px !important; }
    /* Loan cards on pipeline: more vertical breathing room */
    .loan-card { padding: 10px 12px !important; }
    /* Hide the progress nav step labels, keep just the numbers */
    .pn-step { font-size: 9px !important; padding: 4px !important; min-width: 40px !important; }
    /* Custom sidebar toggle arrows easier to hit */
    button[kind="secondary"], button[kind="primary"] {
        min-height: 40px !important;
        font-size: 13px !important;
    }
}
.stDeployButton { display: none; }
/* Keep native sidebar collapse/expand toggle visible so users can reopen the sidebar */
[data-testid="stSidebar"] { background: linear-gradient(180deg, #222222 0%, #181818 100%) !important; border-right: 1px solid rgba(255,255,255,0.1) !important; }
[data-testid="stSidebar"] > div:first-child { padding: 0.1rem 1rem 1rem 1rem !important; }
[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] { padding-top: 0 !important; margin-top: 0 !important; }
[data-testid="stSidebar"] .block-container { padding-top: 0 !important; }
[data-testid="stSidebar"] button, [data-testid="stSidebar"] button[kind], [data-testid="stSidebar"] [data-testid*="baseButton"] { background: rgba(255,255,255,0.07) !important; border: 1px solid rgba(255,255,255,0.1) !important; color: #c0c0c0 !important; border-radius: var(--radius-sm) !important; font-size: 13px !important; font-weight: 500 !important; text-align: left !important; padding: 8px 12px !important; margin-bottom: 3px !important; width: 100% !important; box-shadow: none !important; transition: all 0.2s ease !important; height: auto !important; min-height: 36px !important; opacity: 1 !important; display: block !important; visibility: visible !important; }
[data-testid="stSidebar"] button p, [data-testid="stSidebar"] button span, [data-testid="stSidebar"] button div { background: transparent !important; color: #c0c0c0 !important; }
[data-testid="stSidebar"] button[kind="primary"] { background: rgba(59,130,246,0.08) !important; border: 1px solid var(--accent) !important; color: var(--accent) !important; font-weight: 600 !important; box-shadow: 0 0 8px rgba(59,130,246,0.18) !important; }
[data-testid="stSidebar"] button[kind="primary"] p, [data-testid="stSidebar"] button[kind="primary"] span, [data-testid="stSidebar"] button[kind="primary"] div { color: var(--accent) !important; font-weight: 600 !important; background: transparent !important; }
[data-testid="stSidebar"] button[kind="primary"]:hover { background: rgba(59,130,246,0.14) !important; border-color: var(--accent) !important; color: var(--accent) !important; box-shadow: 0 0 14px rgba(59,130,246,0.35) !important; }
[data-testid="stSidebar"] button[kind="primary"]:focus, [data-testid="stSidebar"] button[kind="primary"]:active { background: rgba(59,130,246,0.08) !important; color: var(--accent) !important; border-color: var(--accent) !important; }
[data-testid="stSidebar"] button:hover { background: rgba(59,130,246,0.12) !important; border-color: rgba(59,130,246,0.35) !important; color: var(--accent) !important; outline: none !important; box-shadow: none !important; }
[data-testid="stSidebar"] button:focus, [data-testid="stSidebar"] button:focus-visible, [data-testid="stSidebar"] button:active, [data-testid="stSidebar"] button[data-focused="true"] { background: rgba(255,255,255,0.07) !important; border-color: rgba(255,255,255,0.1) !important; color: #c0c0c0 !important; outline: none !important; box-shadow: none !important; }
[data-testid="stSidebar"] button:focus p, [data-testid="stSidebar"] button:focus-visible p, [data-testid="stSidebar"] button:active p { color: #c0c0c0 !important; background: transparent !important; }
button { text-align: left !important; justify-content: flex-start !important; }
button * { text-align: left !important; }
button p { text-align: left !important; width: 100% !important; }
button > div { justify-content: flex-start !important; text-align: left !important; }
.block-container {
    padding: 4.5rem 2rem 3rem 2rem !important;
    width: 100% !important;
    max-width: none !important;
    box-sizing: border-box !important;
}
h1 { font-size: 24px !important; font-weight: 800 !important; color: var(--slate-900) !important; }
h2, [data-testid="stMarkdownContainer"] h2, .main h2, .block-container h2 { font-size: 42px !important; font-weight: 800 !important; color: var(--accent) !important; padding: 8px 0 8px 14px !important; border-left: 4px solid var(--accent) !important; text-shadow: 0 0 16px rgba(59,130,246,0.5) !important; margin-bottom: 14px !important; line-height: 1.2 !important; }
h2 span, [data-testid="stMarkdownContainer"] h2 span { font-size: inherit !important; color: var(--accent) !important; font-weight: inherit !important; }
h3 { font-size: 15px !important; font-weight: 600 !important; color: var(--slate-700) !important; }
p, li { color: var(--slate-600) !important; font-size: 13px !important; }
label { color: var(--slate-700) !important; font-size: 13px !important; font-weight: 500 !important; }
[data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] li, [data-testid="stMarkdownContainer"] span { color: var(--slate-600) !important; font-size: 13px !important; }
[data-testid="stMarkdownContainer"] strong { color: var(--slate-900) !important; font-weight: 600 !important; }
button[kind="primary"] { background: rgba(59,130,246,0.08) !important; color: var(--accent) !important; border: 1px solid var(--accent) !important; border-radius: var(--radius-sm) !important; font-weight: 700 !important; font-size: 13px !important; height: 36px !important; box-shadow: 0 0 10px rgba(59, 130, 246, 0.18) !important; transition: all 0.25s ease !important; }
button[kind="primary"]:hover { background: rgba(59,130,246,0.15) !important; color: var(--accent) !important; border-color: var(--accent) !important; box-shadow: 0 0 18px rgba(59, 130, 246, 0.4) !important; transform: translateY(-1px) !important; }
button[kind="primary"] p { color: var(--accent) !important; font-weight: 700 !important; }
button[kind="secondary"] { background: linear-gradient(135deg, #2a2a2a 0%, #222222 100%) !important; color: #c0c0c0 !important; border: 1px solid rgba(255,255,255,0.15) !important; border-radius: var(--radius-sm) !important; font-weight: 500 !important; font-size: 12px !important; height: 34px !important; box-shadow: 0 1px 3px rgba(0,0,0,0.4) !important; }
button[kind="secondary"]:hover { border-color: var(--accent) !important; color: var(--accent) !important; background: var(--accent-light) !important; box-shadow: var(--neon-glow) !important; }
button[kind="secondary"] p { color: var(--slate-600) !important; }
button[kind="secondary"]:hover p { color: var(--accent) !important; }
/* Streamlit form submit buttons can render bright defaults before hover/focus.
   Force dark base state for all form buttons immediately on paint. */
[data-testid="stForm"] [data-testid="stFormSubmitButton"] button,
[data-testid="stForm"] [data-testid="stButton"] button {
    background: linear-gradient(135deg, #2a2a2a 0%, #222222 100%) !important;
    color: #c0c0c0 !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.4) !important;
}
[data-testid="stForm"] [data-testid="stFormSubmitButton"] button[kind="primary"],
[data-testid="stForm"] [data-testid="stButton"] button[kind="primary"] {
    background: rgba(59,130,246,0.10) !important;
    color: var(--accent) !important;
    border: 1px solid var(--accent) !important;
    box-shadow: 0 0 10px rgba(59,130,246,0.20) !important;
}
[data-testid="stForm"] [data-testid="stFormSubmitButton"] button p,
[data-testid="stForm"] [data-testid="stButton"] button p {
    color: inherit !important;
}
[data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea, [data-testid="stSelectbox"] > div > div, [data-testid="stNumberInput"] input { background: var(--bg-subtle) !important; border: 1px solid var(--slate-300) !important; border-radius: var(--radius-sm) !important; color: var(--slate-900) !important; font-size: 13px !important; }
[data-testid="stTextInput"] input:focus, [data-testid="stTextArea"] textarea:focus { border-color: var(--accent) !important; box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1) !important; }
[data-testid="stFileUploader"] { background: rgba(255,255,255,0.02) !important; border: 1.5px dashed rgba(59,130,246,0.3) !important; border-radius: 14px !important; padding: 8px !important; transition: all 0.18s ease-in-out !important; }
[data-testid="stFileUploader"]:hover { border-color: rgba(59,130,246,0.6) !important; background: rgba(59,130,246,0.04) !important; box-shadow: 0 0 24px rgba(59,130,246,0.12) !important; }
[data-testid="stFileUploader"] section { background: transparent !important; }
[data-testid="stFileUploader"] button { background: rgba(59,130,246,0.08) !important; border: 1px solid rgba(59,130,246,0.3) !important; color: #3b82f6 !important; }
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
[data-testid="stSidebar"] [data-testid="baseButton-secondary"]:hover { background: rgba(59,130,246,0.12) !important; }
[data-baseweb="popover"] ul, [data-baseweb="menu"] { background: var(--bg-white) !important; border: 1px solid var(--slate-300) !important; box-shadow: var(--shadow-hover) !important; }
[data-baseweb="popover"] li, [data-baseweb="menu"] li { background: var(--bg-white) !important; color: var(--slate-900) !important; }
[data-baseweb="popover"] li:hover, [data-baseweb="menu"] li:hover { background: var(--accent-light) !important; color: var(--accent) !important; }
[data-baseweb="select"] > div { background: var(--bg-subtle) !important; border-color: var(--slate-300) !important; color: var(--slate-900) !important; }
[data-testid="stToggle"] > label > div[data-checked="true"] { background: var(--accent) !important; }
[data-testid="stHorizontalBlock"] { gap: 0.3rem !important; }
[data-testid="stHorizontalBlock"] > div > div { margin-bottom: 2px !important; }
[data-testid="stVerticalBlock"] { gap: 6px !important; }

/* Pipeline top action bar — tight spacing especially when stacked on narrow screens.
   Uses :has() because Streamlit wraps the marker div in a stElementContainer,
   so the + sibling combinator can't find the columns block directly. */
[data-testid="stElementContainer"]:has(.pa-pipe-controls) {
    margin-bottom: 0 !important;
}
[data-testid="stElementContainer"]:has(.pa-pipe-controls) + [data-testid="stElementContainer"] [data-testid="stHorizontalBlock"],
[data-testid="stElementContainer"]:has(.pa-pipe-controls) ~ [data-testid="stElementContainer"]:first-of-type [data-testid="stHorizontalBlock"] {
    gap: 4px !important;
    row-gap: 4px !important;
    margin-bottom: 6px !important;
}
[data-testid="stElementContainer"]:has(.pa-pipe-controls) ~ [data-testid="stElementContainer"] [data-testid="stHorizontalBlock"] [data-testid="column"] {
    padding: 0 !important;
    margin-bottom: 0 !important;
}
[data-testid="stElementContainer"]:has(.pa-pipe-controls) ~ [data-testid="stElementContainer"] [data-testid="stElementContainer"] {
    margin-bottom: 0 !important;
}
[data-testid="stElementContainer"]:has(.pa-pipe-controls) ~ [data-testid="stElementContainer"] [data-testid="stVerticalBlock"] {
    gap: 4px !important;
}
[data-testid="stElementContainer"]:has(.pa-pipe-controls) ~ [data-testid="stElementContainer"] .stButton > button,
[data-testid="stElementContainer"]:has(.pa-pipe-controls) ~ [data-testid="stElementContainer"] [data-baseweb="select"] > div,
[data-testid="stElementContainer"]:has(.pa-pipe-controls) ~ [data-testid="stElementContainer"] [data-testid="stTextInput"] input {
    height: 36px !important;
    min-height: 36px !important;
}
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
.pn-step.active { background: var(--accent-light); color: var(--accent); border: 1px solid var(--accent); font-weight: 600 !important; box-shadow: 0 0 10px rgba(59, 130, 246, 0.15); }
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
.login-card { max-width: 360px; margin: 0 auto; background: var(--bg-white); border: 1px solid var(--slate-200); border-radius: 16px; padding: 36px 32px 28px; box-shadow: 0 0 30px rgba(59, 130, 246, 0.1), 0 4px 24px rgba(0,0,0,0.4); }
.login-title { font-size: 22px; font-weight: 800; color: var(--slate-900); text-align: center; letter-spacing: -0.4px; }
.login-sub { font-size: 12px; color: var(--slate-500); text-align: center; margin-bottom: 20px; }
.login-page-wrap {
    width: min(420px, 94vw);
    margin: 0 auto;
    padding: 0 0 40px 0;
}
.login-sandbox-btn button { background: rgba(59,130,246,0.08) !important; color: var(--accent) !important; border: 1px solid var(--accent) !important; font-weight: 700 !important; font-size: 13px !important; border-radius: 12px !important; height: 44px !important; min-height: 44px !important; box-shadow: 0 0 14px rgba(59, 130, 246, 0.25) !important; transition: all 0.25s ease !important; display: grid !important; place-items: center !important; text-align: center !important; }
.login-sandbox-btn button:hover { box-shadow: 0 0 30px rgba(59, 130, 246, 0.4) !important; transform: translateY(-2px) !important; }
.login-sandbox-btn [data-testid="stButton"],
.login-sandbox-btn [data-testid="stButton"] > div,
.login-sandbox-btn button > div,
.login-sandbox-btn button p,
.login-sandbox-btn button span {
    width: 100% !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    text-align: center !important;
}
.login-sandbox-btn button p { color: #000 !important; font-weight: 700 !important; width: 100% !important; text-align: center !important; margin: 0 !important; }
.login-divider { display:flex;align-items:center;gap:10px;margin:18px 0 14px; }
.login-divider span { font-size:11px;color:var(--slate-500);white-space:nowrap; }
.login-divider hr { flex:1;border:none;border-top:1px solid var(--slate-200); }
[data-testid="stToast"], div[data-testid="stToast"] > div { background: var(--bg-white) !important; color: var(--slate-900) !important; border: 1px solid var(--slate-300) !important; }
div[data-baseweb="popover"], ul[data-testid="stSelectboxVirtualDropdown"] { background: var(--bg-white) !important; border: 1px solid var(--slate-300) !important; z-index: 999999 !important; }
[data-baseweb="tooltip"] { background: #1a1a1a !important; color: #c0c0c0 !important; border: 1px solid rgba(255,255,255,0.15) !important; box-shadow: none !important; }
[data-baseweb="tooltip"] * { background: transparent !important; color: #c0c0c0 !important; }
div[data-baseweb="popover"] li, ul[data-testid="stSelectboxVirtualDropdown"] li { color: var(--slate-900) !important; }
div[data-baseweb="popover"] li:hover, ul[data-testid="stSelectboxVirtualDropdown"] li:hover { background: var(--accent-light) !important; }
[data-testid="stCaptionContainer"] p { color: var(--slate-500) !important; }
.glow-text { text-shadow: 0 0 40px rgba(59, 130, 246, 0.3); }
/* Pipeline: flat compact cards */
.pipeline-scroll button { height: 14px !important; min-height: 14px !important; font-size: 8px !important; font-weight: 600 !important; padding: 0 4px !important; border-radius: 3px !important; background: rgba(255,255,255,0.05) !important; border: 1px solid rgba(255,255,255,0.1) !important; color: #e5e7eb !important; box-shadow: none !important; transform: none !important; }
.pipeline-scroll button:hover { background: rgba(255,255,255,0.1) !important; border-color: rgba(255,255,255,0.25) !important; color: #ffffff !important; transform: none !important; box-shadow: none !important; }
.pipeline-scroll button p { color: inherit !important; font-size: 8px !important; font-weight: 600 !important; margin: 0 !important; line-height: 1 !important; }
.pipeline-scroll [data-testid="stSelectbox"] > div > div { min-height: 32px !important; height: 32px !important; font-size: 11px !important; padding: 0 8px !important; }
.pipeline-scroll [data-testid="stSelectbox"] { margin-bottom: 0 !important; }
.pipeline-scroll [data-testid="stVerticalBlock"] { gap: 2px !important; }
.pipeline-scroll [data-testid="stHorizontalBlock"] { gap: 4px !important; margin-bottom: 0 !important; }
.pipeline-scroll [data-testid="stMarkdownContainer"] { margin: 0 !important; padding: 0 !important; }
.pipeline-scroll [data-testid="stMarkdownContainer"] p { margin: 0 !important; line-height: 1.2 !important; }
.pipeline-scroll [data-testid="stExpander"] { margin-bottom: 2px !important; margin-top: 0 !important; }
.pipeline-scroll [data-testid="stExpander"] summary { padding: 4px 10px !important; font-size: 11px !important; }
.pipeline-scroll [data-testid="stVerticalBlockBorderWrapper"] { padding: 4px 8px !important; margin-bottom: 4px !important; }
/* Tabbed alignment for loan rows every field lines up across all rows */
/* Marker class for loan rows used by :has() selectors below.
   No display:grid here the row uses inline flexbox. */
.pa-loan-grid {
    display: block;
    width: 100%;
}
/* My loans toggle styled to match top control row */
.pa-myloans-toggle + div [data-testid="stCheckbox"] {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    border-radius: 6px !important;
    padding: 0 10px !important;
    min-height: 26px !important;
    height: 26px !important;
    display: flex !important;
    align-items: center !important;
    transition: all 0.2s ease !important;
}
.pa-myloans-toggle + div [data-testid="stCheckbox"]:hover {
    border-color: rgba(59,130,246,0.4) !important;
    background: rgba(59,130,246,0.05) !important;
}
/* Scanner detect rows: keep filename + dropdown from visually colliding */
[data-testid="stElementContainer"]:has(.pa-scan-detect-rows) ~ [data-testid="stElementContainer"] [data-testid="stHorizontalBlock"] {
    margin-bottom: 14px !important;
    align-items: center !important;
}
.pa-scan-fname, .pa-scan-conf {
    display: flex;
    align-items: center;
    min-height: 36px;
    line-height: 1.3;
    word-break: break-word;
}
.pa-scan-fname { font-weight: 600; color: #e2e8f0; }
@media (max-width: 900px) {
    [data-testid="stElementContainer"]:has(.pa-scan-detect-rows) ~ [data-testid="stElementContainer"] [data-testid="stHorizontalBlock"] {
        margin-bottom: 26px !important;
        row-gap: 10px !important;
        padding-bottom: 10px !important;
        border-bottom: 1px dashed rgba(255,255,255,0.08);
    }
    [data-testid="stElementContainer"]:has(.pa-scan-detect-rows) ~ [data-testid="stElementContainer"] [data-testid="stHorizontalBlock"] > [data-testid="column"] {
        margin-bottom: 8px !important;
    }
    .pa-scan-fname {
        min-height: 0;
        font-size: 14px !important;
        font-weight: 700 !important;
        color: #ffffff !important;
        padding: 6px 0 4px 0;
    }
    .pa-scan-conf  { min-height: 0; padding: 2px 0 6px 0; font-style: italic; }
}
.pa-myloans-toggle + div [data-testid="stCheckbox"] label {
    font-size: 12px !important;
    color: #d1d5db !important;
    font-weight: 500 !important;
    white-space: nowrap !important;
}
/* Primary (Open) button inside pipeline neon-green, more prominent */
.pipeline-scroll [data-testid="stButton"] button,
.pipeline-scroll [data-testid="stButton"] button[kind="primary"],
.pipeline-scroll button[kind="primary"] {
    background: rgba(59,130,246,0.08) !important;
    border: 1px solid var(--accent) !important;
    color: var(--accent) !important;
    font-weight: 800 !important;
    font-size: 8px !important;
    height: 14px !important;
    min-height: 14px !important;
    letter-spacing: 0.3px !important;
    box-shadow: 0 0 8px rgba(59,130,246,0.15) !important;
    padding: 0 4px !important;
}
.pipeline-scroll button[kind="primary"]:hover {
    background: rgba(59,130,246,0.16) !important;
    box-shadow: 0 0 14px rgba(59,130,246,0.4) !important;
    color: var(--accent) !important;
}
.pipeline-scroll button[kind="primary"] p { color: var(--accent) !important; font-weight: 800 !important; font-size: 8px !important; margin: 0 !important; line-height: 1 !important; }
/* Hoverable contact chip tooltip */
.pa-tip { position: relative; cursor: help; display: inline-block; }
.pa-tip-box { visibility: hidden; opacity: 0; position: absolute; bottom: 125%; left: 0; z-index: 9999;
    background: #1a1a1a; border: 1px solid rgba(59,130,246,0.35); border-radius: 8px;
    padding: 8px 10px; min-width: 200px; max-width: 320px;
    box-shadow: 0 6px 24px rgba(0,0,0,0.6); transition: opacity 0.12s ease-in-out;
    white-space: normal; pointer-events: none; }
.pa-tip:hover .pa-tip-box { visibility: visible; opacity: 1; }
/* Scan results: tight like pipeline cards */
.scan-scroll button { height: 26px !important; min-height: 26px !important; font-size: 11px !important; font-weight: 600 !important; padding: 0 7px !important; border-radius: 3px !important; background: rgba(255,255,255,0.05) !important; border: 1px solid rgba(255,255,255,0.1) !important; color: #e5e7eb !important; box-shadow: none !important; transform: none !important; }
.scan-scroll button:hover { background: rgba(255,255,255,0.1) !important; border-color: rgba(255,255,255,0.25) !important; color: #ffffff !important; }
.scan-scroll button p { color: inherit !important; font-size: 11px !important; font-weight: 600 !important; margin: 0 !important; }
.scan-scroll [data-testid="stCheckbox"] label { font-size: 11px !important; font-weight: 700 !important; color: #3b82f6 !important; }
.scan-scroll [data-testid="stCheckbox"] { padding-top: 2px !important; }
.scan-scroll [data-baseweb="select"] > div { min-height: 26px !important; height: 26px !important; font-size: 11px !important; }
.scan-scroll [data-baseweb="select"] * { font-size: 11px !important; }
.scan-scroll div[data-testid="stVerticalBlock"] { gap: 2px !important; }
.scan-scroll div[data-testid="stHorizontalBlock"] { gap: 4px !important; align-items: center !important; }
.scan-scroll div[data-testid="stHorizontalBlock"] > div[data-testid="column"] { min-width: 0 !important; }
.scan-scroll [class*="st-key-scan_"][class*="_stat"] { min-width: 118px !important; }
.scan-scroll [class*="st-key-scan_"][class*="_party"] { min-width: 156px !important; }
.scan-scroll [class*="st-key-scan_"][class*="_fetch"] { min-width: 70px !important; }
.scan-scroll [class*="st-key-scan_"][class*="_guide"] { min-width: 70px !important; }
.scan-scroll [class*="st-key-scan_"] [data-baseweb="select"] {
    min-width: 100% !important;
    white-space: nowrap !important;
}
.scan-scroll [class*="st-key-scan_"] [data-baseweb="select"] * {
    white-space: nowrap !important;
}
.scan-scroll .cond-row { display:flex; align-items:center; gap:6px; padding:3px 0; border-bottom:1px dashed rgba(255,255,255,0.06); }
.scan-scroll .cond-num { color:#3b82f6; font-weight:800; font-size:11px; min-width:22px; }
.scan-scroll .cond-desc { color:#e5e7eb; font-size:12px; line-height:1.35; flex:1; }
.scan-scroll .pa-section { font-size:10px; font-weight:700; color:#9ca3af; text-transform:uppercase; letter-spacing:0.6px; margin:6px 0 2px 0; }
.scan-scroll .pa-needs-list {
    margin: 4px 0 12px 0;
    padding: 8px 10px;
    border: 1px solid rgba(59,130,246,0.16);
    border-left: 3px solid rgba(59,130,246,0.75);
    border-radius: 8px;
    background: rgba(15,23,42,0.34);
}
.scan-scroll .pa-need-row {
    display: flex;
    align-items: flex-start;
    gap: 7px;
    margin: 5px 0;
    color: #e5e7eb;
    font-size: 12.5px;
    line-height: 1.42;
}
.scan-scroll .pa-need-bullet { color: #94a3b8; font-weight: 800; line-height: 1.45; }
.scan-scroll .pa-need-subject { color: #f8fafc; font-weight: 850; }
.scan-scroll .pa-need-body { color: #dbeafe; font-weight: 500; }
/* Aggressively compress condition rows — target ~65-75% of default height. */
.scan-scroll [data-testid="stVerticalBlockBorderWrapper"] {
    padding: 3px 8px !important;
    margin-bottom: 3px !important;
    border-radius: 4px !important;
}
.scan-scroll [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stVerticalBlock"] {
    gap: 0 !important;
}
.scan-scroll [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stHorizontalBlock"] {
    gap: 4px !important;
    margin: 0 !important;
    padding: 0 !important;
}
.scan-scroll [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stElementContainer"] {
    margin: 0 !important;
    padding: 0 !important;
}
.scan-scroll [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stMarkdownContainer"] {
    margin: 0 !important;
    padding: 0 !important;
}
.scan-scroll [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stMarkdownContainer"] p {
    margin: 0 !important;
    padding: 0 !important;
    line-height: 1.22 !important;
}
.scan-scroll [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stMarkdownContainer"] div {
    line-height: 1.22 !important;
}
.scan-scroll [data-testid="stVerticalBlockBorderWrapper"] [data-baseweb="select"] > div {
    min-height: 22px !important;
    height: 22px !important;
}
.scan-scroll [data-testid="stVerticalBlockBorderWrapper"] [data-baseweb="select"] {
    margin: 0 !important;
}
.scan-scroll [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stSelectbox"] {
    margin: 0 !important;
    padding: 0 !important;
}
.scan-scroll [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stMultiSelect"] {
    margin: 0 !important;
    padding: 0 !important;
}
.scan-scroll [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stMultiSelect"] > div {
    min-height: 22px !important;
    padding-top: 0 !important;
    padding-bottom: 0 !important;
}
.scan-scroll [data-testid="stVerticalBlockBorderWrapper"] button {
    height: 22px !important;
    min-height: 22px !important;
    padding: 0 6px !important;
    margin: 0 !important;
}
.scan-scroll [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stCheckbox"] {
    padding: 0 !important;
    margin: 0 !important;
}
/* Higher-specificity override against the global stVerticalBlockBorderWrapper rule */
[data-testid="stMainBlockContainer"] .scan-scroll [data-testid="stVerticalBlockBorderWrapper"] {
    padding: 3px 8px !important;
    margin-bottom: 3px !important;
}
.scan-scroll .pa-need-status {
    display: inline-block;
    margin-left: 7px;
    padding: 1px 5px;
    border: 1px solid rgba(148,163,184,0.24);
    border-radius: 999px;
    color: #93c5fd;
    background: rgba(59,130,246,0.08);
    font-size: 9px;
    font-weight: 800;
    letter-spacing: 0.55px;
    text-transform: uppercase;
    vertical-align: middle;
}
@media (max-width: 768px) {
    /* Prevent condition text clipping on mobile when client-language lines are longer */
    .scan-scroll [style*="line-height:1.38"] span,
    .scan-scroll [style*="line-height:1.35"] {
        white-space: normal !important;
        word-break: break-word !important;
        overflow-wrap: anywhere !important;
    }
}
/* Sidebar section collapse toggle buttons green label style */
[data-testid="stSidebar"] [data-testid="stElementContainer"]:has(hr) + [data-testid="stElementContainer"] button,
[data-testid="stSidebar"] hr + * button,
[data-testid="stSidebar"] .pa-sec-btn button {
    background: transparent !important;
    border: none !important;
    border-bottom: 1px solid rgba(59,130,246,0.2) !important;
    border-radius: 0 !important;
    color: #3b82f6 !important;
    font-size: 11px !important;
    font-weight: 700 !important;
    letter-spacing: 1px !important;
    padding: 4px 2px !important;
    margin-bottom: 4px !important;
    box-shadow: none !important;
    min-height: 28px !important;
    height: 28px !important;
}
[data-testid="stSidebar"] [data-testid="stElementContainer"]:has(hr) + [data-testid="stElementContainer"] button p,
[data-testid="stSidebar"] .pa-sec-btn button p {
    color: #3b82f6 !important;
    font-size: 11px !important;
    font-weight: 700 !important;
}

/* â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
   TAX-DELINQUENCIES THEME OVERRIDES
   Overrides any leftover neon-green hardcoded references.
   â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• */

/* Background grid pattern: remove neon dot pattern */
.stApp::before { display: none !important; }

/* Page-level dark navy */
.stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
    background: #0f1117 !important;
}

/* Sidebar navy */
[data-testid="stSidebar"] {
    background: #161b2b !important;
    border-right: 1px solid #1e293b !important;
}

/* H1 / branding */
[data-testid="stSidebar"] [style*="font-size:18px"][style*="font-weight:800"] {
    color: #ffffff !important;
}

/* H2: replace neon green hero with subdued white + blue accent bar */
h2, [data-testid="stMarkdownContainer"] h2, .main h2, .block-container h2 {
    color: #ffffff !important;
    border-left: 3px solid #2563eb !important;
    text-shadow: none !important;
    font-size: 18px !important;
    font-weight: 600 !important;
    padding: 4px 0 4px 12px !important;
    letter-spacing: 0.3px !important;
}
h2 span, [data-testid="stMarkdownContainer"] h2 span {
    color: #ffffff !important;
}

/* H1 */
h1 {
    color: #ffffff !important;
    font-weight: 700 !important;
    letter-spacing: 0.5px !important;
}

/* H3 / smaller headings */
h3, h4, h5 { color: #e0e0e0 !important; }

/* Body text */
p, li, label, [data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li, [data-testid="stMarkdownContainer"] span {
    color: #e0e0e0 !important;
}
[data-testid="stMarkdownContainer"] strong { color: #ffffff !important; }

/* Labels uppercase */
label, .stSelectbox label, .stTextInput label, .stTextArea label,
.stNumberInput label, .stDateInput label {
    font-size: 11px !important;
    color: #94a3b8 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.6px !important;
    font-weight: 600 !important;
}

/* Cards & containers */
[data-testid="stVerticalBlockBorderWrapper"],
div[data-testid="stExpander"],
div[data-testid="stForm"] {
    background: #1a1f2e !important;
    border: 1px solid #334155 !important;
    border-radius: 10px !important;
    box-shadow: none !important;
}
[data-testid="stVerticalBlockBorderWrapper"]:hover,
div[data-testid="stExpander"]:hover {
    border-color: #475569 !important;
    box-shadow: none !important;
    transform: none !important;
}
/* Keep expanded details/summary surfaces dark (avoid bright white flash) */
div[data-testid="stExpander"] details,
div[data-testid="stExpander"] details[open],
div[data-testid="stExpander"] summary,
div[data-testid="stExpander"] summary[aria-expanded="true"],
div[data-testid="stExpander"] > div {
    background: #1a1f2e !important;
    color: #e5e7eb !important;
}

/* Ensure app pages use full working width (login page has its own wrapper) */
[data-testid="stMainBlockContainer"],
[data-testid="stAppViewContainer"] .main .block-container {
    width: 100% !important;
    max-width: none !important;
}

/* Sidebar internals stay flat */
[data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"] {
    background: transparent !important;
    border: none !important;
}

/* Primary buttons â†’ blue */
button[kind="primary"], .stButton > button[kind="primary"] {
    background: #2563eb !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 6px !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    box-shadow: none !important;
    transition: opacity 0.15s !important;
}
button[kind="primary"]:hover {
    opacity: 0.85 !important;
    background: #2563eb !important;
    color: #ffffff !important;
    transform: none !important;
    box-shadow: none !important;
}
button[kind="primary"] p, button[kind="primary"] span {
    color: #ffffff !important;
    font-weight: 600 !important;
}

/* Secondary buttons â†’ slate */
button[kind="secondary"], .stButton > button[kind="secondary"] {
    background: #334155 !important;
    color: #e0e0e0 !important;
    border: none !important;
    border-radius: 6px !important;
    font-weight: 500 !important;
    font-size: 13px !important;
    box-shadow: none !important;
}
button[kind="secondary"]:hover {
    background: #475569 !important;
    border: none !important;
    color: #ffffff !important;
    box-shadow: none !important;
}
button[kind="secondary"] p { color: #e0e0e0 !important; }
button[kind="secondary"]:hover p { color: #ffffff !important; }

/* Sidebar nav buttons */
[data-testid="stSidebar"] button {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid #1e293b !important;
    color: #cbd5e1 !important;
    border-radius: 6px !important;
    font-weight: 500 !important;
    font-size: 13px !important;
    box-shadow: none !important;
}
[data-testid="stSidebar"] button:hover {
    background: rgba(59,130,246,0.1) !important;
    border-color: #3b82f6 !important;
    color: #ffffff !important;
    box-shadow: none !important;
}
[data-testid="stSidebar"] button[kind="primary"] {
    background: #2563eb !important;
    border: none !important;
    color: #ffffff !important;
    box-shadow: none !important;
}
[data-testid="stSidebar"] button[kind="primary"] p,
[data-testid="stSidebar"] button[kind="primary"] span {
    color: #ffffff !important;
}
[data-testid="stSidebar"] button p,
[data-testid="stSidebar"] button span,
[data-testid="stSidebar"] button div {
    color: #cbd5e1 !important;
}
[data-testid="stSidebar"] button:hover p,
[data-testid="stSidebar"] button:hover span {
    color: #ffffff !important;
}

/* Inputs */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea,
[data-testid="stSelectbox"] > div > div,
[data-testid="stNumberInput"] input,
[data-testid="stDateInput"] input {
    background: #0f1117 !important;
    border: 1px solid #334155 !important;
    border-radius: 6px !important;
    color: #e0e0e0 !important;
    font-size: 13px !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {
    border-color: #3b82f6 !important;
    box-shadow: none !important;
}

/* File uploader compact, less obnoxious */
[data-testid="stFileUploader"] {
    background: #161b2b !important;
    border: 1px dashed #334155 !important;
    border-radius: 6px !important;
    padding: 4px 8px !important;
}
[data-testid="stFileUploader"] section {
    padding: 4px 8px !important;
    min-height: 0 !important;
}
[data-testid="stFileUploader"] section > div {
    padding: 0 !important;
    min-height: 0 !important;
}
[data-testid="stFileUploader"] section small,
[data-testid="stFileUploader"] section span {
    font-size: 11px !important;
    color: #94a3b8 !important;
}
[data-testid="stFileUploader"] button {
    padding: 4px 12px !important;
    font-size: 12px !important;
    min-height: 0 !important;
    height: 28px !important;
}
[data-testid="stFileUploader"] svg { width: 16px !important; height: 16px !important; }
[data-testid="stFileUploaderDropzone"] {
    padding: 6px 10px !important;
    min-height: 0 !important;
}
[data-testid="stFileUploaderDropzoneInstructions"] {
    padding: 0 !important;
    margin: 0 !important;
}
[data-testid="stFileUploaderDropzoneInstructions"] > div {
    font-size: 12px !important;
}
[data-testid="stFileUploader"]:hover {
    border-color: #3b82f6 !important;
    background: rgba(59,130,246,0.04) !important;
    box-shadow: none !important;
}
[data-testid="stFileUploader"] button {
    background: #2563eb !important;
    border: none !important;
    color: #ffffff !important;
}

/* Alerts */
[data-testid="stAlert"] {
    border-radius: 6px !important;
    border: none !important;
    font-weight: 500 !important;
}
[data-testid="stAlert"][data-type="info"], .stAlert[kind="info"] {
    background: #1e3a8a !important; color: #93c5fd !important; border: none !important;
}
[data-testid="stAlert"][data-type="success"], .stAlert[kind="success"] {
    background: #14532d !important; color: #86efac !important; border: none !important;
}
[data-testid="stAlert"][data-type="warning"], .stAlert[kind="warning"] {
    background: #78350f !important; color: #fcd34d !important; border: none !important;
}
[data-testid="stAlert"][data-type="error"], .stAlert[kind="error"] {
    background: #7f1d1d !important; color: #fca5a5 !important; border: none !important;
}

/* Tabs */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    border-bottom: 1px solid #1e293b !important;
}
[data-testid="stTabs"] [role="tab"] {
    color: #94a3b8 !important;
    font-size: 13px !important;
    font-weight: 500 !important;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    color: #3b82f6 !important;
    border-bottom: 2px solid #2563eb !important;
    font-weight: 600 !important;
}

/* Expander */
[data-testid="stExpander"] summary {
    color: #e0e0e0 !important;
    font-weight: 600 !important;
}
[data-testid="stExpander"] summary:hover {
    color: #3b82f6 !important;
    background: rgba(59,130,246,0.05) !important;
}

/* Tables */
[data-testid="stMarkdownContainer"] table {
    background: #1a1f2e !important;
    border: 1px solid #334155 !important;
    box-shadow: none !important;
}
[data-testid="stMarkdownContainer"] thead tr { background: #161b2b !important; }
[data-testid="stMarkdownContainer"] th {
    color: #94a3b8 !important;
    font-size: 11px !important;
    text-transform: uppercase !important;
    border-bottom: 2px solid #1e293b !important;
}
[data-testid="stMarkdownContainer"] td {
    color: #e0e0e0 !important;
    border-bottom: 1px solid #1e293b !important;
}
[data-testid="stMarkdownContainer"] tr:hover td {
    background: #161b2b !important;
}

/* Progress */
[data-testid="stProgress"] > div > div { background: #2563eb !important; }
[data-testid="stProgress"] { background: #1e293b !important; }

/* Toggle */
[data-testid="stToggle"] > label > div[data-checked="true"] {
    background: #2563eb !important;
}

/* Multiselect */
[data-testid="stMultiSelect"] > div {
    background: #0f1117 !important;
    border: 1px solid #334155 !important;
}
[data-testid="stMultiSelect"] span[data-baseweb="tag"] {
    background: rgba(59,130,246,0.15) !important;
    color: #93c5fd !important;
    border: 1px solid #2563eb !important;
}

/* Popover / dropdown menus */
[data-baseweb="popover"] ul, [data-baseweb="menu"],
ul[data-testid="stSelectboxVirtualDropdown"] {
    background: #1a1f2e !important;
    border: 1px solid #334155 !important;
}
[data-baseweb="popover"] li, [data-baseweb="menu"] li,
ul[data-testid="stSelectboxVirtualDropdown"] li {
    background: #1a1f2e !important;
    color: #e0e0e0 !important;
}
[data-baseweb="popover"] li:hover, [data-baseweb="menu"] li:hover,
ul[data-testid="stSelectboxVirtualDropdown"] li:hover {
    background: rgba(59,130,246,0.15) !important;
    color: #93c5fd !important;
}

/* Status chips & badges â†’ BI-style pill colors */
.status-pending  { background: #7f1d1d !important; color: #fca5a5 !important; border: none !important; }
.status-requested{ background: #78350f !important; color: #fcd34d !important; border: none !important; }
.status-cleared  { background: #14532d !important; color: #86efac !important; border: none !important; }
.status-overdue  { background: #1e293b !important; color: #94a3b8 !important; border: none !important; }
.status-closed   { background: #1e293b !important; color: #64748b !important; border: none !important; }

.badge-borrower    { background: #1e3a8a !important; color: #93c5fd !important; border: none !important; }
.badge-title       { background: #1e1b4b !important; color: #c7d2fe !important; border: none !important; }
.badge-underwriter { background: #78350f !important; color: #fcd34d !important; border: none !important; }
.badge-insurance   { background: #14532d !important; color: #86efac !important; border: none !important; }
.badge-closer      { background: #7c2d12 !important; color: #fed7aa !important; border: none !important; }
.badge-jr          { background: #581c87 !important; color: #e9d5ff !important; border: none !important; }
.badge-manager     { background: #14532d !important; color: #86efac !important; border: none !important; }
.badge-appraiser   { background: #14532d !important; color: #86efac !important; border: none !important; }
.badge-default     { background: #1e293b !important; color: #94a3b8 !important; border: none !important; }

/* Loan card */
.loan-card {
    background: #1a1f2e !important;
    border: 1px solid #334155 !important;
    border-radius: 8px !important;
    box-shadow: none !important;
}
.loan-card:hover {
    border-color: #3b82f6 !important;
    background: #1e2532 !important;
    box-shadow: none !important;
    transform: none !important;
}
.loan-num { color: #3b82f6 !important; }
.loan-name { color: #ffffff !important; }
.loan-due { color: #94a3b8 !important; }
.loan-missing { color: #fca5a5 !important; }

/* Stat cards */
.stat-card {
    background: #1a1f2e !important;
    border: 1px solid #334155 !important;
    border-radius: 10px !important;
    box-shadow: none !important;
}
.stat-card:hover {
    border-color: #3b82f6 !important;
    box-shadow: none !important;
    transform: none !important;
}
.stat-num { color: #3b82f6 !important; font-weight: 700 !important; }
.stat-label { color: #94a3b8 !important; }

/* Progress nav */
.progress-nav {
    background: #161b2b !important;
    border: 1px solid #1e293b !important;
    box-shadow: none !important;
}
.pn-step.done {
    background: #14532d !important;
    color: #86efac !important;
    border: 1px solid rgba(34,197,94,0.4) !important;
}
.pn-step.active {
    background: rgba(59,130,246,0.15) !important;
    color: #93c5fd !important;
    border: 1px solid #2563eb !important;
    box-shadow: none !important;
}

/* Custom sidebar toggle button â†’ blue */
#pa-sidebar-toggle {
    background: #2563eb !important;
    color: #ffffff !important;
    border: none !important;
    box-shadow: 0 2px 6px rgba(0,0,0,0.4) !important;
}
#pa-sidebar-toggle:hover {
    background: #1d4ed8 !important;
}

/* Login card */
.login-card {
    background: #1a1f2e !important;
    border: 1px solid #334155 !important;
    box-shadow: 0 4px 24px rgba(0,0,0,0.4) !important;
}
.login-title { color: #ffffff !important; }
.login-sub { color: #94a3b8 !important; }
.login-sandbox-btn button {
    background: #2563eb !important;
    color: #ffffff !important;
    border: none !important;
    box-shadow: none !important;
    display: grid !important;
    place-items: center !important;
    text-align: center !important;
}
.login-sandbox-btn [data-testid="stButton"],
.login-sandbox-btn [data-testid="stButton"] > div,
.login-sandbox-btn button > div,
.login-sandbox-btn button p,
.login-sandbox-btn button span {
    width: 100% !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    text-align: center !important;
}
.login-sandbox-btn button:hover {
    background: #1d4ed8 !important;
    box-shadow: none !important;
    transform: none !important;
}
.login-sandbox-btn button p { color: #ffffff !important; width: 100% !important; text-align: center !important; margin: 0 !important; }
.login-divider hr { border-top: 1px solid #1e293b !important; }
.login-divider span { color: #94a3b8 !important; }

/* HR */
hr { border-color: #1e293b !important; }

/* Caption */
[data-testid="stCaptionContainer"] p { color: #64748b !important; }

/* Toast */
[data-testid="stToast"], div[data-testid="stToast"] > div {
    background: #1a1f2e !important;
    color: #e0e0e0 !important;
    border: 1px solid #334155 !important;
}

/* Tooltip */
[data-baseweb="tooltip"] {
    background: #1a1f2e !important;
    color: #e0e0e0 !important;
    border: 1px solid #334155 !important;
    box-shadow: none !important;
}

/* Select dropdown */
[data-baseweb="select"] > div {
    background: #0f1117 !important;
    border-color: #334155 !important;
    color: #e0e0e0 !important;
}

/* Scrollbar */
::-webkit-scrollbar { width: 6px !important; height: 6px !important; }
::-webkit-scrollbar-track { background: #0f1117 !important; }
::-webkit-scrollbar-thumb { background: #334155 !important; border-radius: 4px !important; }
::-webkit-scrollbar-thumb:hover { background: #475569 !important; }

/* Glow text removed */
.glow-text { text-shadow: none !important; color: #ffffff !important; }

/* Pipeline scroll buttons (kept compact, neutral colors) */
.pipeline-scroll button {
    background: #161b2b !important;
    border: 1px solid #1e293b !important;
    color: #cbd5e1 !important;
}
.pipeline-scroll button:hover {
    background: rgba(59,130,246,0.1) !important;
    border-color: #3b82f6 !important;
    color: #ffffff !important;
}
.pipeline-scroll button[kind="primary"] {
    background: #2563eb !important;
    border: none !important;
    color: #ffffff !important;
    box-shadow: none !important;
}
.pipeline-scroll button[kind="primary"]:hover {
    background: #1d4ed8 !important;
    box-shadow: none !important;
}
.pipeline-scroll button[kind="primary"] p { color: #ffffff !important; }

/* Scan scroll: replace neon green */
.scan-scroll [data-testid="stCheckbox"] label { color: #3b82f6 !important; }
.scan-scroll .cond-num { color: #3b82f6 !important; }
.scan-scroll .pa-section { color: #94a3b8 !important; }

/* â•â•â•â• My Pipeline header fixed at top:12px, 36px tall, aligned with blue X â•â•â•â• */
.pa-pipe-dash {
    position: fixed;
    top: 0;
    left: var(--pa-sidebar-w);
    right: 0;
    z-index: 9000;
    min-height: 56px;
    height: auto;
    background: #0f1117;
    border-bottom: 1px solid #334155;
    padding: 8px 16px 8px 72px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.6);
    display: flex;
    align-items: center;
    align-content: flex-start;
    flex-wrap: wrap;
    gap: 8px 14px;
    overflow: visible;
    white-space: normal;
    min-width: 0;
    box-sizing: border-box;
}
/* Backdrop fills the full header height as it wraps */
.pa-pipe-dash::before {
    content: '';
    position: absolute;
    inset: 0;
    background: #0f1117;
    z-index: -1;
}
body.pa-sidebar-hidden .pa-pipe-dash { left: 0; padding-left: 72px; }
@media (max-width: 768px) {
    .pa-pipe-dash { left: var(--pa-sidebar-w); right: 0; padding-left: 58px; }
    body.pa-sidebar-hidden .pa-pipe-dash { left: 0; padding-left: 58px; }
}
@media (max-width: 480px) {
    .pa-pipe-dash { left: var(--pa-sidebar-w); right: 0; padding-left: 58px; }
    body.pa-sidebar-hidden .pa-pipe-dash { left: 0; padding-left: 58px; }
}
.pa-pipe-dash-title {
    font-size: 11px; font-weight: 700; color: #3b82f6;
    text-transform: uppercase; letter-spacing: 1.2px;
    border-left: 2px solid #3b82f6; padding-left: 8px;
    flex-shrink: 0;
}
.pa-pipe-dash-meta {
    font-size: 10px; color: #94a3b8; font-weight: 500;
    margin-left: auto;
    flex-shrink: 0;
}
.pa-pipe-dash-row {
    display: flex; gap: 4px; align-items: center;
    flex: 1 1 auto;
    flex-wrap: wrap;
    min-width: 0;
    overflow: visible;
    scrollbar-width: thin;
}
.pa-pchip {
    display: inline-flex; align-items: baseline; gap: 4px;
    padding: 1px 8px;
    background: rgba(255,255,255,0.03);
    border: 1px solid #1e293b;
    border-radius: 4px;
    transition: background 0.12s, border-color 0.12s;
    line-height: 1.4;
    flex: 0 0 auto;
    white-space: nowrap;
}
.pa-pchip:hover {
    background: rgba(59,130,246,0.06);
    border-color: var(--c, #3b82f6);
}
.pa-pchip-n {
    font-size: 12px; font-weight: 700;
    font-family: 'Segoe UI', sans-serif;
}
.pa-pchip-l {
    font-size: 9px; color: #94a3b8;
    text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600;
}
.pa-pipe-dash-bar {
    height: 4px; width: 120px; max-width: 12vw; background: #1e293b; border-radius: 2px;
    overflow: hidden; display: flex;
    flex: 0 1 120px;
}
.pa-pipe-dash-bar > div { height: 100%; transition: width 0.3s; }
/* Push main content down so it starts below the fixed header bar */
[data-testid="stMain"] .block-container,
[data-testid="stAppViewContainer"] .main .block-container {
    padding-top: 60px !important;
}
@media (max-width: 1280px) {
    [data-testid="stMain"] .block-container,
    [data-testid="stAppViewContainer"] .main .block-container {
        padding-top: 92px !important;
    }
}
@media (max-width: 900px) {
    [data-testid="stMain"] .block-container,
    [data-testid="stAppViewContainer"] .main .block-container {
        padding-top: 116px !important;
    }
    .pa-pipe-dash-title {
        flex-basis: calc(100% - 160px);
    }
}

/* â•â•â•â• Dense loan table Tax-Delinquencies row density (~22px each) â•â•â•â• */
.pa-loan-row {
    background: #1a1f2e !important;
    border-radius: 0 !important;
    border-bottom: 1px solid #1e293b !important;
    line-height: 1.2 !important;
}
.pa-loan-row:hover { background: #1e2532 !important; }
/* Pipeline action row compact buttons & selects */
.pipeline-scroll [data-testid="stButton"] > button[data-testid*="open_"],
.pipeline-scroll [data-testid="stButton"] > button[data-testid*="notesbtn_"],
.pipeline-scroll [data-testid="stButton"] > button[data-testid*="docsbtn_"] {
    font-size: 8px !important;
    padding: 0 4px !important;
    height: 14px !important;
    min-height: 14px !important;
    line-height: 1 !important;
}
.pipeline-scroll [data-testid="stSelectbox"] select,
.pipeline-scroll [data-testid="stSelectbox"] > div > div {
    font-size: 10px !important;
    min-height: 22px !important;
    height: 22px !important;
    padding: 1px 6px !important;
}
.pipeline-scroll [data-testid="stSelectbox"] { margin-bottom: 0 !important; }
.pipeline-scroll [data-testid="stButton"] { margin-bottom: 0 !important; }
.pipeline-scroll [data-testid="stVerticalBlock"] > [data-testid="stVerticalBlockBorderWrapper"],
.pipeline-scroll [data-testid="stVerticalBlock"] > div { gap: 2px !important; }


.pipeline-scroll [data-testid="stVerticalBlockBorderWrapper"] {
    padding: 2px 6px !important;
    margin-bottom: 2px !important;
    min-height: 0 !important;
    max-height: none !important;
    overflow: visible !important;
    line-height: 1.1 !important;
    border-radius: 0 !important;
}
.pipeline-scroll [data-testid="stVerticalBlock"] { gap: 4px !important; }
.pipeline-scroll [data-testid="stHorizontalBlock"] {
    gap: 4px !important;
    margin-bottom: 0 !important;
    align-items: center !important;
}
.pipeline-scroll [data-testid="stMarkdownContainer"] p,
.pipeline-scroll [data-testid="stMarkdownContainer"] div {
    margin: 0 !important;
    padding: 0 !important;
    line-height: 1.2 !important;
}
.pipeline-scroll button {
    height: 24px !important;
    min-height: 24px !important;
    font-size: 10px !important;
    padding: 0 6px !important;
    line-height: 1 !important;
    border-radius: 0 !important;
}
.pipeline-scroll button p {
    font-size: 10px !important;
    line-height: 1 !important;
    margin: 0 !important;
}
.pipeline-scroll [data-testid="stSelectbox"] > div > div {
    min-height: 24px !important;
    height: 24px !important;
    font-size: 10px !important;
    padding: 0 6px !important;
    border-radius: 0 !important;
}
.pipeline-scroll [data-testid="stExpander"] summary {
    padding: 2px 8px !important;
    font-size: 10px !important;
    min-height: 0 !important;
}
.pipeline-scroll .pa-loan-grid {
    grid-template-columns: 90px 1fr 80px 130px 110px 50px 30px 20px !important;
    gap: 4px !important;
    font-size: 10px !important;
    line-height: 1.1 !important;
    margin-bottom: 2px !important;
}
.pipeline-scroll .loan-num,
.pipeline-scroll .loan-name { font-size: 11px !important; line-height: 1.2 !important; }
.pipeline-scroll .loan-due,
.pipeline-scroll .loan-missing { font-size: 9px !important; line-height: 1.1 !important; }
.pipeline-scroll .badge,
.pipeline-scroll .status-chip {
    font-size: 9px !important;
    padding: 1px 6px !important;
    line-height: 1.2 !important;
}
/* Loan-row widgets only (scoped by Streamlit key classes) */
[class*="st-key-open_"] button,
[class*="st-key-notesbtn_"] button,
[class*="st-key-docsbtn_"] button {
    height: 26px !important;
    min-height: 26px !important;
    font-size: 10px !important;
    padding: 0 6px !important;
    line-height: 1 !important;
    box-shadow: none !important;
    border-radius: 0 !important;
}
[class*="st-key-open_"] button p,
[class*="st-key-notesbtn_"] button p,
[class*="st-key-docsbtn_"] button p {
    font-size: 10px !important;
    line-height: 1 !important;
    margin: 0 !important;
}
[class*="st-key-st_"]:not([class*="st-key-st_yes_"]):not([class*="st-key-st_no_"]) [data-testid="stSelectbox"] > div > div,
[class*="st-key-assign_"] [data-testid="stSelectbox"] > div > div {
    height: 26px !important;
    min-height: 26px !important;
    font-size: 10px !important;
    padding: 0 6px !important;
    border-radius: 0 !important;
}
[class*="st-key-st_"]:not([class*="st-key-st_yes_"]):not([class*="st-key-st_no_"]) [data-baseweb="select"] > div,
[class*="st-key-assign_"] [data-baseweb="select"] > div {
    min-height: 26px !important;
    height: 26px !important;
    display: flex !important;
    align-items: center !important;
}
[class*="st-key-st_"]:not([class*="st-key-st_yes_"]):not([class*="st-key-st_no_"]) [data-baseweb="select"] span,
[class*="st-key-assign_"] [data-baseweb="select"] span {
    line-height: 1.2 !important;
}
[class*="st-key-st_"]:not([class*="st-key-st_yes_"]):not([class*="st-key-st_no_"]) [data-testid="stSelectbox"],
[class*="st-key-assign_"] [data-testid="stSelectbox"],
[class*="st-key-open_"] [data-testid="stButton"] {
    margin: 0 !important;
}
[class*="st-key-st_"]:not([class*="st-key-st_yes_"]):not([class*="st-key-st_no_"]) [data-testid="stElementContainer"],
[class*="st-key-assign_"] [data-testid="stElementContainer"],
[class*="st-key-open_"] [data-testid="stElementContainer"] {
    margin: 0 !important;
    padding: 0 !important;
}
[class*="st-key-open_"],
[class*="st-key-st_"]:not([class*="st-key-st_yes_"]):not([class*="st-key-st_no_"]),
[class*="st-key-assign_"] {
    margin: 0 !important;
    padding: 0 !important;
}
[class*="st-key-open_"] [data-testid="stButton"],
[class*="st-key-st_"]:not([class*="st-key-st_yes_"]):not([class*="st-key-st_no_"]) [data-testid="stSelectbox"],
[class*="st-key-assign_"] [data-testid="stSelectbox"],
[class*="st-key-st_"]:not([class*="st-key-st_yes_"]):not([class*="st-key-st_no_"]) [data-baseweb="select"],
[class*="st-key-assign_"] [data-baseweb="select"] {
    min-height: 26px !important;
    height: 26px !important;
    box-sizing: border-box !important;
}
[class*="st-key-st_"]:not([class*="st-key-st_yes_"]):not([class*="st-key-st_no_"]) [data-testid="stSelectbox"],
[class*="st-key-assign_"] [data-testid="stSelectbox"] {
    position: relative !important;
    top: 3px !important;
}
[class*="st-key-st_"]:not([class*="st-key-st_yes_"]):not([class*="st-key-st_no_"]) [data-baseweb="select"] > div,
[class*="st-key-assign_"] [data-baseweb="select"] > div {
    padding-top: 0 !important;
    padding-bottom: 0 !important;
}
/* Strict alignment only for the OPEN + Status + Assign row */
[data-testid="stHorizontalBlock"]:has([class*="st-key-open_"]):has([class*="st-key-assign_"]) {
    align-items: stretch !important;
}
[data-testid="stHorizontalBlock"]:has([class*="st-key-open_"]):has([class*="st-key-assign_"]) > [data-testid="column"] {
    display: flex !important;
    align-items: stretch !important;
}
[data-testid="stHorizontalBlock"]:has([class*="st-key-open_"]):has([class*="st-key-assign_"]) [data-testid="stVerticalBlock"] {
    gap: 0 !important;
}
[data-testid="stHorizontalBlock"]:has([class*="st-key-open_"]):has([class*="st-key-assign_"]) [data-testid="stElementContainer"] {
    margin: 0 !important;
    padding: 0 !important;
}
/* Keep only loan-row select labels hidden */
[class*="st-key-st_"]:not([class*="st-key-st_yes_"]):not([class*="st-key-st_no_"]) [data-testid="stWidgetLabel"],
[class*="st-key-assign_"] [data-testid="stWidgetLabel"] {
    display: none !important;
}

</style>

""", unsafe_allow_html=True)


# --- Custom sidebar toggle button (injected into parent DOM, survives reruns) ---
import streamlit.components.v1 as _components
_components.html("""
<script>
(function() {
  const doc = window.parent.document;
  const BTN_ID = 'pa-sidebar-toggle';
  const BODY_CLASS = 'pa-sidebar-hidden';
  const STORAGE_KEY = 'pa_sidebar_hidden';

  function applyState() {
    const hidden = localStorage.getItem(STORAGE_KEY) === '1';
    doc.body.classList.toggle(BODY_CLASS, hidden);
    const btn = doc.getElementById(BTN_ID);
    if (btn) btn.innerHTML = hidden ? '<span style="font-size:16px;line-height:1;">&#9776;</span><span style="font-size:7px;letter-spacing:0.6px;font-weight:800;display:block;margin-top:1px;">MENU</span>' : '&#10005;';
  }

  function sidebarExists() {
    return !!doc.querySelector('[data-testid="stSidebar"]');
  }

  function removeBtn() {
    const existing = doc.getElementById(BTN_ID);
    if (existing) existing.remove();
  }

  function inject() {
    if (!sidebarExists()) { removeBtn(); return; }
    if (doc.getElementById(BTN_ID)) { applyState(); return; }
    const btn = doc.createElement('button');
    btn.id = BTN_ID;
    btn.type = 'button';
    btn.title = 'Toggle sidebar';
    btn.onclick = function(e) {
      e.preventDefault();
      e.stopPropagation();
      const nowHidden = !doc.body.classList.contains(BODY_CLASS);
      localStorage.setItem(STORAGE_KEY, nowHidden ? '1' : '0');
      applyState();
    };
    doc.body.appendChild(btn);
    applyState();
  }

  inject();
  // Re-check on DOM mutations: add button if sidebar appeared, remove if it disappeared
  const obs = new MutationObserver(() => {
    if (sidebarExists() && !doc.getElementById(BTN_ID)) inject();
    else if (!sidebarExists() && doc.getElementById(BTN_ID)) removeBtn();
  });
  obs.observe(doc.body, { childList: true, subtree: true });
})();

// â”€â”€ Collapsible green H2 sections â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
(function() {
  const doc = window.parent.document;
  const STORAGE_PREFIX = 'pa_h2_collapsed_';

  // Walk up from h2 to find the stElementContainer ancestor
  function getContainer(h2) {
    let el = h2.parentElement;
    while (el && el !== doc.body) {
      if (el.dataset && el.dataset.testid === 'stElementContainer') return el;
      el = el.parentElement;
    }
    return h2.closest('[data-testid="stVerticalBlock"] > *') || h2.parentElement;
  }

  // Collect all sibling containers after `startEl` until the next one containing an h2
  function collectSiblings(startEl) {
    const out = [];
    let next = startEl.nextElementSibling;
    while (next) {
      if (next.querySelector('h2')) break;
      out.push(next);
      next = next.nextElementSibling;
    }
    return out;
  }

  function applyCollapse(h2, container, collapsed) {
    const sibs = collectSiblings(container);
    sibs.forEach(s => { s.style.display = collapsed ? 'none' : ''; });

    // Add/update chevron
    let chev = h2.querySelector('.pa-h2-chev');
    if (!chev) {
      chev = doc.createElement('span');
      chev.className = 'pa-h2-chev';
      chev.style.cssText = 'display:inline-block;margin-right:8px;font-size:0.65em;vertical-align:middle;user-select:none;transition:transform 0.2s;';
      h2.insertBefore(chev, h2.firstChild);
    }
    chev.textContent = collapsed ? '+' : '-';
  }

  function wireH2(h2) {
    if (h2._paWired) return;
    h2._paWired = true;
    h2.style.cursor = 'pointer';
    h2.title = 'Click to collapse/expand section';

    const container = getContainer(h2);
    const key = STORAGE_PREFIX + (h2.textContent || '').replace(/[+-]/g, '').trim().slice(0, 80);
    const collapsed = localStorage.getItem(key) === '1';
    applyCollapse(h2, container, collapsed);

    h2.addEventListener('click', function(e) {
      e.stopPropagation();
      const next = localStorage.getItem(key) !== '1';
      if (next) localStorage.setItem(key, '1');
      else localStorage.removeItem(key);
      applyCollapse(h2, container, next);
    });
  }

  function scan() {
    // Only target h2s in the MAIN content area, not sidebar
    const h2s = doc.querySelectorAll(
      '[data-testid="stAppViewContainer"] h2, [data-testid="stMain"] h2'
    );
    h2s.forEach(wireH2);
  }

  // Debounce MutationObserver to avoid thrashing
  let _scanTimer = null;
  function debouncedScan() {
    clearTimeout(_scanTimer);
    _scanTimer = setTimeout(scan, 300);
  }

  scan();
  const obs2 = new MutationObserver(debouncedScan);
  obs2.observe(doc.body, { childList: true, subtree: true });
})();
</script>
""", height=0)


# --- Session State Defaults ---
DEFAULTS = {
    "page": "dashboard",
    "authenticated": False,
    "user_id": None,
    "supabase_user_id": None,
    "user_email": "",
    "user_name": "",
    "user_role": "",
    "user_gemini_api_key": "",
    "sandbox_mode": False,
    "scan_results": None,
    "last_fetch_folder": "",
    "reader_folder": "",
    "reader_files": [],
    "reader_open_file": None,
    "reader_page": 1,
    "pipeline_add_open": False,
    "scroll_to": None,
    "dti_income": 0.0,
    "dti_debt": 0.0,
    "dti_housing": 0.0,
    "dti_source": "manual",
    "dti_confidence": "low",
    "cc_loan_amt": 0.0,
    "cc_property_val": 0.0,
    "cc_source": "manual",
    "cc_confidence": "low",
    "force_login": False,
}

# â”€â”€ Persist auth across browser refreshes â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
import json as _json_auth
_SESSION_FILE = os.path.join(os.path.dirname(__file__), ".session_cache.json")
_AUTH_KEYS = ["authenticated", "user_id", "supabase_user_id", "user_email", "user_name", "user_role", "sandbox_mode", "page"]

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


def _env_truthy(name: str, default: str = "1") -> bool:
    """Parse env flags like 1/true/yes/on."""
    return str(os.getenv(name, default)).strip().lower() in {"1", "true", "yes", "on"}


_AUTO_ENTER_SANDBOX = _env_truthy("PA_AUTO_ENTER_SANDBOX", "0")
_SCAN_HISTORY_FILE = os.path.join(os.path.dirname(__file__), "scan_history.json")
_SCAN_HISTORY_DAYS = 7


def _enter_sandbox(page: str = "dashboard") -> None:
    """Authenticate directly into local sandbox mode."""
    st.session_state.authenticated = True
    st.session_state.user_id = "sandbox"
    st.session_state.supabase_user_id = None
    st.session_state.user_email = "sandbox@demo"
    st.session_state.user_name = "Sandbox User"
    st.session_state.user_role = "Processor"
    st.session_state.sandbox_mode = True
    st.session_state.user_gemini_api_key = ""
    st.session_state.force_login = False
    st.session_state.page = page
    _save_session()


def _current_auth_user_key() -> str:
    """Stable per-user key for Supabase-stored settings."""
    return str(
        st.session_state.get("supabase_user_id")
        or st.session_state.get("user_id")
        or ""
    ).strip()


def _auth_user_key_candidates() -> list[str]:
    """Possible stable keys for this account, in preferred order."""
    raw = [
        st.session_state.get("supabase_user_id"),
        st.session_state.get("user_id"),
        st.session_state.get("user_email"),
    ]
    out = []
    seen = set()
    for value in raw:
        key = str(value or "").strip()
        if not key:
            continue
        lk = key.lower()
        if lk in seen:
            continue
        seen.add(lk)
        out.append(key)
    return out


def _save_user_gemini_key_for_account(gemini_key: str) -> dict:
    """Save Gemini key across user-key aliases to survive ID changes."""
    clean = str(gemini_key or "").strip()
    if not clean:
        return {"ok": False, "error": "Missing Gemini key."}
    try:
        import supabase_auth as _sa
    except Exception as e:
        return {"ok": False, "error": f"Supabase auth unavailable: {e}"}

    any_ok = False
    errors = []
    for user_key in _auth_user_key_candidates():
        try:
            result = _sa.save_user_gemini_key(user_key, clean)
            if result.get("ok"):
                any_ok = True
            else:
                errors.append(f"{user_key}: {result.get('error', 'save failed')}")
        except Exception as e:
            errors.append(f"{user_key}: {e}")
    if any_ok:
        return {"ok": True}
    if not errors:
        return {"ok": False, "error": "No account key available for save."}
    return {"ok": False, "error": " | ".join(errors)}


def _loan_user_keys(loan: dict) -> set[str]:
    keys = set()
    for field in ("owner_user_key", "created_by_user_key", "assigned_user_key"):
        value = str(loan.get(field) or "").strip()
        if value:
            keys.add(value)
    shared = loan.get("shared_with_user_keys", [])
    if isinstance(shared, str):
        try:
            import json as _json
            shared = _json.loads(shared)
        except Exception:
            shared = [shared]
    if isinstance(shared, list):
        keys.update(str(v).strip() for v in shared if str(v).strip())
    return keys


def _visible_account_loans(loans: list[dict]) -> list[dict]:
    """Sandbox sees demo loans; real accounts only see loans explicitly tied to them."""
    if st.session_state.get("sandbox_mode", False):
        return loans
    user_key = _current_auth_user_key()
    if not user_key:
        return []
    return [loan for loan in loans if user_key in _loan_user_keys(loan)]


def _stamp_current_user_on_loan(loan_id: int | dict, *, assigned: bool = False) -> None:
    user_key = _current_auth_user_key()
    if not user_key or st.session_state.get("sandbox_mode", False):
        return
    if isinstance(loan_id, dict):
        loan_id = loan_id.get("id")
    if not loan_id:
        return
    try:
        from crm import update_loan
        fields = {
            "owner_user_key": user_key,
            "created_by_user_key": user_key,
        }
        if assigned:
            fields["assigned_user_key"] = user_key
        update_loan(loan_id, **fields)
    except Exception:
        pass


def _scan_history_user_key() -> str:
    return _current_auth_user_key() or "anonymous"


def _load_scan_history_all() -> list[dict]:
    try:
        import json as _json
        with open(_SCAN_HISTORY_FILE, "r", encoding="utf-8") as f:
            data = _json.load(f)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _save_scan_history_all(items: list[dict]) -> None:
    try:
        import json as _json
        cutoff = time.time() - (_SCAN_HISTORY_DAYS * 86400)
        cleaned = [i for i in items if float(i.get("ts", 0) or 0) >= cutoff]
        cleaned = sorted(cleaned, key=lambda i: float(i.get("ts", 0) or 0), reverse=True)[:150]
        with open(_SCAN_HISTORY_FILE, "w", encoding="utf-8") as f:
            _json.dump(cleaned, f, indent=2, ensure_ascii=False, default=str)
    except Exception:
        pass


def _remember_scan_batch(batch: dict) -> None:
    if not isinstance(batch, dict):
        return
    entry = {
        "id": f"{int(time.time() * 1000)}_{abs(hash(str(batch.get('file', ''))))}",
        "ts": time.time(),
        "user_key": _scan_history_user_key(),
        "batch": batch,
    }
    items = _load_scan_history_all()
    sig = (entry["user_key"], batch.get("file"), batch.get("type"), str((batch.get("result") or {}).get("text_length", "")))
    kept = []
    for item in items:
        ib = item.get("batch") or {}
        isig = (item.get("user_key"), ib.get("file"), ib.get("type"), str((ib.get("result") or {}).get("text_length", "")))
        if isig != sig:
            kept.append(item)
    _save_scan_history_all([entry] + kept)


def _recent_scan_history() -> list[dict]:
    key = _scan_history_user_key()
    cutoff = time.time() - (_SCAN_HISTORY_DAYS * 86400)
    items = [
        i for i in _load_scan_history_all()
        if i.get("user_key") == key and float(i.get("ts", 0) or 0) >= cutoff and isinstance(i.get("batch"), dict)
    ]
    _save_scan_history_all(_load_scan_history_all())
    return sorted(items, key=lambda i: float(i.get("ts", 0) or 0), reverse=True)


def _normalize_contact_value(value) -> dict:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        text = value.strip()
        return {"name": text} if text else {}
    return {}


def _clean_display_text(value) -> str:
    text = str(value or "")
    replacements = {
        "": "·",
        "Â—": "-",
        "": "-",
        "": "-",
        "â†’": "->",
        "": "OK",
        "": "OK",
        "": "Error",
        "": "",
        "": "",
        "": "Warning",
        "": "Paused",
        "Â": "",
        "": "",
    }
    for bad, good in replacements.items():
        text = text.replace(bad, good)
    return " ".join(text.split())


def _user_trial_profile() -> dict:
    """Load/create app profile used for 14-day trial gating."""
    if not st.session_state.get("authenticated") or st.session_state.get("sandbox_mode"):
        return {}
    user_key = _current_auth_user_key()
    if not user_key:
        return {}
    try:
        import supabase_auth as _sa
        return _sa.ensure_user_profile(
            user_key,
            email=st.session_state.get("user_email", ""),
            display_name=st.session_state.get("user_name", ""),
            role=st.session_state.get("user_role", ""),
        )
    except Exception:
        return {}


def _trial_days_left(profile: dict) -> int:
    from datetime import datetime, timezone, date
    p = profile or {}
    # Prefer explicit trial_end_date if present
    end_date_str = str(p.get("trial_end_date") or "")
    if end_date_str:
        try:
            end = date.fromisoformat(end_date_str)
            return max(0, (end - date.today()).days)
        except Exception:
            pass
    # Fall back to trial_started_at + trial_days
    started = str(p.get("trial_started_at") or "")
    trial_days = int(p.get("trial_days") or 14)
    try:
        start_dt = datetime.fromisoformat(started.replace("Z", "+00:00"))
        if start_dt.tzinfo is None:
            start_dt = start_dt.replace(tzinfo=timezone.utc)
        used = (datetime.now(timezone.utc) - start_dt).days
        return max(0, trial_days - used)
    except Exception:
        return trial_days


def _has_paid_access(profile: dict) -> bool:
    status = str((profile or {}).get("subscription_status") or "").lower()
    if status in {"active", "paid", "beta_active"}:
        return True
    if status == "trialing":
        return _trial_days_left(profile) > 0
    return False


def _render_trial_gate(profile: dict) -> None:
    st.title("Trial Ended")
    st.markdown(
        """
        Your 14-day beta trial has ended. To keep using Processor Assistant, start the beta plan.

        Beta is **$49/mo** with a 14-day free trial.
        """
    )
    st.link_button("Start Beta Plan", "https://buy.stripe.com/bJe7sLdx87xM6mtaOSdfG00", type="primary")

    st.markdown("<div style='margin-top:24px;'></div>", unsafe_allow_html=True)
    with st.expander("Already paid with a different email?"):
        st.caption("Enter the exact email address you used when you paid on Stripe. We'll link that subscription to your account.")
        stripe_email = st.text_input("Stripe payment email", key="claim_stripe_email", placeholder="you@example.com")
        if st.button("Link My Subscription", key="claim_sub_btn"):
            user_key = st.session_state.get("user_key", "")
            if not stripe_email.strip():
                st.warning("Please enter your Stripe email.")
            elif not user_key:
                st.error("Could not detect your account. Try signing out and back in.")
            else:
                try:
                    import supabase_auth as _sa
                    result = _sa.claim_subscription_by_email(stripe_email.strip(), user_key)
                    if result.get("ok"):
                        st.success("Subscription linked! Reloading...")
                        st.rerun()
                    else:
                        st.error(result.get("error", "Could not link subscription."))
                except Exception as e:
                    st.error(f"Error: {e}")


# Keyword routing for condition responsibility.
# Checked top to bottom. Earlier entries win, so put narrow/specific keywords
# (like "copy of the appraisal invoice" → Processor) BEFORE broader ones
# (like "appraisal" → Appraiser). Same applies to borrower-action overrides:
# "proof of paid appraisal" lands in Borrower's list, not Appraiser.
_PARTY_KEYWORDS_THIRD_PARTY = [
    # Highest precedence: explicit borrower-paid receipts (must come first so
    # "appraisal" doesn't shunt them to Appraiser).
    ("Borrower", [
        "proof of paid", "proof of pay", "paid by borrower",
        "borrower paid", "paid outside closing", " poc ", " poc.",
        "homebuyer education", "homebuyer class", "homebuyer course",
        "fannie mae class", "freddie mac class", "fnma class", "fhlmc class",
        "framework class", "counseling certificate", "education certificate",
        "course completion",
    ]),
    # Loan-processor internal tasks (must come before Appraiser/Underwriter
    # so "copy of the appraisal invoice" routes here, not to Appraiser).
    ("Processor", [
        "copy of the appraisal invoice", "copy of the credit report invoice",
        "copy of the verification of employment invoice",
        "copy of the voe invoice", "copy of the invoice", "fee sheet",
        "broker to ", "broker has ", "fha case", "case number assignment",
        "case # transferred", "case transferred", "case query",
        "transferred to uwm", "sponsor id", "business tax id",
        "corp to obtain", "internal lock", "fha connection",
    ]),
    ("Appraiser", [
        "appraisal", "appraiser", "1004d", "1004 ", "1004-d",
        "property inspection", "property valuation", "final inspection",
        "ead portal", "appraisal logging", "appraisal condition",
        "successful submission report", "ssr",
    ]),
    ("Title", [
        "title commitment", "title search", "title review", "title insurance",
        "clear title", "title company", "settlement agent", "wiring instructions",
        "lien", "payoff statement", "payoff account", "estoppel", "survey",
        "alta", "cpl", "preliminary cd", "warranty deed", "deed of trust",
        "vesting", "security instrument",
    ]),
    ("Insurance", [
        "hazard insurance", "homeowner insurance", "homeowner's insurance",
        "homeowners insurance", "hoi policy", "hoi binder", "insurance binder",
        "hazard dec page", "declarations page", "flood certification",
        "flood determination", "wind coverage", "mortgagee clause",
        "dwelling coverage", "replacement cost",
    ]),
    ("Closer", [
        "closing disclosure", "final closing disclosure", "initial closing disclosure",
        "cd ", "closer ", "closing package", "lock desk", "ctc", "clear to close",
        "fund release", "wire authorization", "closing agent", "closer to confirm",
        "closer to provide",
    ]),
    ("Underwriter", [
        "underwriting review", "underwriter approval", "underwriter review",
        "compliance review", "lender requirements", "investor guidelines",
        "lqi report", "loan quality initiative", "second-level review",
        "slr ", "qc review", "quality control",
        "pmi approval", "pmi coverage", " pmi ", "mi approval", "mi coverage",
        "max interest rate", "interest rate not to exceed", "rate lock",
        "max piti", "max ltv", "max dti", "max cltv",
    ]),
    ("Employer", [
        "verbal verification of employment", "written verification of employment",
        "voe ", "wvoe", "verbal voe", "written voe", "employer verification",
        "employment confirmation", "current voe", "employer to confirm",
    ]),
    ("Realtor", [
        "purchase contract", "purchase agreement", "sales agreement",
        "realtor", "listing agent", "selling agent", "buyer's agent",
        "seller's agent", "real estate agent", "real estate certification",
        "arm's length affidavit", "required parties sign",
    ]),
    ("Seller", [
        "seller to provide", "seller's closing", "seller credit",
        "seller concession", "seller contribution", "seller signature",
    ]),
]

_PARTY_KEYWORDS_BORROWER_ACTION = [
    # Pure borrower-only actions: sign, provide income/asset proof, explain.
    "missing signature", "sign document", "sign disclosure",
    "provide paystub", "provide pay stub", "provide bank statement",
    "provide tax return", "provide w-2", "provide w2", "missing w-2",
    "missing 1040", "provide 1040", "provide 1099", "provide ssa",
    "provide social security", "verify employment",
    "provide income verification", "provide asset", "provide gift letter",
    "borrower consent", "borrower authorization", "borrower acknowledgment",
    "provide id", "provide identification", "provide driver's license",
    "missing disclosure", "provide explanation letter", "letter of explanation",
    "debt verification needed", "income verification needed",
    "asset documentation needed", "motivation letter", "gift funds",
    "earnest money", "name affidavit", "aka",
]


def _infer_condition_party(desc: str) -> str:
    """Infer responsible party from condition text using layered keyword lists.

    Order:
      1. Third-party document/action keywords win first (Title, Appraiser, etc.)
      2. Borrower-action keywords → Borrower
      3. Fall through to Borrower as default
    """
    text = str(desc or "").lower()

    # Step 1: third-party / non-borrower routing
    for party, keywords in _PARTY_KEYWORDS_THIRD_PARTY:
        if any(k in text for k in keywords):
            return party

    # Step 2: explicit borrower-action signals
    if any(k in text for k in _PARTY_KEYWORDS_BORROWER_ACTION):
        return "Borrower"

    # Step 3: default
    return "Borrower"


def _normalize_scanned_conditions(raw_conditions) -> list[dict]:
    """Convert extractor output into UI condition rows."""
    rows = []
    if isinstance(raw_conditions, list):
        source = raw_conditions
    elif isinstance(raw_conditions, str):
        if "No specific conditions found in this document" in raw_conditions:
            return []
        source = []
        for line in raw_conditions.splitlines():
            line = line.strip()
            if not line or line.startswith("**") or line.startswith("```"):
                continue
            if any(skip in line for skip in (
                "Possible reasons:",
                "Raw text preview",
                "PDF may be a scanned image",
                "Conditions may use non-standard formatting",
                "This document type may not contain conditions",
                "If you see condition text above",
            )):
                continue
            if line.startswith("|") and line.endswith("|"):
                parts = [p.strip() for p in line.strip("|").split("|")]
                if len(parts) >= 4 and parts[0] not in {"#", "---"} and not parts[0].startswith("-"):
                    source.append({
                        "num": parts[0],
                        "desc": parts[1],
                        "party": parts[2],
                        "status": parts[3],
                        "confidence": parts[4] if len(parts) >= 5 else "",
                    })
                continue
            cleaned = line.strip(" -*\t")
            if cleaned and "No specific conditions found" not in cleaned:
                source.append({"desc": cleaned})
    else:
        source = []

    for idx, item in enumerate(source):
        cond = dict(item) if isinstance(item, dict) else {"desc": str(item)}
        desc = (cond.get("desc") or cond.get("description") or "").strip()
        if not desc or desc.lower() in {"condition", "-----------"}:
            continue
        cond["num"] = str(cond.get("num") or idx + 1)
        cond["desc"] = desc
        # Always run keyword routing — the user's third-party / borrower-action
        # keyword lists are authoritative. Geminis party tag is too coarse
        # (it labels broker / lender internal items as Borrower).
        _routed = _infer_condition_party(desc)
        _gem_party = (cond.get("party") or "").strip()
        if _routed != "Borrower":
            cond["party"] = _routed  # keyword router found a strong third-party signal
        elif _gem_party and _gem_party != "Borrower":
            cond["party"] = _gem_party  # Gemini gave a non-Borrower hint, trust it
        else:
            cond["party"] = "Borrower"
        cond["status"] = cond.get("status") or "Needed"
        rows.append(cond)
    return rows


def _to_client_language(desc: str, party: str = "Borrower") -> str:
    """Rewrite underwriting condition text into borrower-friendly language."""
    text = _clean_condition_for_client(desc)
    if not text:
        return ""
    low = text.lower()

    if any(k in low for k in ["anti steering", "anti-steering"]):
        return "Please sign the attached anti-steering disclosure form."

    if ("fha connection" in low) or ("case query" in low) or ("case number assignment" in low):
        return "We are working on the FHA case assignment items needed for underwriting."

    if ("appraisal" in low) and ("ordered" in low or "amc" in low):
        return "The appraisal has been ordered. Watch for a link from a third party if payment is needed."

    if ("1004d" in low) or ("final inspection" in low) or ("upon completion of repairs" in low):
        return "We will need a final inspection (1004D) once the listed repairs are completed."

    if ("funds to close" in low) or ("reserves" in low) or ("sufficient funds" in low):
        return "Please send the most recent full bank statement showing the funds needed for closing and reserves. Include all pages, even blank pages."

    if ("paid in full" in low) and ("debt" in low or "credit" in low):
        return "Please send proof the listed debt has been paid in full, plus the account or bank statement showing where the payment came from."

    if "real estate certification" in low:
        return "Please have the required parties sign the Real Estate Certification or addendum so we can add it to the file."

    if "closing disclosure" in low:
        return "Please send the final seller Closing Disclosure once it is available."

    if "invoice" in low:
        if "appraisal" in low:
            return "Please send a copy of the appraisal invoice."
        if "credit report" in low:
            return "Please send a copy of the credit report invoice."
        if "voe" in low or "verification of employment" in low:
            return "Please send a copy of the verification of employment invoice."
        return "Please send a copy of the invoice."

    if ("earnest money" in low) or ("emd" in low):
        return "Please send a copy of the earnest money check and the full bank statement showing it cleared. Include all pages, even blank pages."

    if "bank statement" in low:
        return "Please send the full bank statement requested. Include all pages, even blank pages."

    if ("social security" in low) or (" ssn" in low) or ("w2" in low) or ("w-2" in low):
        return "Please send a copy of your Social Security card or your most recent W-2."

    if ("motivation letter" in low) or ("letter of motivation" in low):
        return "Please write a short letter explaining the reason for the change in housing/credit profile."

    if ("letter of explanation" in low) or ("loe" in low):
        if "signed" in low or "attach" in low:
            return "Please fill in and sign the attached letter of explanation."
        return "Please provide a short signed letter of explanation."

    if ("driver" in low and "license" in low) or ("government id" in low):
        return "Please provide a clear, unexpired copy of your driver's license."

    if ("homeowner" in low and "insurance" in low) or ("hazard insurance" in low) or ("hoi" in low):
        return "Please send your homeowner's insurance choice and your agent's contact info, and we will take it from there."

    if ("vom" in low) or ("verification of mortgage" in low):
        return "Please share contact information for your current or previous mortgage company so we can send the required form."

    if ("please sign" in low) and ("attached" in low):
        return "Please sign the attached form(s) and return them."

    if party in {"Borrower", "Co-Borrower"}:
        cleaned = text
        cleaned = re.sub(r"^(provide|borrower to provide|copy of)\s+", "", cleaned, flags=re.I).strip()
        if cleaned:
            cleaned = cleaned[0].lower() + cleaned[1:] if len(cleaned) > 1 else cleaned.lower()
            return f"Please send {cleaned}"
        return text
    return text


def _clean_condition_for_client(desc: str) -> str:
    """Remove condition IDs and lender notes before showing borrower-facing text."""
    text = " ".join(str(desc or "").split())
    if not text:
        return ""
    text = re.sub(r"\[[A-Z]{2,}-?\d+\]\s*", "", text)
    text = re.sub(r"\*\*?", " ", text)
    text = re.sub(r"\bHigh Confidence\b", "", text, flags=re.I)
    text = re.sub(r"\b\d{1,2}/\d{1,2}\s*-\s*not in upload\b.*", "", text, flags=re.I)
    text = re.sub(r"\b\d{1,2}/\d{1,2}\s*-\s*need\b", "Need", text, flags=re.I)
    text = re.sub(r"\s+\*", " ", text)
    text = re.sub(r"\s+", " ", text).strip(" -.;")
    return text


def _client_need_subject(desc: str) -> str:
    """Pick the bold topic for the client needs list."""
    text = _clean_condition_for_client(desc)
    low = text.lower()
    topic_rules = [
        ("Anti Steering", ["anti steering", "anti-steering"]),
        ("Lead Based Paint", ["lead based paint"]),
        ("FHA Connection", ["fha connection", "case query", "case number assignment"]),
        ("Appraisal", ["appraisal", "1004d", "final inspection", "amc"]),
        ("Earnest Money", ["earnest money"]),
        ("Funds to Close", ["funds to close", "reserves", "sufficient funds", "cash to close"]),
        ("Bank Statement", ["bank statement"]),
        ("SSN/W2", ["social security", " ssn", "w2", "w-2"]),
        ("Employment", ["employment", "pay stub", "paystub", "voe", "verification of employment"]),
        ("Homeowners Insurance", ["homeowner", "hazard insurance", "hoi", "insurance declaration"]),
        ("Driver's License", ["driver", "government id", "license"]),
        ("Letter of Explanation", ["letter of explanation", " loe", "signed letter"]),
        ("Motivation Letter", ["motivation letter", "letter of motivation"]),
        ("Real Estate Certification", ["real estate certification", "seller's real estate agent", "sellers agent"]),
        ("Closing Disclosure", ["closing disclosure", "seller cd", "final seller"]),
        ("Invoice", ["invoice"]),
        ("Tax Bill", ["tax bill"]),
        ("Payoff", ["payoff"]),
        ("Verification of Mortgage", ["verification of mortgage", " vom"]),
    ]
    for subject, needles in topic_rules:
        if any(n in low for n in needles):
            return subject

    candidate = re.split(r"\s+-\s+|:\s+", text, maxsplit=1)[0]
    candidate = re.sub(r"^(provide|copy of|borrower to provide)\s+", "", candidate, flags=re.I).strip()
    words = candidate.split()
    if len(words) > 6:
        candidate = " ".join(words[:6])
    return candidate or "Condition"


def _client_need_item(desc: str, party: str = "Borrower") -> tuple[str, str]:
    """Return subject-first borrower wording for the Client Needs List."""
    subject = _client_need_subject(desc)
    body = _to_client_language(desc, party)
    if not body:
        body = _clean_condition_for_client(desc)
    body = re.sub(r"^(please send|please provide)\s+", "", body, flags=re.I).strip()
    if body:
        body = body[0].upper() + body[1:]
    return subject, body


def _load_user_gemini_key_into_session(force: bool = False) -> str:
    """Load the signed-in user's Gemini key from Supabase into session state."""
    if st.session_state.get("sandbox_mode", False):
        st.session_state.user_gemini_api_key = ""
        return ""
    if st.session_state.get("user_gemini_api_key") and not force:
        return st.session_state.user_gemini_api_key

    user_keys = _auth_user_key_candidates()
    if not user_keys:
        st.session_state.user_gemini_api_key = ""
        return ""

    try:
        import supabase_auth as _sa
        loaded = ""
        for user_key in user_keys:
            loaded = _sa.load_user_gemini_key(
                user_key,
                user_email=str(st.session_state.get("user_email") or ""),
            )
            if loaded:
                break
        st.session_state.user_gemini_api_key = loaded
    except Exception:
        st.session_state.user_gemini_api_key = ""
    return st.session_state.user_gemini_api_key


def _complete_login_session(result: dict, *, sandbox_mode: bool = False, page: str = "dashboard") -> None:
    """Normalize all successful auth paths into one session update.
    If the user already has a saved Gemini key, default landing page becomes
    'pipeline' (skip the scanner/onboarding entry point) regardless of the
    caller's requested page."""
    st.session_state.authenticated = True
    st.session_state.user_id = result.get("user_id")
    st.session_state.supabase_user_id = result.get("supabase_user_id")
    st.session_state.user_email = result.get("email", "")
    st.session_state.user_name = result.get("display_name") or result.get("email", "user").split("@")[0]
    st.session_state.user_role = result.get("role", "Processor")
    st.session_state.sandbox_mode = sandbox_mode
    st.session_state.force_login = False
    st.session_state.user_gemini_api_key = ""
    _load_user_gemini_key_into_session(force=True)
    # Returning users with a saved Gemini key land on pipeline; new users go
    # to dashboard so they hit the onboarding wizard banner.
    if not sandbox_mode and st.session_state.get("user_gemini_api_key"):
        page = "pipeline"
    st.session_state.page = page
    _save_session()


_OAUTH_VERIFIER_CACHE: dict[str, tuple[str, float]] = {}


def _cache_oauth_verifier(flow_id: str, verifier: str) -> None:
    if not flow_id or not verifier:
        return
    now = time.time()
    _OAUTH_VERIFIER_CACHE[flow_id] = (verifier, now + 15 * 60)
    expired = [k for k, (_, exp) in _OAUTH_VERIFIER_CACHE.items() if exp < now]
    for k in expired:
        _OAUTH_VERIFIER_CACHE.pop(k, None)


def _pop_cached_oauth_verifier(flow_id: str) -> str:
    if not flow_id:
        return ""
    item = _OAUTH_VERIFIER_CACHE.pop(flow_id, None)
    if not item:
        return ""
    verifier, expires_at = item
    if expires_at < time.time():
        return ""
    return verifier


def _handle_google_oauth_callback() -> bool:
    """
    Process a Supabase OAuth callback if the app has been redirected back with
    a Google auth code.
    """
    _qp = st.query_params
    oauth_code = _qp.get("code", "")
    oauth_flow = _qp.get("pa_oauth_flow", "")
    oauth_verifier_qp = _qp.get("pa_oauth_v", "")
    oauth_error = _qp.get("error_description", "") or _qp.get("error", "")
    if isinstance(oauth_code, list):
        oauth_code = oauth_code[0] if oauth_code else ""
    if isinstance(oauth_flow, list):
        oauth_flow = oauth_flow[0] if oauth_flow else ""
    if isinstance(oauth_verifier_qp, list):
        oauth_verifier_qp = oauth_verifier_qp[0] if oauth_verifier_qp else ""
    if isinstance(oauth_error, list):
        oauth_error = oauth_error[0] if oauth_error else ""

    if oauth_error:
        st.session_state["oauth_error_message"] = str(oauth_error)
        st.query_params.clear()
        return False
    if not oauth_code:
        return False

    verifier = (
        st.session_state.get("oauth_google_verifier", "")
        or _pop_cached_oauth_verifier(str(oauth_flow))
        or str(oauth_verifier_qp or "")
    )

    try:
        import supabase_auth as _sa
        from db import upsert_oauth_user

        oauth_result = _sa.exchange_google_code(oauth_code, verifier)
        if not oauth_result.get("ok"):
            st.session_state["oauth_error_message"] = oauth_result.get("error", "Google sign-in failed.")
            st.query_params.clear()
            return False

        local_user = upsert_oauth_user(
            email=oauth_result.get("email", ""),
            display_name=oauth_result.get("display_name", ""),
            role=oauth_result.get("role", "Processor"),
            external_id=oauth_result.get("supabase_user_id", ""),
        )
        _complete_login_session(
            {
                "user_id": local_user.get("user_id"),
                "supabase_user_id": oauth_result.get("supabase_user_id"),
                "email": oauth_result.get("email", ""),
                "display_name": local_user.get("display_name") or oauth_result.get("display_name", ""),
                "role": local_user.get("role") or oauth_result.get("role", "Processor"),
            },
            sandbox_mode=False,
            page="dashboard",
        )
        try:
            _sa.accept_terms(
                _current_auth_user_key(),
                email=oauth_result.get("email", ""),
                display_name=local_user.get("display_name") or oauth_result.get("display_name", ""),
                role=local_user.get("role") or oauth_result.get("role", "Processor"),
            )
        except Exception:
            pass
        st.session_state.pop("oauth_google_verifier", None)
        st.session_state.pop("oauth_google_flow_id", None)
        st.session_state.pop("oauth_error_message", None)
        st.query_params.clear()
        st.rerun()
    except Exception as e:
        st.session_state["oauth_error_message"] = f"Google sign-in failed: {e}"
        st.query_params.clear()
    return False


def _render_gemini_key_prompt() -> None:
    """3-step onboarding wizard for new signed-in users without a Gemini key."""
    if not st.session_state.get("authenticated"):
        return
    if st.session_state.get("sandbox_mode", False):
        return
    if st.session_state.get("user_gemini_api_key"):
        return
    if st.session_state.get("gemini_onboarding_skipped"):
        return

    user_key = _current_auth_user_key()
    if not user_key:
        return

    step = int(st.session_state.get("gemini_onboarding_step", 1))

    def _go(n: int):
        st.session_state["gemini_onboarding_step"] = n
        st.rerun()

    # Step indicator
    _dots = ""
    for i in (1, 2, 3):
        _active = "#3b82f6" if i <= step else "#334155"
        _dots += f'<div style="width:32px;height:4px;border-radius:2px;background:{_active};"></div>'

    with st.container(border=True):
        st.markdown(
            f'<div style="display:flex;gap:6px;justify-content:center;margin-bottom:14px;">{_dots}</div>'
            f'<div style="text-align:center;font-size:11px;color:#94a3b8;margin-bottom:4px;letter-spacing:0.5px;">'
            f'STEP {step} OF 3</div>',
            unsafe_allow_html=True,
        )

        if step == 1:
            st.markdown("### Welcome to Processor Assistant")
            st.markdown(
                "Before you start, you'll need a **free Gemini 2.5 Flash API key** from Google. "
                "It's what powers document scanning, condition extraction, and contact pulls. "
                "Google gives generous free usage and the key takes about 60 seconds to set up."
            )
            st.caption("We save your key encrypted to your account — only you can see it.")
            c1, c2, c3 = st.columns([1, 1, 1])
            with c1:
                if st.button("Skip for now", use_container_width=True, key="gem_step1_skip"):
                    st.session_state["gemini_onboarding_skipped"] = True
                    st.rerun()
            with c2:
                if st.button("I already have a key", use_container_width=True, key="gem_step1_have"):
                    _go(3)
            with c3:
                if st.button("Let's set it up →", type="primary", use_container_width=True, key="gem_step1_next"):
                    _go(2)

        elif step == 2:
            st.markdown("### Get your free Gemini API key")
            st.markdown(
                "1. Click **Open Google AI Studio** below — opens in a new tab\n"
                "2. Sign in with the same Google account you just used\n"
                "3. Click **Create API key** → **Create API key in new project**\n"
                "4. Copy the key (starts with `AIza…`) and come back here"
            )
            st.link_button("Open Google AI Studio →", "https://aistudio.google.com/app/apikey", use_container_width=True)
            c1, c2 = st.columns([1, 1])
            with c1:
                if st.button("← Back", use_container_width=True, key="gem_step2_back"):
                    _go(1)
            with c2:
                if st.button("I have my key →", type="primary", use_container_width=True, key="gem_step2_next"):
                    _go(3)

        else:  # step 3
            st.markdown("### Paste your Gemini API key")
            with st.form("gemini_key_bootstrap_form"):
                gemini_key = st.text_input(
                    "Gemini API Key",
                    type="password",
                    placeholder="AIza...",
                    help="Starts with AIza. Get one at https://aistudio.google.com/app/apikey",
                )
                c1, c2 = st.columns([1, 1])
                with c1:
                    back = st.form_submit_button("← Back", use_container_width=True)
                with c2:
                    save_key = st.form_submit_button("Save & Continue", type="primary", use_container_width=True)
                if back:
                    _go(2)
                if save_key:
                    if not gemini_key.strip():
                        st.error("Please paste a Gemini API key first.")
                    elif not gemini_key.strip().startswith("AIza"):
                        st.warning("That doesn't look like a Gemini key (should start with 'AIza'). Save anyway?")
                        st.session_state.user_gemini_api_key = gemini_key.strip()
                    else:
                        try:
                            result = _save_user_gemini_key_for_account(gemini_key)
                            if result.get("ok"):
                                st.session_state.user_gemini_api_key = gemini_key.strip()
                                st.session_state.pop("gemini_onboarding_step", None)
                                st.success("Saved! You're all set.")
                                st.rerun()
                            else:
                                st.session_state.user_gemini_api_key = gemini_key.strip()
                                st.warning(f"Active for this session, but not saved: {result.get('error', 'Supabase save failed')}")
                                st.rerun()
                        except Exception as e:
                            st.session_state.user_gemini_api_key = gemini_key.strip()
                            st.warning(f"Active for this session. Supabase save failed: {e}")
                            st.rerun()


def _render_auth_debug():
    """Temporary on-screen auth state strip for troubleshooting."""
    try:
        auth = bool(st.session_state.get("authenticated", False))
        sandbox = bool(st.session_state.get("sandbox_mode", False))
        force_login = bool(st.session_state.get("force_login", False))
        page = st.session_state.get("page", "")
        user = st.session_state.get("user_id", None)
        st.markdown(
            f"""
            <div style="
                position: fixed;
                right: 14px;
                bottom: 12px;
                z-index: 999999;
                background: rgba(15,17,23,0.92);
                border: 1px solid #334155;
                color: #cbd5e1;
                padding: 6px 10px;
                border-radius: 8px;
                font-size: 11px;
                font-family: 'JetBrains Mono', monospace;
                box-shadow: 0 4px 12px rgba(0,0,0,0.35);
            ">
              auth={auth} | sandbox={sandbox} | force_login={force_login} | page={page} | user={user}
            </div>
            """,
            unsafe_allow_html=True,
        )
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
    _cdesc = _c.get("desc", "")
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
        f'<b style="color:#3b82f6;">#{_cnum}</b> {_cdesc}'
        f'<span style="color:#9ca3af;margin-left:8px;font-size:11px;">'
        f'{_cstat}</span></div>',
        unsafe_allow_html=True,
    )

    return (_chk, _cstat, _cparties)


def show_login_page():
    """Login / Signup page."""
    _oauth_error = st.session_state.pop("oauth_error_message", "")
    if _oauth_error:
        st.error(_oauth_error)

    # Push content down and center in a stable responsive wrapper
    st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)
    st.markdown("""
    <style>
    .login-page-wrap {
        width: min(720px, calc(100vw - 32px)) !important;
        max-width: 720px !important;
        margin-left: auto !important;
        margin-right: auto !important;
        padding-left: 16px !important;
        padding-right: 16px !important;
    }
    button[kind="primary"],
    div[data-testid="stButton"] > button,
    .stButton > button {
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        text-align: center !important;
    }
    button[kind="primary"] *,
    div[data-testid="stButton"] > button *,
    .stButton > button * {
        text-align: center !important;
        justify-content: center !important;
    }
    button[kind="primary"] > div,
    div[data-testid="stButton"] > button > div,
    .stButton > button > div {
        width: 100% !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        text-align: center !important;
    }
    div[data-testid="stButton"] > button div[data-testid="stMarkdownContainer"],
    div[data-testid="stButton"] > button p,
    .stButton > button p {
        width: 100% !important;
        display: block !important;
        text-align: center !important;
        margin: 0 !important;
    }
    </style>
    """, unsafe_allow_html=True)
    st.markdown('<div class="login-page-wrap">', unsafe_allow_html=True)

    st.markdown("""
    <div style="text-align:center;margin-bottom:24px;">
      <div style="display:inline-flex;align-items:center;justify-content:center;
           width:48px;height:48px;background:linear-gradient(135deg,#3b82f6,#1d4ed8);
           border-radius:12px;margin-bottom:12px;">
        <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
          <rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 21h8M12 17v4"/>
        </svg>
      </div>
      <div style="font-size:22px;font-weight:800;color:#ffffff;letter-spacing:-0.5px;line-height:1.1;">
        Processor Assistant
      </div>
      <div style="font-size:11px;color:#9ca3af;margin-top:5px;letter-spacing:0.3px;">
        ONLINE MORTGAGE PROCESSING
      </div>
    </div>
    """, unsafe_allow_html=True)

    if _env_truthy("PA_SHOW_SANDBOX", "0"):
        st.markdown('<div class="login-sandbox-btn">', unsafe_allow_html=True)
        if st.button("Try Sandbox - No Account Needed", type="primary", use_container_width=True):
            _enter_sandbox(page="pipeline")
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown(
            '<div style="text-align:center;font-size:10px;color:#9ca3af;margin-top:4px;margin-bottom:4px;">'
            'Full access - Docs not saved; non-sensitive data and recent scan history may persist</div>',
            unsafe_allow_html=True
        )

    st.markdown('<div style="margin:10px 0 8px 0;">', unsafe_allow_html=True)
    st.markdown(
        """
        <div style="background:rgba(15,23,42,0.72);border:1px solid rgba(59,130,246,0.22);
        border-radius:12px;padding:12px 14px;margin:10px 0;color:#cbd5e1;font-size:12px;line-height:1.45;">
          <b style="color:#fff;">Before you continue:</b> Processor Assistant uses AI to help read mortgage documents.
          AI can make mistakes. You are responsible for reviewing all extracted data, conditions, contacts, generated
          drafts, and compliance-related output before using it. Uploaded PDFs are processed for the scan; the app may
          save non-sensitive extracted fields, loan metadata, settings, and recent scan history for your account.
        </div>
        """,
        unsafe_allow_html=True,
    )
    accepted_terms = st.checkbox(
        "I understand this tool uses AI, outputs must be reviewed, and I agree to use it responsibly.",
        key="login_terms_ack",
        value=False,
    )
    try:
        import supabase_auth as _sa

        if _sa.is_configured():
            oauth_info = _sa.begin_google_oauth()
            if oauth_info.get("ok"):
                st.session_state["oauth_google_verifier"] = oauth_info["verifier"]
                st.session_state["oauth_google_flow_id"] = oauth_info.get("flow_id", "")
                _cache_oauth_verifier(str(oauth_info.get("flow_id", "")), oauth_info["verifier"])
                if accepted_terms:
                    st.markdown(
                        f"""
                        <a href="{oauth_info['url']}" target="_self" style="
                        display:flex;
                        width:100%;
                        align-items:center;
                        justify-content:center;
                        text-decoration:none;
                        padding:12px 14px;
                        border-radius:10px;
                        border:1px solid #334155;
                        background:#161b2b;
                        color:#ffffff;
                        font-weight:600;
                        margin-bottom:8px;
                    ">
                      Sign in with Google
                    </a>
                    """,
                        unsafe_allow_html=True,
                    )
                else:
                    st.button("Sign in with Google", disabled=True, use_container_width=True)
                    st.caption("Please accept the AI/review disclaimer to continue.")
            else:
                st.caption(oauth_info.get("error", "Google sign-in is unavailable right now."))
        else:
            st.caption("Google sign-in will appear automatically once Supabase OAuth is configured.")
    except Exception as e:
        st.caption(f"Google sign-in unavailable: {e}")
    st.markdown('</div>', unsafe_allow_html=True)
    return

    st.markdown("""
    <div class="login-divider">
      <hr/><span>or sign in with your account</span><hr/>
    </div>
    """, unsafe_allow_html=True)

    tab_login, tab_signup = st.tabs(["Login", "Sign Up"])

    with tab_login:
        with st.form("login_form"):
            email = st.text_input("Email", placeholder="you@example.com")
            password = st.text_input("Password", type="password", placeholder="........")
            submitted = st.form_submit_button("Sign In", use_container_width=True, type="primary")
            if submitted and email and password:
                from db import login
                result = login(email, password)
                if result.get("success"):
                    _complete_login_session(result, sandbox_mode=False, page="dashboard")
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

    st.markdown("""
    <div style="text-align:center;margin-top:20px;font-size:10px;color:#d1d5db;">
      Online workspace &nbsp;-&nbsp; Secure access &nbsp;-&nbsp; Cloud AI ready
    </div>
    """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


def show_sidebar():
    """Sidebar navigation. Hide/show is handled by Streamlit's native collapse control
    (the chevron arrow in the sidebar header) pinned automatically, no JS needed."""
    with st.sidebar:
        user_name = st.session_state.get("user_name", "")
        user_role = st.session_state.get("user_role", "")
        is_sandbox = st.session_state.get("sandbox_mode", False)

        st.markdown(
            '<div style="padding:0 0 16px 0;margin:-30px 0 0 0;">'
            '<div style="font-size:18px;font-weight:800;color:var(--slate-900);letter-spacing:-0.3px;">'
            'Processor Assistant</div>'
            '</div>',
            unsafe_allow_html=True,
        )

        # â”€â”€ Who's logged in â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        if is_sandbox:
            st.markdown(
                '<div style="width:100%;display:flex;align-items:center;justify-content:center;'
                'text-align:center;margin:8px 0 12px 0;">'
                '<span style="display:block;width:100%;font-size:12px;color:#3b82f6;letter-spacing:1px;'
                'font-weight:600;text-transform:uppercase;text-align:center;">Sandbox Mode</span></div>',
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

        # â”€â”€ Email Watch live stats for badge â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        import email_watch as _ew
        _ew_status  = _ew.get_status()
        _ew_pending = _ew_status["pending_count"]
        _ew_running = _ew_status["running"]
        _ew_dot     = "ON" if _ew_running else "OFF"
        _ew_badge   = f" ({_ew_pending})" if _ew_pending else ""

        # â”€â”€ Helper: nav button â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        def _nav_btn(label, page_key, btn_key=None, indent=False):
            active = _current_page == page_key
            lbl = label
            cols = st.columns([1, 8]) if indent else None
            ctx = cols[1] if indent else st
            if ctx.button(lbl, key=btn_key or f"nav_{page_key}", use_container_width=True,
                          type=("primary" if active else "secondary")):
                st.session_state.page = page_key
                _save_session()
                st.rerun()

        # â”€â”€ Collapsible section helper â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        def _section_header(label, state_key, default_open=False, divider=True):
            if state_key not in st.session_state:
                st.session_state[state_key] = default_open
            if divider:
                st.markdown("---")
            is_open = st.session_state[state_key]
            chev = "-" if is_open else "+"
            if st.button(f"{chev} {label.upper()}", key=f"_sec_{state_key}",
                         use_container_width=True,
                         help=f"Click to {'collapse' if is_open else 'expand'}"):
                st.session_state[state_key] = not is_open
                st.rerun()
            return st.session_state[state_key]

        # â•â•â•â•â•â•â•â•â•â•â• PRIMARY NAV: Scanner + Pipeline (always visible) â•â•â•â•â•â•â•
        _nav_btn("Scanner",  "dashboard")
        _nav_btn("Pipeline", "pipeline")
        _nav_btn("Pricing",  "pricing")

        # â•â•â•â•â•â•â•â•â•â•â• WORKSPACE: Reader / Email Watch / Team / Billing â•â•â•â•â•â•â•â•
        if _section_header("Workspace", "_sec_open_workspace", default_open=False):
            _nav_btn("Reader", "reader")

            # Email Watch with sub-nav
            _ew_pages   = ("email_watch", "email_watch_controls")
            _ew_active  = _current_page in _ew_pages
            _ew_top_lbl = f"{_ew_dot} Email Watch{_ew_badge}"
            if _ew_active:
                _ew_top_lbl = _ew_top_lbl
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
                for _sub_lbl, _sub_page in (("Controls", "email_watch_controls"),
                                            ("Results",  "email_watch")):
                    _sub_active = _current_page == _sub_page
                    _suffix = f"  ({_ew_pending})" if (_sub_page == "email_watch" and _ew_pending) else ""
                    _c_gutter, _c_btn = st.columns([1, 8])
                    with _c_btn:
                        if st.button(_sub_lbl + _suffix, key=f"nav_{_sub_page}",
                                     use_container_width=True,
                                     type=("primary" if _sub_active else "secondary")):
                            st.session_state.page = _sub_page
                            st.session_state["ew_nav_open"] = True
                            _save_session()
                            st.rerun()

            _nav_btn("Team",    "team")
            _nav_btn("Chat",    "chat")
            _nav_btn("Billing", "billing")
            if not is_sandbox:
                _nav_btn("History", "history")

        # â•â•â•â•â•â•â•â•â•â•â• TOOLS flat top-level collapses (no parent wrapper) â•â•â•
        if _section_header("Quick Tools", "_sec_open_quick", default_open=False):
            _nav_btn("Loan Snapshot",  "snapshot",      "nav_snapshot")
            _nav_btn("Report Issue",   "report_issue",  "nav_report_issue")
            _nav_btn("Missing Docs",   "missing_docs",  "nav_missing_docs")
            _nav_btn("Doc Expiry",     "doc_expiry",    "nav_doc_expiry")
            _nav_btn("Spanish Reply",  "spanish_reply", "nav_spanish")

        if _section_header("Advanced Tools", "_sec_open_advanced", default_open=False):
            _nav_btn("Income Verifier",    "income_verifier",    "nav_income_verifier")
            _nav_btn("Auto Data Entry",    "auto_data_entry",    "nav_auto_data_entry")
            _nav_btn("Credit Summary",     "credit_summary",     "nav_credit_summary")
            _nav_btn("DTI Calculator",     "dti_calculator",     "nav_dti_calculator")
            _nav_btn("Condition Clearer",  "condition_clearer",  "nav_condition_clearer")
            _nav_btn("Compliance Checker", "compliance_checker", "nav_compliance_checker")

        if _section_header("Pipeline Advanced", "_sec_open_pipeline", default_open=False):
            _nav_btn("Closing Package",  "closing_package",  "nav_closing_package")
            _nav_btn("Guideline Checker","guideline_checker","nav_guideline_checker")
            _nav_btn("Fraud Detector",   "fraud_detector",   "nav_fraud_detector")
            _nav_btn("Multi-Borrower",   "multi_borrower",   "nav_multi_borrower")
            _nav_btn("LOS Export",       "los_export",       "nav_los_export")

        if _section_header("Advanced Automation", "_sec_open_automation", default_open=False):
            _nav_btn("Rate Lock Monitor",     "rate_lock_monitor",     "nav_rate_lock_monitor")
            _nav_btn("Underwriting Tracker",  "underwriting_tracker",  "nav_underwriting_tracker")
            _nav_btn("Document Classifier",   "document_classifier",   "nav_document_classifier")
            _nav_btn("Escrow Calculator",     "escrow_calculator",     "nav_escrow_calculator")

        # â•â•â•â•â•â•â•â•â•â•â• SETTINGS â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
        if _section_header("Settings", "_sec_open_settings", default_open=False):
            # Quick Cloud AI status + toggle (no full-page navigation needed)
            try:
                import cloud_client as _sb_cc
                _sb_cfg = _sb_cc.get_config()
                _sb_has_key = bool(_sb_cfg.get("api_key"))
                _sb_on = bool(_sb_cfg.get("enabled")) and _sb_has_key
                if _sb_has_key:
                    _sb_provider = (_sb_cfg.get("provider") or "gemini").lower()
                    _sb_model = _sb_cfg.get("model") or ""
                    _provider_name = {"gemini": "Gemini", "claude": "Claude", "openai": "OpenAI"}.get(_sb_provider, _sb_provider.title())
                    _model_short = _sb_model.replace("gemini-", "").replace("claude-", "").replace("-latest", "")
                    _sb_label_text = f"{_provider_name} - {_model_short}" if _model_short else _provider_name
                    _sb_label = f"Cloud AI: {'ON' if _sb_on else 'OFF'} - {_sb_label_text}"
                    _sb_color = "#3b82f6" if _sb_on else "#9ca3af"
                    st.markdown(
                        f'<div style="font-size:11px;color:{_sb_color};margin:4px 0 6px 4px;font-weight:600;">'
                        f'{_sb_label}</div>',
                        unsafe_allow_html=True,
                    )
                    _sb_btn_label = "Turn Cloud AI OFF" if _sb_on else "Turn Cloud AI ON"
                    if st.button(_sb_btn_label, key="sb_cc_toggle", use_container_width=True, type="secondary"):
                        # Preserve provider/model on toggle; save_config backfills if either is blank
                        _sb_cc.save_config(not _sb_on, _sb_provider,
                                           _sb_cfg.get("api_key",""), _sb_model)
                        st.rerun()
                else:
                    st.markdown(
                        '<div style="font-size:11px;color:#9ca3af;margin:4px 0 6px 4px;">'
                        'Cloud AI: no key set</div>',
                        unsafe_allow_html=True,
                    )
            except Exception:
                pass

            if st.button("AI Settings (Claude / Gemini / OpenAI)", key="nav_ai_settings", use_container_width=True, type="secondary"):
                st.session_state.page = "ai_settings"
                _save_session()
                st.rerun()

        # Logout always visible
        st.markdown("---")
        if st.button("Logout", use_container_width=True):
            _clear_session()
            for key in DEFAULTS:
                st.session_state[key] = DEFAULTS[key]
            st.session_state.pop("oauth_google_verifier", None)
            st.session_state.pop("oauth_google_flow_id", None)
            st.session_state.force_login = True
            st.rerun()


def show_dashboard():
    """Compact document scanning page always auto-detect, additive scanning."""
    _BULK_DOC_TYPES = [
        "Approval Letter", "Loan Estimate (LE)",
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
    _recent_scans = _recent_scan_history()

    # â”€â”€ Header: hero when empty, compact when active â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    if not _has_batches and not _has_upload:
        _loan_ct = 0
        try:
            from crm import get_all_loans as _gl_hero
            _loan_ct = len(_visible_account_loans(_gl_hero()))
        except Exception:
            pass
        _user = st.session_state.get("user_name", "") or "there"
        st.markdown(
            f"""
            <div style="margin:4px 0 8px 0;padding:8px 12px;
                 background:#1a1f2e;border:1px solid #334155;border-radius:6px;
                 display:flex;align-items:center;gap:10px;">
              <div style="width:24px;height:24px;border-radius:4px;background:#2563eb;
                   display:flex;align-items:center;justify-content:center;flex-shrink:0;">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
                     stroke="#ffffff" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">
                  <rect x="3" y="4" width="18" height="16" rx="2"/>
                  <path d="M7 8h10M7 12h10M7 16h6"/>
                </svg>
              </div>
              <div style="font-size:13px;font-weight:600;color:#e0e0e0;flex:1;">
                Welcome back, {_user.split()[0] if _user else 'there'}.
                <span style="font-weight:400;color:#94a3b8;margin-left:6px;">Drop a loan doc to auto-detect & match.</span>
              </div>
              <div style="font-size:11px;color:#94a3b8;white-space:nowrap;">
                <b style="color:#3b82f6;">{_loan_ct}</b> in pipeline
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div style="display:flex;align-items:center;gap:10px;margin:4px 0 10px 0;">'
            '<div style="width:26px;height:26px;border-radius:7px;'
            'background:linear-gradient(135deg,#3b82f6,#1d4ed8);'
            'display:flex;align-items:center;justify-content:center;">'
            '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" '
            'stroke="#0a0a0a" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round">'
            '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M7 8h10M7 12h10M7 16h6"/>'
            '</svg></div>'
            '<div style="font-size:18px;font-weight:800;color:#ffffff;letter-spacing:-0.3px;">Scanner</div>'
            '</div>',
            unsafe_allow_html=True,
        )

    if _recent_scans:
        with st.expander(f"Recent Scans ({len(_recent_scans)} saved for 7 days)", expanded=False):
            for _hi, _entry in enumerate(_recent_scans[:20]):
                _hb = _entry.get("batch") or {}
                _hr = _hb.get("result") or {}
                _hcontacts = _hr.get("contacts", {}) if isinstance(_hr, dict) else {}
                _hcontact_count = len(_hcontacts) if isinstance(_hcontacts, dict) else 0
                _age_hours = int((time.time() - float(_entry.get("ts", 0) or 0)) / 3600)
                _age = f"{_age_hours}h ago" if _age_hours < 48 else f"{int(_age_hours / 24)}d ago"
                _hc1, _hc2 = st.columns([5, 1])
                with _hc1:
                    st.markdown(
                        f'<div style="font-size:12px;color:#e5e7eb;font-weight:600;">{_hb.get("file", "scan")}</div>'
                        f'<div style="font-size:11px;color:#9ca3af;">{_hb.get("type", "Document")} · {_hcontact_count} contact group(s) · {_age}</div>',
                        unsafe_allow_html=True,
                    )
                with _hc2:
                    if st.button("Restore", key=f"restore_scan_{_entry.get('id', _hi)}", use_container_width=True):
                        _restored = dict(_hb)
                        st.session_state.scan_batches.append(_restored)
                        st.toast(f"Restored {_restored.get('file', 'scan')}")
                        st.rerun()

    # â”€â”€ Gemini key warning (scanner needs it) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    if (not st.session_state.get("sandbox_mode", False)
            and not st.session_state.get("user_gemini_api_key")):
        _warn_c1, _warn_c2 = st.columns([4, 1])
        with _warn_c1:
            st.markdown(
                '<div style="background:rgba(245,158,11,0.1);border:1px solid rgba(245,158,11,0.4);'
                'border-radius:8px;padding:12px 14px;margin:8px 0;">'
                '<div style="font-size:13px;font-weight:700;color:#f59e0b;margin-bottom:4px;">'
                'Gemini API Key Required</div>'
                '<div style="font-size:12px;color:#fcd34d;line-height:1.5;">'
                'The scanner uses Gemini 2.5 Flash to read your documents. '
                'Add your free API key to start scanning — takes about 60 seconds.</div>'
                '</div>',
                unsafe_allow_html=True,
            )
        with _warn_c2:
            if st.button("Set up key →", type="primary", use_container_width=True, key="scanner_gem_setup"):
                st.session_state.pop("gemini_onboarding_skipped", None)
                st.session_state["gemini_onboarding_step"] = 1
                st.rerun()

    # â”€â”€ File uploader (additive) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    st.info(
        "Security note: uploaded PDFs are processed for this scan only and are not stored. "
        "The app may save non-sensitive extracted fields, loan metadata, and recent scan history for your signed-in account."
    )
    new_files = st.file_uploader(
        "Drop PDFs here - or click to browse" if not _has_upload else "Add more PDFs",
        type=["pdf"], accept_multiple_files=True,
        key="dash_uploader",
    )

    if new_files:
        import hashlib as _hashlib
        import re as _re
        import io as _io
        import pypdf as _pypdf
        from ai_engine import detect_doc_type as _detect, process_document as _proc

        # â”€â”€ Helper: extract grouping fingerprint from PDF bytes â”€â”€â”€â”€â”€â”€
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

                # Account number digits/dashes, often masked with X or *
                _acct = _re.search(r'(?:account\s*(?:number|#|no\.?)[:\s]*)([\dX*\-]{6,20})', _text, _re.I)
                if not _acct:
                    _acct = _re.search(r'(?:Primary account number[:\s]*)([\d\-]{6,20})', _text, _re.I)
                if not _acct:
                    # Last 4 shown as "...1234" or "ending in 1234"
                    _acct = _re.search(r'ending\s+in\s+(\d{4})', _text, _re.I)
                if _acct:
                    fp["account"] = _re.sub(r'[\s]', '', _acct.group(1)).upper()

                # Names ALL CAPS lines in first 40 lines (borrower name style)
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
                    r'(?:for\s+the\s+period|statement\s+period|period)[:\s]+(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})\s*(?:to|through|[-])\s*(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})',
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

        # â”€â”€ Duplicate detection (MD5) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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
                    st.warning(f"Identical file uploaded {len(_fidxs)}x: {', '.join(_dupe_fnames)} only the first will be scanned.")

        # â”€â”€ Auto-detect + fingerprint every file â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        # Order matters first match wins. Most-specific tokens first so
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
            # HOI last + tightened keywords "insurance dec" / "declarations"
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

        # â”€â”€ Page grouping: find files that belong together â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        # STRICT RULE: only suggest merge when files are clearly pages of the
        # SAME statement same period dates OR consecutive page X-of-Y numbering.
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
            """Both have periods but they differ definitely different months."""
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


        # â”€â”€ Pull approval conditions from already-scanned docs â”€â”€â”€â”€â”€â”€
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
                    _raw_conds = [ln.strip(" -\t") for ln in _raw_conds.splitlines() if ln.strip()]
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

        # â”€â”€ Missing pages analysis per statement â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        # For each uploaded bank statement, check if page sequence has gaps
        _missing_page_notices = []
        _bank_indices = [i for i, d in enumerate(_detections) if d["detected_type"] == "Bank Statement" and i not in _dupes]
        for _bi in _bank_indices:
            _fp = _fingerprints[_bi]
            if _fp["page_total"] and _fp["page_num"]:
                # We have one page of a multi-page statement check if others are present
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

        # â”€â”€ Show missing page warnings â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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

        # â”€â”€ Show approval cross-reference â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        if _approval_bank_conds and _bank_indices:
            st.markdown("---")
            st.markdown(
                f'<div style="background:rgba(59,130,246,0.1);border:1px solid rgba(59,130,246,0.3);border-radius:4px;'
                f'padding:8px 12px;margin-bottom:4px;font-size:12px;color:#3b82f6;">'
                f'<b>Approval cross-reference</b> from <i>{_approval_source}</i>:'
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
                        # no period detected count as 1 unknown
                        _uploaded_periods.add(("unknown", _fp["account"]))
                _months_have = len(_uploaded_periods)
                _ok = _months_have >= _months_req
                _icon = "" if _ok else ""
                _color = "#3b82f6" if _ok else "#ef4444"
                _bg = "rgba(59,130,246,0.1)" if _ok else "rgba(239,68,68,0.1)"
                _border = "rgba(59,130,246,0.3)" if _ok else "rgba(239,68,68,0.3)"
                _note = f"{_months_have} of {_months_req} month(s) uploaded" if not _ok else f"{_months_have} month(s) OK"
                st.markdown(
                    f'<div style="background:{_bg};border:1px solid {_border};border-radius:3px;'
                    f'padding:5px 10px;margin-bottom:4px;font-size:11px;color:{_color};">'
                    f'<b>{_icon}</b> {_ac[:120]} <span style="opacity:0.7;">{_note}</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )

        # â”€â”€ Show grouping suggestions â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        # Per-file checkboxes so user picks exactly which files to merge
        _merge_selections = {}  # group_id -> set of indices to include in merge
        if _groups:
            st.markdown("---")
            st.markdown("**Page grouping detected** select pages to merge:")
            for _gi, _grp in enumerate(_groups):
                _grp_type = _detections[sorted(_grp)[0]]["detected_type"]
                _rep_fp = _fingerprints[sorted(_grp)[0]]

                _match_reasons = []
                if _rep_fp["account"]:
                    _match_reasons.append(f"acct #{_rep_fp['account']}")
                if _rep_fp["period"]:
                    _match_reasons.append(f"{_rep_fp['period'][0]}{_rep_fp['period'][1]}")
                elif _rep_fp["names"]:
                    _match_reasons.append(_rep_fp["names"][0])
                _reason_str = "  ".join(_match_reasons) if _match_reasons else _grp_type

                st.markdown(
                    f'<div style="font-size:12px;font-weight:700;color:#3b82f6;margin-bottom:4px;">'
                    f'Group {_gi+1} {_grp_type} <span style="font-weight:400;color:#9ca3af;">({_reason_str})</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )
                _selected = set()
                for _idx in sorted(_grp, key=lambda i: _fingerprints[i]["page_num"] or 999):
                    _fp = _fingerprints[_idx]
                    _pg_label = f"pg {_fp['page_num']} of {_fp['page_total']}" if _fp["page_num"] else ""
                    _period_label = f"{_fp['period'][0]}{_fp['period'][1]}" if _fp["period"] else ""
                    _label_parts = [new_files[_idx].name]
                    if _pg_label: _label_parts.append(_pg_label)
                    if _period_label: _label_parts.append(_period_label)
                    _cb_label = "    ".join(_label_parts)
                    _checked = st.checkbox(_cb_label, value=True, key=f"dash_merge_{_gi}_{_idx}")
                    if _checked:
                        _selected.add(_idx)
                _merge_selections[_gi] = _selected

                if len(_selected) >= 2:
                    st.caption(f"Will merge {len(_selected)} file(s) into one PDF before scanning.")
                elif len(_selected) == 1:
                    st.caption("Only 1 file selected will scan individually.")
                else:
                    st.caption("No files selected group will be skipped.")
            st.markdown("---")

        # â”€â”€ File list with checkboxes, type dropdowns, delete â”€â”€â”€â”€â”€â”€â”€â”€
        # Visible (non-dupe) indices
        _visible = [_di for _di, _det in enumerate(_detections) if _di not in _dupes]

        # Check all / Uncheck all / Delete selected controls
        _sel_c1, _sel_c2, _sel_c3 = st.columns([1, 1, 2])
        with _sel_c1:
            if st.button("Check All", key="dash_check_all", use_container_width=True):
                for _vi in _visible:
                    st.session_state[f"dash_sel_{_vi}"] = True
                st.rerun()
        with _sel_c2:
            if st.button("Uncheck All", key="dash_uncheck_all", use_container_width=True):
                for _vi in _visible:
                    st.session_state[f"dash_sel_{_vi}"] = False
                st.rerun()
        with _sel_c3:
            if st.button("Delete Selected", key="dash_del_selected", use_container_width=True):
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
        st.markdown('<div class="pa-scan-detect-rows">', unsafe_allow_html=True)
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
                st.markdown(f'<div class="pa-scan-fname" style="font-size:12px;color:{_color};">{_det["name"]}</div>', unsafe_allow_html=True)
            with _c2:
                _ov = st.selectbox("Type", _BULK_DOC_TYPES, index=_didx, key=f"dash_type_{_di}", label_visibility="collapsed")
                _overrides[_di] = _ov
            with _c3:
                st.markdown(f'<div class="pa-scan-conf" style="font-size:11px;color:var(--slate-500);">{_det["confidence"]}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # â”€â”€ Scan button â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        _try_cloud = False
        try:
            import cloud_client as _dash_cc
            _try_cloud = _dash_cc.is_enabled()
        except Exception:
            pass

        _checked_visible = [_vi for _vi in _visible if st.session_state.get(f"dash_sel_{_vi}", True)]
        _scan_clicked = st.button(f"Scan with AI ({len(_checked_visible)} selected)" if _try_cloud else f"Scan ({len(_checked_visible)} selected)",
                                  key="dash_scan", type="primary", disabled=len(_checked_visible) == 0)
        if _scan_clicked:
            # Build the actual list of (bytes, name, type) to scan
            _scan_queue = []  # list of (pdf_bytes, display_name, doc_type)

            _merged_indices = set()
            for _gi, _grp in enumerate(_groups):
                _selected = _merge_selections.get(_gi, set())
                if len(_selected) >= 2:
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
                    _merged_indices.update(_selected)

            # Add remaining non-merged non-dupe checked files
            for _bi, _bf in enumerate(new_files):
                if _bi in _merged_indices or _bi in _dupes:
                    continue
                if not st.session_state.get(f"dash_sel_{_bi}", True):
                    continue
                _bf_type = _overrides.get(_bi, _detections[_bi]["detected_type"])
                _scan_queue.append((_file_bytes_cache[_bi], _bf.name, _bf_type))

            # â”€â”€ Cloud AI: auto-enable when cloud is on no consent prompt needed â”€
            _dash_cloud_doc_types = {"Purchase Contract", "Approval Letter"}
            _dash_user_approved_cloud = _try_cloud

            # Run scans
            from doc_verify import _match_borrower as _mb
            _sq_total = len(_scan_queue)
            _sq_progress = st.progress(0, text="Starting scan...")
            _provider_name = "AI"
            try:
                _provider_name = _dash_cc.get_config().get("provider", "AI").title()
            except Exception:
                pass
            for _sq_i, (_sq_bytes, _sq_name, _sq_type) in enumerate(_scan_queue):
                _sq_will_use_cloud = (_sq_type in _dash_cloud_doc_types and _dash_user_approved_cloud)
                _sq_status = (
                    f"Calling {_provider_name} for {_sq_name}... (2-5 sec)"
                    if _sq_will_use_cloud
                    else f"Scanning {_sq_i + 1} of {_sq_total}: {_sq_name}..."
                )
                _sq_progress.progress(
                    int((_sq_i / _sq_total) * 100),
                    text=_sq_status,
                )
                if _sq_type == "Unknown":
                    st.warning(f"{_sq_name}: Unknown type override the dropdown to scan")
                    continue
                _sq_approved = _dash_user_approved_cloud if _sq_type in _dash_cloud_doc_types else False
                if _sq_will_use_cloud:
                    with st.spinner(f"Sending {_sq_name} to {_provider_name} for AI extraction..."):
                        _result = _proc(_sq_bytes, _sq_type, user_approved_cloud=_sq_approved)
                else:
                    _result = _proc(_sq_bytes, _sq_type, user_approved_cloud=_sq_approved)
                # Safety net: for scanned Purchase Contracts, force one direct PDF-AI retry.
                if (
                    _result.get("success")
                    and _sq_type == "Purchase Contract"
                    and _result.get("image_only")
                ):
                    try:
                        import cloud_client as _cc_retry
                        if not _cc_retry.is_enabled():
                            _result["ai_log"] = "Cloud AI disabled or missing API key"
                        else:
                            _pc_data, _pc_log, _pc_text = _cc_retry.extract_purchase_contract_ai_from_pdf(_sq_bytes)
                            _result["ai_log"] = _pc_log or "PDF OCR returned no log"
                            if _pc_data:
                                _pc_contacts = {
                                    k: v for k, v in {
                                        "buyer": _pc_data.get("buyer", {}),
                                        "seller": _pc_data.get("seller", {}),
                                        "listing_agent": _pc_data.get("listing_agent", {}),
                                        "selling_agent": _pc_data.get("selling_agent", {}),
                                        "title": _pc_data.get("title", {}),
                                    }.items() if isinstance(v, dict) and v.get("name")
                                }
                                _result = {
                                    "success": True,
                                    "doc_type": _sq_type,
                                    "text_length": len(_pc_text or ""),
                                    "conditions": "",
                                    "bank_rules": "",
                                    "extracted_data": _pc_data,
                                    "contacts": _pc_contacts,
                                    "image_only": False,
                                    "ocr_via_cloud": True,
                                    "ai_log": _pc_log,
                                    "raw_text": (_pc_text or "")[:12000],
                                }
                            else:
                                _result["ai_log"] = f"{_pc_log or 'PDF OCR returned empty data'} | no fields extracted"
                    except Exception as _ocr_e:
                        _result["ai_log"] = f"PDF OCR exception: {type(_ocr_e).__name__}: {str(_ocr_e)[:160]}"
                if (
                    _result.get("success")
                    and _sq_type == "Purchase Contract"
                    and _result.get("image_only")
                    and not _result.get("ai_log")
                ):
                    _result["ai_log"] = f"PDF OCR retry skipped; cloud={bool(_try_cloud)} approved={bool(_sq_approved)}"
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
                    try:
                        from crm import get_all_loans as _match_all_loans
                        _visible_loans_for_match = _visible_account_loans(_match_all_loans())
                        _visible_ids = {l.get("id") for l in _visible_loans_for_match}
                    except Exception:
                        _visible_loans_for_match = []
                        _visible_ids = set()
                    if not _visible_loans_for_match or _loan_match.get("loan_id") not in _visible_ids:
                        _loan_match = {
                            "loan_id": None,
                            "loan_num": "",
                            "borrower": None,
                            "confidence": 0,
                            "suggestion": "unknown",
                            "suggested_folder": "",
                        }

                    _batch = st.session_state.scan_batches
                    _new_bidx = len(_batch)
                    _new_batch = {
                        "file": _sq_name,
                        "type": _sq_type,
                        "result": _result,
                        "loan_match": _loan_match,
                    }
                    _batch.append(_new_batch)
                    st.session_state.scan_batches = _batch
                    _remember_scan_batch(_new_batch)
                    if _result.get("image_only"):
                        st.warning(f"{_sq_name}: {_sq_type} - scanned image, logged without extraction")
                    else:
                        st.success(f"{_sq_name}: {_sq_type} OK")
                else:
                    st.error(f"{_sq_name}: {_result.get('error', 'Failed')}")
            _sq_progress.progress(100, text=f"Done - {_sq_total} document(s) scanned")

    # â”€â”€ Show completed scan results â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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
        # â”€â”€ Pagination â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        _PAGE_SIZE = 25
        _total_batches = len(st.session_state.scan_batches)
        _total_pages = max(1, (_total_batches + _PAGE_SIZE - 1) // _PAGE_SIZE)
        if "scan_page" not in st.session_state:
            st.session_state.scan_page = 0
        st.session_state.scan_page = min(st.session_state.scan_page, _total_pages - 1)

        if _total_pages > 1:
            _pg_cols = st.columns([1, 2, 1])
            with _pg_cols[0]:
                if st.button("Prev", key="scan_pg_prev", disabled=st.session_state.scan_page == 0):
                    st.session_state.scan_page -= 1; st.rerun()
            with _pg_cols[1]:
                st.markdown(f'<div style="text-align:center;font-size:12px;color:#9ca3af;padding-top:8px;">Page {st.session_state.scan_page+1} of {_total_pages} ({_total_batches} docs)</div>', unsafe_allow_html=True)
            with _pg_cols[2]:
                if st.button("Next", key="scan_pg_next", disabled=st.session_state.scan_page >= _total_pages - 1):
                    st.session_state.scan_page += 1; st.rerun()

        _page_start = st.session_state.scan_page * _PAGE_SIZE
        _page_end   = min(_page_start + _PAGE_SIZE, _total_batches)

        for _bidx, _batch in enumerate(st.session_state.scan_batches[_page_start:_page_end], start=_page_start):
            _r = _batch["result"]
            _raw_c = _r.get("conditions")
            _norm_conds = _normalize_scanned_conditions(_raw_c)
            _norm_cond_count = len(_norm_conds)
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
            try:
                _current_visible_loans = _visible_account_loans(_gl())
                _current_visible_ids = {l.get("id") for l in _current_visible_loans}
            except Exception:
                _current_visible_loans = []
                _current_visible_ids = set()
            if not _current_visible_loans or (_lm_loan_id and _lm_loan_id not in _current_visible_ids):
                _lm_suggestion = "unknown"
                _lm_borrower = ""
                _lm_loan_num = ""
                _lm_loan_id = None
                _lm_conf = 0

            def _create_pipeline_loan_from_scan() -> dict | None:
                _pcd = (_r.get("extracted_data") or {})
                _txn = _pcd.get("transaction", {}) if isinstance(_pcd, dict) else {}
                _pf_contacts = _r.get("contacts", {}) or {}
                _buyer = _pcd.get("buyer", {}) if isinstance(_pcd, dict) else {}
                _borrower = _buyer.get("name", "") if isinstance(_buyer, dict) else ""
                if not _borrower and isinstance(_pf_contacts, dict):
                    for _cv in _pf_contacts.values():
                        if isinstance(_cv, dict) and _cv.get("name"):
                            _borrower = _cv["name"]
                            break
                if not _borrower:
                    st.error("I parsed the document, but I do not have a borrower name to create the loan.")
                    return None
                _closing = (_txn.get("closing_date", "") if isinstance(_txn, dict) else "") or ""
                _new = _al(
                    loan_num=_r.get("loan_num", "") or "TBD",
                    borrower=_borrower,
                    status="Pending",
                    due_date=_closing,
                    missing_docs="",
                    folder_path="",
                    closing_date=_closing,
                    conditions=_normalize_scanned_conditions(_r.get("conditions", [])),
                    contacts=_pf_contacts,
                    created_by=st.session_state.get("user_name", ""),
                )
                _stamp_current_user_on_loan(_new, assigned=True)
                _la(_new["id"], "created", f"Loan created from scanned {_batch['type']}",
                    user=st.session_state.get("user_name", ""))
                return _new

            # Match badge for expander title
            if _lm_suggestion == "match":
                _match_badge = f" - Loan {_lm_loan_num} ({_lm_borrower})"
            elif _lm_suggestion == "possible":
                _match_badge = f" - Possible: {_lm_borrower}"
            else:
                _match_badge = " - No loan match"

            _del_col, _exp_col, _quick_col = st.columns([1, 8, 2])
            with _del_col:
                if st.button("X", key=f"ds_del_{_bidx}", help="Remove this scan result"):
                    st.session_state.scan_batches.pop(_bidx)
                    st.rerun()
            with _exp_col:
                _exp = st.expander(
                    f"OK {_batch['file']} - {_batch['type']} ({_norm_cond_count} cond){_match_badge}",
                    expanded=(_norm_cond_count > 0)
                )
            with _quick_col:
                if _lm_suggestion != "match":
                    if st.button("Start New Loan", key=f"ds_quick_new_{_bidx}", use_container_width=True):
                        _new_loan = _create_pipeline_loan_from_scan()
                        if _new_loan:
                            st.session_state.scan_batches.pop(_bidx)
                            st.session_state.page = "pipeline"
                            st.toast(f"Loan created for {_new_loan.get('borrower', '')}")
                        st.rerun()
            with _exp:
                # â”€â”€ AI usage badge + raw AI dump (debugging) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
                _r_ai_log = _r.get("ai_log", "")
                _r_ai_raw = _r.get("ai_raw")
                if _r_ai_log:
                    if "CLOUD" in _r_ai_log.upper():
                        st.markdown(
                            f'<div style="display:inline-block;padding:3px 10px;margin:4px 0 8px 0;'
                            f'background:rgba(59,130,246,0.12);border:1px solid rgba(59,130,246,0.4);'
                            f'border-radius:12px;font-size:11px;color:#3b82f6;font-weight:600;">'
                            f'Cloud AI - {_r_ai_log}</div>',
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(
                            f'<div style="display:inline-block;padding:3px 10px;margin:4px 0 8px 0;'
                            f'background:rgba(245,158,11,0.12);border:1px solid rgba(245,158,11,0.4);'
                            f'border-radius:12px;font-size:11px;color:#f59e0b;font-weight:600;">'
                            f'Warning - {_r_ai_log}</div>',
                            unsafe_allow_html=True,
                        )
                    if _r_ai_raw is not None and st.session_state.get("show_ai_debug", False):
                        with st.expander("Raw AI response (debug)", expanded=False):
                            st.json(_r_ai_raw)

                # â”€â”€ Loan match action row â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
                if _lm_suggestion == "match":
                    st.markdown(
                        f'<div style="background:rgba(59,130,246,0.1);border:1px solid rgba(59,130,246,0.3);border-radius:4px;'
                        f'padding:6px 10px;margin-bottom:8px;font-size:12px;color:#3b82f6;">'
                        f'<b>Matched:</b> Loan {_lm_loan_num} - {_lm_borrower} '
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
                                _new_conds = _normalize_scanned_conditions(_r.get("conditions", []))
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
                                # Purchase contract extras closing date, transaction data
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
                                    _msg = f"Purchase Contract merged contacts & dates updated"
                                else:
                                    _msg = f"{_batch['type']} scanned {_added} condition(s) merged"
                                _ul(_lm_loan_id, **_upd)
                                # Record the scan (metadata only no PDF stored)
                                _attach_doc(_lm_loan_id, _batch["file"], _batch["type"],
                                            extracted=_r.get("extracted_data"))
                                _la(_lm_loan_id, "upload", _msg, user=st.session_state.get("user_name", ""))
                                _toast_msg = f"Purchase Contract merged into Loan {_lm_loan_num}" if _batch["type"] == "Purchase Contract" else f"{_added} condition(s) merged into Loan {_lm_loan_num}"
                                st.toast(_toast_msg)
                elif _lm_suggestion == "possible":
                    st.markdown(
                        f'<div style="background:rgba(251,191,36,0.1);border:1px solid rgba(251,191,36,0.3);border-radius:4px;'
                        f'padding:6px 10px;margin-bottom:8px;font-size:12px;color:#fbbf24;">'
                        f'<b>Possible match:</b> {_lm_borrower} (Loan {_lm_loan_num}) '
                        f'<span style="opacity:0.7;">{_lm_conf}% confidence, verify before merging</span>'
                        f'</div>', unsafe_allow_html=True
                    )
                    _pa1, _pa2 = st.columns([1, 1])
                    with _pa1:
                        if st.button("Open & Verify", key=f"ds_popen_{_bidx}"):
                            st.session_state.pending_scan_merge = {
                                "loan_id": _lm_loan_id,
                                "batch_index": _bidx,
                                "file": _batch.get("file", ""),
                                "type": _batch.get("type", ""),
                                "result": _r,
                            }
                            st.session_state.detail_loan_id = _lm_loan_id
                            st.session_state.page = "loan_detail"
                            st.rerun()
                    with _pa2:
                        if st.button("Start New Loan Instead", key=f"ds_pnew_{_bidx}"):
                            _new_loan = _create_pipeline_loan_from_scan()
                            if _new_loan:
                                st.session_state.scan_batches.pop(_bidx)
                                st.session_state.page = "pipeline"
                                st.toast(f"Loan created for {_new_loan.get('borrower', '')}")
                            st.rerun()
                else:
                    # No match offer to start a new loan pre-filled from scan
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
                        _new_loan = _create_pipeline_loan_from_scan()
                        if _new_loan:
                            st.session_state.scan_batches.pop(_bidx)
                            st.session_state.page = "pipeline"
                            st.toast(f"Loan created for {_new_loan.get('borrower', '')}")
                        st.rerun()

                # â”€â”€ New loan form (shown when triggered) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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
                                loan_num=_nl_loannum or "TBD",
                                borrower=_nl_borrower,
                                status="Pending",
                                due_date=_nl_closing or "",
                                missing_docs="",
                                folder_path="",
                                closing_date=_nl_closing or "",
                                conditions=_normalize_scanned_conditions(_r.get("conditions", [])),
                                contacts=_pf_contacts,
                                created_by=st.session_state.get("user_name", ""),
                            )
                            _stamp_current_user_on_loan(_new_lid, assigned=True)
                            _la(_new_lid, "created", f"Loan created from scanned {_batch['type']}",
                                user=st.session_state.get("user_name", ""))
                            st.toast(f"Loan created for {_nl_borrower}")
                            st.session_state.pop(f"ds_start_new_{_bidx}", None)
                            st.rerun()

                # â”€â”€ Conditions (interactive, compact) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
                if _norm_cond_count:
                    st.markdown('<div class="scan-scroll">', unsafe_allow_html=True)
                    st.markdown('<div class="pa-section">Conditions</div>', unsafe_allow_html=True)
                    _PARTY_OPTS_SCAN = [
                        "Borrower", "Co-Borrower", "Title", "Realtor", "Seller",
                        "Processor", "Underwriter", "Jr Underwriter", "Loan Officer",
                        "Closer", "Insurance", "Appraiser", "Employer", "Manager",
                    ]
                    _COND_STATS_SCAN = ["Needed", "Requested", "Important", "Ready to Clear", "Cleared"]

                    def _infer_party(_desc: str) -> str:
                        # Use the global keyword router so Client Needs List filtering
                        # stays in lockstep with the per-condition party tags.
                        return _infer_condition_party(_desc or "")

                    _scan_fkey = f"scan_{_bidx}"

                    _SECTION_ORDER_SCAN = [
                        "Borrower", "Title", "Insurance", "Appraiser",
                        "Employer", "Realtor", "Seller", "Closer",
                        "Processor", "Underwriter",
                    ]
                    _SECTION_LABEL_SCAN = {
                        "Borrower": "Client Conditions",
                        "Title": "Title Conditions",
                        "Insurance": "Insurance Conditions",
                        "Appraiser": "Appraisal Conditions",
                        "Employer": "Employment Conditions",
                        "Realtor": "Realtor Conditions",
                        "Seller": "Seller Conditions",
                        "Closer": "Closer Conditions",
                        "Processor": "Processor Conditions",
                        "Underwriter": "Underwriting Conditions",
                    }
                    _SEND_LABEL_SCAN = {
                        "Borrower": "Send to Borrower",
                        "Title": "Send to Title",
                        "Insurance": "Send to Insurance",
                        "Appraiser": "Send to Appraisal",
                        "Employer": "Send to Employer",
                        "Realtor": "Send to Realtor",
                        "Seller": "Send to Seller",
                        "Closer": "Send to Closer",
                        "Processor": "Send to Processor",
                        "Underwriter": "Send to Underwriter",
                    }
                    _SECTION_CONTACT_KEYS_SCAN = {
                        "Borrower": ["borrower", "buyer", "co_borrower", "client"],
                        "Title": ["title", "title_company", "settlement_agent"],
                        "Insurance": ["insurance", "hoi", "hazard_insurance"],
                        "Appraiser": ["appraiser", "appraisal"],
                        "Employer": ["employer", "employment"],
                        "Realtor": ["selling_agent", "listing_agent", "realtor", "agent"],
                        "Seller": ["seller"],
                        "Closer": ["closer", "title", "settlement_agent"],
                        "Processor": ["processor", "loan_processor"],
                        "Underwriter": ["underwriter", "loan_officer"],
                    }

                    def _scan_contact_email_for_section(_section_party):
                        _contacts = _r.get("contacts", {}) if isinstance(_r, dict) else {}
                        if not isinstance(_contacts, dict):
                            return ""
                        for _key in _SECTION_CONTACT_KEYS_SCAN.get(_section_party, []):
                            _cv = _contacts.get(_key)
                            if isinstance(_cv, dict) and _cv.get("email"):
                                return _clean_display_text(_cv.get("email", ""))
                        return ""

                    def _scan_sections_for_condition(_cond):
                        _uid_local = f"{_scan_fkey}_{_cond.get('_scan_uid', _cond['num'])}"
                        _selected = st.session_state.get(f"{_uid_local}_party")
                        if isinstance(_selected, list):
                            _raw_parties = _selected
                        else:
                            _parsed = _cond.get("parties") or _cond.get("party") or _infer_party(_cond.get("desc", ""))
                            _raw_parties = _parsed if isinstance(_parsed, list) else [_parsed]

                        _aliases = {
                            "Buyer": "Borrower",
                            "Client": "Borrower",
                            "Co-Borrower": "Borrower",
                            "HOI": "Insurance",
                            "Hazard Insurance": "Insurance",
                            "Insurance Agent": "Insurance",
                            "Title Company": "Title",
                            "Escrow": "Title",
                            "Appraisal": "Appraiser",
                            "Jr Underwriter": "Underwriter",
                            "Loan Officer": "Underwriter",
                            "Manager": "Underwriter",
                        }
                        _sections = []
                        for _party in _raw_parties:
                            _party = _aliases.get(str(_party).strip(), str(_party).strip())
                            if _party in _SECTION_ORDER_SCAN and _party not in _sections:
                                _sections.append(_party)
                        return _sections or ["Borrower"]

                    _conds_by_section = {p: [] for p in _SECTION_ORDER_SCAN}
                    for _cond_idx, _cond in enumerate(_norm_conds):
                        _cond_uid = f"{_cond_idx}_{_cond.get('num', _cond_idx)}"
                        _sections = _scan_sections_for_condition(_cond)
                        _primary_section = _sections[0]
                        for _section in _sections:
                            _cond_view = dict(_cond)
                            _cond_view["_scan_uid"] = _cond_uid
                            _cond_view["_section_party"] = _section
                            _cond_view["_primary_section"] = _primary_section
                            _conds_by_section.setdefault(_section, []).append(_cond_view)

                    # Sort mode: "PDF order" (default) keeps conditions in scan order;
                    # "By party" groups them under section headers.
                    _scan_sort_key = f"{_scan_fkey}_cond_sort"
                    _sort_mode = st.session_state.get(_scan_sort_key, "PDF order")

                    _norm_conds_grouped = []
                    if _sort_mode == "By party":
                        for _party in _SECTION_ORDER_SCAN:
                            _section_conds = _conds_by_section.get(_party, [])
                            if _section_conds:
                                _norm_conds_grouped.append({"_section": _party, "_count": len(_section_conds)})
                                _norm_conds_grouped.extend(_section_conds)
                    else:
                        # PDF order: emit each condition once, in its original scan position,
                        # using its primary (first) section for the per-row party tag.
                        for _cond_idx, _cond in enumerate(_norm_conds):
                            _cond_uid = f"{_cond_idx}_{_cond.get('num', _cond_idx)}"
                            _sections = _scan_sections_for_condition(_cond)
                            _primary_section = _sections[0]
                            _cond_view = dict(_cond)
                            _cond_view["_scan_uid"] = _cond_uid
                            _cond_view["_section_party"] = _primary_section
                            _cond_view["_primary_section"] = _primary_section
                            _norm_conds_grouped.append(_cond_view)

                    # Sort row + Summarized toggle + always-on Client Needs List
                    _plain_map_key = f"{_scan_fkey}_plain_map"
                    _plain_sig_key = f"{_scan_fkey}_plain_sig"
                    _summary_key = f"{_scan_fkey}_summary_on"
                    _summary_map_key = f"{_scan_fkey}_summary_map"
                    _summary_sig_key = f"{_scan_fkey}_summary_sig"
                    _sort_c1, _sort_c2, _sort_c3 = st.columns([2.0, 1.4, 1.4])
                    with _sort_c2:
                        _summary_on = st.toggle(
                            "Summarized",
                            value=bool(st.session_state.get(_summary_key, False)),
                            key=f"{_summary_key}_toggle",
                            help="Bold subject + one short instruction per condition (Gemini)",
                        )
                        if _summary_on != bool(st.session_state.get(_summary_key, False)):
                            st.session_state[_summary_key] = _summary_on
                            st.rerun()
                    with _sort_c3:
                        _new_sort = st.selectbox(
                            "Sort", ["PDF order", "By party"],
                            index=0 if _sort_mode == "PDF order" else 1,
                            key=f"{_scan_sort_key}_select",
                            label_visibility="collapsed",
                        )
                        if _new_sort != _sort_mode:
                            st.session_state[_scan_sort_key] = _new_sort
                            st.rerun()

                    _originals = [str(c.get("desc", "")) for c in _norm_conds]
                    _plain_sig = "\n".join(_originals)
                    if (
                        not st.session_state.get(_plain_map_key)
                        or st.session_state.get(_plain_sig_key) != _plain_sig
                    ):
                        st.session_state[_plain_map_key] = {o: _to_client_language(o, "Borrower") for o in _originals}
                        st.session_state[_plain_sig_key] = _plain_sig

                    # When Summarized toggle is on and we don't have a cached map (or
                    # the underlying conditions changed), fetch summarized text from Gemini.
                    if _summary_on and st.session_state.get(_summary_sig_key) != _plain_sig:
                        _gem_key = st.session_state.get("user_gemini_api_key", "")
                        with st.spinner("Summarizing conditions..."):
                            try:
                                import cloud_client as _cc_sum
                                _summarized, _sum_log = _cc_sum.translate_conditions_to_summarized(_originals, api_key_override=_gem_key)
                                st.session_state[_summary_map_key] = dict(zip(_originals, _summarized))
                                st.session_state[_summary_sig_key] = _plain_sig
                            except Exception as _se:
                                st.warning(f"Could not summarize: {_se}")
                                st.session_state[_summary_map_key] = {}

                    def _needs_status_label(_raw_status: str) -> str:
                        s = str(_raw_status or "").strip().lower()
                        if s == "cleared":
                            return "Received"
                        if s in {"ready to clear", "requested"}:
                            return "Submitted"
                        return "Needed"

                    # Internal/third-party signals that should usually skip the
                    # Client Needs List. EXCEPT when the condition is asking the
                    # borrower to prove payment / show receipt (those are real
                    # borrower tasks, e.g. proof of paid appraisal, paid homebuyer
                    # education class invoice, etc.).
                    _CLIENT_NEEDS_SKIP = (
                        "fee sheet", "broker to ", "broker has ",
                        "fha case", "case query", "case number assignment",
                        "case # transferred", "case transferred",
                        "transferred to uwm", "sponsor id", "business tax id",
                        "corp to obtain", "internal lock", "fha connection",
                        "underwriter to obtain", "underwriter to review",
                        "lqi report", "loan quality initiative",
                        "mcr,", "pmi approval", "pmi coverage",
                        "max interest rate", "interest rate not to exceed",
                        "warranty deed", "security instrument", "title commitment",
                        "alta", "cpl,", "preliminary cd", "mortgagee clause",
                        "ssr ", "ead portal", "appraisal logging",
                    )
                    # If an "invoice" condition has any of these, it IS a borrower
                    # task — they need to provide proof of payment / participation.
                    _CLIENT_NEEDS_INVOICE_KEEP = (
                        "proof of pay", "proof of paid", "paid by borrower",
                        "borrower paid", "paid outside", "poc ", " poc.",
                        "receipt", "homebuyer education", "homebuyer class",
                        "homebuyer course", "fannie mae class", "freddie mac class",
                        "fnma class", "fhlmc class", "framework class",
                        "counseling certificate", "education certificate",
                        "course completion",
                    )

                    def _is_client_need_condition(_cond) -> bool:
                        _desc_l = str(_cond.get("desc", "")).lower()
                        # Invoice items: skip unless this is proof-of-payment / class receipt
                        if "invoice" in _desc_l:
                            if not any(k in _desc_l for k in _CLIENT_NEEDS_INVOICE_KEEP):
                                return False
                        elif any(skip in _desc_l for skip in _CLIENT_NEEDS_SKIP):
                            return False
                        _sections = _scan_sections_for_condition(_cond)
                        return "Borrower" in _sections

                    st.markdown('<div class="pa-section" style="margin-top:8px;">Client Needs List</div>', unsafe_allow_html=True)
                    import html as _html
                    _needs_rows = []
                    for _cond_idx, _cond in enumerate(_norm_conds):
                        _cond_uid = f"{_cond_idx}_{_cond.get('num', _cond_idx)}"
                        _cond_for_needs = dict(_cond)
                        _cond_for_needs["_scan_uid"] = _cond_uid
                        if not _is_client_need_condition(_cond_for_needs):
                            continue
                        _base_uid = f"{_scan_fkey}_{_cond_uid}"
                        _row_status = st.session_state.get(f"{_base_uid}_stat", _cond.get("status", "Needed"))
                        _status_label = _needs_status_label(_row_status)
                        _subject, _body = _client_need_item(str(_cond.get("desc", "")), "Borrower")
                        _needs_rows.append(
                            '<div class="pa-need-row">'
                            '<span class="pa-need-bullet">-</span>'
                            '<div>'
                            f'<span class="pa-need-subject">{_html.escape(_subject)}</span>'
                            f'<span class="pa-need-body"> - {_html.escape(_body)}</span>'
                            f'<span class="pa-need-status">{_html.escape(_status_label)}</span>'
                            '</div>'
                            '</div>'
                        )
                    if _needs_rows:
                        st.markdown('<div class="pa-needs-list">' + "".join(_needs_rows) + '</div>', unsafe_allow_html=True)
                        # Visual breathing room between the Client Needs List and
                        # the parsed conditions list below it.
                        st.markdown(
                            '<div style="height:28px;border-top:1px dashed rgba(255,255,255,0.08);margin:28px 0 12px 0;"></div>',
                            unsafe_allow_html=True,
                        )

                    for _c in _norm_conds_grouped:
                        if _c.get("_section"):
                            _section_party = _c["_section"]
                            _section_count = _c["_count"]
                            st.markdown(
                                f'<div class="pa-section" style="margin-top:12px;">'
                                f'{_SECTION_LABEL_SCAN.get(_section_party, _section_party + " Conditions")} '
                                f'<span style="color:#64748b;font-size:11px;font-weight:600;">'
                                f'{_section_count} item{"s" if _section_count != 1 else ""}</span></div>',
                                unsafe_allow_html=True,
                            )
                            continue
                        _section_party_for_row = _c.get("_section_party") or "Borrower"
                        _is_primary_row = _section_party_for_row == (_c.get("_primary_section") or _section_party_for_row)
                        _base_uid = f"{_scan_fkey}_{_c.get('_scan_uid', _c['num'])}"
                        _uid = f"{_base_uid}_{_section_party_for_row}"
                        with st.container(border=True):
                            _top1, _top2 = st.columns([0.35, 8])
                            with _top1:
                                _chk = st.checkbox("", value=False, key=f"{_uid}_chk",
                                                   label_visibility="collapsed")
                            with _top2:
                                _conf = (_c.get("confidence") or "").strip()
                                _conf_badge = (
                                    f' <span style="color:#93c5fd;font-size:10px;opacity:0.8;">{_conf}</span>'
                                    if _conf else ""
                                )
                                import html as _html
                                import re as _re_desc
                                _orig_desc = str(_c.get("desc", ""))
                                _pmap = st.session_state.get(_plain_map_key, {})
                                _client_desc = str(_pmap.get(_orig_desc) or _orig_desc)
                                _has_alt = bool(_client_desc and _client_desc != _orig_desc)
                                _primary_desc = _orig_desc
                                _secondary_desc = _client_desc
                                _primary_desc_html = _html.escape(_primary_desc)
                                _secondary_desc_html = _html.escape(_secondary_desc)
                                _secondary_label = "Client language"

                                # If Summarized toggle is on and we have a Gemini summary
                                # for this condition, render it INSTEAD of the original
                                # desc, with **bold** converted to HTML <b>.
                                if _summary_on:
                                    _smap = st.session_state.get(_summary_map_key, {})
                                    _sum_desc = str(_smap.get(_orig_desc) or "").strip()
                                    if _sum_desc:
                                        _esc = _html.escape(_sum_desc)
                                        # Convert **bold** to <b>bold</b>
                                        _primary_desc_html = _re_desc.sub(
                                            r"\*\*(.+?)\*\*",
                                            r"<b style='color:#ffffff;'>\1</b>",
                                            _esc,
                                        )

                                _desc_html = (
                                    f'<div style="font-size:13px;line-height:1.38;padding:1px 0 4px;">'
                                    f'<b style="color:#3b82f6;">#{_c["num"]}</b> '
                                    f'<span style="color:#e5e7eb;">{_primary_desc_html}</span>{_conf_badge}</div>'
                                )
                                if _has_alt:
                                    _desc_html += (
                                        f'<div style="font-size:11px;line-height:1.35;padding:0 0 5px 22px;'
                                        f'color:#94a3b8;"><b>{_secondary_label}:</b> {_secondary_desc_html}</div>'
                                    )
                                st.markdown(_desc_html, unsafe_allow_html=True)

                            _ctrl1, _ctrl2, _ctrl3 = st.columns([1.5, 3.4, 1.15])
                            with _ctrl1:
                                if _is_primary_row:
                                    _sidx = _COND_STATS_SCAN.index(_c["status"]) if _c["status"] in _COND_STATS_SCAN else 0
                                    _cstat = st.selectbox("Status", _COND_STATS_SCAN, index=_sidx,
                                                          key=f"{_base_uid}_stat", label_visibility="collapsed")
                                else:
                                    st.caption("Shared")
                            with _ctrl2:
                                if _is_primary_row:
                                    _default_parties = _scan_sections_for_condition(_c)
                                    _party_key = f"{_base_uid}_party"
                                    _current_parties = st.session_state.get(_party_key)
                                    if not isinstance(_current_parties, list):
                                        _current_parties = [p for p in _default_parties if p in _PARTY_OPTS_SCAN]
                                    if len(_current_parties) > 1:
                                        _party_cols = st.columns([3.4, 1])
                                        with _party_cols[1]:
                                            if st.button("Unselect All", key=f"{_base_uid}_party_clear",
                                                         use_container_width=True):
                                                st.session_state[_party_key] = []
                                                st.rerun()
                                        with _party_cols[0]:
                                            _cparties = st.multiselect(
                                                "Responsible parties", _PARTY_OPTS_SCAN,
                                                default=[p for p in _default_parties if p in _PARTY_OPTS_SCAN],
                                                key=_party_key, label_visibility="collapsed",
                                            )
                                    else:
                                        _cparties = st.multiselect(
                                            "Responsible parties", _PARTY_OPTS_SCAN,
                                            default=[p for p in _default_parties if p in _PARTY_OPTS_SCAN],
                                            key=_party_key, label_visibility="collapsed",
                                        )
                                else:
                                    st.caption(f"Also included in {_SECTION_LABEL_SCAN.get(_section_party_for_row, _section_party_for_row)}")
                            with _ctrl3:
                                if st.button("Guide", key=f"{_uid}_guide", use_container_width=True,
                                             help="Check vs. Fannie/Freddie guidelines"):
                                    st.session_state[f"{_uid}_guide_open"] = True
                                    st.session_state.pop(f"{_uid}_guide_results", None)

                        # â”€â”€ Guidelines panel (toggled by ) â”€â”€
                        if st.session_state.get(f"{_uid}_guide_open"):
                            _gc1, _gc2 = st.columns([9, 0.5])
                            with _gc2:
                                if st.button("Close", key=f"{_uid}_guide_close", help="Close"):
                                    for _k in (f"{_uid}_guide_open", f"{_uid}_guide_results"):
                                        st.session_state.pop(_k, None)
                                    st.rerun()
                            _gres = st.session_state.get(f"{_uid}_guide_results")
                            if _gres is None:
                                with st.spinner("Searching Fannie Mae & Freddie Mac"):
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
                                    f'border-radius:6px;margin:4px 0 4px 32px;">{_gres["error"]}</div>',
                                    unsafe_allow_html=True,
                                )
                            elif isinstance(_gres, list) and _gres:
                                for _gm in _gres[:4]:
                                    _src = _gm.get("source", "")
                                    _sec = _gm.get("section", "")
                                    _pg  = _gm.get("page", "")
                                    _sc  = _gm.get("score", 0)
                                    _ex  = (_gm.get("excerpt", "") or "").replace("\n", " ")[:360]
                                    _sec_part = f"  <b>{_sec}</b>" if _sec else ""
                                    st.markdown(
                                        f'<div style="font-size:11px;color:#e5e7eb;padding:6px 10px;margin:3px 0 3px 32px;'
                                        f'background:rgba(59,130,246,0.05);border-left:2px solid rgba(59,130,246,0.45);'
                                        f'border-radius:4px;">'
                                        f'<span style="color:#3b82f6;font-weight:700;">{_src}</span>'
                                        f'{_sec_part}'
                                        f' <span style="color:#9ca3af;">p.{_pg}  {_sc}% match</span><br/>'
                                        f'<span style="color:#cbd5e1;font-size:10.5px;">{_ex}</span>'
                                        f'</div>',
                                        unsafe_allow_html=True,
                                    )
                            elif isinstance(_gres, list):
                                st.markdown(
                                    '<div style="font-size:11px;color:#6b7280;padding:4px 0 4px 32px;">'
                                    'No relevant guideline sections found.</div>',
                                    unsafe_allow_html=True,
                                )

                    def _scan_condition_checked_for_section(_cond, _section_party):
                        _cond_key = _cond.get("_scan_uid", _cond["num"])
                        if st.session_state.get(f"{_scan_fkey}_{_cond_key}_{_section_party}_chk", False):
                            return True
                        if st.session_state.get(f"{_scan_fkey}_{_cond_key}_chk", False):
                            return True
                        for _party in _scan_sections_for_condition(_cond):
                            if st.session_state.get(f"{_scan_fkey}_{_cond_key}_{_party}_chk", False):
                                return True
                        return False

                    def _render_scan_email_draft(_draft_party):
                        _checked_for_email = [
                            c for c in _conds_by_section.get(_draft_party, [])
                            if _scan_condition_checked_for_section(c, _draft_party)
                        ]
                        _group_to = _draft_party or "Borrower"
                        _group_lang = st.session_state.get(f"{_scan_fkey}_{_draft_party}_email_group_lang", "English")
                        if not _checked_for_email:
                            return
                        try:
                            from ai_engine import draft_email as _draft
                            import urllib.parse as _uparse
                            _is_client_party = _group_to in {"Borrower", "Co-Borrower"}
                            _cond_text = "\n".join(
                                f"- #{c['num']}: {(_to_client_language(c['desc'], _group_to) if _is_client_party else c['desc'])}"
                                for c in _checked_for_email
                            )
                            _ebody = _draft(_cond_text, _group_to, _group_lang)
                        except Exception as _e:
                            _ebody = f"(Draft failed: {_e})"
                            import urllib.parse as _uparse
                        _subject = f"{_SEND_LABEL_SCAN.get(_group_to, 'Conditions request')} - {_batch['type']}"
                        _recipient_email = _scan_contact_email_for_section(_group_to)
                        _compose_params = {"su": _subject, "body": _ebody}
                        if _recipient_email:
                            _compose_params["to"] = _recipient_email
                        _gmail_compose = "https://mail.google.com/mail/?view=cm&fs=1&" + _uparse.urlencode(_compose_params)
                        import html as _html
                        _preview_body = _html.escape(_ebody).replace("\n", "<br>")
                        st.markdown(
                            f'<div style="margin:12px 0;padding:14px 16px;border:1px solid rgba(59,130,246,0.30);'
                            f'border-radius:14px;background:#161b2b;box-shadow:0 10px 24px rgba(0,0,0,0.20);">',
                            unsafe_allow_html=True,
                        )
                        st.markdown(
                            f'<div style="font-size:13px;font-weight:800;color:#fff;margin-bottom:8px;">'
                            f'Draft for {_SECTION_LABEL_SCAN.get(_group_to, _group_to)}</div>'
                            f'<div style="display:grid;grid-template-columns:90px 1fr;gap:6px 10px;font-size:12px;margin-bottom:12px;">'
                            f'<div style="color:#9ca3af;">To</div><div style="color:#e5e7eb;">{_recipient_email or "No parsed email found yet"}</div>'
                            f'<div style="color:#9ca3af;">Subject</div><div style="color:#e5e7eb;">{_subject}</div>'
                            f'</div>'
                            f'<div style="background:#0f172a;border:1px solid rgba(255,255,255,0.08);border-radius:12px;'
                            f'padding:14px 16px;color:#e5e7eb;font-size:13px;line-height:1.55;">'
                            f'{_preview_body}</div>',
                            unsafe_allow_html=True,
                        )
                        st.text_area(
                            "Edit draft before composing",
                            value=_ebody,
                            height=180,
                            key=f"{_scan_fkey}_{_draft_party}_email_body_edit",
                            label_visibility="collapsed",
                        )
                        _edited_body = st.session_state.get(f"{_scan_fkey}_{_draft_party}_email_body_edit", _ebody)
                        _compose_params["body"] = _edited_body
                        _gmail_compose = "https://mail.google.com/mail/?view=cm&fs=1&" + _uparse.urlencode(_compose_params)
                        _draft_cols = st.columns([1, 2, 3])
                        with _draft_cols[0]:
                            if st.button("Close Draft", key=f"{_scan_fkey}_{_draft_party}_email_group_close"):
                                st.session_state.pop(f"{_scan_fkey}_email_group_open", None)
                                st.rerun()
                        with _draft_cols[1]:
                            st.markdown(
                                f'<a href="{_gmail_compose}" target="_blank" style="display:inline-block;'
                                f'margin-top:4px;padding:4px 12px;background:rgba(66,133,244,0.12);'
                                f'border:1px solid rgba(66,133,244,0.4);border-radius:6px;color:#4285f4;'
                                f'font-size:11px;font-weight:700;text-decoration:none;">Compose in Gmail</a>',
                                unsafe_allow_html=True,
                            )
                        with _draft_cols[2]:
                            if st.button("Translate / Spanish Reply", key=f"{_scan_fkey}_{_draft_party}_translate"):
                                st.session_state["spanish_reply_data"] = {"subject": _subject, "body": _edited_body}
                                st.session_state.page = "spanish_reply"
                                st.rerun()
                            st.caption("Gmail opens ready to review. It will not send automatically.")
                        st.markdown('</div>', unsafe_allow_html=True)

                    # Auto-group checked conditions by their per-condition party assignment.
                    # If 5 conditions are checked and span 3 parties, we generate 3 separate
                    # email drafts — one per party — with the right To address each.
                    _parties_with_checked = []
                    for _section_party in _SECTION_ORDER_SCAN:
                        _section_conds = _conds_by_section.get(_section_party, [])
                        if not _section_conds:
                            continue
                        _checked_for_email = [
                            c for c in _section_conds
                            if _scan_condition_checked_for_section(c, _section_party)
                        ]
                        if _checked_for_email:
                            _parties_with_checked.append(_section_party)

                    if _parties_with_checked:
                        _send_cols = st.columns([3, 1.1, 1.4])
                        with _send_cols[0]:
                            _summary = ", ".join(
                                _SECTION_LABEL_SCAN.get(p, p).replace(" Conditions", "")
                                for p in _parties_with_checked
                            )
                            st.markdown(
                                f'<div style="font-size:12px;color:#94a3b8;padding:8px 0;">'
                                f'Will draft {len(_parties_with_checked)} email'
                                f'{"s" if len(_parties_with_checked) != 1 else ""}: '
                                f'<span style="color:#e2e8f0;">{_summary}</span></div>',
                                unsafe_allow_html=True,
                            )
                        with _send_cols[1]:
                            st.selectbox(
                                "Language", ["English", "Spanish"],
                                key=f"{_scan_fkey}_email_group_lang_global",
                                label_visibility="collapsed",
                            )
                        with _send_cols[2]:
                            if st.button("Draft emails", type="primary",
                                         key=f"{_scan_fkey}_email_draft_all_btn",
                                         use_container_width=True):
                                # Open every party that has a checked condition; renderer
                                # below will draw one draft block per opened party.
                                st.session_state[f"{_scan_fkey}_email_groups_open"] = list(_parties_with_checked)
                        _open_groups = st.session_state.get(f"{_scan_fkey}_email_groups_open", [])
                        for _open_party in _open_groups:
                            if _open_party in _parties_with_checked:
                                # Mirror the global language pick into the per-party state key
                                # the existing _render_scan_email_draft reads from
                                st.session_state[f"{_scan_fkey}_{_open_party}_email_group_lang"] = \
                                    st.session_state.get(f"{_scan_fkey}_email_group_lang_global", "English")
                                _render_scan_email_draft(_open_party)
                    st.markdown('</div>', unsafe_allow_html=True)
                elif _cond_count and "No specific conditions found in this document" not in str(_raw_c):
                    st.markdown(
                        '<div style="font-size:12px;color:#9ca3af;margin:6px 0;">'
                        'Conditions were detected, but no actionable condition rows were parsed.'
                        '</div>',
                        unsafe_allow_html=True,
                    )
                if _cont_count:
                    _cchips = []
                    for _k, _v in _r.get("contacts", {}).items():
                        if not isinstance(_v, dict):
                            continue
                        _name = _clean_display_text(_v.get("name", "") or _v.get("company", ""))
                        _parts = [_clean_display_text(p) for p in [_name, _v.get("phone", ""), _v.get("email", "")] if p]
                        if _parts:
                            _cchips.append(
                                f'<span style="display:inline-block;font-size:11px;'
                                f'background:rgba(59,130,246,0.08);border:1px solid rgba(59,130,246,0.2);'
                                f'border-radius:10px;padding:2px 8px;margin:2px 4px 2px 0;color:#e5e7eb;">'
                                f'<b style="color:#3b82f6;">{_clean_display_text(_k.replace("_"," ").title())}</b>: '
                                f'{" · ".join(_parts)}</span>'
                            )
                    if _cchips:
                        st.markdown('<div class="pa-section" style="margin-top:8px;">Contacts</div>', unsafe_allow_html=True)
                        st.markdown("".join(_cchips), unsafe_allow_html=True)

                # â”€â”€ Purchase Contract extended fields â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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
                        _la_str = " · ".join(_clean_display_text(v) for v in [_la_info.get("name"), _la_info.get("brokerage"), _la_info.get("phone"), _la_info.get("email")] if v)
                        _rows.append(("Listing Agent", _la_str))
                    if _sa_info.get("name"):
                        _sa_str = " · ".join(_clean_display_text(v) for v in [_sa_info.get("name"), _sa_info.get("brokerage"), _sa_info.get("phone"), _sa_info.get("email")] if v)
                        _rows.append(("Selling Agent", _sa_str))
                    if _title_info.get("company"):
                        _tc_str = " · ".join(_clean_display_text(v) for v in [_title_info.get("company"), _title_info.get("contact"), _title_info.get("phone"), _title_info.get("email")] if v)
                        _rows.append(("Title Company", _tc_str))
                    if _rows:
                        st.markdown("**Purchase Contract Details**")
                        for _lbl, _val in _rows:
                            st.markdown(f"- **{_clean_display_text(_lbl)}**: {_clean_display_text(_val)}")

                # â”€â”€ 1003 Application extended fields â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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
                        if not last4: return ""
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
                                f'<div style="font-size:11px;font-weight:700;color:#3b82f6;letter-spacing:0.08em;text-transform:uppercase;margin-bottom:4px;">{_sec_title}</div>'
                                f'<table style="border-collapse:collapse;width:100%;">{_rows_html}</table>'
                                f'</div>',
                                unsafe_allow_html=True
                            )

                # â”€â”€ W-2 extended fields + income calc â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
                if _batch.get("type") == "W-2":
                    _w2d = (_r.get("extracted_data") or {})
                    _w2_recs = _w2d.get("w2_records", [])
                    _w2_calc = _w2d.get("income_calc", {})

                    def _fmt_money(val):
                        try:
                            return f"${float(val):,.2f}"
                        except Exception:
                            return str(val) if val else ""

                    def _w2_ssn_html(ssn):
                        if not ssn: return ""
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
                            if _wr.get("box1_wages"):    _rows_h += f'<tr><td style="color:#9ca3af;padding:2px 12px 2px 0;font-size:12px;white-space:nowrap;">Box 1 Wages</td><td style="color:#3b82f6;font-size:12px;font-weight:700;">{_fmt_money(_wr["box1_wages"])}</td></tr>'
                            if _wr.get("box2_fed_tax"):  _rows_h += f'<tr><td style="color:#9ca3af;padding:2px 12px 2px 0;font-size:12px;white-space:nowrap;">Box 2 Fed Tax W/H</td><td style="color:#e5e7eb;font-size:12px;">{_fmt_money(_wr["box2_fed_tax"])}</td></tr>'
                            if _wr.get("box3_ss_wages"): _rows_h += f'<tr><td style="color:#9ca3af;padding:2px 12px 2px 0;font-size:12px;white-space:nowrap;">Box 3 SS Wages</td><td style="color:#e5e7eb;font-size:12px;">{_fmt_money(_wr["box3_ss_wages"])}</td></tr>'
                            if _wr.get("box5_medicare_wages"): _rows_h += f'<tr><td style="color:#9ca3af;padding:2px 12px 2px 0;font-size:12px;white-space:nowrap;">Box 5 Medicare Wages</td><td style="color:#e5e7eb;font-size:12px;">{_fmt_money(_wr["box5_medicare_wages"])}</td></tr>'
                            if _wr.get("state"):         _rows_h += f'<tr><td style="color:#9ca3af;padding:2px 12px 2px 0;font-size:12px;white-space:nowrap;">State</td><td style="color:#e5e7eb;font-size:12px;">{_wr["state"]}</td></tr>'
                            if _wr.get("state_wages"):   _rows_h += f'<tr><td style="color:#9ca3af;padding:2px 12px 2px 0;font-size:12px;white-space:nowrap;">State Wages</td><td style="color:#e5e7eb;font-size:12px;">{_fmt_money(_wr["state_wages"])}</td></tr>'
                            if _wr.get("box12"):         _rows_h += f'<tr><td style="color:#9ca3af;padding:2px 12px 2px 0;font-size:12px;white-space:nowrap;">Box 12</td><td style="color:#e5e7eb;font-size:12px;">{_wr["box12"]}</td></tr>'
                            if _wr.get("box14"):         _rows_h += f'<tr><td style="color:#9ca3af;padding:2px 12px 2px 0;font-size:12px;white-space:nowrap;">Box 14 Other</td><td style="color:#e5e7eb;font-size:12px;">{_wr["box14"]}</td></tr>'
                            st.markdown(
                                f'<div style="margin-bottom:10px;">'
                                f'<div style="font-size:11px;font-weight:700;color:#3b82f6;letter-spacing:0.08em;text-transform:uppercase;margin-bottom:4px;">Tax Year {_yr}</div>'
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
                            _ic_rows += f'<tr><td style="color:#3b82f6;padding:3px 16px 3px 0;font-size:13px;font-weight:700;">Monthly Income</td><td style="color:#3b82f6;font-size:13px;font-weight:700;text-align:right;">{_fmt_money(_ic["monthly_avg"])}</td></tr>'
                        st.markdown(
                            f'<div style="background:rgba(59,130,246,0.06);border:1px solid rgba(59,130,246,0.25);border-radius:6px;padding:10px 14px;margin-top:8px;">'
                            f'<div style="font-size:11px;font-weight:700;color:#3b82f6;letter-spacing:0.08em;text-transform:uppercase;margin-bottom:6px;">Income Calculation ({_method})</div>'
                            f'<table style="border-collapse:collapse;width:100%;">{_ic_rows}</table>'
                            f'</div>',
                            unsafe_allow_html=True
                        )

                # â”€â”€ Credit Report display â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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
                        if not ssn: return ""
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
                            f'<div style="font-size:11px;font-weight:700;color:#3b82f6;letter-spacing:0.08em;text-transform:uppercase;margin-bottom:4px;">Borrower</div>'
                            f'<table style="border-collapse:collapse;width:100%;">{_pi_rows}</table>'
                            f'</div>', unsafe_allow_html=True
                        )

                    # Scores all 3 + middle highlighted (sort: low, MID, high so middle is center)
                    if _cr_scores:
                        _score_html = '<div style="display:flex;gap:12px;flex-wrap:wrap;margin-bottom:10px;">'
                        _sorted_scores = sorted(_cr_scores.items(), key=lambda x: x[1])
                        # Reorder: [lowest, middle, highest] â†’ display as [lowest, middle, highest]
                        for _bur, _scr in _sorted_scores:
                            _is_mid = (_bur == _cr_mid_bur and _scr == _cr_mid)
                            _bg = "rgba(59,130,246,0.15)" if _is_mid else "rgba(255,255,255,0.05)"
                            _border = "rgba(59,130,246,0.5)" if _is_mid else "rgba(255,255,255,0.12)"
                            _badge = '<div style="font-size:9px;color:#3b82f6;font-weight:700;letter-spacing:0.1em;">MIDDLE</div>' if _is_mid else ''
                            _score_color = "#3b82f6" if _is_mid else ("#ef4444" if _scr < 620 else ("#f59e0b" if _scr < 680 else "#e5e7eb"))
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
                        st.markdown('<div style="font-size:12px;color:#3b82f6;margin-bottom:8px;">No derogatory items detected</div>', unsafe_allow_html=True)

                    # Summary row
                    _sum_parts = []
                    if _cr_inq:   _sum_parts.append(f"{_cr_inq} inquir{'y' if _cr_inq==1 else 'ies'}")
                    if _cr_past_due > 0: _sum_parts.append(f"Past due: ${_cr_past_due:,.2f}")
                    if _sum_parts:
                        st.caption("  ".join(_sum_parts))

                # â”€â”€ 1099 display â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
                if _batch.get("type") == "1099":
                    _tf = (_r.get("extracted_data") or {})

                    def _1099_ssn_html(ssn):
                        if not ssn: return ""
                        import re as _re4
                        digits = _re4.sub(r'\D', '', str(ssn))
                        last4 = digits[-4:] if len(digits) >= 4 else digits
                        return (f'<span style="filter:blur(3px);color:#9ca3af;user-select:none;">***-**-</span>'
                                f'<span style="color:#e5e7eb;">{last4}</span>')

                    def _fmt_m(val):
                        try: return f"${float(val):,.2f}"
                        except: return str(val) if val else ""

                    st.markdown("**1099 Details**")
                    _rows_h = ""
                    if _tf.get("form_type"):     _rows_h += f'<tr><td style="color:#9ca3af;padding:2px 12px 2px 0;font-size:12px;white-space:nowrap;">Form</td><td style="color:#e5e7eb;font-size:12px;font-weight:700;">{_tf["form_type"]} Tax Year {_tf.get("year","")}</td></tr>'
                    if _tf.get("recipient_name"):_rows_h += f'<tr><td style="color:#9ca3af;padding:2px 12px 2px 0;font-size:12px;white-space:nowrap;">Recipient</td><td style="color:#e5e7eb;font-size:12px;"><b>{_tf["recipient_name"]}</b></td></tr>'
                    if _tf.get("recipient_ssn"): _rows_h += f'<tr><td style="color:#9ca3af;padding:2px 12px 2px 0;font-size:12px;white-space:nowrap;">SSN</td><td style="font-size:12px;">{_1099_ssn_html(_tf["recipient_ssn"])}</td></tr>'
                    if _tf.get("payer_name"):    _rows_h += f'<tr><td style="color:#9ca3af;padding:2px 12px 2px 0;font-size:12px;white-space:nowrap;">Payer</td><td style="color:#e5e7eb;font-size:12px;">{_tf["payer_name"]}</td></tr>'
                    if _tf.get("payer_tin"):     _rows_h += f'<tr><td style="color:#9ca3af;padding:2px 12px 2px 0;font-size:12px;white-space:nowrap;">Payer TIN</td><td style="color:#e5e7eb;font-size:12px;">{_tf["payer_tin"]}</td></tr>'
                    if _tf.get("box1"):          _rows_h += f'<tr><td style="color:#9ca3af;padding:2px 12px 2px 0;font-size:12px;white-space:nowrap;">Box 1 Income</td><td style="color:#3b82f6;font-size:12px;font-weight:700;">{_fmt_m(_tf["box1"])}</td></tr>'
                    if _tf.get("box2"):          _rows_h += f'<tr><td style="color:#9ca3af;padding:2px 12px 2px 0;font-size:12px;white-space:nowrap;">Box 2</td><td style="color:#e5e7eb;font-size:12px;">{_fmt_m(_tf["box2"])}</td></tr>'
                    if _tf.get("box4_fed_tax"):  _rows_h += f'<tr><td style="color:#9ca3af;padding:2px 12px 2px 0;font-size:12px;white-space:nowrap;">Fed Tax W/H</td><td style="color:#e5e7eb;font-size:12px;">{_fmt_m(_tf["box4_fed_tax"])}</td></tr>'
                    if _rows_h:
                        st.markdown(f'<table style="border-collapse:collapse;width:100%;margin-bottom:8px;">{_rows_h}</table>', unsafe_allow_html=True)

                    # Income calc box
                    if _tf.get("annual_income", 0) > 0:
                        st.markdown(
                            f'<div style="background:rgba(59,130,246,0.06);border:1px solid rgba(59,130,246,0.25);border-radius:6px;padding:10px 14px;">'
                            f'<div style="font-size:11px;font-weight:700;color:#3b82f6;letter-spacing:0.08em;text-transform:uppercase;margin-bottom:4px;">Income (annual Ã· 12)</div>'
                            f'<table style="border-collapse:collapse;width:100%;">'
                            f'<tr><td style="color:#9ca3af;padding:3px 16px 3px 0;font-size:12px;">Annual</td><td style="color:#e5e7eb;font-size:12px;text-align:right;">{_fmt_m(_tf["annual_income"])}</td></tr>'
                            f'<tr><td style="color:#3b82f6;padding:3px 16px 3px 0;font-size:13px;font-weight:700;">Monthly</td><td style="color:#3b82f6;font-size:13px;font-weight:700;text-align:right;">{_fmt_m(_tf["monthly_income"])}</td></tr>'
                            f'</table>'
                            f'</div>', unsafe_allow_html=True
                        )

                # â”€â”€ Mortgage Statement display â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
                if _batch.get("type") == "Mortgage Statement":
                    _ms = (_r.get("extracted_data") or {})
                    def _fmt_ms(v):
                        try: return f"${float(v.replace(',','')):,.2f}" if v else ""
                        except: return v or ""
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
                        for l, v in _ms_rows if v and v != ""
                    )
                    if _ms_html:
                        st.markdown("**Mortgage Statement**")
                        st.markdown(f'<table style="border-collapse:collapse;width:100%;">{_ms_html}</table>', unsafe_allow_html=True)

                # â”€â”€ Image-only stub (scanned PDF, no text layer) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
                if _r.get("image_only"):
                    _img_labels = {
                        "VA Certificate of Eligibility": ("VA Certificate of Eligibility", "Document received and logged. This is a scanned image fields cannot be auto-extracted. Verify manually and attach to loan file."),
                        "DD-214": ("DD-214 Certificate of Release", "Document received and logged. This is a scanned image fields cannot be auto-extracted. Verify discharge status and service dates manually."),
                        "Hazard Insurance": ("Hazard Insurance / HOI Declarations", "Document received and logged. This is a scanned image verify policy number, coverage amounts, and expiration date manually."),
                        "Government ID": ("Government ID", "Document received and logged. This is a scanned image verify name, DOB, ID number, and expiration manually."),
                    }
                    _img_title, _img_msg = _img_labels.get(_batch.get("type"), ("Document", "Received and logged. Scanned image manual review required."))
                    st.markdown(f"**{_img_title}**")
                    st.markdown(
                        f'<div style="background:rgba(245,158,11,0.08);border:1px solid rgba(245,158,11,0.3);'
                        f'border-radius:4px;padding:8px 12px;font-size:12px;color:#fbbf24;margin-top:4px;">'
                        f'Scanned image PDF text extraction not available for this scanned image.<br>'
                        f'<span style="color:#9ca3af;">{_img_msg}</span>'
                        + (f'<br><span style="color:#f59e0b;">AI log: {(_r.get("ai_log","") or "none")}</span>' if _batch.get("type") == "Purchase Contract" else "")
                        + '</div>',
                        unsafe_allow_html=True
                    )

                # â”€â”€ VA COE display â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
                if _batch.get("type") == "VA Certificate of Eligibility" and not _r.get("image_only"):
                    _coe = (_r.get("extracted_data") or {})
                    _coe_rows = [
                        ("Veteran Name",        _coe.get("veteran_name")),
                        ("Entitlement Amount",  f'${_coe["entitlement_amount"]}' if _coe.get("entitlement_amount") else None),
                        ("Entitlement Code",    _coe.get("entitlement_code")),
                        ("Remaining Entitlement",f'${_coe["remaining_entitlement"]}' if _coe.get("remaining_entitlement") else None),
                        ("Loan Guaranty",       _coe.get("loan_guaranty")),
                        ("Funding Fee Exempt",  "YES Service-Connected Disability" if _coe.get("funding_fee_exempt") else None),
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
                        st.markdown('<div style="background:rgba(59,130,246,0.08);border:1px solid rgba(59,130,246,0.3);border-radius:4px;padding:6px 10px;font-size:12px;color:#3b82f6;margin-top:6px;">Funding fee exemption noted</div>', unsafe_allow_html=True)

                # â”€â”€ DD-214 display â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
                if _batch.get("type") == "DD-214" and not _r.get("image_only"):
                    _dd = (_r.get("extracted_data") or {})
                    def _dd_ssn_html(ssn):
                        if not ssn: return ""
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
                        st.markdown("**DD-214 Certificate of Release**")
                        st.markdown(f'<table style="border-collapse:collapse;width:100%;">{_dd_rows_html}</table>', unsafe_allow_html=True)
                    if _dd.get("disability_noted"):
                        st.markdown('<div style="background:rgba(59,130,246,0.08);border:1px solid rgba(59,130,246,0.3);border-radius:4px;padding:6px 10px;font-size:12px;color:#3b82f6;margin-top:6px;">Service-connected disability noted verify VA funding fee exemption</div>', unsafe_allow_html=True)

                # â”€â”€ Government ID display â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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
                    if _gid.get("id_type"):  _gid_html += f'<tr><td style="color:#9ca3af;padding:2px 12px 2px 0;font-size:12px;white-space:nowrap;">ID Type</td><td style="color:#3b82f6;font-size:12px;font-weight:700;">{_gid["id_type"]}</td></tr>'
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

                if _norm_cond_count > 10:
                    st.caption(f"...and {_norm_cond_count - 10} more conditions")



def _pipeline_cond_row(c, contacts=None, loan_num="", borrower=""):
    import urllib.parse as _uparse
    _status = c.get("status", "")
    _bg = "rgba(59,130,246,0.15)" if _status in ("Cleared","Ready to Clear") else "rgba(245,158,11,0.12)" if _status == "Requested" else "rgba(239,68,68,0.12)"
    _clr = "#3b82f6" if _status in ("Cleared","Ready to Clear") else "#f59e0b" if _status == "Requested" else "#ef4444"
    _parties = c.get("party", []) if isinstance(c.get("party"), list) else [c.get("party", "")]
    _party_str = ", ".join(_parties)

    # Map party label â†’ contacts key
    _party_key_map = {
        "Borrower": ["borrower", "co_borrower"],
        "Co-Borrower": ["co_borrower", "borrower"],
        "Title": ["title"],
        "Insurance": ["insurance"],
        "Listing Agent": ["listing_agent"],
        "Selling Agent": ["selling_agent"],
        "Employer": ["employer"],
    }
    _remind_btn = ""
    if contacts and _status not in ("Cleared", "Ready to Clear"):
        _email = ""
        for _p in _parties:
            for _key in _party_key_map.get(_p, [_p.lower().replace(" ", "_")]):
                _cv = contacts.get(_key, {})
                if isinstance(_cv, dict):
                    _email = _cv.get("email", "")
                elif isinstance(_cv, str):
                    pass
                if _email:
                    break
            if _email:
                break
        if _email:
            _cond_text = c.get("text", "")
            _body = (
                f"Hi,\n\nThis is a friendly reminder regarding the following outstanding item "
                f"for loan #{loan_num} {borrower}:\n\n"
                f"  {_cond_text}\n\n"
                f"Please provide this at your earliest convenience so we can keep the file moving.\n\n"
                f"Thank you,"
            )
            _gurl = "https://mail.google.com/mail/?view=cm&fs=1&" + _uparse.urlencode({
                "to": _email,
                "su": f"Reminder: {loan_num} {_cond_text[:50]}",
                "body": _body,
            })
            _remind_btn = (
                f'<a href="{_gurl}" target="_blank" style="margin-left:6px;padding:1px 7px;'
                f'background:rgba(66,133,244,0.1);border:1px solid rgba(66,133,244,0.3);'
                f'border-radius:3px;color:#4285f4;font-size:9px;font-weight:700;'
                f'text-decoration:none;white-space:nowrap;">Remind</a>'
            )

    return (
        f'<div style="display:flex;align-items:center;gap:8px;padding:3px 0;border-bottom:1px solid rgba(255,255,255,0.05);">'
        f'<span style="font-size:10px;padding:1px 7px;border-radius:3px;font-weight:600;background:{_bg};color:{_clr};white-space:nowrap;">{_status}</span>'
        f'<span style="font-size:11px;color:#d1d5db;">{c.get("text","")}</span>'
        f'<span style="font-size:9px;color:#6b7280;margin-left:auto;white-space:nowrap;">{_party_str}</span>'
        f'{_remind_btn}'
        f'</div>'
    )


def show_pipeline():
    """Color-coded CRM loan pipeline dashboard."""
    import os
    # Handle dash header chip click set status filter from query param
    _qp = st.query_params
    _qp_filter = _qp.get("pipefilter", "")
    if isinstance(_qp_filter, list):
        _qp_filter = _qp_filter[0] if _qp_filter else ""
    if _qp_filter:
        st.session_state["pipeline_filter_val"] = _qp_filter
        if "pipeline_filter" in st.session_state:
            del st.session_state["pipeline_filter"]
        st.query_params.clear()
        st.rerun()
    from crm import (
        get_all_loans, add_loan, set_status, delete_loan, update_loan,
        STATUS_OPTIONS, STATUS_EMOJI, STATUS_COLORS,
        get_trash, restore_loan, permanently_delete, empty_trash,
        get_retention_days, set_retention_days, RETENTION_OPTIONS,
        log_activity,
    )

    import json as _json

    from db import get_all_users
    all_users = get_all_users()
    user_names = ["(Unassigned)"] + [
        u.get("display_name") or u["email"] for u in all_users
    ]
    my_name = st.session_state.get("user_name", "")

    # â”€â”€ Top action bar â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    st.markdown('<div class="pa-pipe-controls">', unsafe_allow_html=True)
    tb1, tb2, tb3, tb4, tb5 = st.columns([1.45, 1.9, 2.4, 1.8, 1.0])
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
            label_visibility="collapsed",
        )
        st.session_state["pipeline_filter_val"] = filter_status
    with tb3:
        search_loan = st.text_input(
            "Search", placeholder="Loan # or borrower name",
            key="pipeline_search",
            label_visibility="collapsed",
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
                "Loan Amount (Highâ†’Low)",
                "Loan Amount (Lowâ†’High)",
                "Loan Type",
                "Borrower (Aâ†’Z)",
            ],
            key="pipeline_sort",
            label_visibility="collapsed",
        )
    with tb5:
        st.markdown('<div class="pa-myloans-toggle">', unsafe_allow_html=True)
        my_loans_only = st.checkbox("My loans", key="pipeline_myloans")
    st.markdown('</div></div>', unsafe_allow_html=True)

    # â”€â”€ Add Loan form â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    if st.session_state.get("pipeline_add_open"):
        with st.container(border=True):
            st.markdown(
                '<span style="font-size:14px;font-weight:700;color:#ffffff;">Add New Loan</span>',
                unsafe_allow_html=True,
            )

            # â”€â”€ Bulk Upload auto-fill from documents â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            _add_bulk_key = "add_loan_bulk"
            with st.expander("Upload documents to auto-fill loan details", expanded=not st.session_state.get(_add_bulk_key)):
                _add_bulk_files = st.file_uploader(
                    "Drop your loan package - approval letter, purchase contract, 1003, etc.",
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

                    # Check for cloud AI and consent for bulk scan
                    _al_cloud_enabled = False
                    try:
                        import cloud_client as _al_cc
                        _al_cloud_enabled = _al_cc.is_enabled()
                    except Exception:
                        pass

                    # First pass: check if batch contains cloud-supported docs
                    _al_has_cloud_docs = False
                    if _al_cloud_enabled:
                        for _af in _add_bulk_files:
                            _af_bytes = _af.read()
                            _af.seek(0)
                            _det = _ald(_af_bytes)
                            if _det["doc_type"] in ("Purchase Contract", "Approval Letter"):
                                _al_has_cloud_docs = True
                                break
                            _af.seek(0)

                    # Show consent prompt once for batch if needed
                    _al_batch_consent_key = "cloud_consent_bulk_batch"
                    _al_user_approved_cloud = False
                    if _al_has_cloud_docs:
                        _al_session_consent = st.session_state.get("cloud_consent_session", None)
                        if _al_session_consent == "yes":
                            _al_user_approved_cloud = True
                        elif _al_session_consent == "no":
                            _al_user_approved_cloud = False
                        else:
                            _al_batch_state = st.session_state.get(_al_batch_consent_key, None)
                            if _al_batch_state is None:
                                st.info("This batch contains documents that support cloud AI augmentation.")
                                _alb1, _alb2, _alb3 = st.columns(3)
                                with _alb1:
                                    if st.button("Send to Cloud AI", key="bulk_consent_yes"):
                                        st.session_state[_al_batch_consent_key] = "yes_once"
                                        st.rerun()
                                with _alb2:
                                    if st.button("Skip AI for batch", key="bulk_consent_no"):
                                        st.session_state[_al_batch_consent_key] = "no"
                                        st.rerun()
                                with _alb3:
                                    if st.button("Always for session", key="bulk_consent_session"):
                                        st.session_state["cloud_consent_session"] = "yes"
                                        st.session_state[_al_batch_consent_key] = "yes_once"
                                        st.rerun()
                            elif _al_batch_state == "yes_once":
                                _al_user_approved_cloud = True
                            elif _al_batch_state == "no":
                                _al_user_approved_cloud = False

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
                        _result = _alp(_af_bytes, _dtype, user_approved_cloud=_al_user_approved_cloud)
                        if not _result.get("success"):
                            _al_scanned.append({"name": _af.name, "type": _dtype, "status": "failed"})
                            continue

                        _al_scanned.append({"name": _af.name, "type": _dtype, "status": "ok"})

                        # â”€â”€ Pull from extracted_data FIRST (engine already parsed these) â”€â”€
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

                        # â”€â”€ Regex mining on raw text for anything not already found â”€â”€
                        from pypdf import PdfReader as _AL_PR
                        import io as _al_io
                        try:
                            _al_reader = _AL_PR(_al_io.BytesIO(_af_bytes))
                            _al_text = "\n".join((p.extract_text() or "") for p in _al_reader.pages[:5])
                        except Exception:
                            _al_text = ""

                        if _al_text:
                            # â”€â”€ Use extract_contacts() same logic as the regular scanner â”€â”€
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

                            # Fallback: mine loan number with regex (relaxed allow dashes, shorter numbers)
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

                            # Mine closing date (relaxed many formats)
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
                        f'<b style="color:#3b82f6;">Scanned {len(_sc)} file(s):</b> '
                        f'{_ok} processed, {_skip} skipped<br>'
                        + "".join(
                            f'<span style="color:{"#3b82f6" if s["status"]=="ok" else "#ef4444"};">'
                            f'{"" if s["status"]=="ok" else ""}</span> '
                            f'{s["name"]} â†’ {s["type"]}&nbsp;&nbsp;'
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
                            f'<div style="background:#0a1a0a;border:1px solid rgba(59,130,246,0.2);border-radius:8px;'
                            f'padding:10px;margin:4px 0;font-size:12px;color:#3b82f6;">'
                            f'Auto-filled: {" &nbsp;&nbsp; ".join(_parts)}'
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
                            f'Not found in documents: <b>{", ".join(_not_found)}</b> '
                            f'fill these in manually below.</div>',
                            unsafe_allow_html=True,
                        )
                    if st.button("Remove Clear scan results", key="add_loan_bulk_clear"):
                        st.session_state.pop(_add_bulk_key, None)
                        for _k in ["pl_new_num", "pl_new_borrower", "pl_new_closing",
                                    "pl_new_lock"]:
                            st.session_state.pop(_k, None)
                        st.rerun()

            # â”€â”€ Manual fields (pre-filled from bulk if available) â”€â”€â”€â”€â”€
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
                    f'From bulk scan: <b style="color:#3b82f6;">{len(_bf_conds)}</b> condition(s) '
                    f'and <b style="color:#3b82f6;">{len(_bf_contacts)}</b> contact group(s) '
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
                        _stamp_current_user_on_loan(_new, assigned=True)
                        _cond_note = f", {len(_bf_conds)} conditions" if _bf_conds else ""
                        _cont_note = f", {len(_bf_contacts)} contact groups" if _bf_contacts else ""
                        log_activity(_new["id"], "created",
                            f"Loan created {new_borrower} #{new_loan_num}{_cond_note}{_cont_note}",
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

    # â”€â”€ Inbox (incoming shared loans) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    from sharing import scan_inbox, dismiss_from_inbox, inbox_count, scan_notifications, dismiss_notification
    # â”€â”€ Activity notifications from shared loans â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    _notifs = scan_notifications()
    if _notifs:
        _event_labels = {"opened": "opened", "updated": "updated", "status_changed": "changed status", "touched": "touched"}
        with st.expander(f"{len(_notifs)} notification{'s' if len(_notifs)!=1 else ''}", expanded=True):
            for _nf in _notifs:
                _ev = _event_labels.get(_nf.get("event",""), _nf.get("event",""))
                _nc1, _nc2 = st.columns([5, 1])
                with _nc1:
                    st.markdown(
                        f'<div style="font-size:12px;color:#d1d5db;">'
                        f'<b style="color:#3b82f6;">{_nf.get("by","?")}</b> {_ev} '
                        f'<b>#{_nf.get("loan_num","")}</b> {_nf.get("borrower","")}'
                        f'</div>'
                        f'<div style="font-size:10px;color:#6b7280;">{_nf.get("ts","")[:16]}</div>',
                        unsafe_allow_html=True,
                    )
                with _nc2:
                    if st.button("Dismiss", key=f"notif_dismiss_{_nf.get('_file','')}_{_nf.get('ts','')}",
                                 use_container_width=True):
                        dismiss_notification(_nf["_file"])
                        st.rerun()

    inbox_items = scan_inbox()
    if inbox_items:
        n = len(inbox_items)
        with st.expander(f"Inbox {n} shared loan{'s' if n != 1 else ''} waiting", expanded=True):
            st.caption("Loans shared directly with you by teammates. Accept to add to your pipeline.")
            for item in inbox_items:
                ib1, ib2, ib3, ib4 = st.columns([3, 2, 1, 1])
                share_id = item.get("share_id", "?")
                with ib1:
                    st.markdown(
                        f"<div style='font-weight:700;color:#ffffff;'>"
                        f"#{item.get('loan_num','')} &nbsp; {item.get('borrower','')}</div>"
                        f"<div style='font-size:12px;color:#9ca3af;'>"
                        f"From: {item.get('last_updated_by','?')} &nbsp;&nbsp; "
                        f"Updated: {item.get('last_updated','')[:10]}</div>",
                        unsafe_allow_html=True,
                    )
                with ib2:
                    shared_with_list = ", ".join(item.get("shared_with", []))
                    st.markdown(
                        f"<div style='font-size:12px;color:#d1d5db;'>"
                        f"Status: <b>{item.get('status','')}</b><br>"
                        f"Shared with: {shared_with_list or 'you'}</div>",
                        unsafe_allow_html=True,
                    )
                with ib3:
                    if st.button("Accept", key=f"inbox_accept_{share_id}", use_container_width=True):
                        # Import into local pipeline
                        _accepted = add_loan(
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
                        _stamp_current_user_on_loan(_accepted, assigned=True)
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

    # â”€â”€ Load and filter loans â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    all_account_loans = _visible_account_loans(get_all_loans())
    loans = list(all_account_loans)

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

    # â”€â”€ Sort loans â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    def _last_name(name):
        """Extract last name for sorting: 'Carlos & Diana Reyes' â†’ 'reyes'."""
        parts = name.strip().split()
        return parts[-1].lower() if parts else ""

    def _first_name(name):
        """Extract first name for sorting: 'Carlos & Diana Reyes' â†’ 'carlos'."""
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
    elif sort_by == "Loan Amount (Highâ†’Low)":
        loans.sort(key=lambda l: float(l.get("loan_amount") or 0), reverse=True)
    elif sort_by == "Loan Amount (Lowâ†’High)":
        loans.sort(key=lambda l: float(l.get("loan_amount") or 0))
    elif sort_by == "Loan Type":
        loans.sort(key=lambda l: str(l.get("loan_type") or "").lower())
    elif sort_by == "Borrower (Aâ†’Z)":
        loans.sort(key=lambda l: str(l.get("borrower") or "").lower())
    else:  # Newest (default most recently created first)
        loans.sort(key=lambda l: l.get("id") or 0, reverse=True)

    if not loans:
        st.info("No loans in pipeline yet. Click **+Add Loan** to get started.")
        return

    # â”€â”€ Need `all_loans` and `counts` for downstream filtering/sorting â”€â”€â”€â”€â”€â”€
    all_loans = list(all_account_loans)
    counts = {s: sum(1 for l in all_loans if l["status"] == s) for s in STATUS_OPTIONS}

    # â”€â”€ Visual break between header section and loan rows â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    st.markdown(
        '<div style="height:2px;background:linear-gradient(90deg,rgba(59,130,246,0.35) 0%,rgba(59,130,246,0.08) 60%,transparent 100%);margin:8px 0 0 0;"></div>'
        '<div style="display:flex;align-items:center;gap:14px;margin:6px 0 6px 0;">'
        '<div style="font-size:13px;font-weight:800;color:#3b82f6;text-transform:uppercase;letter-spacing:2px;'
        'padding:4px 12px;background:rgba(59,130,246,0.08);border:1px solid rgba(59,130,246,0.3);border-radius:4px;">Loans</div>'
        '<div style="flex:1;height:1px;background:rgba(255,255,255,0.08);"></div>'
        '</div>',
        unsafe_allow_html=True,
    )

    # â”€â”€ Loan rows (scrollable container ~33vh) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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
            "Cleared":   "#3b82f6",
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
            team_line = f'<div style="font-size:9px;color:#9ca3af;margin-top:0px;">{" | ".join(parts)}</div>'

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
                    _lock_clr, _lock_lbl = "#3b82f6", f"Lock {_lock_exp}"
                _lock_badge = (
                    f'<span style="background:{_lock_clr};color:#fff;'
                    f'padding:1px 6px;border-radius:3px;font-size:10px;font-weight:500;">{_lock_lbl}</span>'
                )
            except Exception:
                pass

        _closing_dt = loan.get("closing_date") or loan.get("due_date") or "-"
        _lock_dt = loan.get("lock_expiry") or ""
        _dates_html = f'Closing: {_closing_dt}'
        _dates_html += f' &nbsp;|&nbsp; Lock: {_lock_dt if _lock_dt else "Not set"}'
        _missing_txt = loan.get("missing_docs", "") or "None"

        # â”€â”€ Progress calculation â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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
            # No conditions use milestone-based progress
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
            _bar_color = "#3b82f6"
        elif _pct >= 40:
            _bar_color = "#f59e0b"
        else:
            _bar_color = "#ef4444"

        # â”€â”€ Inline badges â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        _inline_badges = ""
        if _lock_badge:
            _inline_badges += f"&nbsp;{_lock_badge}"
        if _missing_txt and _missing_txt != "None":
            _inline_badges += (
                f'&nbsp;<span style="background:rgba(245,158,11,0.1);color:#f59e0b;padding:1px 5px;'
                f'border-radius:3px;font-size:9px;font-weight:500;border:1px solid rgba(245,158,11,0.3);">'
                f'Missing</span>'
            )
        # â”€â”€ 24hr response countdown badge (loan-level, not condition-level) â”€â”€
        if status == "Requested" and loan.get("requested_at"):
            try:
                from datetime import datetime as _dt2
                _elapsed = (_dt2.now() - _dt2.fromisoformat(loan["requested_at"])).total_seconds()
                _hrs_left = max(0, 24 - _elapsed / 3600)
                if _elapsed > 86400:
                    _inline_badges += (
                        f'&nbsp;<span style="background:rgba(239,68,68,0.15);color:#ef4444;padding:1px 6px;'
                        f'border-radius:3px;font-size:9px;font-weight:700;border:1px solid rgba(239,68,68,0.4);">'
                        f'NO RESPONSE {int((_elapsed-86400)/3600)}h overdue</span>'
                    )
                else:
                    _inline_badges += (
                        f'&nbsp;<span style="background:rgba(245,158,11,0.1);color:#f59e0b;padding:1px 6px;'
                        f'border-radius:3px;font-size:9px;font-weight:600;border:1px solid rgba(245,158,11,0.3);">'
                        f' {_hrs_left:.1f}h to respond</span>'
                    )
            except Exception:
                pass

        # â”€â”€ Contact chips â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        _contacts_data = loan.get("contacts", {})
        _contact_chips = []
        _contact_label_map = {
            "seller": "Seller", "listing_agent": "L.Agent", "selling_agent": "B.Agent",
            "title": "Title", "insurance": "HOI",
        }
        for _ck in ["seller", "listing_agent", "selling_agent", "title", "insurance"]:
            _cv = _normalize_contact_value(_contacts_data.get(_ck))
            if not _cv:
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
                _tip_rows.append(f'<div style="color:#d1d5db;font-size:12px;">Phone: {_cphone}</div>')
            if _cemail:
                _tip_rows.append(f'<div style="color:#d1d5db;font-size:12px;">Email: {_cemail}</div>')
            _tip_html = "".join(_tip_rows) if _tip_rows else '<div style="color:#9ca3af;font-size:11px;">No contact details</div>'
            _tooltip = (
                f'<span class="pa-tip-box">'
                f'<div style="color:#3b82f6;font-size:10px;font-weight:700;text-transform:uppercase;margin-bottom:4px;">{_clabel}</div>'
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
                f'<div style="font-size:9px;color:#9ca3af;margin-top:2px;margin-bottom:4px;">'
                + " | ".join(_contact_chips) + '</div>'
            )

        _orders_line = ""

        _loan_num = loan.get('loan_num', '-')
        _borrower = loan.get('borrower', '-')
        _status_clr = border_color

        # â”€â”€ Delete query param handling â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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
            st.toast("Moved to Trash")
            st.rerun()
        _qp_cancel = _qp.get("cancel_del", "")
        if isinstance(_qp_cancel, list):
            _qp_cancel = _qp_cancel[0] if _qp_cancel else ""
        if _qp_cancel == str(lid):
            st.session_state.pop(_del_key, None)
            st.query_params.clear()
            st.rerun()

        # â”€â”€ Remove link â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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

        # â”€â”€ Single compact row â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        st.markdown(
            f'<div class="pa-loan-grid" style="border-left:3px solid {_status_clr};background:#161b2b;padding:2px 6px 3px 6px;margin-bottom:0;">'
            # Line 1: loan# | borrower | status | badges | bar | % | x
            f'<div style="display:flex;align-items:center;gap:6px;min-height:20px;">'
            f'<span style="width:96px;font-size:10px;font-weight:700;color:#fff;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;flex-shrink:0;">#{_loan_num}</span>'
            f'<span style="width:170px;font-size:10px;color:#d1d5db;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;flex-shrink:0;">{_borrower}</span>'
            f'<span style="width:88px;font-size:10px;color:{_status_clr};font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;flex-shrink:0;">{emoji}{status}</span>'
            f'<span style="flex:1;overflow:hidden;white-space:nowrap;text-overflow:ellipsis;">{_inline_badges}</span>'
            f'<div style="width:60px;flex-shrink:0;background:rgba(255,255,255,0.1);height:4px;border-radius:2px;">'
            f'<div style="background:{_bar_color};width:{_pct}%;height:100%;border-radius:2px;"></div></div>'
            f'<span style="width:34px;font-size:10px;color:{_bar_color};font-weight:700;text-align:right;flex-shrink:0;">{_pct}%</span>'
            f'<span style="width:16px;flex-shrink:0;text-align:right;">{_remove_html}</span>'
            f'</div>'
            # Line 2: Close and Lock on their own line
            f'<div style="display:flex;gap:16px;min-height:16px;padding:2px 0 1px 0;">'
            f'<span style="font-size:10px;color:#6b7280;">Close: <span style="color:#9ca3af;">{_closing_dt}</span></span>'
            f'<span style="font-size:10px;color:#6b7280;">Lock: <span style="color:#9ca3af;">{_lock_dt if _lock_dt else "-"}</span></span>'
            f'</div>'
            + (f'<div style="font-size:9px;color:#9ca3af;padding:1px 0 0 0;">{_contacts_line}</div>' if _contacts_line else '')
            + f'</div>',
            unsafe_allow_html=True,
        )

        # â”€â”€ Compact action row: Open | Status | Assign â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        ac1, ac2, ac3 = st.columns([1, 1.5, 2])
        with ac1:
            if st.button("OPEN", key=f"open_{lid}", type="primary", use_container_width=True):
                from sharing import notify_shared_members as _nsm
                _nsm(loan, my_name, "opened")
                st.session_state.detail_loan_id = lid
                st.session_state.page = "loan_detail"
                st.rerun()
        with ac2:
            _status_confirm_key = f"status_confirm_{lid}"
            _status_pending_key = f"status_pending_{lid}"
            _new_status = st.selectbox(
                "Status", STATUS_OPTIONS, index=STATUS_OPTIONS.index(status) if status in STATUS_OPTIONS else 0,
                key=f"st_{lid}", label_visibility="collapsed",
            )
            if _new_status != status and not st.session_state.get(_status_confirm_key):
                st.session_state[_status_pending_key] = _new_status
                st.session_state[_status_confirm_key] = True
                st.rerun()
        # â”€â”€ Confirmation prompt outside columns so it renders full-width â”€â”€
        if st.session_state.get(_status_confirm_key):
            _pending = st.session_state.get(_status_pending_key, "")
            _cf1, _cf2, _cf3 = st.columns([3, 1, 1])
            with _cf1:
                st.markdown(
                    f'<div style="font-size:11px;color:#f59e0b;padding:4px 0;">'
                    f'Change status to <b>{_pending}</b>?</div>',
                    unsafe_allow_html=True,
                )
            with _cf2:
                if st.button("Yes", key=f"st_yes_{lid}", type="primary", use_container_width=True):
                    set_status(lid, _pending)
                    log_activity(lid, "status_manual", f"Status manually changed -> {_pending}", user=my_name or "Unknown")
                    from sharing import notify_shared_members as _nsm
                    _nsm(loan, my_name, "status_changed")
                    st.session_state.pop(_status_confirm_key, None)
                    st.session_state.pop(_status_pending_key, None)
                    st.rerun()
            with _cf3:
                if st.button("No", key=f"st_no_{lid}", use_container_width=True):
                    st.session_state.pop(_status_confirm_key, None)
                    st.session_state.pop(_status_pending_key, None)
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

        # â”€â”€ Notes & Conditions + Docs & Contacts expandable rows â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        _notes_key = f"notes_open_{lid}"
        _docs_key = f"docs_open_{lid}"
        _notes_open = st.session_state.get(_notes_key, False)
        _docs_open = st.session_state.get(_docs_key, False)
        _nb1, _nb2 = st.columns(2)
        with _nb1:
            _notes_lbl = f"Notes & Conditions - {'Hide' if _notes_open else 'Show'}"
            if st.button(_notes_lbl, key=f"notesbtn_{lid}", use_container_width=True):
                st.session_state[_notes_key] = not _notes_open
                st.rerun()
        with _nb2:
            _docs_lbl = f"Docs & Contacts - {'Hide' if _docs_open else 'Show'}"
            if st.button(_docs_lbl, key=f"docsbtn_{lid}", use_container_width=True):
                st.session_state[_docs_key] = not _docs_open
                st.rerun()

        if st.session_state.get(_notes_key):
            from crm import get_activity as _get_act
            _notes_txt = loan.get("notes", "") or "No notes."
            _conds = loan.get("conditions", [])
            _activity = _get_act(lid)
            _status_changes = [a for a in _activity if a.get("action") in ("status_manual", "status")]
            _activity_html = ""
            if _status_changes:
                _activity_html = (
                    '<div style="font-size:10px;font-weight:700;color:#3b82f6;text-transform:uppercase;'
                    'letter-spacing:0.8px;margin:10px 0 6px 0;">Status History</div>'
                    + "".join([
                        f'<div style="display:flex;gap:10px;padding:2px 0;font-size:10px;border-bottom:1px solid rgba(255,255,255,0.04);">'
                        f'<span style="color:#6b7280;white-space:nowrap;">{a["ts"]}</span>'
                        f'<span style="color:#d1d5db;">{a.get("detail","")}</span>'
                        f'<span style="color:#9ca3af;margin-left:auto;white-space:nowrap;">{a.get("user","") or "-"}</span>'
                        f'</div>'
                        for a in reversed(_status_changes[:10])
                    ])
                )
            st.markdown(
                f'<div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);'
                f'border-radius:6px;padding:10px 14px;margin-bottom:4px;">'
                f'<div style="font-size:10px;font-weight:700;color:#3b82f6;text-transform:uppercase;'
                f'letter-spacing:0.8px;margin-bottom:6px;">Notes</div>'
                f'<div style="font-size:12px;color:#d1d5db;line-height:1.5;">{_notes_txt}</div>'
                + (
                    f'<div style="font-size:10px;font-weight:700;color:#3b82f6;text-transform:uppercase;'
                    f'letter-spacing:0.8px;margin:10px 0 6px 0;">Conditions</div>'
                    + "".join([_pipeline_cond_row(c, contacts=loan.get("contacts",{}), loan_num=loan.get("loan_num",""), borrower=loan.get("borrower","")) for c in _conds])
                    if _conds else '<div style="color:#6b7280;font-size:11px;margin-top:8px;">No conditions.</div>'
                )
                + _activity_html
                + f'</div>',
                unsafe_allow_html=True,
            )

        if st.session_state.get(_docs_key):
            _pl_contacts = loan.get("contacts", {}) or {}
            _hoi_col, _title_col = st.columns(2)

            # â”€â”€ HOI side â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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
                        st.toast("HOI Request generated")
                        st.rerun()
                    except Exception as _e:
                        st.error(f"HOI gen failed: {_e}")
                _p_hoi = st.session_state.get(f"_pl_hoi_path_{lid}")
                if _p_hoi:
                    try:
                        with open(_p_hoi, "rb") as _fh:
                            st.download_button(
                                "Download HOI",
                                _fh.read(),
                                file_name=_p_hoi.split(chr(92))[-1] if chr(92) in _p_hoi else _p_hoi.split("/")[-1],
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                key=f"pl_dl_hoi_{lid}",
                                use_container_width=True,
                            )
                    except FileNotFoundError:
                        pass
                _rc = _pl_contacts.get("insurance") or {}
                if isinstance(_rc, str): _rc = {"name": _rc}
                _name = _rc.get("contact") or _rc.get("name") or _rc.get("company") or ""
                _phone, _email = _rc.get("phone", ""), _rc.get("email", "")
                import urllib.parse as _uparse
                _gmail_hoi = ("https://mail.google.com/mail/?view=cm&fs=1&" + _uparse.urlencode({"to": _email, "su": f"Re: {loan.get('loan_num','')} HOI"})) if _email else ""
                st.markdown(
                    '<div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.1);'
                    'border-radius:8px;padding:10px 12px;margin-top:6px;">'
                    '<div style="font-size:10px;color:#3b82f6;font-weight:700;text-transform:uppercase;margin-bottom:6px;">HOI / Insurance</div>'
                    + (f'<div style="color:#ffffff;font-size:12px;font-weight:600;margin-bottom:4px;">{_name}</div>' if _name else '')
                    + (f'<div style="color:#9ca3af;font-size:11px;margin-bottom:2px;">{_phone}</div>' if _phone else '')
                    + (f'<div style="display:flex;align-items:center;gap:8px;margin-top:4px;">'
                       f'<span style="color:#9ca3af;font-size:11px;">{_email}</span>'
                       f'<a href="{_gmail_hoi}" target="_blank" style="padding:2px 8px;background:rgba(66,133,244,0.12);'
                       f'border:1px solid rgba(66,133,244,0.35);border-radius:4px;color:#4285f4;font-size:10px;'
                       f'font-weight:700;text-decoration:none;">Gmail</a></div>' if _email else '')
                    + ('' if (_name or _phone or _email) else '<span style="color:#9ca3af;font-size:11px;">Not set</span>')
                    + '</div>',
                    unsafe_allow_html=True,
                )

            # â”€â”€ Title side â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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
                        st.toast("Title Request generated")
                        st.rerun()
                    except Exception as _e:
                        st.error(f"Title gen failed: {_e}")
                _p_ttl = st.session_state.get(f"_pl_title_path_{lid}")
                if _p_ttl:
                    try:
                        with open(_p_ttl, "rb") as _fh:
                            st.download_button(
                                "Download Title",
                                _fh.read(),
                                file_name=_p_ttl.split(chr(92))[-1] if chr(92) in _p_ttl else _p_ttl.split("/")[-1],
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                key=f"pl_dl_title_{lid}",
                                use_container_width=True,
                            )
                    except FileNotFoundError:
                        pass
                _rc = _pl_contacts.get("title") or {}
                if isinstance(_rc, str): _rc = {"name": _rc}
                _name = _rc.get("contact") or _rc.get("name") or _rc.get("company") or ""
                _phone, _email = _rc.get("phone", ""), _rc.get("email", "")
                _gmail_ttl = ("https://mail.google.com/mail/?view=cm&fs=1&" + _uparse.urlencode({"to": _email, "su": f"Re: {loan.get('loan_num','')} Title"})) if _email else ""
                st.markdown(
                    '<div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.1);'
                    'border-radius:8px;padding:10px 12px;margin-top:6px;">'
                    '<div style="font-size:10px;color:#3b82f6;font-weight:700;text-transform:uppercase;margin-bottom:6px;">Title Company</div>'
                    + (f'<div style="color:#ffffff;font-size:12px;font-weight:600;margin-bottom:4px;">{_name}</div>' if _name else '')
                    + (f'<div style="color:#9ca3af;font-size:11px;margin-bottom:2px;">{_phone}</div>' if _phone else '')
                    + (f'<div style="display:flex;align-items:center;gap:8px;margin-top:4px;">'
                       f'<span style="color:#9ca3af;font-size:11px;">{_email}</span>'
                       f'<a href="{_gmail_ttl}" target="_blank" style="padding:2px 8px;background:rgba(66,133,244,0.12);'
                       f'border:1px solid rgba(66,133,244,0.35);border-radius:4px;color:#4285f4;font-size:10px;'
                       f'font-weight:700;text-decoration:none;">Gmail</a></div>' if _email else '')
                    + ('' if (_name or _phone or _email) else '<span style="color:#9ca3af;font-size:11px;">Not set</span>')
                    + '</div>',
                    unsafe_allow_html=True,
                )

        # â”€â”€ Share this loan â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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
                        f"Share <b>#{loan.get('loan_num')} {loan.get('borrower')}</b> with:</div>",
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
                                    st.success(f"Shared with: {', '.join(ok)}")
                                for name, err in fail.items():
                                    st.error(f"{name}: {err}")
                                st.session_state[share_key] = False
                            else:
                                st.warning("Pick at least one person to share with.")

        st.markdown('<div style="height:2px;border-bottom:1px solid rgba(255,255,255,0.05);margin:2px 0;"></div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # â”€â”€ Removed / Recover Section â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    trash_items = get_trash()
    _cur_retention = get_retention_days()
    _ret_label = "Forever" if _cur_retention == 0 else f"{_cur_retention} days"
    _trash_label = f"Removed Loans ({len(trash_items)})" if trash_items else "Removed Loans"
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
                st.toast(f"Retention set to {_new_ret}")
                st.rerun()
        with rt3:
            if trash_items and st.button("Empty Removed", key="empty_trash", use_container_width=True):
                empty_trash()
                st.toast("All removed loans permanently deleted")
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
                        f'<span style="font-weight:700;color:#3b82f6;">#{tl.get("loan_num", "-")}</span>'
                        f' &nbsp;{tl.get("borrower", "-")}'
                        f' &nbsp;<span style="color:#9ca3af;font-size:10px;">removed {tl.get("deleted_on", "?")}</span>'
                        f' &nbsp;{_exp_tag}',
                        unsafe_allow_html=True,
                    )
                with tc2:
                    if st.button("Restore", key=f"restore_{t_lid}", use_container_width=True):
                        restore_loan(t_lid)
                        st.toast(f"Restored #{tl.get('loan_num', '')}")
                        st.rerun()
                with tc3:
                    if st.button("Delete", key=f"permdel_{t_lid}", use_container_width=True):
                        permanently_delete(t_lid)
                        st.toast("Permanently deleted")
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

    # â”€â”€ Smart Search (index-powered, instant) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    import document_index as _didx
    _sq = st.text_input("Search saved docs (borrower, loan #, doc type, keyword):",
                        placeholder="e.g. Smith bank statement  or  LOAN-12345",
                        key="reader_smart_search")
    if _sq:
        _hits = _didx.search(_sq)
        if _hits:
            st.caption(f"{len(_hits)} result(s)")
            for _h in _hits:
                _label = "  ".join(filter(None, [
                    _h.get("borrower"), _h.get("doc_type"),
                    _h.get("month"), _h.get("year"),
                ]))
                _fname = _h.get("file_name") or os.path.basename(_h["file_path"])
                _c1, _c2 = st.columns([6, 2])
                with _c1:
                    st.markdown(
                        f'<div style="font-size:13px;font-weight:600;color:#c0c0c0;">{_fname}</div>'
                        f'<div style="font-size:11px;color:#666;">{_label}</div>'
                        f'<div style="font-size:10px;color:#444;">{_h["file_path"]}</div>',
                        unsafe_allow_html=True,
                    )
                with _c2:
                    if os.path.exists(_h["file_path"]):
                        if st.button("Open", key=f"sr_open_{_h['id']}", use_container_width=True):
                            _ext = os.path.splitext(_h["file_path"])[1].lower()
                            st.session_state["reader_open_file"] = {
                                "name": _fname, "path": _h["file_path"],
                                "rel": _fname, "ext": _ext, "size_kb": 0,
                            }
                            st.session_state["reader_page"] = 1
                            st.rerun()
                    else:
                        st.caption("_(moved)_")
            st.markdown("---")
    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

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
                    f" Download {open_file['name']}",
                    _ifh.read(),
                    file_name=open_file["name"],
                    mime=f"image/{open_file['ext'].lstrip('.')}",
                    key=f"img_dl_{open_file['name']}",
                )
        else:
            # Offer download for office docs / unknown types
            try:
                with open(open_file["path"], "rb") as _ofh:
                    st.info("This file type can't be rendered inline download it below.")
                    st.download_button(
                        f" Download {open_file['name']}",
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
        "Add each person once after that, sharing is one click."
    )

    config = get_team_config()

    # â”€â”€ My Inbox Setup â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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
        f"<code style='color:#3b82f6;'>{config.get('my_inbox','(not set)')}</code>"
        f"</div>",
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # â”€â”€ Add Team Member â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    st.markdown("### Add a Team Member")
    st.caption(
        "Add each person you work with. You'll need their inbox folder path "
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
                    st.success(f"{new_name} added inbox is reachable!")
                else:
                    st.warning(
                        f"{new_name} added, but can't reach their inbox right now: {msg}. "
                        "You can still add them and share when the folder is accessible."
                    )
                st.rerun()

    st.markdown("---")

    # â”€â”€ Current Team List â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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
                    f"<div style='color:#3b82f6;font-size:13px;'>{m.get('role','')}</div>",
                    unsafe_allow_html=True,
                )
            with mc3:
                inbox_path = m.get("inbox", "")
                reachable = os.path.isdir(inbox_path) if inbox_path else False
                dot = "" if reachable else ""
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


# --- Quick Tool Functions ---

def show_snapshot_page():
    """Loan Snapshot - Complete vs Missing document view."""
    from loan_snapshot import generate_snapshot, get_missing_docs_email_body, DOCUMENT_REQUIREMENTS
    from crm import get_all_loans
    from pathlib import Path

    # Show current loan banner
    current_loan = show_current_loan_banner()

    if not current_loan:
        st.warning("Please select a loan to view its snapshot.")
        return

    # Try filesystem-based snapshot if folder exists; fall back to loan.documents list
    folder_path = current_loan.get("folder_path", "")
    if folder_path and Path(folder_path).exists():
        snapshot = generate_snapshot(Path(folder_path))
    else:
        # Synthesize snapshot from loan.documents / missing_docs
        docs = current_loan.get("documents", []) or []
        present_types = set()
        for d in docs:
            t = (d.get("doc_type") or d.get("type") or "").lower()
            for req_type, info in DOCUMENT_REQUIREMENTS.items():
                aliases = [a.lower() for a in info.get("aliases", [])] + [req_type.lower()]
                if any(a in t for a in aliases):
                    present_types.add(req_type)

        complete, missing = [], []
        for req_type, info in DOCUMENT_REQUIREMENTS.items():
            if req_type in present_types:
                complete.append({"document": req_type, "files": []})
            elif info.get("required"):
                missing.append({"document": req_type, "required": True})

        snapshot = {
            "loan_folder": current_loan.get("borrower", ""),
            "complete": complete,
            "missing": missing,
            "stale": [],
            "partial": [],
            "complete_count": len(complete),
            "missing_count": len(missing),
            "stale_count": 0,
            "partial_count": 0,
        }

    st.markdown(
        '<div style="font-size:18px;font-weight:800;color:#ffffff;letter-spacing:-0.3px;margin-bottom:16px;">'
        'Loan Snapshot</div>',
        unsafe_allow_html=True,
    )

    sc1, sc2, sc3, sc4 = st.columns(4)
    with sc1:
        st.markdown(f'<div class="stat-card"><div class="stat-num" style="color:#3b82f6;">{snapshot["complete_count"]}</div><div class="stat-label">Complete</div></div>', unsafe_allow_html=True)
    with sc2:
        st.markdown(f'<div class="stat-card"><div class="stat-num" style="color:#ef4444;">{snapshot["missing_count"]}</div><div class="stat-label">Missing</div></div>', unsafe_allow_html=True)
    with sc3:
        st.markdown(f'<div class="stat-card"><div class="stat-num" style="color:#f59e0b;">{snapshot["stale_count"]}</div><div class="stat-label">Stale</div></div>', unsafe_allow_html=True)
    with sc4:
        st.markdown(f'<div class="stat-card"><div class="stat-num" style="color:#a78bfa;">{snapshot["partial_count"]}</div><div class="stat-label">Optional</div></div>', unsafe_allow_html=True)

    if snapshot["missing"]:
        st.markdown('<div style="font-size:11px;font-weight:700;color:#9ca3af;text-transform:uppercase;letter-spacing:0.5px;margin:14px 0 6px;">Missing</div>', unsafe_allow_html=True)
        for m in snapshot["missing"]:
            st.markdown(
                f'<div style="padding:5px 10px;margin:3px 0;background:rgba(239,68,68,0.1);'
                f'border-left:3px solid #ef4444;border-radius:4px;font-size:12px;color:#ef4444;">'
                f'{m["document"]}</div>',
                unsafe_allow_html=True,
            )

    if snapshot.get("stale"):
        st.markdown('<div style="font-size:11px;font-weight:700;color:#9ca3af;text-transform:uppercase;letter-spacing:0.5px;margin:14px 0 6px;">Needs Refresh</div>', unsafe_allow_html=True)
        for sdoc in snapshot["stale"]:
            st.markdown(
                f'<div style="padding:5px 10px;margin:3px 0;background:rgba(245,158,11,0.1);'
                f'border-left:3px solid #f59e0b;border-radius:4px;font-size:12px;color:#f59e0b;">'
                f'{sdoc["document"]} {sdoc["age_days"]}d old</div>',
                unsafe_allow_html=True,
            )

    if snapshot["missing"]:
        st.markdown("---")
        if st.button("Generate Missing Docs Email", key="gen_missing_email", type="secondary"):
            st.text_area("Email body", value=get_missing_docs_email_body(snapshot), height=180)


def show_report_issue_page():
    """Report Issue saves locally with SSN/account masking."""
    from feedback_reporter import save_report

    st.markdown('<div id="report_issue"></div>', unsafe_allow_html=True)

    if st.session_state.get("scroll_to") == "report_issue":
        st.markdown('<script>document.getElementById("report_issue").scrollIntoView({behavior: "smooth"});</script>', unsafe_allow_html=True)
        del st.session_state["scroll_to"]

    st.markdown(
        '<div style="font-size:18px;font-weight:800;color:#ffffff;letter-spacing:-0.3px;margin-bottom:16px;">'
        'Report Issue</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div style="background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.3);border-radius:8px;padding:12px;margin-bottom:20px;">'
        '<div style="font-size:13px;color:#ef4444;">'
        '<b>SSN & Bank Account Masking:</b> Last 4 digits only will be shared (XXX-XX-XXXX, XXXX-XXXX).</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    issue_text = st.text_area("Describe the problem:", height=120, key="report_issue_text")

    col1, col2 = st.columns(2)
    with col1:
        loan_id = st.text_input("Loan ID (optional)", key="report_loan_id")
    with col2:
        attached_file = st.text_input("Attach file path (optional)", key="report_file")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Submit Report", type="primary", key="report_submit"):
            if issue_text.strip():
                result = save_report(
                    issue_text,
                    attached_file if attached_file else None,
                    loan_id if loan_id else None,
                )
                if result.get("success"):
                    st.success(f"Report saved: {result.get('report_id')}")
                    st.markdown("**Report saved successfully!** Sensitive data has been masked before sharing.")
                else:
                    st.error("Failed to save report")
            else:
                st.warning("Please describe the issue")
    with col2:
        if st.button("Cancel", key="report_cancel"):
            st.session_state["show_report_issue"] = False
            st.rerun()


def show_missing_docs_page():
    """Missing Docs Checker."""
    from loan_snapshot import scan_folder_for_documents, DOCUMENT_REQUIREMENTS
    from crm import get_all_loans
    from pathlib import Path

    st.markdown('<div id="missing_docs"></div>', unsafe_allow_html=True)

    if st.session_state.get("scroll_to") == "missing_docs":
        st.markdown('<script>document.getElementById("missing_docs").scrollIntoView({behavior: "smooth"});</script>', unsafe_allow_html=True)
        del st.session_state["scroll_to"]

    st.markdown(
        '<div style="font-size:18px;font-weight:800;color:#ffffff;letter-spacing:-0.3px;margin-bottom:16px;">'
        'Missing Documents Checker</div>',
        unsafe_allow_html=True,
    )

    _DOCS_BASE = os.path.join(os.path.dirname(__file__), "loan_docs")
    all_loans = _visible_account_loans(get_all_loans())
    loan_options = {f"{l['borrower']} ({l['loan_num']})": str(l["id"]) for l in all_loans}
    loan_options["Custom Folder"] = None

    selected_label = st.selectbox("Select Loan", list(loan_options.keys()), key="missing_loan_select")
    selected_id = loan_options[selected_label]

    folder = None
    if selected_id is None:
        folder_input = st.text_input("Folder path", key="missing_folder_input")
        if folder_input:
            folder = Path(folder_input)
    else:
        folder = Path(os.path.join(_DOCS_BASE, selected_id))

    if folder and folder.exists():
        found = scan_folder_for_documents(folder)
        all_required = [d for d, info in DOCUMENT_REQUIREMENTS.items() if info.get("required")]

        st.markdown('<div style="font-size:11px;font-weight:700;color:#9ca3af;text-transform:uppercase;letter-spacing:0.5px;margin:10px 0 6px;">Required Documents</div>', unsafe_allow_html=True)
        for doc_type in all_required:
            if doc_type in found:
                st.markdown(
                    f'<div style="padding:5px 10px;margin:3px 0;background:rgba(59,130,246,0.1);'
                    f'border-left:3px solid #3b82f6;border-radius:4px;font-size:12px;color:#3b82f6;">'
                    f'{doc_type}</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f'<div style="padding:5px 10px;margin:3px 0;background:rgba(239,68,68,0.1);'
                    f'border-left:3px solid #ef4444;border-radius:4px;font-size:12px;color:#ef4444;">'
                    f'{doc_type}</div>',
                    unsafe_allow_html=True,
                )
    elif folder:
        st.warning("No documents folder found for this loan yet.")

    if st.button("Close", key="missing_close", type="secondary"):
        st.session_state["show_missing_docs"] = False
        st.rerun()


def show_doc_expiry_page():
    """Document Expiry Tracker."""
    from doc_expiry_tracker import get_expiry_warnings
    from crm import get_all_loans
    from pathlib import Path

    st.markdown('<div id="doc_expiry"></div>', unsafe_allow_html=True)

    if st.session_state.get("scroll_to") == "doc_expiry":
        st.markdown('<script>document.getElementById("doc_expiry").scrollIntoView({behavior: "smooth"});</script>', unsafe_allow_html=True)
        del st.session_state["scroll_to"]

    st.markdown(
        '<div style="font-size:18px;font-weight:800;color:#ffffff;letter-spacing:-0.3px;margin-bottom:16px;">'
        'Document Expiry Tracker</div>',
        unsafe_allow_html=True,
    )

    _DOCS_BASE = os.path.join(os.path.dirname(__file__), "loan_docs")
    all_loans = _visible_account_loans(get_all_loans())
    loan_options = {f"{l['borrower']} ({l['loan_num']})": str(l["id"]) for l in all_loans}
    loan_options["Custom Folder"] = None

    selected_label = st.selectbox("Select Loan", list(loan_options.keys()), key="expiry_loan_select")
    selected_id = loan_options[selected_label]

    folder = None
    if selected_id is None:
        folder_input = st.text_input("Folder path", key="expiry_folder_input")
        if folder_input:
            folder = Path(folder_input)
    else:
        folder = Path(os.path.join(_DOCS_BASE, selected_id))

    if folder and folder.exists():
        warnings = get_expiry_warnings(folder)

        if warnings["expired"]:
            st.markdown('<div style="font-size:11px;font-weight:700;color:#ef4444;text-transform:uppercase;letter-spacing:0.5px;margin:10px 0 6px;">Expired</div>', unsafe_allow_html=True)
            for doc in warnings["expired"]:
                st.markdown(
                    f'<div style="padding:5px 10px;margin:3px 0;background:rgba(239,68,68,0.15);'
                    f'border-left:3px solid #ef4444;border-radius:4px;font-size:12px;color:#ef4444;">'
                    f'{doc.name}</div>',
                    unsafe_allow_html=True,
                )

        if warnings["expiring_soon"]:
            st.markdown('<div style="font-size:11px;font-weight:700;color:#f59e0b;text-transform:uppercase;letter-spacing:0.5px;margin:10px 0 6px;">Expiring Soon</div>', unsafe_allow_html=True)
            for doc in warnings["expiring_soon"]:
                st.markdown(
                    f'<div style="padding:5px 10px;margin:3px 0;background:rgba(245,158,11,0.15);'
                    f'border-left:3px solid #f59e0b;border-radius:4px;font-size:12px;color:#f59e0b;">'
                    f'{doc.name} {doc.days_until_expiry}d</div>',
                    unsafe_allow_html=True,
                )

        if warnings["okay"]:
            st.markdown('<div style="font-size:11px;font-weight:700;color:#9ca3af;text-transform:uppercase;letter-spacing:0.5px;margin:10px 0 6px;">OK</div>', unsafe_allow_html=True)
            for doc in warnings["okay"]:
                st.markdown(
                    f'<div style="padding:5px 10px;margin:3px 0;background:rgba(59,130,246,0.1);'
                    f'border-left:3px solid #3b82f6;border-radius:4px;font-size:12px;color:#3b82f6;">'
                    f'{doc.name} {doc.days_until_expiry}d</div>',
                    unsafe_allow_html=True,
                )

        if not any([warnings["expired"], warnings["expiring_soon"], warnings["okay"]]):
            st.info("No tracked documents found for this loan.")
    elif folder:
        st.warning("No documents folder found for this loan yet.")

    if st.button("Close", key="expiry_close", type="secondary"):
        st.session_state["show_doc_expiry"] = False
        st.rerun()


def show_spanish_reply_page():
    """Spanish Reply auto-detect language, translate, draft."""
    from spanish_reply import detect_language, translate_to_english, translate_to_spanish, get_spanish_template, get_english_template

    st.markdown('<div id="spanish_reply"></div>', unsafe_allow_html=True)

    if st.session_state.get("scroll_to") == "spanish_reply":
        st.markdown('<script>document.getElementById("spanish_reply").scrollIntoView({behavior: "smooth"});</script>', unsafe_allow_html=True)
        del st.session_state["scroll_to"]

    st.markdown(
        '<div style="font-size:18px;font-weight:800;color:#ffffff;letter-spacing:-0.3px;margin-bottom:8px;">'
        'Spanish Reply Window</div>'
        '<div style="font-size:13px;color:#9ca3af;margin-bottom:16px;">'
        'Auto-detects language and helps you reply in the borrower\'s preferred language</div>',
        unsafe_allow_html=True,
    )

    # Use sample text if no email data
    m = st.session_state.get("spanish_reply_data") or {}
    original_text = (m.get("subject", "") + "\n" + m.get("body", "")).strip()

    # Always show the input area and sample buttons
    st.markdown("**Enter or paste a borrower email:**")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Sample Spanish Email", key="sample_spanish"):
            sample_text = "Estimado seÃ±or, necesitamos los documentos de su prÃ©stamo para continuar con el proceso. Por favor envÃ­e sus estados de cuenta y talones de pago."
            st.session_state["spanish_input_text"] = sample_text
            st.rerun()
    with col2:
        if st.button("Sample English Email", key="sample_english"):
            sample_text = "Dear borrower, we need your loan documents to continue processing. Please send your bank statements and pay stubs."
            st.session_state["spanish_input_text"] = sample_text
            st.rerun()

    original_text = st.text_area("Email text", height=100, key="spanish_input_text",
                               placeholder="Paste a borrower email here, or click a sample button above...",
                               value=original_text if original_text else st.session_state.get("spanish_input_text", ""))

    # Process the text if we have any
    if original_text and original_text.strip():
        st.markdown("---")

        detection = detect_language(original_text)

        if detection.is_spanish:
            st.markdown(
                f'<div style="padding:7px 12px;margin-bottom:14px;background:rgba(167,139,250,0.15);'
                f'border-left:3px solid #a78bfa;border-radius:4px;font-size:12px;color:#a78bfa;">'
                f'Spanish Email Detected {detection.confidence:.0%} confidence</div>',
                unsafe_allow_html=True,
            )

            with st.spinner("Translating..."):
                english_translation = translate_to_english(original_text)

            if english_translation and not english_translation.startswith("[Error"):
                st.success("Translation complete!")
                st.markdown("**English Translation:**")
                st.text_area("Translated text", value=english_translation, height=110, key="spanish_translated")
            else:
                st.error(" Translation failed. Please check your internet connection.")
                st.markdown("**Original Spanish Text:**")
                st.text_area("Original text", value=original_text, height=110, key="spanish_original")

            st.markdown("**Write your reply in English:**")
            english_reply = st.text_area("Your reply in English", height=90, key="spanish_reply_en",
                                       placeholder="Type your response in English here... e.g., 'Thank you for your email. We need your bank statements and pay stubs.'")

            if st.button("Translate to Spanish & Generate Email Draft", key="spanish_translate_btn", type="primary", disabled=not english_reply.strip()):
                if english_reply.strip():
                    with st.spinner("Translating to Spanish..."):
                        spanish_draft = translate_to_spanish(english_reply)

                    if spanish_draft and not spanish_draft.startswith("[Error"):
                        st.success("Spanish translation complete!")
                        st.markdown("**Spanish Email Draft (ready to copy to Gmail):**")
                        st.text_area("Copy this Spanish text to Gmail", value=spanish_draft, height=150, key="spanish_final_draft")
                        st.info("Copy the text above and paste it into Gmail to send to your Spanish-speaking borrower!")
                    else:
                        st.error(" Translation failed. Please try again.")
                else:
                    st.warning("Please enter a reply first.")
    else:
        st.markdown(
            '<div style="padding:7px 12px;margin-bottom:14px;background:rgba(59,130,246,0.1);'
            'border-left:3px solid #3b82f6;border-radius:4px;font-size:12px;color:#3b82f6;">'
            'English Email Detected Generate Spanish Reply Templates</div>',
            unsafe_allow_html=True,
        )

        st.markdown("**Enter the loan conditions/requirements:**")
        conditions = st.text_area("Conditions (e.g., '1. Bank statements\\n2. Pay stubs')", height=80, key="spanish_conds",
                                placeholder="1. Government-issued photo ID\n2. Recent bank statements\n3. Recent pay stubs")

        if st.button("Generate Spanish & English Email Templates", key="spanish_gen_btn", type="primary"):
            tab_es, tab_en = st.tabs(["Spanish Draft", "English Draft"])
            with tab_es:
                st.markdown("**Spanish Email Template (ready to send to borrower):**")
                st.text_area("Spanish version", value=get_spanish_template(conditions), height=220, key="spanish_gen_out")
            with tab_en:
                st.markdown("**English Email Template (for reference):**")
                st.text_area("English version", value=get_english_template(conditions), height=220, key="english_gen_out")

            if conditions.strip():
                st.info("Copy the Spanish draft and paste into Gmail to send to your Spanish-speaking borrower!")
            else:
                st.info("Add conditions above to generate personalized email templates.")

    st.markdown("---")
    col_close, col_clear = st.columns(2)
    with col_close:
        if st.button("Close", key="spanish_close", type="secondary"):
            st.session_state["spanish_reply_data"] = None
            st.session_state["spanish_input_text"] = ""
            for key in ["spanish_translated", "spanish_reply_en", "spanish_final_draft", "spanish_gen_out", "english_gen_out"]:
                st.session_state.pop(key, None)
            st.rerun()
    with col_clear:
        if st.button("Clear All", key="spanish_clear", type="secondary"):
            st.session_state["spanish_input_text"] = ""
            for key in ["spanish_translated", "spanish_reply_en", "spanish_final_draft", "spanish_gen_out", "english_gen_out"]:
                st.session_state.pop(key, None)
            st.rerun()


# --- New Advanced Tool Pages ---

def show_income_verifier_page():
    """Income Verifier - Full Income/Employment Verification + 1003 Comparison."""
    from income_verifier import IncomeVerifier
    from crm import get_all_loans

    # Show current loan banner
    current_loan = show_current_loan_banner()

    st.markdown(
        '<div style="font-size:18px;font-weight:800;color:#ffffff;letter-spacing:-0.3px;margin-bottom:16px;">'
        'Income & Employment Verifier</div>',
        unsafe_allow_html=True,
    )

    st.markdown("Compare extracted document data against 1003 loan application data.")

    # Select loan
    all_loans = _visible_account_loans(get_all_loans())
    loan_options = {f"{l['borrower']} ({l['loan_num']})": l for l in all_loans}
    selected_loan = st.selectbox("Select Loan", list(loan_options.keys()))

    if selected_loan:
        loan_data = loan_options[selected_loan]

        # Get extracted data (this would come from AI processing)
        scan_results = st.session_state.get("scan_results")
        extracted_data = scan_results.get("extracted_data", {}) if scan_results else {}

        if extracted_data:
            verifier = IncomeVerifier()
            results = verifier.verify_income(extracted_data, loan_data)

            # Display results
            st.markdown(f"## Status: {results['overall_status']}")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Income Matches", len(results.get("income_matches", [])))
            with col2:
                st.metric("Income Discrepancies", len(results.get("income_discrepancies", [])))
            with col3:
                st.metric("Employment Matches", len(results.get("employment_matches", [])))

            if results["income_discrepancies"] or results["employment_discrepancies"]:
                st.markdown("### Issues Requiring Attention")
                for disc in results["income_discrepancies"] + results["employment_discrepancies"]:
                    st.error(f"{disc}")

            if results["recommendations"]:
                st.markdown("### Recommendations")
                for rec in results["recommendations"]:
                    st.info(f"{rec}")
        else:
            st.warning("No extracted data available. Please scan documents first.")


def show_auto_data_entry_page():
    """Auto Data Entry - Automatically fill forms from extracted document data."""
    from auto_data_entry import AutoDataEntry

    st.markdown(
        '<div style="font-size:18px;font-weight:800;color:#ffffff;letter-spacing:-0.3px;margin-bottom:16px;">'
        'Auto Data Entry</div>',
        unsafe_allow_html=True,
    )

    st.markdown("Automatically fill loan application forms using extracted document data.")

    # Sample form template
    form_template = {
        "borrower_name": "",
        "borrower_ssn": "",
        "borrower_dob": "",
        "monthly_gross_income": "",
        "employer_name": "",
        "account_number": "",
        "loan_amount": ""
    }

    # Get extracted data
    scan_results = st.session_state.get("scan_results")
    extracted_data = scan_results.get("extracted_data", {}) if scan_results else {}

    if extracted_data:
        data_entry = AutoDataEntry()
        filled_form = data_entry.fill_form(extracted_data, form_template)

        st.markdown("### Filled Form Fields")
        for field, value in filled_form.items():
            if value:
                st.success(f"{field.replace('_', ' ').title()}: {value}")
            else:
                st.warning(f" {field.replace('_', ' ').title()}: Not filled")

        # Show statistics
        stats = data_entry.get_fill_statistics(form_template, filled_form)
        st.markdown(f"**Completion: {stats['completion_percentage']:.1f}%** ({stats['filled_fields']}/{stats['total_fields']} fields)")

        # Validation
        errors = data_entry.validate_filled_form(filled_form)
        if errors:
            st.markdown("### Validation Issues")
            for error in errors:
                st.error(f"{error}")
    else:
        st.warning("No extracted data available. Please scan documents first.")


def show_credit_summary_page():
    """Credit Summary - Basic Credit Report Import & Summary."""
    from credit_summary import CreditSummary

    st.markdown(
        '<div style="font-size:18px;font-weight:800;color:#ffffff;letter-spacing:-0.3px;margin-bottom:16px;">'
        'Credit Report Summary</div>',
        unsafe_allow_html=True,
    )

    credit_text = st.text_area("Paste credit report text here", height=200)

    if credit_text and st.button("Analyze Credit Report", type="primary"):
        summary = CreditSummary().summarize(credit_text)

        # Main metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Credit Score", summary.get("credit_score", "N/A"))
        with col2:
            st.metric("Risk Level", summary.get("risk_level", "Unknown"))
        with col3:
            st.metric("Accounts", summary.get("total_accounts", 0))

        # Flags and recommendations
        if summary.get("flags"):
            st.markdown("### Red Flags")
            for flag in summary["flags"]:
                st.error(flag)

        if summary.get("recommendations"):
            st.markdown("### Recommendations")
            for rec in summary["recommendations"]:
                st.info(f"{rec}")

        st.markdown(f"**Analysis:** {summary.get('analysis', 'No analysis available')}")


def show_current_loan_banner():
    """Show current loan information banner."""
    from crm import get_all_loans

    loans = _visible_account_loans(get_all_loans())
    if loans:
        # Show current/selected loan
        current_loan_id = st.session_state.get("current_loan_id")
        if current_loan_id:
            current_loan = next((l for l in loans if l.get("id") == current_loan_id), None)
            if current_loan:
                st.markdown(
                    f'<div style="background:#1a1a1a;border:1px solid #3b82f6;border-radius:8px;padding:12px 16px;margin-bottom:20px;">'
                    f'<div style="color:#3b82f6;font-weight:600;font-size:14px;margin-bottom:4px;">Current Loan</div>'
                    f'<div style="color:#ffffff;font-weight:700;font-size:16px;">{current_loan["borrower"]}</div>'
                    f'<div style="color:#9ca3af;font-size:13px;margin-top:2px;">{current_loan["loan_num"]} {current_loan["status"]}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                return current_loan

        # If no current loan, show selector
        loan_options = {str(l["id"]): f"{l['borrower']} ({l['loan_num']})" for l in loans}
        selected_loan_id = st.selectbox(
            "Select Current Loan:",
            options=list(loan_options.keys()),
            format_func=lambda x: loan_options[x],
            key="current_loan_selector"
        )
        if selected_loan_id:
            st.session_state["current_loan_id"] = int(selected_loan_id)
            st.rerun()

    return None

def show_dti_calculator_page():
    """DTI Calculator - Debt-to-Income & Closing Cost Calculator."""
    from dti_calculator import DTICalculator

    # Show current loan banner
    current_loan = show_current_loan_banner()

    st.markdown(
        '<div style="font-size:18px;font-weight:800;color:#ffffff;letter-spacing:-0.3px;margin-bottom:16px;">'
        'DTI & Closing Cost Calculator</div>',
        unsafe_allow_html=True,
    )

    calc = DTICalculator()

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### DTI Calculation")

        # Pull from scanned data button
        col_pull, col_manual = st.columns([1, 1])
        with col_pull:
            if st.button("Pull from Last Scan", key="pull_scan_dti"):
                from financial_extractor import FinancialDataExtractor

                # Get extracted data using the financial extractor
                scan_results = st.session_state.get("scan_results")
                if scan_results:
                    extractor = FinancialDataExtractor()
                    dti_data = extractor.extract_for_dti(scan_results)

                    # Update session state with extracted data
                    st.session_state["dti_income"] = dti_data["monthly_gross_income"]
                    st.session_state["dti_debt"] = dti_data["monthly_debt_payments"]
                    st.session_state["dti_source"] = dti_data["source"]
                    st.session_state["dti_confidence"] = dti_data["confidence"]
                    st.rerun()

        with col_manual:
            if st.button("Clear Manual Input", key="clear_manual_dti"):
                st.session_state["dti_income"] = 0.0
                st.session_state["dti_debt"] = 0.0
                st.session_state["dti_housing"] = 0.0
                st.rerun()

        # Input fields with session state persistence
        income = st.number_input("Monthly Gross Income", min_value=0.0,
                               value=st.session_state.get("dti_income", 0.0), key="dti_income_input")
        debt = st.number_input("Monthly Debt Payments", min_value=0.0,
                             value=st.session_state.get("dti_debt", 0.0), key="dti_debt_input")
        housing = st.number_input("Proposed Housing Payment", min_value=0.0,
                                value=st.session_state.get("dti_housing", 0.0), key="dti_housing_input")
        loan_type = st.selectbox("Loan Type", ["conventional", "fha", "va"])

        # Show data source indicator
        data_source = st.session_state.get("dti_source", "manual")
        confidence = st.session_state.get("dti_confidence", "low")

        if data_source == "scanned_documents":
            confidence_icon = {"high": "", "medium": "", "low": ""}.get(confidence, "")
            st.info(f"Auto-filled from scanned documents ({confidence_icon} {confidence} confidence)")
        elif st.session_state.get("dti_income", 0) > 0:
            st.info("Manually entered data")

        if st.button("Calculate DTI", type="primary"):
            result = calc.calculate_dti(income, debt, housing, loan_type)

            # Check for errors
            if "error" in result:
                st.error(f" Calculation Error: {result['error']}")
                st.info("Please ensure Monthly Gross Income is greater than $0")
                return

            st.markdown(f"**Front-End DTI:** {result['front_end_dti']:.1f}% (Limit: {result['front_end_limit']}%)")
            st.markdown(f"**Back-End DTI:** {result['back_end_dti']:.1f}% (Limit: {result['back_end_limit']}%)")
            st.markdown(f"**Status:** {result['overall_qualified']}")

            if result.get("recommendations"):
                st.markdown("### Recommendations")
                for rec in result["recommendations"]:
                    st.info(rec)

    with col2:
        st.markdown("### Closing Cost Calculator")

        # Pull from scanned data button for closing costs
        col_pull_cc, col_clear_cc = st.columns([1, 1])
        with col_pull_cc:
            if st.button("Pull from Last Scan", key="pull_scan_cc"):
                from financial_extractor import FinancialDataExtractor

                # Get extracted data using the financial extractor
                scan_results = st.session_state.get("scan_results")
                if scan_results:
                    extractor = FinancialDataExtractor()
                    closing_data = extractor.extract_for_closing_costs(scan_results)

                    # Update session state with extracted data
                    st.session_state["cc_loan_amt"] = closing_data["loan_amount"]
                    st.session_state["cc_property_val"] = closing_data["property_value"]
                    st.session_state["cc_source"] = closing_data["source"]
                    st.session_state["cc_confidence"] = closing_data["confidence"]
                    st.rerun()

        with col_clear_cc:
            if st.button("Clear", key="clear_cc"):
                st.session_state["cc_loan_amt"] = 0.0
                st.session_state["cc_property_val"] = 0.0
                st.rerun()

        # Input fields with session state persistence
        loan_amt = st.number_input("Loan Amount ($)", min_value=0.0,
                                 value=st.session_state.get("cc_loan_amt", 0.0), key="cc_loan_amt_input")
        property_val = st.number_input("Property Value ($)", min_value=0.0,
                                     value=st.session_state.get("cc_property_val", 0.0), key="cc_property_val_input")
        loan_type_cc = st.selectbox("Transaction Type", ["purchase", "refinance"], key="cc_type")

        # Show data source indicator
        data_source = st.session_state.get("cc_source", "manual")
        confidence = st.session_state.get("cc_confidence", "low")

        if data_source == "scanned_documents":
            confidence_icon = {"high": "", "medium": "", "low": ""}.get(confidence, "")
            st.info(f"Auto-filled from scanned documents ({confidence_icon} {confidence} confidence)")
        elif st.session_state.get("cc_loan_amt", 0) > 0 or st.session_state.get("cc_property_val", 0) > 0:
            st.info("Manually entered data")

        if st.button("Calculate Closing Costs", type="primary"):
            result = calc.calculate_closing_costs(loan_amt, property_val, loan_type_cc)

            st.markdown(f"**Total Closing Costs:** ${result['total_closing_costs']:,.2f}")
            st.markdown(f"**Total Cash Needed:** ${result['total_cash_needed']:,.2f}")
            st.markdown(f"**LTV Ratio:** {result['ltv_ratio']:.1f}%")


def show_condition_clearer_page():
    """Condition Clearer - Underwriting Condition Clearing Module."""
    from condition_clearer import ConditionClearer

    st.markdown(
        '<div style="font-size:18px;font-weight:800;color:#ffffff;letter-spacing:-0.3px;margin-bottom:16px;">'
        'Underwriting Condition Clearer</div>',
        unsafe_allow_html=True,
    )

    condition_text = st.text_area("Enter underwriting condition", height=100,
                                 placeholder="Example: Provide paystub for the last 30 days")

    # Get uploaded documents
    uploaded_docs = st.session_state.get("scan_batches", [])

    if condition_text and st.button("Check Condition", type="primary"):
        clearer = ConditionClearer()
        result = clearer.clear_condition(condition_text, uploaded_docs)

        st.markdown(f"## Status: {result['status']}")
        st.markdown(f"**Confidence:** {result['confidence']}%")
        st.markdown(f"**Reason:** {result['reason']}")

        if result.get("matching_docs"):
            st.markdown("### Matching Documents")
            for doc in result["matching_docs"]:
                st.success(f"{doc['filename']} ({doc['confidence']}% match)")


def show_compliance_checker_page():
    """Compliance Checker - Compliance Checklist + Flagging System."""
    from compliance_checker import ComplianceChecker

    st.markdown(
        '<div style="font-size:18px;font-weight:800;color:#ffffff;letter-spacing:-0.3px;margin-bottom:16px;">'
        'Compliance Checker</div>',
        unsafe_allow_html=True,
    )

    # Sample loan data input
    st.markdown("### Loan Information")
    col1, col2, col3 = st.columns(3)

    with col1:
        loan_type = st.selectbox("Loan Type", ["conventional", "fha", "va", "usda"])
        dti = st.number_input("DTI Ratio (%)", min_value=0.0, max_value=100.0)

    with col2:
        ltv = st.number_input("LTV Ratio (%)", min_value=0.0, max_value=200.0)
        credit_score = st.number_input("Credit Score", min_value=300, max_value=900)

    with col3:
        loan_amount = st.number_input("Loan Amount ($)", min_value=0)

    loan_data = {
        "loan_type": loan_type,
        "dti_ratio": dti,
        "ltv_ratio": ltv,
        "credit_score": credit_score,
        "loan_amount": loan_amount
    }

    if st.button("Run Compliance Check", type="primary"):
        checker = ComplianceChecker()
        results = checker.check_compliance(loan_data)

        # Overall status
        st.markdown(f"## Overall Status: {results['overall_status']}")
        st.markdown(f"**Compliance Score:** {results['compliance_score']}%")

        # Category breakdown
        for category_name, category_results in results["check_categories"].items():
            with st.expander(f"{category_name.title()} - {category_results['status']}", expanded=True):
                st.markdown(f"**Score:** {category_results['score']}%")
                if category_results.get("flags"):
                    for flag in category_results["flags"]:
                        if "" in flag:
                            st.error(flag)
                        elif "" in flag:
                            st.warning(flag)
                        else:
                            st.info(flag)

        # Recommendations
        if results.get("recommendations"):
            st.markdown("### Recommendations")
            for rec in results["recommendations"]:
                st.info(f"{rec}")


# --- New Advanced Tool Pages ---

def show_closing_package_page():
    """Closing Package Generator - Create and organize closing packages."""
    from closing_package import ClosingPackageGenerator

    st.markdown(
        '<div style="font-size:18px;font-weight:800;color:#ffffff;letter-spacing:-0.3px;margin-bottom:16px;">'
        'Closing Package Generator</div>',
        unsafe_allow_html=True,
    )

    st.markdown("Generate organized closing packages from loan documents.")

    borrower_name = st.text_input("Borrower Name", key="closing_borrower")
    loan_folder = st.text_input("Loan Folder Path", key="closing_folder")

    if borrower_name and loan_folder and st.button("Generate Closing Package", type="primary"):
        generator = ClosingPackageGenerator()
        result = generator.generate(loan_folder, borrower_name)

        if result.get("success"):
            st.success("Closing package generated successfully!")
            st.markdown(f"**Package Location:** {result['package_folder']}")
            st.markdown(f"**Documents Included:** {result['documents_included']}")
            st.markdown(f"**Documents Missing:** {len(result.get('missing_documents', []))}")

            if result.get("missing_documents"):
                st.warning("Missing documents:")
                for doc in result["missing_documents"]:
                    st.write(f"{doc}")
        else:
            st.error(f" Failed to generate package: {result.get('error', 'Unknown error')}")


def show_pipeline_dashboard_page():
    """Pipeline Dashboard with Deadline Alerts."""
    from pipeline_dashboard import PipelineDashboard
    from crm import get_all_loans

    st.markdown(
        '<div style="font-size:18px;font-weight:800;color:#ffffff;letter-spacing:-0.3px;margin-bottom:16px;">'
        'Pipeline Dashboard</div>',
        unsafe_allow_html=True,
    )

    st.markdown("Monitor loan pipeline with deadline alerts and status tracking.")

    loans = _visible_account_loans(get_all_loans())
    dashboard = PipelineDashboard()
    alerts = dashboard.get_alerts(loans)
    summary = dashboard.get_pipeline_summary(loans)

    # Show alerts
    if alerts["total"] > 0:
        st.markdown("## Pipeline Alerts")

        if alerts["urgent"]:
            st.error("### URGENT (Closing within 3 days)")
            for alert in alerts["urgent"]:
                st.write(f"{alert['message']}")

        if alerts["warning"]:
            st.warning("### WARNING (Closing within 7 days)")
            for alert in alerts["warning"]:
                st.write(f"{alert['message']}")

        if alerts["notice"]:
            st.info("### NOTICE (Closing within 14 days)")
            for alert in alerts["notice"]:
                st.write(f"{alert['message']}")

    # Show summary
    st.markdown("## Pipeline Summary")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Loans", summary["total_loans"])
    with col2:
        st.metric("Closing This Week", summary["closing_this_week"])
    with col3:
        st.metric("Closing This Month", summary["closing_this_month"])
    with col4:
        st.metric("Avg Days in Pipeline", f"{summary['average_days_in_pipeline']:.1f}")


def show_guideline_checker_page():
    """Investor Guideline Checker."""
    from guideline_checker import GuidelineChecker

    st.markdown(
        '<div style="font-size:18px;font-weight:800;color:#ffffff;letter-spacing:-0.3px;margin-bottom:16px;">'
        'Investor Guideline Checker</div>',
        unsafe_allow_html=True,
    )

    st.markdown("Check loans against Fannie Mae and Freddie Mac guidelines.")

    investor = st.selectbox("Investor", ["fannie", "freddie"], format_func=lambda x: x.title() + " Mae")
    dti = st.number_input("DTI Ratio (%)", min_value=0.0, max_value=100.0)
    ltv = st.number_input("LTV Ratio (%)", min_value=0.0, max_value=200.0)
    credit_score = st.number_input("Credit Score", min_value=300, max_value=900)
    loan_amount = st.number_input("Loan Amount ($)", min_value=0)

    loan_data = {
        "dti_ratio": dti,
        "ltv_ratio": ltv,
        "credit_score": credit_score,
        "loan_amount": loan_amount
    }

    if st.button("Check Guidelines", type="primary"):
        checker = GuidelineChecker(investor)
        result = checker.check(loan_data)

        st.markdown(f"## {result['status']}")

        if result["flags"]:
            st.markdown("### Issues Found")
            for flag in result["flags"]:
                st.error(flag)

        if result["warnings"]:
            st.markdown("### Warnings")
            for warning in result["warnings"]:
                st.warning(warning)

        if result["passed"]:
            st.success("Loan meets all guidelines!")
        else:
            st.error(" Loan does not meet guidelines - review required")


def show_fraud_detector_page():
    """Automated Red Flag / Fraud Detector."""
    from fraud_detector import FraudDetector

    st.markdown(
        '<div style="font-size:18px;font-weight:800;color:#ffffff;letter-spacing:-0.3px;margin-bottom:16px;">'
        'Fraud Detector</div>',
        unsafe_allow_html=True,
    )

    st.markdown("Scan documents for common fraud indicators and red flags.")

    # Sample extracted data input
    st.markdown("### Document Analysis Results")
    large_deposit = st.checkbox("Large unexplained deposit detected")
    income_drop = st.checkbox("Recent income drop")
    employment_gap = st.checkbox("Employment gap found")

    extracted_data = {
        "large_deposit": large_deposit,
        "income_drop": income_drop,
        "employment_gap": employment_gap,
        "deposits": [{"amount": 5000, "description": "unexplained deposit"}] if large_deposit else []
    }

    if st.button("Scan for Fraud", type="primary"):
        detector = FraudDetector()
        flags = detector.scan(extracted_data)
        risk_assessment = detector.get_risk_score(flags)

        st.markdown(f"## Risk Level: {risk_assessment['risk_level']}")
        st.markdown(f"**Risk Score:** {risk_assessment['score']}")

        if flags:
            st.markdown("### Red Flags Detected")
            for flag in flags:
                severity_color = {"low": "blue", "medium": "orange", "high": "red", "critical": "red"}
                st.error(f"{flag['description']} - {flag['recommendation']}")
        else:
            st.success("No fraud indicators detected")


def show_multi_borrower_page():
    """Multi-Borrower Support."""
    from multi_borrower import MultiBorrowerHandler

    st.markdown(
        '<div style="font-size:18px;font-weight:800;color:#ffffff;letter-spacing:-0.3px;margin-bottom:16px;">'
        'Multi-Borrower Support</div>',
        unsafe_allow_html=True,
    )

    st.markdown("Handle loans with primary and co-borrowers.")

    primary_borrower = st.text_input("Primary Borrower Name", key="primary_name")
    co_borrower = st.text_input("Co-Borrower Name (optional)", key="co_name")

    # Sample file list
    files = [
        "/path/to/primary_paystub.pdf",
        "/path/to/primary_bank_statement.pdf",
        "/path/to/joint_1003.pdf",
        "/path/to/co_borrower_paystub.pdf"
    ]

    st.markdown("### Sample Files to Process")
    for file in files:
        st.code(file)

    if primary_borrower and st.button("Process Multi-Borrower Loan", type="primary"):
        handler = MultiBorrowerHandler()
        result = handler.process(files, primary_borrower, co_borrower)

        st.success("Multi-borrower processing complete!")
        st.markdown(f"**Primary Borrower:** {result['primary_borrower']}")
        if result['co_borrower']:
            st.markdown(f"**Co-Borrower:** {result['co_borrower']}")

        st.markdown(f"**Documents Assigned:** {len(result['documents_assigned']['primary'])} to primary, {len(result['documents_assigned']['co_borrower'])} to co-borrower")


def show_los_export_page():
    """Basic LOS Export."""
    from los_export import LOSExport

    st.markdown(
        '<div style="font-size:18px;font-weight:800;color:#ffffff;letter-spacing:-0.3px;margin-bottom:16px;">'
        'LOS Export</div>',
        unsafe_allow_html=True,
    )

    st.markdown("Export loan data for import into Loan Origination Systems.")

    export_format = st.selectbox("Export Format", ["csv", "json", "pdf"])
    export_path = st.text_input("Export Directory", value="./exports")

    # Sample loan data
    loan_data = {
        "loan_id": "LOAN12345",
        "borrower_name": "John Doe",
        "loan_amount": 300000,
        "loan_type": "conventional",
        "monthly_income": 8500,
        "monthly_debt": 2500,
        "credit_score": 750,
        "property_value": 400000
    }

    st.markdown("### Sample Loan Data")
    st.json(loan_data)

    if st.button("Export to LOS", type="primary"):
        exporter = LOSExport()
        result = exporter.export(loan_data, export_path, export_format)

        if result["success"]:
            st.success("Export successful!")
            st.markdown("**Files Created:**")
            for file_path in result["files_created"]:
                st.code(file_path)
        else:
            st.error(f" Export failed: {', '.join(result['errors'])}")


# --- New Advanced Automation Pages ---

def show_rate_lock_monitor_page():
    """Rate Lock Monitor - Track interest rate locks and expiration alerts."""
    from rate_lock_monitor import RateLockMonitor
    from crm import get_all_loans

    st.markdown(
        '<div style="font-size:18px;font-weight:800;color:#ffffff;letter-spacing:-0.3px;margin-bottom:16px;">'
        'Rate Lock Monitor</div>',
        unsafe_allow_html=True,
    )

    st.markdown("Track interest rate locks, monitor expirations, and get float-down alerts.")

    loans = _visible_account_loans(get_all_loans())
    monitor = RateLockMonitor()

    # Sample lock data (in real app, this would come from loan records)
    lock_data = {
        "lock_date": "2024-12-15",
        "lock_expiry_date": "2025-01-15",
        "locked_rate": 6.25,
        "lock_days": 30,
        "current_market_rate": 6.0
    }

    if st.button("Monitor Rate Locks", type="primary"):
        result = monitor.monitor_lock(lock_data)

        st.markdown(f"## Lock Status: {result['status']}")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Days Until Expiry", result.get("days_until_expiry", 0))
        with col2:
            st.metric("Locked Rate", f"{result.get('locked_rate', 0):.2f}%")
        with col3:
            st.metric("Float-Down Available", "Yes" if result.get("float_down_available") else "No")

        if result.get("alerts"):
            st.markdown("### Alerts")
            for alert in result["alerts"]:
                if alert["type"] == "critical":
                    st.error(f"{alert['message']}")
                elif alert["type"] == "warning":
                    st.warning(f"{alert['message']}")
                else:
                    st.info(f"{alert['message']}")

        if result.get("recommendations"):
            st.markdown("### Recommendations")
            for rec in result["recommendations"]:
                st.info(rec)


def show_underwriting_tracker_page():
    """Underwriting Condition Tracker - Automate condition clearing and tracking."""
    from underwriting_tracker import UnderwritingConditionTracker

    st.markdown(
        '<div style="font-size:18px;font-weight:800;color:#ffffff;letter-spacing:-0.3px;margin-bottom:16px;">'
        'Underwriting Condition Tracker</div>',
        unsafe_allow_html=True,
    )

    st.markdown("Track and automate underwriting condition clearing and monitoring.")

    loan_id = st.text_input("Loan ID", key="tracker_loan_id")

    # Sample conditions
    conditions = [
        {"id": "paystub", "description": "Provide paystub for last 30 days", "due_date": "2025-01-15"},
        {"id": "bank_stmt", "description": "Provide bank statements for last 60 days", "due_date": "2025-01-20"},
        {"id": "appraisal", "description": "Order and provide appraisal", "due_date": "2025-01-10"}
    ]

    # Sample submitted documents
    submitted_docs = [
        {"filename": "paystub_december.pdf", "doc_type": "paystub", "submitted_date": "2025-01-05"},
        {"filename": "bank_statement.pdf", "doc_type": "bank_statement", "submitted_date": "2025-01-08"}
    ]

    if loan_id and st.button("Track Conditions", type="primary"):
        tracker = UnderwritingConditionTracker()
        results = tracker.track_conditions(loan_id, conditions, submitted_docs)

        st.markdown(f"## Overall Progress: {results['overall_progress']:.1f}%")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Conditions", results["total_conditions"])
        with col2:
            st.metric("Cleared", results["cleared_conditions"])
        with col3:
            st.metric("Pending", results["pending_conditions"])

        if results["condition_status"]:
            st.markdown("### Condition Status")
            for condition in results["condition_status"]:
                status_icon = {"cleared": "", "pending": "", "overdue": ""}.get(condition["status"], "")
                st.markdown(f"{status_icon} **{condition['description']}** - {condition['status'].title()}")

                if condition.get("recommendations"):
                    for rec in condition["recommendations"]:
                        st.caption(f"{rec}")


def show_document_classifier_page():
    """Automated Document Classifier - AI-powered document classification and routing."""
    from document_classifier import AutomatedDocumentClassifier

    # Show current loan banner
    current_loan = show_current_loan_banner()

    st.markdown(
        '<div style="font-size:18px;font-weight:800;color:#ffffff;letter-spacing:-0.3px;margin-bottom:16px;">'
        'Automated Document Classifier</div>',
        unsafe_allow_html=True,
    )

    st.markdown("Automatically classify and route documents to appropriate loan folders.")

    file_path = st.text_input("Document File Path", key="classifier_file_path")

    if file_path and st.button("Classify Document", type="primary"):
        classifier = AutomatedDocumentClassifier()
        result = classifier.classify_document(file_path)

        if result["primary_classification"]:
            st.success(f"Classified as: **{result['primary_classification'].replace('_', ' ').title()}**")
            st.markdown(f"**Confidence:** {result['confidence']}%")
            st.markdown(f"**Routing Folder:** {result['routing_folder'].replace('_', ' ').title()}")

            if result.get("recommendations"):
                st.markdown("### Recommendations")
                for rec in result["recommendations"]:
                    st.info(rec)
        else:
            st.error(" Document type not recognized")

        if result.get("secondary_classifications"):
            st.markdown("### Could Also Be")
            for secondary in result["secondary_classifications"]:
                st.caption(f"{secondary.replace('_', ' ').title()}")


def show_escrow_calculator_page():
    """Escrow Calculator - Closing costs and escrow analysis."""
    from escrow_calculator import EscrowCalculator

    st.markdown(
        '<div style="font-size:18px;font-weight:800;color:#ffffff;letter-spacing:-0.3px;margin-bottom:16px;">'
        'Escrow Calculator</div>',
        unsafe_allow_html=True,
    )

    st.markdown("Calculate closing costs, escrow requirements, and cash needed to close.")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Loan Information")
        loan_amount = st.number_input("Loan Amount ($)", min_value=0.0, key="escrow_loan_amt")
        property_value = st.number_input("Property Value ($)", min_value=0.0, key="escrow_prop_val")
        loan_type = st.selectbox("Loan Type", ["conventional", "fha", "va"], key="escrow_loan_type")
        location = st.selectbox("Location", ["standard", "high_cost", "low_cost"], key="escrow_location")

    with col2:
        st.markdown("### Additional Costs")
        include_warranty = st.checkbox("Include Home Warranty", key="escrow_warranty")
        escrow_months = st.slider("Escrow Months", 1, 6, 2, key="escrow_months")
        annual_tax = st.number_input("Annual Property Tax ($)", min_value=0.0, key="escrow_tax")
        annual_insurance = st.number_input("Annual Hazard Insurance ($)", min_value=0.0, key="escrow_insurance")

    loan_data = {
        "loan_amount": loan_amount,
        "property_value": property_value,
        "loan_type": loan_type,
        "location": location,
        "include_home_warranty": include_warranty,
        "escrow_months": escrow_months,
        "annual_property_tax": annual_tax if annual_tax > 0 else None,
        "annual_hazard_insurance": annual_insurance if annual_insurance > 0 else None
    }

    if st.button("Calculate Closing Costs", type="primary"):
        calculator = EscrowCalculator()
        result = calculator.calculate_closing_costs(loan_data)

        if "error" in result:
            st.error(result["error"])
        else:
            st.success("Calculation Complete!")

            # Main results
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Closing Costs", f"${result['total_closing_costs']:,.2f}")
            with col2:
                st.metric("Total Cash Needed", f"${result['total_cash_needed']:,.2f}")
            with col3:
                st.metric("Cost-to-Loan Ratio", f"{result['cost_to_loan_ratio']:.1f}%")

            # Detailed breakdown
            st.markdown("### Cost Breakdown")
            breakdown = result["breakdown"]
            for cost_type, amount in breakdown.items():
                display_name = cost_type.replace("_", " ").title()
                st.write(f"**{display_name}**: ${amount:,.2f}")


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
    """Email Watch Controls: status, start/stop, credentials, settings."""
    import email_watch as ew

    st.markdown("## Email Watch  Controls")
    st.caption(
        "Watch your inbox for new attachments. Runs in the background "
        "you can use Scanner or Pipeline normally while it checks."
    )

    cfg = ew.get_config()
    status = ew.get_status()

    # â”€â”€ Status card â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    if status["running"]:
        st.markdown(
            f'<div style="background:rgba(59,130,246,0.05);border-left:4px solid #3b82f6;border-radius:8px;'
            f'padding:10px 16px;margin-bottom:16px;">'
            f'<span style="font-size:14px;font-weight:700;color:#a9dfbf;">Watching inbox</span>'
            f'<span style="font-size:12px;color:#7dcea0;margin-left:12px;">'
            f'Last check: {status["last_time"] or ""}  {status["last_status"]}</span></div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<div style="background:rgba(255,255,255,0.1);border-left:4px solid rgba(255,255,255,0.05);border-radius:8px;'
            f'padding:10px 16px;margin-bottom:16px;">'
            f'<span style="font-size:14px;font-weight:700;color:#9ca3af;">Inbox watch is off</span>'
            + (f'<span style="font-size:12px;color:#d1d5db;margin-left:12px;">'
               f'Last check: {status["last_time"]}  {status["last_status"]}</span>'
               if status["last_time"] else "")
            + '</div>',
            unsafe_allow_html=True,
        )

    # â”€â”€ Toggle â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    t1, t2, t3 = st.columns([1, 1, 3])
    with t1:
        if status["running"]:
            if st.button("Stop Watching", use_container_width=True, type="primary"):
                ew.stop()
                st.success("Inbox watch stopped.")
                st.rerun()
        else:
            if st.button("Start Watching", use_container_width=True, type="primary"):
                try:
                    ew.start()
                    st.success("Inbox watch started - checking every "
                               f"{cfg.get('interval_minutes', 5)} minutes.")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Could not start: {exc} - Set up your credentials below first.")
    with t2:
        if st.button("Check Now", use_container_width=True,
                     help="Run one check immediately without waiting for interval"):
            with st.spinner("Checking inbox"):
                _found, _msg = ew.check_now()
            if _msg.startswith("Error"):
                st.error(_msg)
            elif _found:
                st.success(f"Found {_found} new PDF(s) - see below.")
            else:
                st.info(_msg)
            st.rerun()

    # â”€â”€ Credentials setup â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    with st.expander("Email Credentials" + (" (configured)" if cfg else " (not set up)"), expanded=not cfg):
        st.markdown(
            '<div style="background:rgba(251,191,36,0.05);border-left:3px solid #fbbf24;border-radius:6px;'
            'padding:8px 14px;margin-bottom:12px;font-size:12px;color:#f9e79f;">'
            '<b>Gmail users:</b> You must use an App Password, not your real password.<br>'
            'Go to: <b>myaccount.google.com > Security > 2-Step Verification > App Passwords</b><br>'
            'Select "Mail" + "Windows Computer" > copy the 16-character code > paste below.</div>',
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
                st.success("Credentials saved. Click â–¶ Start Watching to begin.")
                st.rerun()
            else:
                st.error("Enter both email address and app password.")

    # â”€â”€ How it works â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    with st.expander("¸ How Email Watch works"):
        st.markdown("""
**What it does:**
- Checks your inbox every N minutes (runs in the background you can use the rest of the app normally)
- Looks for **unread emails with PDF attachments**
- Downloads each PDF to the `incoming/` folder in this app's directory
- Reads the first 3 pages of the PDF to extract borrower names
- Fuzzy-matches those names against every loan in your Pipeline
- Shows a notification card here and in the sidebar

**Privacy:**
- Your credentials are saved locally in `email_config.json` in the app folder
- The app connects to your IMAP server, downloads attachments, then disconnects
- Uses your configured IMAP connection to read matching messages and attachments

**Toggle:**
- On: background thread checks every N minutes, then sleeps
- Off: thread stops within a few seconds no more peeking

**Borrower matching confidence:**
- 80%+ = high confidence match (name found in PDF text)
- 5079% = possible match (partial name found)
- Below 50% = no match file saved to `incoming/` folder, you decide
        """)


def show_email_watch_page():
    """Email Watch Results: pending matches and incoming queue."""
    import email_watch as ew

    _ew_status  = ew.get_status()
    _ew_pending = _ew_status["pending_count"]
    _ew_running = _ew_status["running"]

    # compact status strip + Controls shortcut
    _dot   = "" if _ew_running else ""
    _state = f"Watching  last check {_ew_status['last_time'] or ''}" if _ew_running else "Watch is off"
    _rs1, _rs2 = st.columns([5, 1])
    with _rs1:
        st.markdown(
            f'<div style="background:#1e1e1e;border-left:3px solid '
            f'{"#3b82f6" if _ew_running else "rgba(255,255,255,0.15)"};border-radius:6px;'
            f'padding:6px 14px;font-size:12px;color:#9ca3af;">'
            f'{_dot} {_state}  <b style="color:#fff">{_ew_pending} attachment(s) waiting</b></div>',
            unsafe_allow_html=True,
        )
    with _rs2:
        if st.button("Controls", key="ew_goto_controls", use_container_width=True):
            st.session_state.page = "email_watch_controls"
            st.session_state["ew_nav_open"] = True
            st.rerun()

    st.markdown("## Email Watch  Results")

    # â”€â”€ Pending matches â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    matches = ew.get_matches()
    if matches:
        st.markdown(f"### {len(matches)} New Attachment(s) Waiting for Action")
        for i, m in enumerate(matches):
            conf  = m.get("confidence", 0)
            sugg  = m.get("suggestion", "unknown")
            bname = m.get("borrower") or "Unknown borrower"
            lnum  = m.get("loan_num", "")

            if sugg == "match":
                conf_color = "#3b82f6"
                conf_label = f"Matched {bname}  Loan {lnum} ({conf}% confidence)"
            elif sugg == "possible":
                conf_color = "#fbbf24"
                conf_label = f"Possible match {bname}  Loan {lnum} ({conf}%)"
            else:
                conf_color = "#ef4444"
                conf_label = "? No pipeline match found"

            with st.expander(f"{m['filename']}    {m.get('received', '')}    {conf_label}", expanded=True):
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
                            f'<div style="font-size:12px;color:#3b82f6;margin-top:4px;">'
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
                        _icon = "" if _fname_low.endswith(_IMG_EXT) else ("" if _fname_low.endswith(".pdf") else "")
                        if st.button(f"{_icon} Preview", key=f"ew_preview_{i}", use_container_width=True):
                            _toggle = f"ew_preview_open_{i}"
                            st.session_state[_toggle] = not st.session_state.get(_toggle, False)
                    if folder and os.path.isdir(folder):
                        if st.button("Save to folder", key=f"ew_save_{i}", use_container_width=True, type="primary"):
                            import shutil
                            dest = os.path.join(folder, m["filename"])
                            shutil.copy2(m["file_path"], dest)
                            try:
                                import document_index as _di
                                _di.index_document(
                                    file_path=dest,
                                    borrower=m.get("borrower") or m.get("matched_loan"),
                                    loan_number=m.get("loan_num"),
                                    doc_type=m.get("doc_type"),
                                    key_points=m.get("summary") or m.get("doc_type"),
                                )
                            except Exception:
                                pass
                            ew.dismiss(i)
                            st.success(f"Saved to {dest}")
                            st.rerun()
                    # Direct download works for every file type
                    try:
                        with open(m["file_path"], "rb") as _dfh:
                            st.download_button(
                                " Download", _dfh.read(),
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
                    # Spanish Reply button
                    if st.button("Spanish Reply", key=f"ew_spanish_{i}", use_container_width=True):
                        st.session_state["spanish_reply_data"] = m
                        st.session_state.page = "spanish_reply"
                        st.session_state["scroll_to"] = "spanish_reply"
                        _save_session()
                        st.rerun()

                # â”€â”€ Preview panel (below columns, full width) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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

    # â”€â”€ Incoming Queue all files in the incoming/ folder â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    import email_watch as ew
    _incoming_dir = os.path.join(os.path.dirname(__file__), "incoming")
    _inbox_files  = []
    if os.path.isdir(_incoming_dir):
        _inbox_files = [
            f for f in os.listdir(_incoming_dir)
            if f.lower().endswith(".pdf")
        ]

    _iq_label = f"Incoming Queue {len(_inbox_files)} file(s) waiting" if _inbox_files \
                else "Incoming Queue empty"
    with st.expander(_iq_label, expanded=bool(_inbox_files)):
        if not _inbox_files:
            st.markdown(
                '<span style="color:#9ca3af;font-size:13px;">No files in the incoming folder. '
                'Files appear here when Email Watch downloads attachments.</span>',
                unsafe_allow_html=True,
            )
        else:
            st.caption(
                "These files came from your email inbox. Review each one "
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

                _v_color = {"pass": "#3b82f6", "review": "#fbbf24", "check": "#ef4444"}.get(
                    _qv.get("verdict", "check"), "#ef4444"
                )
                _v_icon  = {"pass": "", "review": "â–³", "check": "?"}.get(
                    _qv.get("verdict", "check"), "Search"
                )
                _bname = _qv.get("borrower") or "Unknown borrower"
                _lnum  = _qv.get("loan_num", "")
                _match_label = f"  {_bname}  Loan {_lnum}" if _qv.get("borrower") else "  No pipeline match"

                with st.container():
                    st.markdown(
                        f'<div style="background:rgba(255,255,255,0.1);border-left:3px solid {_v_color};'
                        f'border-radius:6px;padding:8px 12px;margin-bottom:6px;">'
                        f'<span style="font-weight:700;color:#ffffff;font-size:13px;">'
                        f'{_v_icon} {_qfname}</span>'
                        f'<span style="font-size:12px;color:#9ca3af;">{_match_label}</span><br>'
                        f'<span style="font-size:11px;color:#3b82f6;">{_qv.get("doc_type","Document")}  '
                        f'{_qv.get("page_count",0)} pages  '
                        f'{_qv.get("days_old","?")}d old</span></div>',
                        unsafe_allow_html=True,
                    )
                    _qa, _qb, _qc, _qd = st.columns([3, 1, 1, 1])
                    with _qa:
                        for _ok in _qv.get("ok_list", []):
                            st.markdown(f'<span style="color:#3b82f6;font-size:11px;">{_ok}</span><br>',
                                        unsafe_allow_html=True)
                        for _fl in _qv.get("flags", []):
                            st.markdown(f'<span style="color:#ef4444;font-size:11px;">{_fl}</span><br>',
                                        unsafe_allow_html=True)
                    _dest_folder = _qv.get("suggested_folder", "")
                    with _qb:
                        if _dest_folder and os.path.isdir(_dest_folder):
                            if st.button("Yes - Save", key=f"iq_yes_{_qi}",
                                         use_container_width=True, type="primary"):
                                import shutil as _shu
                                _dest = os.path.join(_dest_folder, _qfname)
                                _shu.move(_qfpath, _dest)
                                try:
                                    import document_index as _di
                                    _di.index_document(
                                        file_path=_dest,
                                        borrower=_qv.get("borrower"),
                                        loan_number=_qv.get("loan_num"),
                                        doc_type=_qv.get("doc_type"),
                                        key_points=_qv.get("doc_type"),
                                    )
                                except Exception:
                                    pass
                                st.success(f"Moved to {_dest}")
                                st.rerun()
                        else:
                            _manual = st.text_input("Save to:", key=f"iq_path_{_qi}",
                                                    placeholder=r"C:\Loans\Smith",
                                                    label_visibility="collapsed")
                            if _manual and st.button("Yes", key=f"iq_yes_m_{_qi}",
                                                     use_container_width=True, type="primary"):
                                import shutil as _shu
                                os.makedirs(_manual, exist_ok=True)
                                _final = os.path.join(_manual, _qfname)
                                _shu.move(_qfpath, _final)
                                try:
                                    import document_index as _di
                                    _di.index_document(
                                        file_path=_final,
                                        borrower=_qv.get("borrower"),
                                        doc_type=_qv.get("doc_type"),
                                        key_points=_qv.get("doc_type"),
                                    )
                                except Exception:
                                    pass
                                st.success("Moved.")
                                st.rerun()
                    with _qc:
                        if st.button("Read", key=f"iq_read_{_qi}", use_container_width=True):
                            st.session_state.reader_open_file = _qfpath
                            st.session_state.page = "reader"
                            st.rerun()
                    with _qd:
                        if st.button("No", key=f"iq_no_{_qi}", use_container_width=True):
                            try:
                                os.remove(_qfpath)
                            except Exception:
                                pass
                            st.rerun()

    st.caption("Go to **Email Watch > Controls** to start/stop watching or update credentials.")


# --- AI Settings Page ---
def show_ollama_page():
    import cloud_client  as _cc

    st.title("AI Settings")
    st.caption("Smart document extraction uses Google Gemini 2.5 Flash.")

    # â”€â”€ Cloud AI settings â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    st.markdown("### Cloud AI")

    cc_cfg = _cc.get_config()
    _real_user = bool(st.session_state.get("authenticated") and not st.session_state.get("sandbox_mode"))
    _user_key = _current_auth_user_key()
    _saved_gemini_key = st.session_state.get("user_gemini_api_key", "")

    # â”€â”€ Enable toggle saves immediately on change (matches sidebar button) â”€â”€
    cc_enabled_now = st.toggle(
        "Enable Cloud AI",
        value=bool(cc_cfg.get("enabled")),
        key="cc_enabled_live",
        help="Saves instantly when you click. Requires API key set below.",
    )
    if cc_enabled_now != bool(cc_cfg.get("enabled")):
        _cc.save_config(
            cc_enabled_now,
            "gemini",
            cc_cfg.get("api_key", ""),
            "gemini-2.5-flash",
        )
        st.rerun()

    cc_provider = "gemini"
    cc_model = "gemini-2.5-flash"
    st.markdown(
        """
        <div style="background:rgba(59,130,246,0.08);border:1px solid rgba(59,130,246,0.25);
        border-radius:12px;padding:12px 14px;margin:10px 0 14px 0;color:#dbeafe;font-size:13px;">
          <b>Required:</b> Create a Google AI Studio API key and paste it below.
          Without a Gemini 2.5 Flash key, smart parsing will not work correctly.
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.text_input("Provider", value="Google Gemini", disabled=True)
    st.text_input("Model", value=cc_model, disabled=True)
    st.caption("Gemini 2.5 Flash is the only enabled model for now.")

    # Key + Save inside a form so a half-typed key doesn't auto-save
    with st.form("cloud_settings_form"):
        _key_help = {
            "gemini": "Create a key at aistudio.google.com/app/apikey",
        }
        cc_key = st.text_input(
            "API Key",
            value=_saved_gemini_key if (cc_provider == "gemini" and _real_user) else cc_cfg.get("api_key", ""),
            type="password",
            key="cc_key",
            help=_key_help.get(cc_provider, ""),
        )
        cc_save = st.form_submit_button("Save Provider / Model / Key", type="primary")

    if cc_save:
        key_to_store_locally = cc_key
        if _real_user and _user_key:
            try:
                _save_result = _save_user_gemini_key_for_account(cc_key)
                if not _save_result.get("ok"):
                    st.warning(
                        f"Gemini key is active for this session, but was not saved: {_save_result.get('error', 'Supabase save failed')}"
                    )
                    st.session_state.user_gemini_api_key = cc_key.strip()
                    key_to_store_locally = ""
                else:
                    st.session_state.user_gemini_api_key = cc_key.strip()
                    key_to_store_locally = ""
            except Exception as e:
                st.warning(f"Gemini key is active for this session. Supabase save failed: {e}")
                st.session_state.user_gemini_api_key = cc_key.strip()
                key_to_store_locally = ""

        _cc.save_config(cc_enabled_now, cc_provider, key_to_store_locally, cc_model)
        if _real_user:
            st.success("Cloud AI settings saved. Your Gemini key is linked to your account.")
        else:
            st.success("Cloud AI settings saved.")
        st.rerun()

    if st.button("Test Cloud Connection", key="cc_test"):
        if not cc_cfg.get("api_key"):
            st.warning("Save an API key first.")
        else:
            with st.spinner("Testing..."):
                ok, msg = _cc.ping()
            if ok:
                st.success(f"OK: {msg}")
            else:
                st.error(f"Error: {msg}")

    with st.expander("How to get an API key"):
        st.markdown("""
**Google Gemini 2.5 Flash**
1. Go to [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
2. Sign in with your Google account.
3. Click **Create API key**.
4. Copy the key and paste it into the API Key box above.
5. Click **Save Provider / Model / Key**.

Keep this key private. Processor Assistant stores it encrypted for your signed-in account.
        """)

    # â”€â”€ Processing log â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    st.markdown("---")
    st.markdown("### Processing Log")
    st.caption("Every Cloud AI call is logged here.")

    cc_lines = _cc.get_recent_log(40)

    if cc_lines:
        log_c1, log_c2 = st.columns([5, 1])
        with log_c2:
            if st.button("Clear Log", key="ai_clear_log"):
                _cc.clear_log()
                st.rerun()
        st.code("\n".join(sorted(cc_lines, reverse=True)), language=None)
    else:
        st.info("No processing log yet - scan a Purchase Contract or Approval Letter to see entries here.")

    # â”€â”€ Cloud Backup (Supabase) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    st.markdown("---")
    st.markdown("### Cloud Backup (Supabase)")
    st.caption("Local SQLite is the primary store. Supabase is a backup mirror - batched every 60s, "
               "scanned PDFs and sensitive fields (SSN, DOB, account #s) are never uploaded.")

    try:
        import supabase_sync as _sb
        sb_status = _sb.get_status()

        sc1, sc2, sc3 = st.columns(3)
        with sc1:
            if sb_status["enabled"]:
                st.success("Connected")
            elif sb_status["paused"]:
                st.warning("Paused")
            elif sb_status["configured"]:
                st.error("Config error")
            else:
                st.info("Not configured (set SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY env vars)")
        with sc2:
            st.metric("Calls (last hour)", f"{sb_status['calls_last_hour']} / {sb_status['hourly_cap']}")
        with sc3:
            st.metric("Pending in queue", sb_status["queue_size"])

        if sb_status.get("last_flush"):
            st.caption(f"Last sync: {sb_status['last_flush']}")
        if sb_status.get("last_error"):
            st.caption(f"Last error: {sb_status['last_error']}")

        bc1, bc2, bc3 = st.columns(3)
        with bc1:
            if st.button("Sync now", key="sb_sync_now", use_container_width=True,
                         disabled=not sb_status["configured"]):
                result = _sb.force_flush()
                if result.get("ok"):
                    st.success(f"Synced {result.get('synced', 0)} records")
                else:
                    st.error(f"Sync failed: {result.get('reason') or result.get('errors')}")
                st.rerun()
        with bc2:
            pause_label = "Resume sync" if sb_status["paused"] else "Pause sync"
            if st.button(pause_label, key="sb_toggle_pause", use_container_width=True):
                _sb.set_paused(not sb_status["paused"])
                st.rerun()
        with bc3:
            if st.button("Restore from backup", key="sb_restore", use_container_width=True,
                         disabled=not sb_status["configured"]):
                st.session_state["sb_show_restore_confirm"] = True

        if st.session_state.get("sb_show_restore_confirm"):
            st.warning("This will OVERWRITE your local pipeline.json with cloud data. "
                       "A backup will be saved as pipeline.json.pre_restore_backup. Continue?")
            rc1, rc2 = st.columns(2)
            with rc1:
                if st.button("Yes, restore now", key="sb_restore_confirm", type="primary", use_container_width=True):
                    result = _sb.restore_from_cloud()
                    if result.get("ok"):
                        st.success(f"Restored {result.get('restored_loans', 0)} loans. "
                                   f"Old data backed up to {result.get('backup_path')}")
                    else:
                        st.error(f"Restore failed: {result.get('reason')}")
                    st.session_state["sb_show_restore_confirm"] = False
            with rc2:
                if st.button("Cancel", key="sb_restore_cancel", use_container_width=True):
                    st.session_state["sb_show_restore_confirm"] = False
                    st.rerun()
    except Exception as _e:
        st.caption(f"Backup module not available: {_e}")


# --- Billing & Usage Page ---
def show_pricing_page():
    beta_payment_link = "https://buy.stripe.com/bJe7sLdx87xM6mtaOSdfG00"

    st.title("Pricing")
    st.caption("Simple beta pricing while Processor Assistant is still early-access.")

    _lo, _mid, _ro = st.columns([1, 2, 1])
    with _mid:
        st.markdown(
            """
            <div style="border:1px solid rgba(59,130,246,0.45);border-radius:14px;
            padding:18px;background:rgba(59,130,246,0.08);">
              <div style="font-size:12px;font-weight:800;color:#3b82f6;text-transform:uppercase;">Available Now</div>
              <div style="font-size:24px;font-weight:900;color:#fff;margin-top:6px;">Beta</div>
              <div style="font-size:34px;font-weight:900;color:#fff;margin:10px 0;">$49<span style="font-size:14px;color:#9ca3af;">/mo</span></div>
              <div style="font-size:13px;color:#d1d5db;">Includes a 14-day free trial.</div>
              <hr style="border-color:rgba(255,255,255,0.08);margin:16px 0;">
              <div style="font-size:13px;color:#e5e7eb;line-height:1.7;">
                Scanner, pipeline, recent scan history, saved non-sensitive loan data, and user account settings.
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            f"""
            <a href="{beta_payment_link}" target="_blank" rel="noopener noreferrer"
               style="display:block;text-align:center;margin-top:12px;padding:12px 16px;
               border-radius:10px;background:#2563eb;color:#fff;font-size:14px;
               font-weight:800;text-decoration:none;">
              Start Beta - 14 Day Free Trial
            </a>
            """,
            unsafe_allow_html=True,
        )


def show_chat_page():
    """Simple in-app chat for signed-in Processor Assistant users."""
    import html as _html
    from datetime import datetime as _dt
    import chat_store as _chat

    st.title("Chat")
    st.caption("Shared app chat for signed-in Processor Assistant users. Do not paste full documents, SSNs, bank account numbers, or other sensitive borrower data.")

    if st.session_state.get("sandbox_mode", False):
        st.info("Sandbox chat is local-only. Sign in with Google to use shared team chat.")

    top1, top2 = st.columns([1, 5])
    with top1:
        if st.button("Refresh", use_container_width=True, key="chat_refresh"):
            st.rerun()

    messages = _chat.load_messages(limit=80)
    if not messages:
        st.info("No messages yet. Start the room.")
    else:
        st.markdown(
            """
            <div style="display:flex;flex-direction:column;gap:10px;margin:8px 0 18px 0;">
            """,
            unsafe_allow_html=True,
        )
        current_user = str(st.session_state.get("user_email") or st.session_state.get("user_id") or "")
        for msg in messages:
            user_name = _html.escape(str(msg.get("user_name") or "User"))
            user_email = _html.escape(str(msg.get("user_email") or ""))
            text = _html.escape(str(msg.get("text") or "")).replace("\n", "<br>")
            ts_raw = str(msg.get("ts") or "")
            try:
                ts = _dt.fromisoformat(ts_raw.replace("Z", "+00:00")).strftime("%m/%d %I:%M %p")
            except Exception:
                ts = ts_raw[:16].replace("T", " ")
            own = current_user and current_user.lower() == str(msg.get("user_email") or "").lower()
            align = "margin-left:auto;" if own else "margin-right:auto;"
            bg = "rgba(37,99,235,0.22)" if own else "rgba(30,41,59,0.82)"
            border = "rgba(96,165,250,0.35)" if own else "rgba(148,163,184,0.22)"
            st.markdown(
                f"""
                <div style="{align}max-width:78%;border:1px solid {border};border-radius:14px;
                            background:{bg};padding:10px 12px;">
                  <div style="display:flex;gap:10px;align-items:baseline;margin-bottom:5px;">
                    <span style="font-weight:800;color:#fff;font-size:13px;">{user_name}</span>
                    <span style="font-size:11px;color:#94a3b8;">{ts}</span>
                  </div>
                  <div style="font-size:14px;line-height:1.45;color:#e5e7eb;">{text}</div>
                  <div style="font-size:10px;color:#64748b;margin-top:5px;">{user_email}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

    with st.form("app_chat_form", clear_on_submit=True):
        message = st.text_area(
            "Message",
            placeholder="Type a quick team update...",
            height=95,
            label_visibility="collapsed",
            key="chat_message_text",
        )
        send = st.form_submit_button("Send Message", use_container_width=True)
        if send:
            result = _chat.save_message(
                user_key=_current_auth_user_key(),
                user_name=str(st.session_state.get("user_name") or ""),
                user_email=str(st.session_state.get("user_email") or ""),
                text=message,
            )
            if result.get("ok"):
                st.rerun()
            else:
                st.error(result.get("error", "Could not save message."))


def show_billing_page():
    import billing as _bl

    uid  = st.session_state.get("user_id", "")
    role = st.session_state.get("user_role", "Processor")

    st.title("$ Usage & Billing")
    st.caption("Tracks document scans processed each month and calculates your monthly cost.")

    # â”€â”€ Current month summary â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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

    # â”€â”€ Usage bar â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    pct = usage["pct_used"]
    bar_color = "#3b82f6" if pct < 80 else ("#f59e0b" if pct < 100 else "#ef4444")
    st.markdown(
        f'<div style="background:rgba(255,255,255,0.1);border-radius:8px;padding:12px 16px;margin:8px 0 16px;">'
        f'<div style="font-size:13px;color:#d1d5db;margin-bottom:6px;">'
        f'Quota: {usage["scans"]} / {usage["included"]} scans used ({pct}%)</div>'
        f'<div style="background:rgba(255,255,255,0.03);border-radius:4px;height:10px;">'
        f'<div style="background:{bar_color};width:{min(pct,100)}%;height:10px;border-radius:4px;'
        f'transition:width 0.4s;"></div></div></div>',
        unsafe_allow_html=True,
    )

    # â”€â”€ Breakdown by doc type â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    if usage["by_doc_type"]:
        st.markdown("#### Scans by Document Type")
        rows = sorted(usage["by_doc_type"].items(), key=lambda x: -x[1])
        for dtype, count in rows:
            pct_dt = round(count / max(usage["scans"], 1) * 100)
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:4px;">'
                f'<span style="font-size:13px;color:#d1d5db;width:220px;">{dtype or "Unknown"}</span>'
                f'<div style="flex:1;background:rgba(255,255,255,0.03);border-radius:4px;height:8px;">'
                f'<div style="background:#3b82f6;width:{pct_dt}%;height:8px;border-radius:4px;"></div></div>'
                f'<span style="font-size:13px;color:#d1d5db;width:40px;text-align:right;">{count}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

    # â”€â”€ Billing note â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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
            st.markdown(f'<div style="font-size:13px;color:#9ca3af;"> {n}</div>',
                        unsafe_allow_html=True)

    # â”€â”€ Monthly history â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    st.markdown("---")
    st.markdown("### Monthly History")
    history = _bl.get_history(uid, months=6)
    if history:
        for h in history:
            c1, c2, c3 = st.columns([3, 2, 2])
            c1.markdown(f"**{_bl.format_month(h['year_month'])}**")
            c2.markdown(f"{h['scans']} scans"
                        + (f"  {h['overage']} overage" if h["overage"] else ""))
            c3.markdown(f"**${h['total_cost']:.2f}**")
    else:
        st.info("No billing history yet scan a document to start tracking.")

    # â”€â”€ Pricing reference â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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

    # â”€â”€ Admin view (Manager role only) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    if role == "Manager":
        st.markdown("---")
        st.markdown("### All Users Current Month")
        all_usage = _bl.get_all_users_usage()
        if all_usage:
            for u in all_usage:
                ua1, ua2, ua3, ua4 = st.columns([3, 2, 2, 2])
                ua1.markdown(f"**{u['display_name'] or u['email']}**  {u['role']}")
                ua2.markdown(f"{u['scans']} scans")
                ua3.markdown(f"{u['overage']} overage" if u["overage"] else "")
                ua4.markdown(f"**${u['total_cost']:.2f}**")
        else:
            st.info("No scan data for current month.")


# --- Loan Detail Page ---
def show_loan_detail():
    """Full detail view for a single loan all info, activity, documents."""
    from crm import (
        get_loan, add_loan, update_loan, set_status, delete_loan,
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
        st.warning("Loan not found it may have been removed.")
        if st.button("Back to Pipeline"):
            st.session_state.page = "pipeline"
            st.rerun()
        return

    my_name = st.session_state.get("user_name", "")
    status = loan.get("status", "Pending")
    border_color = STATUS_COLORS.get(status, "#444")

    _pending_scan = st.session_state.get("pending_scan_merge")
    if isinstance(_pending_scan, dict) and _pending_scan.get("loan_id") == lid:
        _ps_result = _pending_scan.get("result") or {}
        _ps_type = _pending_scan.get("type") or "Document"
        _ps_file = _pending_scan.get("file") or "scanned document"
        st.markdown(
            f'<div style="background:rgba(251,191,36,0.10);border:1px solid rgba(251,191,36,0.35);'
            f'border-radius:6px;padding:10px 12px;margin:8px 0;color:#fbbf24;font-size:13px;">'
            f'<b>Pending scanned {_ps_type}:</b> {_ps_file}<br>'
            f'<span style="color:#d1d5db;">You opened this loan to verify the possible match. Merge it here to save parsed contacts and dates to this loan.</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
        def _create_loan_from_pending_scan() -> dict | None:
            _pcd = (_ps_result.get("extracted_data") or {})
            _txn = _pcd.get("transaction", {}) if isinstance(_pcd, dict) else {}
            _buyer = _pcd.get("buyer", {}) if isinstance(_pcd, dict) else {}
            _contacts = _ps_result.get("contacts", {}) or {}
            _borrower = _buyer.get("name", "") if isinstance(_buyer, dict) else ""
            if not _borrower and isinstance(_contacts, dict):
                for _cv in _contacts.values():
                    if isinstance(_cv, dict) and _cv.get("name"):
                        _borrower = _cv["name"]
                        break
            if not _borrower:
                st.error("I parsed the document, but I do not have a borrower name to create the loan.")
                return None
            _closing = (_txn.get("closing_date", "") if isinstance(_txn, dict) else "") or ""
            _new = add_loan(
                loan_num=_ps_result.get("loan_num", "") or "TBD",
                borrower=_borrower,
                status="Pending",
                due_date=_closing,
                missing_docs="",
                folder_path="",
                closing_date=_closing,
                conditions=_normalize_scanned_conditions(_ps_result.get("conditions", [])),
                contacts=_contacts if isinstance(_contacts, dict) else {},
                created_by=st.session_state.get("user_name", ""),
            )
            _stamp_current_user_on_loan(_new, assigned=True)
            return _new

        _pm1, _pm2, _pm3 = st.columns([1, 1, 1])
        with _pm1:
            if st.button("Merge Scanned Contract Into This Loan", key=f"detail_pending_merge_{lid}", type="primary", use_container_width=True):
                from crm import attach_document as _attach_doc
                _existing_conds = loan.get("conditions", []) or []
                _existing_contacts = loan.get("contacts", {}) or {}
                if not isinstance(_existing_contacts, dict):
                    _existing_contacts = {}
                _new_conds = _normalize_scanned_conditions(_ps_result.get("conditions", []))
                _new_contacts = _ps_result.get("contacts", {}) or {}
                _upd = {}
                for _nc in _new_conds:
                    if not any(_nc.get("desc") == _ec.get("desc") for _ec in _existing_conds):
                        _existing_conds.append(_nc)
                _upd["conditions"] = _existing_conds
                if isinstance(_new_contacts, dict):
                    _existing_contacts.update({k: v for k, v in _new_contacts.items() if v})
                if _ps_type == "Purchase Contract":
                    _pcd = (_ps_result.get("extracted_data") or {})
                    _txn = _pcd.get("transaction", {}) if isinstance(_pcd, dict) else {}
                    if _txn.get("closing_date") and not loan.get("closing_date"):
                        _upd["closing_date"] = _txn["closing_date"]
                        _upd["due_date"] = _txn["closing_date"]
                    for _ak, _av in [
                        ("listing_agent", _pcd.get("listing_agent", {}) if isinstance(_pcd, dict) else {}),
                        ("selling_agent", _pcd.get("selling_agent", {}) if isinstance(_pcd, dict) else {}),
                        ("title", _pcd.get("title", {}) if isinstance(_pcd, dict) else {}),
                    ]:
                        if isinstance(_av, dict) and any(v for v in _av.values()):
                            _existing_contacts[_ak] = _av
                _upd["contacts"] = _existing_contacts
                update_loan(lid, **_upd)
                _attach_doc(lid, _ps_file, _ps_type, extracted=_ps_result.get("extracted_data"))
                log_activity(lid, "upload", f"{_ps_type} merged from scanner", user=my_name)
                _bi = _pending_scan.get("batch_index")
                if isinstance(_bi, int) and 0 <= _bi < len(st.session_state.get("scan_batches", [])):
                    st.session_state.scan_batches.pop(_bi)
                st.session_state.pop("pending_scan_merge", None)
                st.toast(f"{_ps_type} merged into loan")
                st.rerun()
        with _pm2:
            if st.button("Create New Loan From This Scan", key=f"detail_pending_create_new_{lid}", use_container_width=True):
                from crm import attach_document as _attach_doc
                _new_loan = _create_loan_from_pending_scan()
                if _new_loan:
                    _attach_doc(_new_loan["id"], _ps_file, _ps_type, extracted=_ps_result.get("extracted_data"))
                    log_activity(_new_loan["id"], "created", f"Loan created from scanned {_ps_type}", user=my_name)
                    _bi = _pending_scan.get("batch_index")
                    if isinstance(_bi, int) and 0 <= _bi < len(st.session_state.get("scan_batches", [])):
                        st.session_state.scan_batches.pop(_bi)
                    st.session_state.pop("pending_scan_merge", None)
                    st.session_state.detail_loan_id = _new_loan["id"]
                    st.toast(f"Loan created for {_new_loan.get('borrower', '')}")
                    st.rerun()
        with _pm3:
            if st.button("Dismiss Pending Scan", key=f"detail_pending_dismiss_{lid}", use_container_width=True):
                st.session_state.pop("pending_scan_merge", None)
                st.rerun()

    # â”€â”€ Back button â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    if st.button("Back to Pipeline", key="back_to_pipeline"):
        st.session_state.page = "pipeline"
        st.rerun()

    # â”€â”€ Header â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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
        _ld_label = f"{status} no conditions tracked yet"
    _ld_bar_color = "#3b82f6" if _ld_pct >= 75 else ("#f59e0b" if _ld_pct >= 40 else "#ef4444")

    st.markdown(
        f'<div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.1);border-left:3px solid {border_color};'
        f'border-radius:3px;padding:12px 14px;margin:4px 0;">'
        f'<div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:8px;">'
        f'<span style="font-size:16px;font-weight:700;color:#3b82f6;">#{loan.get("loan_num","")}</span>'
        f'<span style="font-size:15px;font-weight:600;color:#ffffff;">{loan.get("borrower","")}</span>'
        f'<span class="status-chip status-{status.lower()}" style="font-size:13px;">'
        f'<span style="color:{border_color};font-size:10px;"></span> {status}</span>'
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

    # â”€â”€ Key Dates â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    st.markdown(
        '<span style="font-size:13px;font-weight:700;color:#3b82f6;text-transform:uppercase;'
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
            f'<div style="font-size:10px;color:#3b82f6;font-weight:700;text-transform:uppercase;">Closing Date</div>'
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
            f'<div style="font-size:14px;color:#ffffff;margin-top:4px;">{_created or ""}</div></div>',
            unsafe_allow_html=True,
        )
    with d5:
        st.markdown(
            f'<div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.1);border-radius:8px;padding:10px;">'
            f'<div style="font-size:10px;color:#9ca3af;font-weight:700;text-transform:uppercase;">Last Updated</div>'
            f'<div style="font-size:14px;color:#ffffff;margin-top:4px;">{_updated or ""}</div></div>',
            unsafe_allow_html=True,
        )

    # â”€â”€ Loan Details â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    st.markdown(
        '<span style="font-size:13px;font-weight:700;color:#3b82f6;text-transform:uppercase;'
        'letter-spacing:0.5px;margin-top:12px;display:inline-block;">Loan Details</span>',
        unsafe_allow_html=True,
    )
    ld1, ld2 = st.columns(2)
    with ld1:
        _fields_left = [
            ("Loan #", loan.get("loan_num", "")),
            ("Borrower", loan.get("borrower", "")),
            ("Status", f'{STATUS_EMOJI.get(status,"")}  {status}'),
            ("Created By", loan.get("created_by") or ""),
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
            ("Due Date", loan.get("due_date") or ""),
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

    # â”€â”€ Missing Docs â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    _missing = loan.get("missing_docs", "")
    st.markdown(
        '<span style="font-size:13px;font-weight:700;color:#3b82f6;text-transform:uppercase;'
        'letter-spacing:0.5px;margin-top:12px;display:inline-block;">Missing Documents</span>',
        unsafe_allow_html=True,
    )
    if _missing:
        _docs = [d.strip() for d in _missing.split(",") if d.strip()]
        _doc_html = "".join(
            f'<div style="display:flex;align-items:center;gap:6px;margin-bottom:3px;">'
            f'<span style="color:#ef4444;"></span>'
            f'<span style="color:#ffb86c;font-size:13px;">{d}</span></div>'
            for d in _docs
        )
        st.markdown(_doc_html, unsafe_allow_html=True)
    else:
        st.markdown(
            '<span style="color:#3b82f6;font-size:13px;">All documents received</span>',
            unsafe_allow_html=True,
        )

    # â”€â”€ Lender (drives mortgagee clause on generated templates) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    from template_filler import get_lender_names as _get_lenders
    _lender_options = ["(none)"] + _get_lenders()
    _cur_lender = loan.get("lender", "") or "(none)"
    _lender_idx = _lender_options.index(_cur_lender) if _cur_lender in _lender_options else 0
    st.markdown(
        '<span style="font-size:13px;font-weight:700;color:#3b82f6;text-transform:uppercase;'
        'letter-spacing:0.5px;margin-top:12px;display:inline-block;">Lender</span>',
        unsafe_allow_html=True,
    )
    _new_lender = st.selectbox(
        "Lender", _lender_options, index=_lender_idx,
        key=f"detail_lender_{lid}", label_visibility="collapsed",
        help="Drives the mortgagee clause used when generating HOI / Title requests.",
    )
    _lender_val = "" if _new_lender == "(none)" else _new_lender
    if _lender_val != loan.get("lender", ""):
        update_loan(lid, lender=_lender_val)
        log_activity(lid, "update", f"Lender set to {_new_lender}", user=my_name)
        st.rerun()

    # â”€â”€ Generate Templates (HOI + Title Request) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    st.markdown(
        '<span style="font-size:13px;font-weight:700;color:#3b82f6;text-transform:uppercase;'
        'letter-spacing:0.5px;margin-top:12px;display:inline-block;">Generate Documents</span>',
        unsafe_allow_html=True,
    )

    def _build_gmail_compose_url(to: str, subject: str, body: str) -> str:
        """Compose URL that opens Gmail in the browser pre-filled."""
        from urllib.parse import quote
        return (
            f"https://mail.google.com/mail/?view=cm&fs=1"
            f"&to={quote(to or '')}"
            f"&su={quote(subject)}"
            f"&body={quote(body)}"
        )

    _gen_c1, _gen_c2 = st.columns(2)
    with _gen_c1:
        if st.button("Generate HOI Request", key=f"gen_hoi_{lid}", use_container_width=True):
            try:
                from template_filler import fill_template, build_context, OUTPUT_ROOT
                import os as _os, re as _re
                _ctx = build_context(loan)
                _safe = _re.sub(r"[^A-Za-z0-9_-]+", "_", _ctx["borrower_name"])[:40]
                _out = _os.path.join(OUTPUT_ROOT, str(lid), f"HOI Request_{_safe}.docx")
                fill_template("HOI Request.docx", _ctx, _out)
                log_activity(lid, "generated", f"HOI Request generated", user=my_name)
                st.session_state[f"_gen_hoi_path_{lid}"] = _out
                # Build pre-filled Gmail compose URL targeted at the HOI/Insurance contact
                _ins = (loan.get("contacts", {}) or {}).get("insurance", {}) or {}
                _to = _ins.get("email", "")
                _subject = f"HOI / Evidence of Insurance Request Loan {_ctx['loan_num']} {_ctx['borrower_name']}"
                _body = (
                    f"Hi {_ins.get('contact') or _ins.get('name') or 'there'},\n\n"
                    f"Please provide Evidence of Insurance for the following loan. "
                    f"The full request form is attached.\n\n"
                    f"Borrower(s): {_ctx['borrower_name']}\n"
                    f"Property: {_ctx['property_address']}\n"
                    f"Estimated Funding: {_ctx['funding_date']}\n"
                    f"Loan Number: {_ctx['loan_num']}\n"
                    f"Loan Amount: {_ctx['loan_amount']}\n\n"
                    f"Mortgagee Clause:\n{_ctx['mortgagee_clause']}\n\n"
                    f"Please provide an invoice with balance due (or paid-in-full invoice) "
                    f"and cover the full loan amount OR provide the RCE.\n\n"
                    f"Thank you,\n{_ctx['loan_processor']}"
                )
                st.session_state[f"_gen_hoi_email_{lid}"] = _build_gmail_compose_url(_to, _subject, _body)
                st.toast("HOI Request generated")
                st.rerun()
            except Exception as _e:
                st.error(f"Generation failed: {_e}")
    with _gen_c2:
        if st.button("Generate Title Request", key=f"gen_title_{lid}", use_container_width=True):
            try:
                from template_filler import fill_template, build_context, OUTPUT_ROOT
                import os as _os, re as _re
                _ctx = build_context(loan)
                _safe = _re.sub(r"[^A-Za-z0-9_-]+", "_", _ctx["borrower_name"])[:40]
                _out = _os.path.join(OUTPUT_ROOT, str(lid), f"Title Request_{_safe}.docx")
                fill_template("Title Request copy.docx", _ctx, _out)
                log_activity(lid, "generated", f"Title Request generated", user=my_name)
                st.session_state[f"_gen_title_path_{lid}"] = _out
                _ttl = (loan.get("contacts", {}) or {}).get("title", {}) or {}
                _to = _ttl.get("email", "")
                _subject = f"Title Work Request Loan {_ctx['loan_num']} {_ctx['borrower_name']}"
                _body = (
                    f"Hi {_ttl.get('contact') or _ttl.get('name') or 'there'},\n\n"
                    f"Please provide tax pro-rations and title docs as soon as available. "
                    f"The full request form is attached. Summary below:\n\n"
                    f"Borrower(s): {_ctx['borrower_name']}\n"
                    f"Property: {_ctx['property_address']}\n"
                    f"Estimated Funding: {_ctx['funding_date']}\n"
                    f"Loan Number: {_ctx['loan_num']}\n"
                    f"Loan Amount: {_ctx['loan_amount']}\n\n"
                    f"Mortgagee Information:\n{_ctx['mortgagee_clause']}\n\n"
                    f"Items needed: Prelim Title + 24 mo chain, Title Fees in CD format, "
                    f"Payoff (refi only), CPL/ICPL, Wire Instructions, EMD receipt (purchase), "
                    f"Plat Map, Survey (TX/FL), Title E&O, CC&Rs (if applicable), Tax Cert, "
                    f"License # for settlement agent and company.\n\n"
                    f"Thank you,\n{_ctx['loan_processor']}"
                )
                st.session_state[f"_gen_title_email_{lid}"] = _build_gmail_compose_url(_to, _subject, _body)
                st.toast("Title Request generated")
                st.rerun()
            except Exception as _e:
                st.error(f"Generation failed: {_e}")

    # Download + Gmail compose buttons for freshly generated docs
    for _lbl, _skey, _ekey in [
        ("HOI Request",   f"_gen_hoi_path_{lid}",   f"_gen_hoi_email_{lid}"),
        ("Title Request", f"_gen_title_path_{lid}", f"_gen_title_email_{lid}"),
    ]:
        _p = st.session_state.get(_skey)
        _e = st.session_state.get(_ekey)
        if not _p:
            continue
        _dl_c1, _dl_c2 = st.columns([2, 1])
        with _dl_c1:
            try:
                with open(_p, "rb") as _fh:
                    st.download_button(
                        f" Download {_lbl} ({_p.split(chr(92))[-1] if chr(92) in _p else _p.split('/')[-1]})",
                        _fh.read(),
                        file_name=_p.split(chr(92))[-1] if chr(92) in _p else _p.split("/")[-1],
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        key=f"dl_{_skey}",
                        use_container_width=True,
                    )
            except FileNotFoundError:
                pass
        with _dl_c2:
            if _e:
                st.link_button("Open in Gmail", _e, use_container_width=True)

    # â”€â”€ Quick-copy Title & HOI contacts â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    _qc_contacts = loan.get("contacts", {}) or {}
    st.markdown(
        '<span style="font-size:13px;font-weight:700;color:#3b82f6;text-transform:uppercase;'
        'letter-spacing:0.5px;margin-top:12px;display:inline-block;">Title &amp; HOI Contact Copy</span>',
        unsafe_allow_html=True,
    )
    _qc_c1, _qc_c2 = st.columns(2)
    for _col, _role_key, _role_label in [
        (_qc_c1, "title", "Title"),
        (_qc_c2, "insurance", "HOI / Insurance"),
    ]:
        with _col:
            _rc = _normalize_contact_value(_qc_contacts.get(_role_key))
            _name = _rc.get("contact") or _rc.get("name") or _rc.get("company") or ""
            _phone = _rc.get("phone", "")
            _email = _rc.get("email", "")
            st.markdown(
                f'<div style="font-size:10px;color:#3b82f6;font-weight:700;'
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

    # â”€â”€ Open Conditions (interactive checkbox, status, parties, email) â”€â”€â”€â”€
    _conditions = loan.get("conditions", [])
    st.markdown(
        '<span style="font-size:13px;font-weight:700;color:#3b82f6;text-transform:uppercase;'
        'letter-spacing:0.5px;margin-top:12px;display:inline-block;">Open Conditions</span>',
        unsafe_allow_html=True,
    )

    PARTY_OPTIONS_LD = [
        "Borrower", "Co-Borrower", "Title", "Realtor", "Seller",
        "Underwriter", "Jr Underwriter", "Loan Officer", "Closer",
        "Insurance", "Appraiser", "Manager",
    ]
    COND_STATUSES_LD = {
        "Needed":         {"label": "Needed",         "emoji": ""},
        "Requested":      {"label": "Requested",      "emoji": ""},
        "Important":      {"label": "Important",      "emoji": ""},
        "Ready to Clear": {"label": "Ready to Clear", "emoji": ""},
        "Cleared":        {"label": "Cleared",        "emoji": ""},
    }

    _ld_fkey = f"ld_{lid}"

    if _conditions:
        _ld_checked = []
        for _c in _conditions:
            _c["desc"] = _c.get("desc", _c.get("description", ""))
            if "num" not in _c:
                _c["num"] = str(_conditions.index(_c) + 1)
            if "party" not in _c:
                _c["party"] = "Borrower"
            _chk, _cstat, _cparties = _render_condition(_c, _ld_fkey, PARTY_OPTIONS_LD, COND_STATUSES_LD)
            if _chk:
                _ld_checked.append({**_c, "party": _cparties[0] if _cparties else _c["party"], "all_parties": _cparties})

            # â”€â”€ Per-condition Guidelines check â”€â”€
            _ld_uid = f"{_ld_fkey}_{_c['num']}"
            _gb1, _gb2 = st.columns([0.5, 9.5])
            with _gb1:
                if st.button("Guide", key=f"{_ld_uid}_guide", help="Check vs. Fannie/Freddie guidelines"):
                    st.session_state[f"{_ld_uid}_guide_open"] = True
                    st.session_state.pop(f"{_ld_uid}_guide_results", None)
            if st.session_state.get(f"{_ld_uid}_guide_open"):
                _gc1, _gc2 = st.columns([9, 0.5])
                with _gc2:
                    if st.button("Close", key=f"{_ld_uid}_guide_close"):
                        for _k in (f"{_ld_uid}_guide_open", f"{_ld_uid}_guide_results"):
                            st.session_state.pop(_k, None)
                        st.rerun()
                _gres = st.session_state.get(f"{_ld_uid}_guide_results")
                if _gres is None:
                    with st.spinner("Searching Fannie Mae & Freddie Mac"):
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
                        f'border-radius:6px;margin:4px 0 4px 32px;">{_gres["error"]}</div>',
                        unsafe_allow_html=True,
                    )
                elif isinstance(_gres, list) and _gres:
                    for _gm in _gres[:4]:
                        _src = _gm.get("source", "")
                        _sec = _gm.get("section", "")
                        _pg  = _gm.get("page", "")
                        _sc  = _gm.get("score", 0)
                        _ex  = (_gm.get("excerpt", "") or "").replace("\n", " ")[:360]
                        _sec_part = f"  <b>{_sec}</b>" if _sec else ""
                        st.markdown(
                            f'<div style="font-size:11px;color:#e5e7eb;padding:6px 10px;margin:3px 0 3px 32px;'
                            f'background:rgba(59,130,246,0.05);border-left:2px solid rgba(59,130,246,0.45);'
                            f'border-radius:4px;">'
                            f'<span style="color:#3b82f6;font-weight:700;">{_src}</span>'
                            f'{_sec_part}'
                            f' <span style="color:#9ca3af;">p.{_pg}  {_sc}% match</span><br/>'
                            f'<span style="color:#cbd5e1;font-size:10.5px;">{_ex}</span>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )
                elif isinstance(_gres, list):
                    st.markdown(
                        '<div style="font-size:11px;color:#6b7280;padding:4px 0 4px 32px;">'
                        'No relevant guideline sections found.</div>',
                        unsafe_allow_html=True,
                    )

        # â”€â”€ Email Draft below conditions, auto-populate from stored contacts â”€â”€
        st.markdown(
            '<span style="font-size:13px;font-weight:700;color:#3b82f6;text-transform:uppercase;'
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
            _cv = _normalize_contact_value(_cv)
            if not _cv:
                continue
            _clabel = _party_display_labels.get(_ck, _ck.replace("_", " ").title())
            _cname = _cv.get("name") or _cv.get("company") or ""
            _cemail = _cv.get("email", "")
            _display = f"{_clabel}{f' {_cname}' if _cname else ''}{f' ({_cemail})' if _cemail else ''}"
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
            _ld_recipients = st.multiselect(
                "Send to", _party_choices,
                default=[_party_choices[0]] if _party_choices else [],
                key=f"ld_recip_multi_{lid}", label_visibility="visible"
            )
        with _em_c2:
            _ld_lang = st.selectbox(
                "Language", ["English", "Spanish"],
                key=f"ld_lang_{lid}", label_visibility="visible"
            )
        with _em_c3:
            if _ld_checked:
                st.markdown(
                    f'<div style="padding-top:26px;font-size:11px;color:#3b82f6;font-weight:600;">'
                    f'{len(_ld_checked)} checked</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    '<div style="padding-top:26px;font-size:10px;color:#9ca3af;">check above</div>',
                    unsafe_allow_html=True,
                )

        def _recipient_type_from_label(label: str) -> str:
            s = str(label or "").lower()
            if "appraiser" in s:
                return "Appraiser"
            if "realtor" in s or "listing agent" in s or "selling agent" in s:
                return "Realtor"
            if "borrower" in s or "buyer" in s or "co-borrower" in s:
                return "Borrower"
            return str(label or "Borrower").split("(")[0].strip()

        _ld_d1, _ld_d2 = st.columns([1, 1])
        with _ld_d1:
            _ld_draft_btn = st.button("Draft Email", key=f"ld_draft_{lid}",
                                      type="primary", use_container_width=True)
        with _ld_d2:
            _ld_ai_btn = st.button("Draft with AI", key=f"ld_ai_draft_{lid}",
                                   use_container_width=True)

        if _ld_draft_btn:
            from ai_engine import draft_email as _de
            import urllib.parse
            _targets = _ld_recipients or (_party_choices[:1] if _party_choices else [])
            for _ld_recipient in _targets:
                _recip_contact = _normalize_contact_value(_contact_party_map.get(_ld_recipient, {}))
                _recip_type = _recipient_type_from_label(_ld_recipient)
                _is_client_party = _recip_type == "Borrower"
                if _ld_checked:
                    _cond_lines = [
                        f"- Condition #{c['num']}: {(_to_client_language(c['desc'], 'Borrower') if _is_client_party else c['desc'])}"
                        for c in _ld_checked
                    ]
                else:
                    _cond_lines = [
                        f"- Condition #{c['num']}: {(_to_client_language(c['desc'], 'Borrower') if _is_client_party else c['desc'])}"
                        for c in _conditions[:10]
                    ]
                _email_out = _de("\n".join(_cond_lines), _recip_type, _ld_lang)
                _recip_email = _recip_contact.get("email", "")
                st.markdown(f"**Draft: {_ld_recipient}**")
                if _recip_email:
                    st.markdown(
                        f'<div style="font-size:11px;color:#9ca3af;margin-bottom:4px;">To: <b>{_recip_email}</b></div>',
                        unsafe_allow_html=True,
                    )
                st.container(border=True).markdown(_email_out)
                _gmail_url = "https://mail.google.com/mail/?view=cm&fs=1&" + urllib.parse.urlencode({
                    "to": _recip_email,
                    "su": f"Re: {loan.get('loan_num','')} {loan.get('borrower','')}",
                    "body": _email_out,
                })
                st.markdown(
                    f'<a href="{_gmail_url}" target="_blank" style="display:inline-block;margin-top:8px;'
                    f'padding:6px 16px;background:rgba(66,133,244,0.12);border:1px solid rgba(66,133,244,0.4);'
                    f'border-radius:6px;color:#4285f4;font-size:12px;font-weight:700;text-decoration:none;">'
                    f'Compose in Gmail</a>',
                    unsafe_allow_html=True,
                )

        if _ld_ai_btn:
            import ai_router as _ld_ar
            import urllib.parse
            _ld_backend = _ld_ar.get_preferred_backend()
            if _ld_backend == "script":
                st.warning("AI backend not configured. Go to AI Settings.")
            else:
                _targets = _ld_recipients or (_party_choices[:1] if _party_choices else [])
                _conds_for_ai = _ld_checked if _ld_checked else _conditions[:10]
                for _ld_recipient in _targets:
                    _recip_type = _recipient_type_from_label(_ld_recipient)
                    with st.spinner(f"Drafting with AI for {_ld_recipient}"):
                        _ld_ai_text, _ld_ai_log = _ld_ar.draft_email_enhanced(
                            _conds_for_ai, _recip_type, _ld_lang
                        )
                    if _ld_ai_text:
                        _recip_contact2 = _normalize_contact_value(_contact_party_map.get(_ld_recipient, {}))
                        _recip_email2 = _recip_contact2.get("email", "")
                        st.markdown(f"**AI Draft: {_ld_recipient}**")
                        st.container(border=True).markdown(_ld_ai_text)
                        _gmail_url2 = "https://mail.google.com/mail/?view=cm&fs=1&" + urllib.parse.urlencode({
                            "to": _recip_email2,
                            "su": f"Re: {loan.get('loan_num','')} {loan.get('borrower','')}",
                            "body": _ld_ai_text,
                        })
                        st.markdown(
                            f'<a href="{_gmail_url2}" target="_blank" style="display:inline-block;margin-top:8px;'
                            f'padding:6px 16px;background:rgba(66,133,244,0.12);border:1px solid rgba(66,133,244,0.4);'
                            f'border-radius:6px;color:#4285f4;font-size:12px;font-weight:700;text-decoration:none;">'
                            f'Compose in Gmail</a>',
                            unsafe_allow_html=True,
                        )
    else:
        st.markdown(
            '<span style="color:#9ca3af;font-size:12px;">No conditions attached to this loan yet. '
            'Upload and scan a document to extract conditions.</span>',
            unsafe_allow_html=True,
        )

    # â”€â”€ Parties & Contacts â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    _contacts = loan.get("contacts", {})
    st.markdown(
        '<span style="font-size:13px;font-weight:700;color:#3b82f6;text-transform:uppercase;'
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
        import urllib.parse as _uparse2
        _contact_html = '<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">'
        for _ck, _cv in _contacts.items():
            _cv = _normalize_contact_value(_cv)
            if not _cv:
                continue
            if not any(str(v).strip() for v in _cv.values()):
                continue
            _clabel = _party_labels.get(_ck, _ck.replace("_", " ").title())
            _cname = _cv.get("name") or _cv.get("company") or _cv.get("contact") or ""
            _cphone = _cv.get("phone", "")
            _cemail = _cv.get("email", "")
            _cbrok = _cv.get("brokerage", "")
            _cpos = _cv.get("position", "")
            _gmail_link = ""
            if _cemail:
                _gurl = "https://mail.google.com/mail/?view=cm&fs=1&" + _uparse2.urlencode({
                    "to": _cemail,
                    "su": f"Re: {loan.get('loan_num','')} {loan.get('borrower','')}",
                })
                _gmail_link = (
                    f'<a href="{_gurl}" target="_blank" style="margin-left:8px;padding:1px 8px;'
                    f'background:rgba(66,133,244,0.12);border:1px solid rgba(66,133,244,0.35);'
                    f'border-radius:4px;color:#4285f4;font-size:10px;font-weight:700;text-decoration:none;">Gmail</a>'
                )
            _contact_html += (
                f'<div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.1);border-radius:8px;padding:10px;">'
                f'<div style="font-size:10px;color:#3b82f6;font-weight:700;text-transform:uppercase;margin-bottom:4px;">{_clabel}</div>'
                f'<div style="color:#ffffff;font-size:13px;font-weight:600;margin-bottom:4px;">{_cname or ""}</div>'
                + (f'<div style="color:#9ca3af;font-size:11px;margin-bottom:2px;">{_cphone}</div>' if _cphone else '')
                + (f'<div style="display:flex;align-items:center;font-size:11px;color:#9ca3af;">{_cemail}{_gmail_link}</div>' if _cemail else '')
                + (f'<div style="color:#9ca3af;font-size:11px;">{_cbrok}</div>' if _cbrok else '')
                + (f'<div style="color:#9ca3af;font-size:11px;">{_cpos}</div>' if _cpos else '')
                + f'</div>'
            )
        _contact_html += '</div>'
        st.markdown(_contact_html, unsafe_allow_html=True)
    else:
        st.markdown(
            '<span style="color:#9ca3af;font-size:12px;">No contact information attached. '
            'Upload a Purchase Contract or 1003 to populate parties.</span>',
            unsafe_allow_html=True,
        )

    # â”€â”€ Scan & Attach Document â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    st.markdown(
        '<span style="font-size:13px;font-weight:700;color:#3b82f6;text-transform:uppercase;'
        'letter-spacing:0.5px;margin-top:12px;display:inline-block;">Scan &amp; Attach Document</span>',
        unsafe_allow_html=True,
    )
    with st.expander("Upload a document to scan and populate loan data", expanded=False):
        _scan_doc_types = [
            "Approval Letter", "Loan Estimate (LE)",
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
        _cloud_enabled = False
        try:
            import cloud_client as _cc_check
            _cloud_enabled = _cc_check.is_enabled()
        except Exception:
            pass

        # Auto-approve cloud when enabled user configured their key intentionally
        _cloud_doc_types = {"Purchase Contract", "Approval Letter"}
        _user_approved_cloud = _cloud_enabled and _scan_dtype in _cloud_doc_types

        _scan_btn_label = (
            f"Scan with AI" if _user_approved_cloud else "Scan"
        )
        if _scan_file and st.button(_scan_btn_label, key=f"detail_scan_btn_{lid}",
                                     type="primary", use_container_width=True):
            _ld_provider = "AI"
            try:
                _ld_provider = _cc_check.get_config().get("provider", "AI").title()
            except Exception:
                pass
            _spinner_label = (
                f"Sending {_scan_dtype} to {_ld_provider}... (2-5 sec)"
                if _user_approved_cloud
                else f"Scanning {_scan_dtype}..."
            )
            with st.spinner(_spinner_label):
                from ai_engine import process_document as _proc_doc
                _pdf_bytes = _scan_file.read()
                _scan_result = _proc_doc(_pdf_bytes, _scan_dtype, user_approved_cloud=_user_approved_cloud)

            if not _scan_result.get("success"):
                st.error(_scan_result.get("error", "Scan failed could not extract text from this PDF."))
            else:
                st.session_state[_scan_key] = _scan_result
                st.success(f"Scanned {_scan_dtype} {_scan_result.get('text_length', 0):,} chars extracted")

        # Process scan results if available
        if _scan_key in st.session_state and st.session_state[_scan_key]:
            _sr = st.session_state[_scan_key]
            _sr_dtype = _sr.get("doc_type", "")
            _merged_something = False

            # â”€â”€ AI usage indicator (cloud vs regex-only) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            _ai_log = _sr.get("ai_log", "")
            if _ai_log and "CLOUD" in _ai_log.upper():
                st.markdown(
                    f'<div style="display:inline-block;padding:3px 10px;margin:4px 0 8px 0;'
                    f'background:rgba(59,130,246,0.12);border:1px solid rgba(59,130,246,0.4);'
                    f'border-radius:12px;font-size:11px;color:#3b82f6;font-weight:600;">'
                    f'Cloud AI augmented - {_ai_log}</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f'<div style="display:inline-block;padding:3px 10px;margin:4px 0 8px 0;'
                    f'background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.12);'
                    f'border-radius:12px;font-size:11px;color:#9ca3af;">'
                    f'Regex extraction only (Cloud AI off)</div>',
                    unsafe_allow_html=True,
                )

            # â”€â”€ Purchase Contract â†’ merge contacts + show extracted data â”€â”€
            if _sr_dtype == "Purchase Contract" and _sr.get("extracted_data"):
                _pcd = _sr["extracted_data"]
                _pc_buyer = _pcd.get("buyer", {})
                _pc_seller = _pcd.get("seller", {})
                _pc_la = _pcd.get("listing_agent", {})
                _pc_sa = _pcd.get("selling_agent", {})
                _pc_title = _pcd.get("title", {})
                _pc_txn = _pcd.get("transaction", {})

                _pc_rows = [
                    f'Buyer: {_pc_buyer.get("name","")}',
                    f'Seller: {_pc_seller.get("name","")}',
                    f'Price: ${_pc_txn.get("purchase_price","")}',
                    f'Close: {_pc_txn.get("closing_date","")}',
                ]
                if _pc_txn.get("date_signed"):
                    _pc_rows.append(f'Date Signed: {_pc_txn["date_signed"]}')
                if _pc_txn.get("obligation_date"):
                    _pc_rows.append(f'Obligation Date: {_pc_txn["obligation_date"]}')
                if _pc_txn.get("seller_concessions"):
                    _pc_rows.append(f'Seller Concessions: {_pc_txn["seller_concessions"]}')
                if _pc_la.get("name"):
                    _la_str = f'Listing Agent: {_pc_la["name"]}'
                    if _pc_la.get("brokerage"): _la_str += f'  {_pc_la["brokerage"]}'
                    if _pc_la.get("phone"):     _la_str += f'  {_pc_la["phone"]}'
                    if _pc_la.get("email"):     _la_str += f'  {_pc_la["email"]}'
                    _pc_rows.append(_la_str)
                if _pc_sa.get("name"):
                    _sa_str = f'Selling Agent: {_pc_sa["name"]}'
                    if _pc_sa.get("brokerage"): _sa_str += f'  {_pc_sa["brokerage"]}'
                    if _pc_sa.get("phone"):     _sa_str += f'  {_pc_sa["phone"]}'
                    if _pc_sa.get("email"):     _sa_str += f'  {_pc_sa["email"]}'
                    _pc_rows.append(_sa_str)
                if _pc_title.get("company"):
                    _tc_str = f'Title: {_pc_title["company"]}'
                    if _pc_title.get("contact"): _tc_str += f'  {_pc_title["contact"]}'
                    if _pc_title.get("phone"):   _tc_str += f'  {_pc_title["phone"]}'
                    _pc_rows.append(_tc_str)
                st.markdown(
                    '<div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.1);border-radius:8px;'
                    'padding:10px;margin:8px 0;font-size:12px;color:#9ca3af;">'
                    '<b style="color:#3b82f6;">Purchase Contract found:</b><br>'
                    + '<br>'.join(_pc_rows) +
                    '</div>',
                    unsafe_allow_html=True,
                )

                if st.button("Merge contacts into this loan", key=f"detail_merge_pc_{lid}",
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
                    log_activity(lid, "upload", f"Purchase Contract scanned contacts merged", user=my_name)
                    st.session_state.pop(_scan_key, None)
                    st.toast("Contacts merged into loan")
                    st.rerun()

            # â”€â”€ 1003 Application â†’ merge contacts â”€â”€
            elif _sr_dtype == "1003 Application" and _sr.get("extracted_data"):
                _app = _sr["extracted_data"]
                _app_b = _app.get("borrower", {})
                _app_cb = _app.get("co_borrower", {})
                _app_emp = _app.get("employment", {})

                st.markdown(
                    '<div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.1);border-radius:8px;'
                    'padding:10px;margin:8px 0;font-size:12px;color:#9ca3af;">'
                    '<b style="color:#3b82f6;">1003 Application found:</b><br>'
                    f'Borrower: {_app_b.get("name","")}  Phone: {_app_b.get("phone","")}<br>'
                    f'Employer: {_app_emp.get("employer","")}'
                    '</div>',
                    unsafe_allow_html=True,
                )

                if st.button("Merge contacts into this loan", key=f"detail_merge_1003_{lid}",
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
                    log_activity(lid, "upload", f"1003 Application scanned contacts merged", user=my_name)
                    st.session_state.pop(_scan_key, None)
                    st.toast("Contacts merged into loan")
                    st.rerun()

            # â”€â”€ All other doc types â†’ merge conditions â”€â”€
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
                        f'<b style="color:#3b82f6;">{_sr_dtype} scanned:</b> '
                        f'{len(_new_conds)} condition(s) found</div>',
                        unsafe_allow_html=True,
                    )
                    # Preview the conditions
                    for _nc in _new_conds:
                        st.markdown(
                            f'<span style="color:#fbbf24;font-size:12px;"></span> '
                            f'<span style="color:#ffffff;font-size:12px;">{_nc["desc"]}</span> '
                            f'<span style="color:#9ca3af;font-size:11px;">{_nc["party"]}</span>',
                            unsafe_allow_html=True,
                        )

                    if st.button("Merge conditions into this loan", key=f"detail_merge_conds_{lid}",
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
                        log_activity(lid, "upload", f"{_sr_dtype} scanned {_added} condition(s) added", user=my_name)
                        st.session_state.pop(_scan_key, None)
                        st.toast(f"{_added} condition(s) merged")
                        st.rerun()
                else:
                    st.info("No conditions extracted from this document.")

            # â”€â”€ Bank Statement â†’ show rules â”€â”€
            elif _sr.get("bank_rules"):
                st.markdown(
                    f'<div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.1);border-radius:8px;'
                    f'padding:10px;margin:8px 0;font-size:12px;color:#9ca3af;">'
                    f'<b style="color:#3b82f6;">Bank Statement Analysis:</b></div>',
                    unsafe_allow_html=True,
                )
                st.markdown(_sr["bank_rules"])
                log_activity(lid, "upload", "Bank Statement scanned and reviewed", user=my_name)

    # â”€â”€ Approval Fetch â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    _SHOW_APPROVAL_FETCH = False  # Legacy offline folder fetch is kept in code but hidden for now.
    if _SHOW_APPROVAL_FETCH:
        import os as _af_os
        _af_key = f"approval_fetch_{lid}"

        # Step 1: Upload the approval letter
        _af_file = st.file_uploader(
            "Upload Approval Letter PDF", type=["pdf"],
            key=f"af_upload_{lid}", label_visibility="collapsed",
        )

        # Check cloud AI support for Approval Letter
        _af_cloud_enabled = False
        try:
            import cloud_client as _af_cc
            _af_cloud_enabled = _af_cc.is_enabled()
        except Exception:
            pass

        # Determine user approval for cloud AI on Approval Letter
        _af_user_approved_cloud = False
        _af_cloud_consent_key = f"af_cloud_consent_{lid}"
        if _af_cloud_enabled:
            _af_session_consent = st.session_state.get("cloud_consent_session", None)
            if _af_session_consent == "yes":
                _af_user_approved_cloud = True
            elif _af_session_consent == "no":
                _af_user_approved_cloud = False
            else:
                # Show consent prompt
                _af_consent_state = st.session_state.get(_af_cloud_consent_key, None)
                if _af_consent_state is None:
                    st.info("This document type supports cloud AI augmentation for better extraction.")
                    _afc1, _afc2, _afc3 = st.columns(3)
                    with _afc1:
                        if st.button("Send to Cloud AI", key=f"af_consent_yes_{lid}"):
                            st.session_state[_af_cloud_consent_key] = "yes_once"
                            st.rerun()
                    with _afc2:
                        if st.button("Skip AI for this scan", key=f"af_consent_no_{lid}"):
                            st.session_state[_af_cloud_consent_key] = "no"
                            st.rerun()
                    with _afc3:
                        if st.button("Always for session", key=f"af_consent_session_{lid}"):
                            st.session_state["cloud_consent_session"] = "yes"
                            st.session_state[_af_cloud_consent_key] = "yes_once"
                            st.rerun()
                elif _af_consent_state == "yes_once":
                    _af_user_approved_cloud = True
                elif _af_consent_state == "no":
                    _af_user_approved_cloud = False

        if _af_file and st.button("Scan Approval Letter", key=f"af_scan_btn_{lid}",
                                   type="primary", use_container_width=True):
            _af_provider = "AI"
            try:
                _af_provider = _af_cc.get_config().get("provider", "AI").title()
            except Exception:
                pass
            _af_spinner = (
                f"Sending Approval Letter to {_af_provider}... (2-5 sec)"
                if _af_user_approved_cloud
                else "Extracting conditions from approval letter..."
            )
            with st.spinner(_af_spinner):
                from ai_engine import process_document as _af_proc, extract_contacts as _af_contacts
                from pypdf import PdfReader as _AF_PR
                _af_bytes = _af_file.read()
                _af_result = _af_proc(_af_bytes, "Approval Letter", user_approved_cloud=_af_user_approved_cloud)

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
                                "confidence": _cells[4] if len(_cells) >= 5 else "",
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
                f'<span style="color:#3b82f6;font-weight:700;font-size:13px;">Approval Letter Scanned</span><br>'
                f'<span style="color:#9ca3af;font-size:12px;">Borrower: <b style="color:#ffffff;">'
                f'{_af_borrower or "Unknown"}</b>  '
                f'{_af_data["cond_count"]} condition(s) extracted  '
                f'{_af_data["text_length"]:,} chars'
                f'{"  Commitment: <b style=color:#9ca3af;>" + _af_data.get("commitment_date","") + "</b>" if _af_data.get("commitment_date") else ""}'
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
                    if st.button("Remove Clear Approval", key=f"af_clear_{lid}",
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
                            f'<div class="stat-card"><div class="stat-num" style="color:#3b82f6;">'
                            f'{len(_af_found)}</div>'
                            f'<div class="stat-label">Documents Found</div></div>',
                            unsafe_allow_html=True,
                        )
                    with _s3:
                        st.markdown(
                            f'<div class="stat-card"><div class="stat-num" style="color:#ef4444;">'
                            f'{len(_af_missing)}</div>'
                            f'<div class="stat-label">Still Missing</div></div>',
                            unsafe_allow_html=True,
                        )

                    # Found conditions
                    if _af_found:
                        st.markdown(
                            '<div style="font-size:13px;font-weight:700;color:#3b82f6;'
                            'margin:12px 0 6px 0;">FOUND Documents located in folder</div>',
                            unsafe_allow_html=True,
                        )
                        for _c, _matches in _af_found:
                            _best = _matches[0]
                            _conf_color = "#3b82f6" if _best["score"] >= 70 else (
                                "#fbbf24" if _best["score"] >= 50 else "#f59e0b"
                            )
                            st.markdown(
                                f'<div style="display:flex;gap:10px;align-items:flex-start;'
                                f'background:rgba(59,130,246,0.05);border-left:3px solid #3b82f6;'
                                f'border-radius:6px;padding:8px 12px;margin-bottom:4px;">'
                                f'<span style="color:#3b82f6;font-weight:700;font-size:12px;min-width:20px;"></span>'
                                f'<div style="flex:1;">'
                                f'<span style="color:#ffffff;font-size:13px;font-weight:600;">'
                                f'#{_c["num"]} {_c["desc"][:80]}</span><br>'
                                f'<span style="color:#9ca3af;font-size:11px;">{_best["file_name"]}'
                                f' &nbsp;&nbsp; <span style="color:{_conf_color};">{_best["score"]}% match</span>'
                                f' &nbsp;&nbsp; {_best["match_type"]}</span>'
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
                            'margin:12px 0 6px 0;">MISSING No matching documents found</div>',
                            unsafe_allow_html=True,
                        )
                        for _c in _af_missing:
                            st.markdown(
                                f'<div style="display:flex;gap:10px;align-items:flex-start;'
                                f'background:rgba(239,68,68,0.05);border-left:3px solid #ef4444;'
                                f'border-radius:6px;padding:8px 12px;margin-bottom:4px;">'
                                f'<span style="color:#ef4444;font-weight:700;font-size:12px;min-width:20px;"></span>'
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

                    # Merge button push conditions + found/missing status into the loan
                    st.markdown("---")
                    _mc1, _mc2 = st.columns([1, 1])
                    with _mc1:
                        if st.button("Merge conditions into this loan", key=f"af_merge_{lid}",
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
                                f"Approval letter scanned {_added} condition(s) merged, "
                                f"{len(_af_found)} found, {len(_af_missing)} missing",
                                user=my_name)
                            st.session_state.pop(_af_key, None)
                            st.toast(f"{_added} conditions merged into loan")
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
                                f"Approval letter scanned {_added} condition(s) merged",
                                user=my_name)
                            st.session_state.pop(_af_key, None)
                            st.toast(f"{_added} conditions merged")
                            st.rerun()

                elif _af_scan_res and _af_scan_res.get("error"):
                    st.error(_af_scan_res["error"])

    # â”€â”€ Notes â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    st.markdown(
        '<span style="font-size:13px;font-weight:700;color:#3b82f6;text-transform:uppercase;'
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
        from sharing import notify_shared_members as _nsm
        _nsm(loan, my_name, "updated")
        st.toast("Notes saved")
        st.rerun()

    # â”€â”€ Quick Actions â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    st.markdown(
        '<span style="font-size:13px;font-weight:700;color:#3b82f6;text-transform:uppercase;'
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

    # â”€â”€ Team Visibility â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    _ld_docs = loan.get("documents", [])
    _ld_doc_count = len(_ld_docs)
    _ld_borrower_email = ""
    _ld_contacts = loan.get("contacts", {}) or {}
    for _ld_ck in ("borrower", "co_borrower"):
        _ld_ce = (_ld_contacts.get(_ld_ck) or {}).get("email", "")
        if _ld_ce:
            _ld_borrower_email = _ld_ce
            break

    st.markdown(
        '<span style="font-size:13px;font-weight:700;color:#3b82f6;text-transform:uppercase;'
        'letter-spacing:0.5px;margin-top:16px;display:inline-block;">Documents</span>',
        unsafe_allow_html=True,
    )
    _td1, _td2 = st.columns([2, 1])
    with _td1:
        st.markdown(
            f'<div style="font-size:14px;color:#d1d5db;padding-top:6px;">'
            f'<b style="color:#3b82f6;">{_ld_doc_count}</b> document(s) added to this loan</div>',
            unsafe_allow_html=True,
        )
    with _td2:
        _loan_num_str = loan.get("loan_num", str(lid))
        _borrower_str = loan.get("borrower", "")
        _mailto_subject = f"Loan {_loan_num_str} {_borrower_str} Document Request"
        _mailto_body = (
            f"Hello,%0A%0A"
            f"Please find below the document checklist for Loan #{_loan_num_str} {_borrower_str}.%0A%0A"
            f"Documents received: {_ld_doc_count}%0A%0A"
            f"Please upload or email any outstanding documents at your earliest convenience.%0A%0A"
            f"Thank you"
        )
        _mailto_to = _ld_borrower_email or ""
        _mailto_link = f"mailto:{_mailto_to}?subject={_mailto_subject}&body={_mailto_body}"
        st.link_button("Email Documents", _mailto_link, use_container_width=True)

    # â”€â”€ Ask AI Assistant â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    st.markdown(
        '<span style="font-size:13px;font-weight:700;color:#3b82f6;text-transform:uppercase;'
        'letter-spacing:0.5px;margin-top:16px;display:inline-block;">Ask AI Assistant</span>',
        unsafe_allow_html=True,
    )
    _ai_chat_enabled = False
    try:
        import cloud_client as _ld_cc
        _ai_chat_enabled = _ld_cc.is_enabled()
    except Exception:
        pass

    if not _ai_chat_enabled:
        st.markdown(
            '<div style="font-size:12px;color:#9ca3af;padding:6px 0;">Add your Claude API key in AI Settings to enable the loan assistant.</div>',
            unsafe_allow_html=True,
        )
    else:
        _chat_key = f"loan_chat_{lid}"
        if _chat_key not in st.session_state:
            st.session_state[_chat_key] = []

        # Render existing messages
        for _cm in st.session_state[_chat_key]:
            with st.chat_message(_cm["role"]):
                st.markdown(_cm["content"])

        _user_q = st.chat_input("Ask anything about this loan...", key=f"loan_chat_input_{lid}")
        if _user_q:
            st.session_state[_chat_key].append({"role": "user", "content": _user_q})
            with st.chat_message("user"):
                st.markdown(_user_q)

            # Build loan context summary
            _lc_parts = [
                f"Loan #{loan.get('loan_num','')} {loan.get('borrower','')}",
                f"Status: {loan.get('status','')}",
                f"Property: {loan.get('property_address', '')}",
                f"Purchase Price: {loan.get('purchase_price','')}",
                f"Loan Amount: {loan.get('loan_amount','')}",
                f"Closing Date: {loan.get('closing_date','')}",
                f"Lock Expiry: {loan.get('lock_expiry','')}",
            ]
            _conds = loan.get("conditions", [])
            if _conds:
                _open_conds = [c.get("desc","") for c in _conds if c.get("status") not in ("Cleared","Ready to Clear")]
                if _open_conds:
                    _lc_parts.append(f"Open conditions ({len(_open_conds)}): " + "; ".join(_open_conds[:8]))
            _loan_ctx = "\n".join(_lc_parts)

            _system_prompt = (
                f"You are a mortgage loan assistant. Here is the loan file context:\n\n{_loan_ctx}\n\n"
                f"Answer questions clearly and concisely. If asked about something not in the loan context, say so."
            )

            try:
                import cloud_client as _ld_cc2
                _chat_history = st.session_state[_chat_key][:-1]  # exclude the just-added user msg
                _messages = [{"role": m["role"], "content": m["content"]} for m in _chat_history]
                _messages.append({"role": "user", "content": _user_q})
                _ai_reply = _ld_cc2.chat(_messages, system=_system_prompt)
            except Exception as _ce:
                _ai_reply = f"Error: {_ce}"

            st.session_state[_chat_key].append({"role": "assistant", "content": _ai_reply})
            with st.chat_message("assistant"):
                st.markdown(_ai_reply)

        if st.session_state[_chat_key]:
            if st.button("Clear chat", key=f"loan_chat_clear_{lid}", use_container_width=False):
                st.session_state[_chat_key] = []
                st.rerun()

    # â”€â”€ Activity Log â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    st.markdown(
        '<span style="font-size:13px;font-weight:700;color:#3b82f6;text-transform:uppercase;'
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
            "status": "â†’",
            "reassign": "User",
            "note": "",
            "dates": "",
            "removed": "Remove",
            "docs": "",
            "upload": "Attach",
            "email": "Email",
            "share": "â†—",
        }
        for entry in activity[:30]:
            _ts = entry.get("ts", "")[:16].replace("T", " ")
            _action = entry.get("action", "")
            _detail = entry.get("detail", "")
            _user = entry.get("user", "")
            _icon = _act_icons.get(_action, "")
            _user_tag = f'<span style="color:#3b82f6;font-weight:600;">{_user}</span>  ' if _user else ""
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
def show_persistent_header():
    """My Pipeline header shown on every authenticated page.
    Compact sticky strip with title + status counts + progress bar."""
    try:
        from crm import get_all_loans, STATUS_OPTIONS
        loans = _visible_account_loans(get_all_loans() or [])
    except Exception:
        loans = []
        STATUS_OPTIONS = ["Pending", "Requested", "Cleared", "Overdue", "Closed"]

    counts = {s: sum(1 for l in loans if l.get("status") == s) for s in STATUS_OPTIONS}
    total = len(loans)
    closed = counts.get("Cleared", 0) + counts.get("Closed", 0)
    in_prog = counts.get("Requested", 0)
    pct_clr = int((closed / total) * 100) if total else 0
    pct_ip  = int((in_prog / total) * 100) if total else 0
    pct_pen = max(0, 100 - pct_clr - pct_ip)
    chip_html = ''.join([
        f'<a href="?pipefilter={s}&page=pipeline" class="pa-pchip" style="--c:{c};text-decoration:none;cursor:pointer;">'
        f'<span class="pa-pchip-n" style="color:{c};">{counts.get(s, 0) if s != "All" else total}</span>'
        f'<span class="pa-pchip-l">{s}</span></a>'
        for s, c in [("All","#3b82f6"),("Pending","#ef4444"),("Requested","#f59e0b"),
                     ("Cleared","#3b82f6"),("Overdue","#9ca3af"),("Closed","#9ca3af")]
    ])
    st.markdown(
        f"""
        <div class="pa-pipe-dash">
          <span class="pa-pipe-dash-title">My Pipeline</span>
          <div class="pa-pipe-dash-row">{chip_html}</div>
          <div class="pa-pipe-dash-bar">
            <div style="background:#3b82f6;width:{pct_clr}%;"></div>
            <div style="background:#f59e0b;width:{pct_ip}%;"></div>
            <div style="background:#ef4444;width:{pct_pen}%;"></div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def main():
    _handle_google_oauth_callback()
    if not st.session_state.authenticated:
        # If user explicitly logged out, show login once, then stop forcing it.
        if st.session_state.get("force_login", False):
            st.session_state.force_login = False
            show_login_page()
            return
        if _AUTO_ENTER_SANDBOX:
            _enter_sandbox(page="dashboard")
            st.rerun()
        show_login_page()
    else:
        _load_user_gemini_key_into_session()
        _profile = _user_trial_profile()
        if _profile and not _has_paid_access(_profile):
            show_sidebar()
            show_persistent_header()
            _render_trial_gate(_profile)
            return
        _qp_page = st.query_params.get("page", "")
        if isinstance(_qp_page, list):
            _qp_page = _qp_page[0] if _qp_page else ""
        if _qp_page:
            st.session_state.page = str(_qp_page)
        show_sidebar()
        show_persistent_header()
        _render_gemini_key_prompt()
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
        elif page == "ollama" or page == "ai_settings":
            show_ollama_page()
        elif page == "billing":
            show_billing_page()
        elif page == "pricing":
            show_pricing_page()
        elif page == "chat":
            show_chat_page()
        elif page == "history":
            show_history()
        elif page == "reader":
            show_reader()
        elif page == "loan_detail":
            show_loan_detail()
        elif page == "snapshot":
            show_snapshot_page()
        elif page == "report_issue":
            show_report_issue_page()
        elif page == "missing_docs":
            show_missing_docs_page()
        elif page == "doc_expiry":
            show_doc_expiry_page()
        elif page == "spanish_reply":
            show_spanish_reply_page()
        elif page == "income_verifier":
            show_income_verifier_page()
        elif page == "auto_data_entry":
            show_auto_data_entry_page()
        elif page == "credit_summary":
            show_credit_summary_page()
        elif page == "dti_calculator":
            show_dti_calculator_page()
        elif page == "condition_clearer":
            show_condition_clearer_page()
        elif page == "compliance_checker":
            show_compliance_checker_page()
        elif page == "closing_package":
            show_closing_package_page()
        elif page == "pipeline_dashboard":
            show_pipeline_dashboard_page()
        elif page == "guideline_checker":
            show_guideline_checker_page()
        elif page == "fraud_detector":
            show_fraud_detector_page()
        elif page == "multi_borrower":
            show_multi_borrower_page()
        elif page == "los_export":
            show_los_export_page()
        elif page == "rate_lock_monitor":
            show_rate_lock_monitor_page()
        elif page == "underwriting_tracker":
            show_underwriting_tracker_page()
        elif page == "document_classifier":
            show_document_classifier_page()
        elif page == "escrow_calculator":
            show_escrow_calculator_page()
        else:
            show_dashboard()


if __name__ == "__main__":
    main()
