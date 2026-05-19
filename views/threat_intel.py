"""Threat Intelligence view — real data from alerts + placeholder feed status."""
from __future__ import annotations

import streamlit as st

from components.visuals import _section_label, render_top_ports_chart
from services import data as data_svc
from theme import C_SUB, C_TEXT
from views._shared import page_title


def _dataframe(df, **kwargs: object) -> None:
    try:
        st.dataframe(df, width="stretch", **kwargs)  # type: ignore[arg-type]
    except TypeError:
        st.dataframe(df, use_container_width=True, **kwargs)  # type: ignore[arg-type]


def _style_severity(val: object) -> str:
    s = str(val).strip()
    if s == "Critical":
        return "color: #E64833; font-weight: 600; background-color: rgba(230, 72, 51, 0.14)"
    if s == "High":
        return "color: #EAB308; font-weight: 600;"
    return ""


def render_threat_intel_view() -> None:
    page_title(
        "Threat Intelligence",
        "Port targeting, top malicious IPs, feed status, and recent attack history",
    )

    with st.container(border=True):
        _section_label("Top Targeted Ports", "last 24 h · malicious flows by destination port")
        render_top_ports_chart(chart_key="threat_intel_top_ports")

    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

    # ── Row 1: feed status (placeholder) + known bad IPs (real DB) ─────────
    c1, c2 = st.columns(2)

    with c1:
        with st.container(border=True):
            st.markdown(f"#### <span style='color:{C_TEXT};'>Global threat feeds</span>", unsafe_allow_html=True)
            st.caption("External OSINT feed status — connect API keys to enable live sync.")
            feeds_df = __import__("pandas").DataFrame({
                "Feed": ["Abuse.ch", "Emerging Threats", "Custom STIX"],
                "Status": ["Placeholder", "Placeholder", "Placeholder"],
                "Last update": ["—", "—", "—"],
            })
            _dataframe(feeds_df, hide_index=True)

    with c2:
        with st.container(border=True):
            st.markdown(f"#### <span style='color:{C_TEXT};'>Top malicious source IPs</span>", unsafe_allow_html=True)
            st.caption("Live from `alerts` — highest-hit source IPs flagged Malicious in the last 7 days.")
            df_ips, ips_ok = data_svc.fetch_top_malicious_ips(limit=20)
            if not ips_ok:
                st.info("Demo mode — sample malicious IPs below.")
            if df_ips.empty and ips_ok:
                st.info("No malicious source IPs recorded in the last 7 days.")
            else:
                _dataframe(
                    df_ips,
                    hide_index=True,
                    column_config={
                        "IP": st.column_config.TextColumn("Source IP"),
                        "Hits (7d)": st.column_config.NumberColumn("Hits (7d)", format="%d"),
                        "Top Severity": st.column_config.TextColumn("Top Severity"),
                        "Max Conf": st.column_config.NumberColumn("Max Confidence", format="%.4f"),
                    },
                )

    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

    # ── Row 2: recent malicious alerts (real DB) ───────────────────────────
    with st.container(border=True):
        st.markdown(f"#### <span style='color:{C_TEXT};'>Recent malicious alerts</span>", unsafe_allow_html=True)
        st.caption("Live from `alerts` where `prediction = 'Malicious'`, newest first.")
        df_hist, hist_ok = data_svc.fetch_recent_malicious_alerts(limit=50)
        if not hist_ok:
            st.info("Demo mode — sample malicious alert history below.")
        if df_hist.empty and hist_ok:
            st.info("No malicious alerts found in the database.")
        else:
            styled = (
                df_hist.style
                .map(_style_severity, subset=["Severity"])
                .hide(axis="index")
            )
            try:
                st.dataframe(
                    styled,
                    width="stretch",
                    height=420,
                    column_config={
                        "ID": st.column_config.NumberColumn("ID", format="%d"),
                        "Time (UTC)": st.column_config.TextColumn("Time (UTC)"),
                        "Severity": st.column_config.TextColumn("Severity"),
                        "Src IP": st.column_config.TextColumn("Src IP"),
                        "Dst IP": st.column_config.TextColumn("Dst IP"),
                        "Dst Port": st.column_config.NumberColumn("Dst Port", format="%d"),
                        "Protocol": st.column_config.TextColumn("Protocol"),
                        "Confidence": st.column_config.NumberColumn("Confidence", format="%.4f"),
                        "Status": st.column_config.TextColumn("Status"),
                    },
                )
            except TypeError:
                st.dataframe(
                    styled,
                    use_container_width=True,
                    height=420,
                    column_config={
                        "ID": st.column_config.NumberColumn("ID", format="%d"),
                        "Time (UTC)": st.column_config.TextColumn("Time (UTC)"),
                        "Severity": st.column_config.TextColumn("Severity"),
                        "Src IP": st.column_config.TextColumn("Src IP"),
                        "Dst IP": st.column_config.TextColumn("Dst IP"),
                        "Dst Port": st.column_config.NumberColumn("Dst Port", format="%d"),
                        "Protocol": st.column_config.TextColumn("Protocol"),
                        "Confidence": st.column_config.NumberColumn("Confidence", format="%.4f"),
                        "Status": st.column_config.TextColumn("Status"),
                    },
                )
