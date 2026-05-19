"""
NetAegis — Streamlit entrypoint.

Run from project root:
    streamlit run app.py

Routed views live in ``views/`` (imported here only). A ``pages/`` directory is not
used so Streamlit runs this file directly — avoiding multipage + custom sidebar
routing conflicts.
"""
from __future__ import annotations

import time

import streamlit as st

from components.sidebar import render_sidebar
from components.visuals import inject_base_styles
from services import data as data_svc
from theme import DASHBOARD_REFRESH_SEC, DASHBOARD_REFRESH_SEC_UNDER_ATTACK
from utils.state import (
    apply_attack_hold_to_metrics,
    get_simulated_threat_count,
    init_attack_session_state,
    merge_session_into_active_threats_metric,
    merge_session_into_flows_metric,
    sync_attack_hold,
    tick_demo_background_flows,
)
from views.analytics import render_analytics_view
from views.overview import render_overview_view
from views.settings import render_settings_view
from views.threat_intel import render_threat_intel_view
from views.xai_forensics import render_xai_forensics_view


def main() -> None:
    st.set_page_config(
        page_title="NetAegis",
        page_icon="🛡️",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    init_attack_session_state()

    mysql_ok = data_svc.fetch_mysql_connected()
    metrics, db_ok = data_svc.fetch_dashboard_metrics()
    tick_demo_background_flows(enabled=not db_ok)
    metrics = merge_session_into_flows_metric(metrics)
    metrics = merge_session_into_active_threats_metric(metrics)

    raw_threats = metrics["active_threats"][0]
    raw_n = int(raw_threats) if isinstance(raw_threats, (int, float)) else 0

    show_amber, held_display = sync_attack_hold(raw_n)
    metrics = apply_attack_hold_to_metrics(metrics, held_display, show_amber)

    db_attack = data_svc.fetch_attack_active() if mysql_ok else False
    sim_n = get_simulated_threat_count()
    pulse_under_attack = bool(db_attack or show_amber or sim_n > 0)

    # One global <style> block (proven path — same as sidebar theme overrides).
    inject_base_styles(attack_active=pulse_under_attack)

    sniffer_live = data_svc.fetch_sniffer_likely_live() if mysql_ok else False
    selected_page = render_sidebar(live=sniffer_live, mysql_ok=mysql_ok)

    # Wrap every page in st.empty() so navigating between pages clears the
    # previous page's widget tree — prevents settings widgets bleeding into overview.
    _page = st.empty()
    with _page.container():
        if selected_page == "Overview":
            render_overview_view(
                metrics=metrics,
                db_ok=db_ok,
                show_amber=show_amber or sim_n > 0,
            )
        elif selected_page == "Threat Intel":
            render_threat_intel_view()
        elif selected_page == "Analytics":
            render_analytics_view()
        elif selected_page == "XAI Forensics":
            render_xai_forensics_view()
        elif selected_page == "Settings":
            render_settings_view()

    if selected_page == "Overview":
        refresh_sec = (
            DASHBOARD_REFRESH_SEC_UNDER_ATTACK
            if (pulse_under_attack or raw_n > 0)
            else DASHBOARD_REFRESH_SEC
        )
        time.sleep(refresh_sec)
        st.rerun()


if __name__ == "__main__":
    main()
