"""XAI Forensics deep-dive view."""
from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from services import data as data_svc
from theme import C_ACCENT, C_BG, C_BORDER, C_CARD, C_SUB, C_TEXT, _PLOTLY_WIDTH

from views._shared import PLOTLY_CHART_CONFIG, page_title

_INCIDENT_OPTIONS = ("INC-2026-08A", "INC-2026-08B", "INC-2026-08C")


def render_xai_forensics_view() -> None:
    page_title(
        "XAI Forensics",
        "Explainability overlays — attention maps and per-feature attribution",
    )

    st.selectbox(
        "Select Incident ID",
        options=list(_INCIDENT_OPTIONS),
        index=0,
        key="xai_forensics_incident_id",
        help="Investigation scope — wire to your case management system.",
    )

    st.caption(
        "Placeholders below mirror the overview XAI widgets; connect an alert or flow ID selector for live inference."
    )

    st.markdown(
        f"<p style='font-size:0.76rem; color:{C_SUB}; margin:4px 0 8px 0;"
        "text-transform:uppercase; letter-spacing:0.1em;'>Attention map (sequence)</p>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""
        <div style="
            background:{C_CARD};
            border:1px solid {C_BORDER};
            border-radius:10px;
            padding:12px 14px;
            color:{C_TEXT};
            font-size:0.9rem;
            line-height:1.45;
            margin-bottom:10px;
        ">
            <strong style="color:{C_TEXT};">Heatmap placeholder</strong> — Token- or packet-segment
            attention weights from EdgeBERT (render with <code>go.Heatmap</code> once logits are wired).
        </div>
        """,
        unsafe_allow_html=True,
    )

    attn_z = [
        [0.02, 0.05, 0.11, 0.08, 0.03],
        [0.04, 0.09, 0.22, 0.14, 0.06],
        [0.03, 0.07, 0.18, 0.31, 0.09],
        [0.02, 0.04, 0.09, 0.12, 0.05],
    ]
    fig_attn = go.Figure(
        go.Heatmap(
            z=attn_z,
            colorscale=[
                [0.0, C_BG],
                [0.5, "#3D1410"],
                [1.0, C_ACCENT],
            ],
            showscale=True,
            colorbar=dict(tickfont=dict(color=C_SUB, size=9), title=dict(text="α", font=dict(color=C_SUB))),
            hovertemplate="seg %{y} · step %{x}<br>α: <b>%{z:.3f}</b><extra></extra>",
        )
    )
    fig_attn.update_layout(
        paper_bgcolor=C_BG,
        plot_bgcolor=C_BG,
        font=dict(color=C_SUB),
        margin=dict(l=0, r=12, t=8, b=0),
        height=320,
        xaxis=dict(tickfont=dict(color=C_SUB, size=9), title=dict(text="Position", font=dict(color=C_SUB))),
        yaxis=dict(tickfont=dict(color=C_SUB, size=9), title=dict(text="Layer", font=dict(color=C_SUB))),
    )
    st.plotly_chart(fig_attn, width=_PLOTLY_WIDTH, config=PLOTLY_CHART_CONFIG, key="xai_attention_map")

    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

    col_left, col_right = st.columns(2, gap="large")

    with col_left:
        st.markdown(
            f"<p style='font-size:0.76rem; color:{C_SUB}; margin:0 0 8px 0;"
            "text-transform:uppercase; letter-spacing:0.1em;'>Feature Importance by Attack Class</p>",
            unsafe_allow_html=True,
        )
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
            margin=dict(l=0, r=0, t=8, b=0),
            height=360,
            xaxis=dict(tickfont=dict(color=C_SUB, size=9), tickangle=-30),
            yaxis=dict(tickfont=dict(color=C_SUB, size=9)),
        )
        st.plotly_chart(fig_h, width=_PLOTLY_WIDTH, config=PLOTLY_CHART_CONFIG, key="xai_feature_importance")

    with col_right:
        st.markdown(
            f"<p style='font-size:0.76rem; color:{C_SUB}; margin:0 0 8px 0;"
            "text-transform:uppercase; letter-spacing:0.1em;'>Attention Weight Comparison</p>",
            unsafe_allow_html=True,
        )
        xai = data_svc.mock_xai_radar()
        cats = xai["features"] + [xai["features"][0]]
        fig_r = go.Figure()
        fig_r.add_trace(
            go.Scatterpolar(
                r=xai["benign"] + [xai["benign"][0]],
                theta=cats,
                fill="toself",
                name="Benign",
                line=dict(color="#22C55E", width=1.5),
                fillcolor="rgba(34, 197, 94, 0.13)",
            )
        )
        fig_r.add_trace(
            go.Scatterpolar(
                r=xai["attack"] + [xai["attack"][0]],
                theta=cats,
                fill="toself",
                name="Attack",
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
            height=360,
            title=dict(text="Radar — benign vs attack", font=dict(color=C_TEXT, size=13)),
        )
        st.plotly_chart(fig_r, width=_PLOTLY_WIDTH, config=PLOTLY_CHART_CONFIG, key="xai_radar_compare")
