"""Titles and Plotly defaults for routed views (``app.py`` applies base CSS)."""
from __future__ import annotations

import streamlit as st

from theme import C_SUB, C_TEXT

PLOTLY_CHART_CONFIG = {
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


def page_title(title: str, subtitle: str = "") -> None:
    sub = f'<p style="color:{C_SUB};font-size:0.9rem;margin-top:6px;">{subtitle}</p>' if subtitle else ""
    st.markdown(
        f'<h1 style="margin-bottom:0.2rem;">{title}</h1>{sub}',
        unsafe_allow_html=True,
    )
