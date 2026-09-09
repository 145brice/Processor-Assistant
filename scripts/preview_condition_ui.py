"""Synthetic browser fixture: real app styles, no loan data or external services.

Run with: streamlit run scripts/preview_condition_ui.py
"""
import ast
from pathlib import Path
import sys

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ui_refinement import apply_workspace_style, party_picker

st.set_page_config(layout='wide')
tree = ast.parse((ROOT / 'app.py').read_text(encoding='utf-8'))
for node in tree.body:
    if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
        args = node.value.args
        if args and isinstance(args[0], ast.Constant) and isinstance(args[0].value, str):
            if args[0].value.lstrip().startswith('<style>'):
                st.markdown(args[0].value, unsafe_allow_html=True)
                break
apply_workspace_style()
with st.sidebar:
    st.subheader('Processor Assistant')
    st.button('Scanner', type='primary')
    st.button('Pipeline')
    st.button('Overview')
st.subheader('Borrower conditions')
for index in range(12):
    check, description, party, status, actions = st.columns([0.4, 6.2, 1.9, 1.7, 1.3])
    with check:
        st.checkbox('Select', key=f'scan_preview_{index}_chk', label_visibility='collapsed')
    with description:
        st.markdown(f'<div class="pa-condition-description"><b>#{index + 1} Homeowners insurance</b> — Provide the current policy.</div>', unsafe_allow_html=True)
    with party:
        party_picker('Responsible parties', ['Borrower', 'Co-Borrower', 'Title', 'Insurance', 'Appraiser', 'Processor', 'Underwriter'],
                     default=['Borrower'], key=f'scan_preview_{index}_party')
    with status:
        st.selectbox('Status', ['Needed', 'Requested', 'Cleared'], key=f'scan_preview_{index}_stat', label_visibility='collapsed')
    with actions:
        with st.popover('Actions', use_container_width=True):
            st.button('Plain', key=f'plain_{index}')
            st.button('Draft', key=f'draft_{index}')
