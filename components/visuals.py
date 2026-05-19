"""Charts, banners, and layout blocks for NetAegis."""
from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from services import data as data_svc
from theme import (
    ATTACK_ALERT_WINDOW_SEC,
    C_ACCENT,
    C_BG,
    C_BORDER,
    C_CARD,
    C_SUB,
    C_SUCCESS,
    C_TEXT,
    C_WARN,
    _PLOTLY_WIDTH,
)

_PLOTLY_CONFIG = {
    "displayModeBar": False,
    "scrollZoom": False,
    "doubleClick": False,
    "showAxisDragHandles": False,
    "showAxisRangeEntryBoxes": False,
    "modeBarButtonsToRemove": [
        "zoom2d", "pan2d", "select2d", "lasso2d", "zoomIn2d", "zoomOut2d",
        "autoScale2d", "resetScale2d",
    ],
}


def inject_base_styles(*, attack_active: bool = False) -> None:
    """
    Global theme CSS. Attack glow lives **here** (same document-global block as the
    rest of the theme) so it actually applies. Separate ``st.markdown`` / iframe
    injections often fail to reach ``.stApp`` / ``[data-testid="stMain"]``.
    """
    attack_css = ""
    if attack_active:
        attack_css = f"""
        @keyframes aegis-attack-pulse {{
            0%, 100% {{
                box-shadow:
                    0 0 0 2px rgba(230, 72, 51, 0.6),
                    0 0 36px 10px rgba(230, 72, 51, 0.28);
            }}
            50% {{
                box-shadow:
                    0 0 0 4px rgba(255, 55, 40, 0.95),
                    0 0 80px 28px rgba(230, 72, 51, 0.58);
            }}
        }}
        /* Soft diffuse red depth at edges (low opacity, no hard frame) */
        @keyframes aegis-attack-main {{
            0%, 100% {{
                box-shadow:
                    inset 0 0 72px 32px rgba(210, 58, 48, 0.045),
                    inset 0 0 140px 72px rgba(185, 42, 36, 0.028),
                    inset 0 0 220px 108px rgba(165, 36, 30, 0.018),
                    0 0 52px 14px rgba(220, 62, 50, 0.055);
            }}
            50% {{
                box-shadow:
                    inset 0 0 92px 40px rgba(235, 62, 50, 0.085),
                    inset 0 0 175px 88px rgba(200, 48, 40, 0.052),
                    inset 0 0 260px 125px rgba(175, 42, 34, 0.034),
                    0 0 78px 22px rgba(235, 68, 52, 0.095);
            }}
        }}
        /* Outer shell — full window frame */
        .stApp,
        div[data-testid="stApp"] {{
            outline: 3px solid rgba(230, 72, 51, 0.75) !important;
            outline-offset: -3px !important;
            animation: aegis-attack-pulse 1.1s ease-in-out infinite !important;
        }}
        /* Inner layout: sidebar + main together */
        [data-testid="stAppViewContainer"] {{
            outline: 2px solid rgba(230, 72, 51, 0.45) !important;
            outline-offset: -2px !important;
        }}
        /* Main column — soft pulsing vignette (fixes “only sidebar glows”) */
        [data-testid="stMain"],
        section.main {{
            position: relative !important;
            animation: aegis-attack-main 1.1s ease-in-out infinite !important;
        }}
        [data-testid="stMain"]::before,
        section.main::before {{
            content: "";
            pointer-events: none;
            position: absolute;
            inset: 0;
            z-index: 1;
            background: radial-gradient(
                ellipse 130% 120% at 50% 48%,
                transparent 38%,
                rgba(200, 52, 42, 0.045) 68%,
                rgba(175, 38, 32, 0.09) 100%
            );
            animation: aegis-attack-main-vignette 1.1s ease-in-out infinite;
        }}
        @keyframes aegis-attack-main-vignette {{
            0%, 100% {{ opacity: 0.45; }}
            50% {{ opacity: 0.82; }}
        }}
        [data-testid="stSidebar"] {{
            box-shadow:
                inset -3px 0 0 rgba(230, 72, 51, 0.55),
                -4px 0 32px rgba(230, 72, 51, 0.2) !important;
        }}
        [data-testid="stHeader"] {{
            box-shadow:
                0 2px 0 rgba(230, 72, 51, 0.5) !important;
        }}
        """

    st.markdown(
        f"""
        <style>
        html, body, [data-testid="stAppViewContainer"] {{
            background-color: {C_BG} !important;
            color: {C_TEXT};
            font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
        }}
        [data-testid="stHeader"] {{
            background-color: rgba(14, 14, 16, 0.97) !important;
            border-bottom: 1px solid {C_BORDER} !important;
        }}
        [data-testid="stSidebar"] {{
            background-color: {C_BG} !important;
            border-right: 1px solid {C_BORDER} !important;
        }}
        [data-testid="stVerticalBlockBorderWrapper"] {{
            background: {C_CARD} !important;
            border: 1px solid {C_BORDER} !important;
            border-radius: 12px !important;
        }}
        [data-testid="stMetricValue"] {{
            color: {C_TEXT} !important;
            font-size: 2rem !important;
            font-weight: 700 !important;
        }}
        [data-testid="stMetricLabel"] {{
            color: {C_SUB} !important;
            font-size: 0.78rem !important;
            text-transform: uppercase;
            letter-spacing: 0.07em;
        }}
        footer {{ visibility: hidden; }}
        #MainMenu {{ visibility: hidden; }}
        /* Full-width analyst queues (Glide grid chrome) */
        [data-testid="stDataFrame"] {{
            border: 1px solid {C_BORDER} !important;
            border-radius: 10px !important;
            overflow: hidden !important;
            background: #0a0a0c !important;
        }}
        {attack_css}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_attack_banner(show: bool) -> None:
    """Full-width red alert banner — only rendered when an attack is active."""
    if not show:
        return
    st.html(
        f"""
        <div style="
            width:100%;box-sizing:border-box;margin:0 0 14px 0;padding:16px 20px;
            border-radius:10px;background:rgba(61,20,16,0.55);
            border:1px solid rgba(230,72,51,0.45);border-left:4px solid {C_ACCENT};
            color:{C_TEXT};font-family:'Inter','Segoe UI',system-ui,sans-serif;
            display:flex;align-items:center;gap:14px;
        ">
            <span style="font-size:1.5rem;line-height:1;">&#9888;</span>
            <div>
                <div style="font-weight:700;font-size:1rem;letter-spacing:0.04em;color:{C_ACCENT};">
                    ACTIVE THREAT DETECTED
                </div>
                <div style="margin-top:4px;font-size:0.84rem;color:{C_SUB};line-height:1.45;">
                    Malicious traffic identified on your network. Review the alert queues below.
                </div>
            </div>
        </div>
        """
    )


def render_metrics_row(data: dict[str, tuple[Any, int | float | str | None]]) -> None:
    c1, c2, c3, c4 = st.columns(4, gap="medium")
    with c1:
        with st.container(border=True):
            vo, do = data["flows_analyzed"]
            kw: dict = {
                "help": (
                    "Lifetime flows in `alerts` plus session demo/simulated traffic "
                    "(increments on refresh and Simulate Attack)."
                ),
            }
            if do is not None:
                kw["delta"] = do
                kw["delta_color"] = "normal" if isinstance(do, (int, float)) and do > 0 else "inverse"
            val = f"{int(vo):,}" if isinstance(vo, (int, float)) else vo
            st.metric("Total Flows Analyzed", val, **kw)
    with c2:
        with st.container(border=True):
            vi, di = data["active_threats"]
            sess_n = max(0, int(st.session_state.get("active_threats", 0) or 0))
            base = int(vi) if isinstance(vi, (int, float)) else 0
            display_threats = max(base, sess_n)
            kw = {
                "help": (
                    f"Count of Malicious rows with event_time in the last {ATTACK_ALERT_WINDOW_SEC}s "
                    f"({ATTACK_ALERT_WINDOW_SEC // 60} min), using UTC. Includes sidebar simulate + amber hold."
                ),
            }
            if di is not None:
                kw["delta"] = di
                kw["delta_color"] = "inverse"
            st.metric("Active Threats", f"{display_threats:,}", **kw)
    with c3:
        with st.container(border=True):
            vc, dc = data["compliance_score"]
            kw = {"help": "Benign share (24h)."}
            if dc is not None:
                kw["delta"] = f"{dc}pp"
            st.metric("Compliance Score", vc, **kw)
    with c4:
        with st.container(border=True):
            vt, dt = data["time_to_remediate"]
            kw = {"help": "Mean remediation time for Resolved (7d)."}
            if dt is not None:
                kw["delta"] = f"{dt}m"
                kw["delta_color"] = "inverse"
            st.metric("Avg. Time to Remediate", vt, **kw)


def render_threat_map(
    *,
    chart_key: str = "threat_map",
    height: int = 580,
    projection_scale: float | None = None,
) -> None:
    origins, map_db_ok = data_svc.fetch_threat_origins()
    if not map_db_ok:
        st.caption("MySQL unreachable — demo map markers.")
    if not origins:
        st.caption(
            "No malicious source IPs in the last 24h — map is empty. "
            "Run the sniffer or `attack_sim.py`."
        )
        return

    scale = projection_scale if projection_scale is not None else 1.42

    lats = [o["lat"] for o in origins]
    lons = [o["lon"] for o in origins]
    labels = [o["label"] for o in origins]
    sizes = [o["size"] for o in origins]

    fig = go.Figure()
    fig.add_trace(
        go.Scattergeo(
            lat=lats,
            lon=lons,
            mode="markers",
            marker=dict(
                size=[s * 3.8 for s in sizes],
                color=C_ACCENT,
                opacity=0.07,
            ),
            hoverinfo="skip",
            showlegend=False,
        )
    )
    fig.add_trace(
        go.Scattergeo(
            lat=lats,
            lon=lons,
            mode="markers",
            marker=dict(
                size=[s * 2.0 for s in sizes],
                color=C_ACCENT,
                opacity=0.2,
            ),
            hoverinfo="skip",
            showlegend=False,
        )
    )
    fig.add_trace(
        go.Scattergeo(
            lat=lats,
            lon=lons,
            mode="markers+text",
            marker=dict(
                size=[max(7, s * 0.72) for s in sizes],
                color=C_ACCENT,
                opacity=1,
                line=dict(color="rgba(255,255,255,0.55)", width=1.1),
            ),
            text=labels,
            textposition="top center",
            textfont=dict(color=C_SUB, size=10),
            hovertemplate="<b>%{text}</b><br>weight: %{customdata}<extra></extra>",
            customdata=sizes,
            showlegend=False,
        )
    )

    fig.update_layout(
        paper_bgcolor=C_CARD,
        margin=dict(l=0, r=0, t=0, b=0),
        height=height,
        uirevision="netaegis-map",
    )
    fig.update_geos(
        bgcolor=C_BG,
        showframe=False,
        showcoastlines=True,
        coastlinecolor="#2D2D30",
        showland=True,
        landcolor="#151517",
        showocean=True,
        oceancolor=C_BG,
        showlakes=False,
        showcountries=True,
        countrycolor="#2A2A2E",
        projection_type="natural earth",
        center=dict(lat=22, lon=12),
        projection_scale=scale,
        lataxis=dict(range=[-42, 74], showgrid=False),
        lonaxis=dict(range=[-128, 168], showgrid=False),
    )

    st.plotly_chart(fig, width=_PLOTLY_WIDTH, config=_PLOTLY_CONFIG, key=chart_key)


def render_top_ports_chart(*, chart_key: str = "top_ports_chart") -> None:
    df, ports_db_ok = data_svc.fetch_top_ports()
    if not ports_db_ok:
        st.caption("MySQL unreachable — demo port counts.")
    if df.empty:
        st.caption("No malicious port hits in the last 24 hours.")
        return

    n = len(df)
    # Build a proper dark-red gradient: top bar is full accent, fades to muted for lower bars
    bar_colors = [
        f"rgba(230, 72, 51, {0.9 - 0.55 * i / max(n - 1, 1):.2f})"
        for i in range(n)
    ]
    fig = go.Figure(
        go.Bar(
            x=df["Hits"],
            y=df["Port"],
            orientation="h",
            marker=dict(
                color=bar_colors,
                line=dict(width=0),
            ),
            text=[f"{int(h)}" for h in df["Hits"]],
            textposition="outside",
            textfont=dict(color=C_SUB, size=12),
            hovertemplate="%{y}<br><b>%{x}</b> hits<extra></extra>",
        )
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=C_SUB),
        margin=dict(l=4, r=36, t=4, b=4),
        height=max(220, 44 * n),
        bargap=0.35,
        xaxis=dict(
            showgrid=True,
            gridcolor=C_BORDER,
            zeroline=False,
            showticklabels=True,
            tickfont=dict(size=10, color=C_SUB),
        ),
        yaxis=dict(
            showgrid=False,
            autorange="reversed",
            tickfont=dict(size=12, color=C_TEXT),
        ),
    )
    st.plotly_chart(fig, width=_PLOTLY_WIDTH, config=_PLOTLY_CONFIG, key=chart_key)


def _show_alert_queue_dataframe(df: pd.DataFrame, *, height_px: int) -> None:
    cfg = _alert_queue_column_config()
    try:
        st.dataframe(
            df,
            hide_index=True,
            width="stretch",
            height=height_px,
            column_config=cfg,
        )
    except TypeError:
        st.dataframe(
            df,
            hide_index=True,
            use_container_width=True,
            height=height_px,
            column_config=cfg,
        )


def _alert_queue_column_config() -> dict[str, Any]:
    return {
        "ID": st.column_config.NumberColumn("ID", format="%d"),
        "Event Time": st.column_config.TextColumn("Event Time"),
        "Prediction": st.column_config.TextColumn("Prediction"),
        "Confidence": st.column_config.NumberColumn("Confidence", format="%.4f"),
        "Severity": st.column_config.TextColumn("Severity"),
        "Src IP": st.column_config.TextColumn("Src IP"),
        "Dst IP": st.column_config.TextColumn("Dst IP"),
        "Src Port": st.column_config.NumberColumn("Src Port", format="%d"),
        "Dst Port": st.column_config.NumberColumn("Dst Port", format="%d"),
        "Protocol": st.column_config.TextColumn("Protocol"),
        "Pkt Rate": st.column_config.NumberColumn("Pkt Rate", format="%.14f"),
        "Status": st.column_config.TextColumn("Status"),
    }


def render_malicious_activity_feed(*, limit: int = 100, height_px: int = 440) -> None:
    df, db_ok = data_svc.fetch_malicious_alerts_queue(limit)
    if not db_ok:
        st.caption("MySQL unreachable — demo malicious queue rows.")
    if df.empty and db_ok:
        st.caption("No malicious alerts in the database yet.")
        return
    _show_alert_queue_dataframe(df, height_px=height_px)


def render_activity_feed(*, limit: int = 100, height_px: int = 440) -> None:
    df, db_ok = data_svc.fetch_all_alerts_queue(limit)
    if not db_ok:
        st.caption("MySQL unreachable — demo analyst queue rows.")
    if df.empty and db_ok:
        st.caption("No alerts in the database yet.")
        return
    _show_alert_queue_dataframe(df, height_px=height_px)


def _section_label(title: str, subtitle: str = "") -> None:
    sub = (
        f"<span style='color:{C_SUB}; font-size:0.78rem; margin-left:10px;'>{subtitle}</span>"
        if subtitle else ""
    )
    st.markdown(
        f"<p style='font-size:0.76rem; color:{C_SUB}; margin:4px 0 6px 0;"
        f"text-transform:uppercase; letter-spacing:0.1em;'>{title}{sub}</p>",
        unsafe_allow_html=True,
    )


def _col_label(col: Any, text: str) -> None:
    col.markdown(
        f"<p style='font-size:0.76rem; color:{C_SUB}; margin:0 0 8px 0;"
        f"text-transform:uppercase; letter-spacing:0.1em;'>{text}</p>",
        unsafe_allow_html=True,
    )


def render_xai_panel() -> None:
    """XAI + signatures — full-width section below map (not in expander)."""
    st.markdown(
        f"<h3 style='color:{C_TEXT}; font-size:1.05rem; margin:8px 0 4px 0;'>"
        "XAI Forensics & Attack Signatures</h3>",
        unsafe_allow_html=True,
    )
    st.caption(
        "Attention-based explainability (EdgeBERT). Connect an alert selector later for live weights."
    )
    col_radar, col_heat = st.columns(2, gap="large")
    xai = data_svc.mock_xai_radar()
    cats = xai["features"] + [xai["features"][0]]

    with col_radar:
        _col_label(col_radar, "Attention Weight Comparison")
        fig_r = go.Figure()
        fig_r.add_trace(
            go.Scatterpolar(
                r=xai["benign"] + [xai["benign"][0]],
                theta=cats,
                fill="toself",
                name="Benign Baseline",
                line=dict(color=C_SUCCESS, width=1.5),
                fillcolor="rgba(34, 197, 94, 0.13)",
            )
        )
        fig_r.add_trace(
            go.Scatterpolar(
                r=xai["attack"] + [xai["attack"][0]],
                theta=cats,
                fill="toself",
                name="Attack Pattern",
                line=dict(color=C_ACCENT, width=1.5),
                fillcolor="rgba(230, 72, 51, 0.13)",
            )
        )
        fig_r.update_layout(
            paper_bgcolor=C_BG,
            polar=dict(
                bgcolor="#111113",
                radialaxis=dict(visible=True, range=[0, 1], gridcolor=C_BORDER),
                angularaxis=dict(gridcolor=C_BORDER),
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.22,
                x=0.5,
                xanchor="center",
                font=dict(color=C_SUB, size=10),
                bgcolor="rgba(0,0,0,0)",
            ),
            margin=dict(l=40, r=40, t=10, b=40),
            height=340,
        )
        col_radar.plotly_chart(fig_r, width=_PLOTLY_WIDTH, config=_PLOTLY_CONFIG)

    with col_heat:
        _col_label(col_heat, "Feature Importance by Attack Class")
        df_h = data_svc.mock_xai_heatmap()
        fig_h = go.Figure(
            go.Heatmap(
                z=df_h.values,
                x=df_h.columns.tolist(),
                y=df_h.index.tolist(),
                colorscale=[
                    [0.0, C_BG],
                    [0.35, "#3D1410"],
                    [0.65, "#8B2315"],
                    [1.0, C_ACCENT],
                ],
                showscale=True,
                colorbar=dict(tickfont=dict(color=C_SUB, size=9), thickness=10),
                hovertemplate="%{y} · %{x}<br>Score: <b>%{z:.2f}</b><extra></extra>",
            )
        )
        fig_h.update_layout(
            paper_bgcolor=C_BG,
            plot_bgcolor=C_BG,
            font=dict(color=C_SUB),
            margin=dict(l=0, r=0, t=0, b=0),
            height=340,
            xaxis=dict(tickfont=dict(color=C_SUB, size=9), tickangle=-30),
            yaxis=dict(tickfont=dict(color=C_SUB, size=9)),
        )
        col_heat.plotly_chart(fig_h, width=_PLOTLY_WIDTH, config=_PLOTLY_CONFIG)


def render_placeholder_page(title: str, hint: str) -> None:
    st.markdown(
        f"<h2 style='color:{C_TEXT};'>{title}</h2><p style='color:{C_SUB};'>{hint}</p>",
        unsafe_allow_html=True,
    )
