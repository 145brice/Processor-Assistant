"""Public copy and navigation switches configured by the app operator."""
import os


def advanced_tools_enabled():
    # On for everyone; the sidebar keeps them inside a collapsed "More Tools" group.
    return os.getenv("PA_ENABLE_ADVANCED_TOOLS", "1").strip().lower() in {"1", "true", "yes", "on"}


def beta_offer():
    end = os.getenv("PA_BETA_END_DATE", "").strip()
    spots = os.getenv("PA_FOUNDER_SPOTS", "").strip()
    price = os.getenv("PA_FOUNDER_MONTHLY_PRICE", "").strip()
    if end and spots and price:
        return (f"Free beta access until {end} in exchange for feedback. The first {spots} beta users "
                f"lock in a founder price of {price}/month after launch.")
    return ("Free beta access until we reach 20 users, in exchange for feedback. "
            "Pricing after beta will be announced before launch.")


def render_gemini_setup_video():
    import streamlit as st
    video = os.getenv("PA_GEMINI_SETUP_VIDEO", "").strip()
    if video:
        st.video(video)
        st.caption("Quick setup: enable billing on your Google AI account, create a key, and paste it here.")


CORE_PAGES = {"dashboard", "pipeline", "loan_detail", "history", "ai_settings", "ollama", "billing", "pricing"}


def visible_page(page):
    return page if advanced_tools_enabled() or page in CORE_PAGES else "dashboard"
