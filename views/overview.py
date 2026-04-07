"""Overview / Command Center — tight vertical rhythm, prominent branding."""
from __future__ import annotations

from typing import Any

import streamlit as st

from components.visuals import (
    render_activity_feed,
    render_attack_banner,
    render_malicious_activity_feed,
    render_metrics_row,
    render_threat_map,
    render_xai_panel,
    _section_label,
)
from theme import C_ACCENT, C_BORDER, C_SUB, C_TEXT


def render_overview_view(
    metrics: dict[str, tuple[Any, int | float | str | None]],
    db_ok: bool,
    show_amber: bool,
) -> None:
    st.markdown(
        """
        <style>
        div[data-testid="stMain"] [data-testid="stVerticalBlock"] > div {
            gap: 0.5rem !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # ── Title ──────────────────────────────────────────────────────────────
    with st.container():
        st.markdown(
            f"""
            <div style="padding:0 0 6px 0;">
                <h1 style="margin:0; font-size:clamp(2.15rem, 4.2vw, 2.85rem); font-weight:800;
                            color:{C_TEXT}; letter-spacing:-0.03em; line-height:1.08;">
                    Net<span style="color:{C_ACCENT};">Aegis</span>
                </h1>
                <p style="margin:4px 0 0 0; color:{C_SUB}; font-size:0.84rem;">
                    Command Center · Real-time network intelligence · EdgeBERT v2.1
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if show_amber:
            render_attack_banner(show_amber)

    # ── KPI metrics ────────────────────────────────────────────────────────
    with st.container():
        if not db_ok:
            st.warning("Cannot reach MySQL — check `.env` and `init_db.py`.")
        render_metrics_row(metrics)

    # ── Global threat map — full width (ports chart lives on Threat Intel) ─
    with st.container(border=True):
        hdr_l, hdr_r = st.columns([10, 2])
        with hdr_l:
            _section_label("Global Threat Origins", "last 24 h · malicious src IPs")
        with hdr_r:
            st.checkbox(
                "Full screen",
                key="overview_map_expand",
                help="Larger map below — uses a separate chart so Streamlit IDs stay unique.",
            )
        render_threat_map(
            chart_key="overview_threat_map_main",
            height=620,
        )

    if st.session_state.get("overview_map_expand"):
        with st.expander("Global Threat Origins — expanded view", expanded=True):
            render_threat_map(
                chart_key="overview_threat_map_expanded",
                height=820,
                projection_scale=1.58,
            )

    st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)

    # ── Malicious activity table ───────────────────────────────────────────
    with st.container(border=True):
        st.markdown(
            f"""
            <div style="display:flex; justify-content:space-between; align-items:flex-start;
                        gap:12px; flex-wrap:wrap; margin-bottom:4px;">
                <div>
                    <h3 style="margin:0; font-size:1.12rem; font-weight:700; color:{C_TEXT};">
                        Malicious flows — last 100
                    </h3>
                    <p style="margin:6px 0 0 0; color:{C_SUB}; font-size:0.8rem; line-height:1.45;">
                        Direct SQL: <code style="color:{C_SUB};">prediction = 'Malicious'</code>,
                        newest 100 rows — IPs, ports, protocol, packet rate.
                    </p>
                </div>
                <span style="font-size:0.68rem; color:{C_SUB}; background:{C_BORDER};
                             padding:4px 10px; border-radius:999px; white-space:nowrap;
                             align-self:flex-start;">Threats</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        render_malicious_activity_feed(limit=100, height_px=460)

    st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)

    # ── All activity table ─────────────────────────────────────────────────
    with st.container(border=True):
        st.markdown(
            f"""
            <div style="display:flex; justify-content:space-between; align-items:flex-start;
                        gap:12px; flex-wrap:wrap; margin-bottom:4px;">
                <div>
                    <h3 style="margin:0; font-size:1.12rem; font-weight:700; color:{C_TEXT};">
                        Analyst queue — last 100 alerts
                    </h3>
                    <p style="margin:6px 0 0 0; color:{C_SUB}; font-size:0.8rem; line-height:1.45;">
                        Newest 100 rows from <code style="color:{C_SUB};">alerts</code>
                        (benign and malicious), sorted by event time.
                    </p>
                </div>
                <span style="font-size:0.68rem; color:{C_SUB}; background:{C_BORDER};
                             padding:4px 10px; border-radius:999px; white-space:nowrap;
                             align-self:flex-start;">Live</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        render_activity_feed(limit=100, height_px=460)

    st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)

    # ── XAI panel ──────────────────────────────────────────────────────────
    with st.container(border=True):
        render_xai_panel()
