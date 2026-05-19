"""Analytics view — real data from alerts + protocol breakdown."""
from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from services import data as data_svc
from theme import C_ACCENT, C_BG, C_BORDER, C_SUB, C_TEXT, _PLOTLY_WIDTH
from views._shared import PLOTLY_CHART_CONFIG, page_title


def render_analytics_view() -> None:
    page_title("Analytics", "24-hour traffic and protocol breakdown — live from MySQL alerts")

    analytics, ok = data_svc.fetch_analytics_metrics()
    if not ok:
        st.info("Demo mode — sample analytics below. Click **Simulate Attack** on Overview for live spikes.")

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        with st.container(border=True):
            st.metric("Total Flows (24h)", f"{analytics['total']:,}",
                      help="All alert rows with event_time in the last 24 h.")
    with m2:
        with st.container(border=True):
            st.metric("TCP Traffic share", f"{analytics['tcp_pct']}%",
                      help="Share of L4 traffic classified as TCP (24h).")
    with m3:
        with st.container(border=True):
            st.metric("Malicious flows (24h)", f"{analytics['mal_cnt']:,}",
                      help="Flows predicted Malicious in the last 24 h.")
    with m4:
        with st.container(border=True):
            st.metric("Unique attacker IPs", f"{analytics['bad_ips']:,}",
                      help="Distinct malicious source IPs in the last 24 h.")

    st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)

    # ── Hourly alert counts (real) + Protocol donut (real) ─────────────────
    df_hourly, hourly_ok = data_svc.fetch_hourly_alert_counts()
    proto = analytics.get("proto_counts", {"TCP": 0, "UDP": 0, "ICMP": 0, "Other": 0})

    # Line chart — total vs malicious per hour
    fig_line = go.Figure()
    if not df_hourly.empty:
        fig_line.add_trace(go.Scatter(
            x=df_hourly["Hour"],
            y=df_hourly["Total"],
            name="Total alerts",
            mode="lines",
            line=dict(color="#3F3F46", width=2),
            fill="tozeroy",
            fillcolor="rgba(63,63,70,0.18)",
            hovertemplate="%{x|%H:%M}<br>Total: <b>%{y:,}</b><extra></extra>",
        ))
        fig_line.add_trace(go.Scatter(
            x=df_hourly["Hour"],
            y=df_hourly["Malicious"],
            name="Malicious",
            mode="lines",
            line=dict(color=C_ACCENT, width=2),
            fill="tozeroy",
            fillcolor="rgba(230, 72, 51, 0.15)",
            hovertemplate="%{x|%H:%M}<br>Malicious: <b>%{y:,}</b><extra></extra>",
        ))
    else:
        fig_line.add_annotation(
            text="No data in the last 24 h", x=0.5, y=0.5,
            xref="paper", yref="paper", showarrow=False,
            font=dict(color=C_SUB, size=14),
        )
    fig_line.update_layout(
        paper_bgcolor=C_BG, plot_bgcolor=C_BG,
        font=dict(color=C_SUB),
        margin=dict(l=48, r=24, t=32, b=48),
        height=420,
        title=dict(text="Alert volume — last 24 hours", font=dict(color=C_TEXT, size=16)),
        legend=dict(font=dict(color=C_SUB, size=11), bgcolor="rgba(0,0,0,0)"),
        xaxis=dict(showgrid=True, gridcolor=C_BORDER,
                   tickfont=dict(color=C_SUB, size=10),
                   title=dict(text="Time (UTC)", font=dict(color=C_SUB, size=11))),
        yaxis=dict(showgrid=True, gridcolor=C_BORDER,
                   tickfont=dict(color=C_SUB, size=10),
                   title=dict(text="Alert count", font=dict(color=C_SUB, size=11))),
    )

    # Donut — protocol split
    proto_labels = list(proto.keys())
    proto_vals = [int(v) for v in proto.values()]
    fig_donut = go.Figure(go.Pie(
        labels=proto_labels,
        values=proto_vals,
        hole=0.58,
        marker=dict(
            colors=[C_ACCENT, "#3F3F46", "#52525B", C_BORDER],
            line=dict(color=C_BG, width=2),
        ),
        textinfo="label+percent",
        textfont=dict(color=C_TEXT, size=12),
        hovertemplate="%{label}<br>%{value:,} flows (%{percent})<extra></extra>",
    ))
    fig_donut.update_layout(
        paper_bgcolor=C_BG,
        font=dict(color=C_SUB),
        margin=dict(l=24, r=24, t=48, b=24),
        height=420,
        title=dict(text="Protocol breakdown (24h)", font=dict(color=C_TEXT, size=16), x=0.5),
        showlegend=True,
        legend=dict(font=dict(color=C_SUB, size=11), bgcolor="rgba(0,0,0,0)"),
    )

    ca, cb = st.columns(2)
    with ca:
        st.plotly_chart(
            fig_line,
            width=_PLOTLY_WIDTH,
            config=PLOTLY_CHART_CONFIG,
            key="analytics_hourly_alerts",
        )
    with cb:
        st.plotly_chart(
            fig_donut,
            width=_PLOTLY_WIDTH,
            config=PLOTLY_CHART_CONFIG,
            key="analytics_protocol_donut",
        )

