"""Synthetic scanner preview using the app's actual layout and styles."""
import ast
from pathlib import Path
import sys
import types

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ui_refinement import apply_workspace_style, render_scanner_intro

st.set_page_config(layout="wide", initial_sidebar_state="expanded")
tree = ast.parse((ROOT / "app.py").read_text(encoding="utf-8-sig"))
for node in tree.body:
    if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
        args = node.value.args
        if args and isinstance(args[0], ast.Constant) and isinstance(args[0].value, str):
            if args[0].value.lstrip().startswith("<style>"):
                st.markdown(args[0].value, unsafe_allow_html=True)
                break
apply_workspace_style()
with st.sidebar:
    st.button("Dark", key="preview_theme")
    st.subheader("Processor Assistant")
    st.markdown("**Preview account**")
    st.markdown('<div style="font-size:12px;color:var(--accent);margin-bottom:12px">Manager</div>', unsafe_allow_html=True)
    for label in ("Scanner", "Pipeline", "Overview", "Pricing", "Private Lender Learning"):
        st.button(label, type="primary" if label == "Scanner" else "secondary", use_container_width=True)
    st.divider()
    st.button("More tools")
    st.button("Settings")
    st.divider()
    st.button("Logout")

chips = "".join(f'<a class="pa-pchip" href="#" style="--c:var({color});text-decoration:none"><span class="pa-pchip-n">{count}</span><span class="pa-pchip-l">{label}</span></a>'
                for count, label, color in [(12, "All", "--slate-700"), (4, "Pending UW", "--accent"),
                                           (2, "Requested", "--orange"), (3, "Cleared", "--green"),
                                           (2, "Overdue", "--red"), (1, "Closed", "--green-dark")])
st.markdown('<div class="pa-pipe-dash"><span class="pa-pipe-dash-title">My Pipeline</span><div class="pa-pipe-dash-row">' + chips + '</div></div>', unsafe_allow_html=True)

# Compile the real empty-scanner layout; exclude document processing and use no account data.
scanner = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "show_dashboard")
scanner.body = scanner.body[:next(i for i, node in enumerate(scanner.body)
                                  if isinstance(node, ast.If) and isinstance(node.test, ast.Name)
                                  and node.test.id == "new_files")]
compliance = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                  and node.name == "render_compliance_statement")
footer = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
              and node.name == "render_site_footer")
sys.modules["cloud_client"] = types.SimpleNamespace(get_config=lambda: {"api_key": "preview-only"})
st.session_state.sandbox_mode = True
_recent_scan_history = lambda: []
exec(compile(ast.Module(body=[scanner, compliance, footer], type_ignores=[]), str(ROOT / "app.py"), "exec"))
show_dashboard()
render_site_footer()
