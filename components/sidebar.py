"""NetAegis sidebar — pill nav buttons + Material icons, palette-aligned."""
from __future__ import annotations

import streamlit as st

from theme import C_ACCENT, C_BORDER, C_CARD, C_SUB, C_SUCCESS, C_TEXT

_NAV_PAGES: list[tuple[str, str, str]] = [
    ("dashboard", "Overview", "Overview"),
    ("travel_explore", "Threat Intel", "Threat Intel"),
    ("insert_chart", "Analytics", "Analytics"),
    ("model_training", "XAI Forensics", "XAI Forensics"),
    ("settings", "Settings", "Settings"),
]


def _nav_key(internal: str) -> str:
    return "navbtn_" + internal.lower().replace(" ", "_")


def inject_sidebar_nav_css() -> None:
    st.markdown(
        f"""
        <style>
        div[data-testid="stSidebar"] button[kind="secondary"] {{
            width: 100% !important;
            justify-content: flex-start !important;
            background: transparent !important;
            border: none !important;
            color: {C_SUB} !important;
            border-radius: 9999px !important;
            font-weight: 500 !important;
            font-size: 0.9rem !important;
            padding: 0.5rem 0.85rem !important;
            margin-bottom: 2px !important;
            min-height: auto !important;
            transition: background 0.15s ease, color 0.15s ease !important;
        }}
        div[data-testid="stSidebar"] button[kind="secondary"]:hover {{
            background: rgba(244, 244, 245, 0.06) !important;
            color: {C_TEXT} !important;
        }}
        div[data-testid="stSidebar"] button[kind="primary"] {{
            width: 100% !important;
            justify-content: flex-start !important;
            border-radius: 9999px !important;
            font-weight: 600 !important;
            font-size: 0.9rem !important;
            padding: 0.5rem 0.85rem !important;
            margin-bottom: 2px !important;
            min-height: auto !important;
            background: linear-gradient(165deg, {C_ACCENT}, #C73E2B) !important;
            color: {C_TEXT} !important;
            border: 1px solid rgba(255, 255, 255, 0.12) !important;
            box-shadow:
                0 4px 14px rgba(230, 72, 51, 0.35),
                0 1px 3px rgba(0, 0, 0, 0.45) !important;
        }}
        div[data-testid="stSidebar"] button[kind="primary"]:hover {{
            filter: brightness(1.06) !important;
        }}
        /* Tighter vertical rhythm in sidebar */
        div[data-testid="stSidebar"] [data-testid="stVerticalBlock"] > div {{
            gap: 0.25rem !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar(live: bool, mysql_ok: bool) -> str:
    if "netaegis_nav" not in st.session_state:
        st.session_state["netaegis_nav"] = "Overview"

    inject_sidebar_nav_css()

    with st.sidebar:
        st.markdown(
            f"<p style='font-size:0.65rem; color:{C_SUB}; text-transform:uppercase;"
            f"letter-spacing:0.14em; margin:4px 0 8px 2px; font-weight:600;'>Navigate</p>",
            unsafe_allow_html=True,
        )

        for mat_name, label_txt, internal in _NAV_PAGES:
            active = st.session_state["netaegis_nav"] == internal
            icon = f":material/{mat_name}:"
            if st.button(
                label_txt,
                key=_nav_key(internal),
                width="stretch",
                type="primary" if active else "secondary",
                icon=icon,
            ):
                st.session_state["netaegis_nav"] = internal
                st.rerun()

        st.markdown(
            f"<div style='height:1px;background:{C_BORDER};margin:10px 0;'></div>",
            unsafe_allow_html=True,
        )

        dot = C_SUCCESS if live else C_ACCENT
        live_lbl = "Live · Monitoring" if live else "Offline · Check sniffer"
        st.markdown(
            f"""
            <div style="display:flex; align-items:center; gap:10px;
                        background:{C_CARD}; border:1px solid {C_BORDER};
                        border-radius:9999px; padding:8px 12px; margin-bottom:8px;">
                <span style="width:8px; height:8px; border-radius:50%;
                             background:{dot}; box-shadow:0 0 8px {dot};
                             flex-shrink:0;"></span>
                <span style="font-size:0.78rem; color:{C_TEXT}; font-weight:500;">{live_lbl}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        mysql_color = C_SUCCESS if mysql_ok else C_ACCENT
        mysql_text = "Connected" if mysql_ok else "Offline"
        sniffer_color = C_SUCCESS if live else C_ACCENT
        sniffer_text = "Running" if live else "Stopped"

        st.markdown(
            f"""
            <div style="font-size:0.72rem; color:{C_SUB};
                        border:1px solid {C_BORDER}; border-radius:12px;
                        background:{C_CARD}; padding:10px 12px;">
                <div style="font-weight:700; color:{C_TEXT}; letter-spacing:0.08em;
                            text-transform:uppercase; font-size:0.6rem; margin-bottom:8px;">
                    System status
                </div>
                <div style="display:flex; justify-content:space-between; align-items:center;
                            margin-bottom:6px;">
                    <span>ML engine</span>
                    <span style="color:{C_SUCCESS}; font-weight:600;">Active</span>
                </div>
                <div style="display:flex; justify-content:space-between; align-items:center;
                            margin-bottom:6px;">
                    <span>MySQL</span>
                    <span style="color:{mysql_color}; font-weight:600;">{mysql_text}</span>
                </div>
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span>Sniffer</span>
                    <span style="color:{sniffer_color}; font-weight:600;">{sniffer_text}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            f"<div style='height:1px;background:{C_BORDER};margin:10px 0;'></div>",
            unsafe_allow_html=True,
        )

    return str(st.session_state.get("netaegis_nav", "Overview"))
