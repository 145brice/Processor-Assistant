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
    current = list(st.session_state.get(key, default))
    st.session_state[key] = current
    with st.popover(
        party_summary(current), use_container_width=True,
    ):
        with st.container(key=f'{key}_choices'):
            st.caption(label)
            for index, party in enumerate(options):
                choice_key = f'{key}_choice_{index}'
                st.session_state[choice_key] = party in current
                st.checkbox(
                    party, key=choice_key, on_change=_update_parties,
                    args=(key, options),
                )
    return st.session_state[key]


def _update_parties(key, options):
    st.session_state[key] = [
        party for index, party in enumerate(options)
        if st.session_state.get(f'{key}_choice_{index}', False)
    ]
