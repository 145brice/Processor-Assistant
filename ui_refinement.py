"""Shared presentation for the condition workspace."""
from pathlib import Path

import streamlit as st


def apply_workspace_style():
    st.markdown(
        '<style>' + Path(__file__).with_name('workspace.css').read_text(encoding='utf-8') + '</style>',
        unsafe_allow_html=True,
    )


def party_summary(parties):
    if not parties:
        return 'Assign party'
    if len(parties) == 1:
        return parties[0]
    return f'{parties[0]} +{len(parties) - 1}'


def party_picker(label, options, *, default, key, label_visibility='collapsed', placeholder='Parties'):
    """Keep assignments editable without allowing tags to expand the table row."""
    current = st.session_state.get(key, default)
    with st.popover(
        party_summary(current), use_container_width=True,
        help='Responsible parties: ' + (', '.join(current) or 'Unassigned'),
    ):
        st.markdown('**Responsible parties**')
        st.caption('Assign everyone involved in this condition.')
        selected = st.multiselect(
            label, options, default=default, key=key,
            label_visibility=label_visibility, placeholder=placeholder,
        )
    return selected
