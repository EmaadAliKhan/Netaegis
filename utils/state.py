"""
NetAegis session-state helpers — 90-second attack hold after a malicious trigger.

Uses monotonic wall time (``time.time()``) for the latch end so Streamlit session
serialization does not break datetime comparisons.

``ATTACK_HOLD_SEC`` matches ``theme.ATTACK_ALERT_WINDOW_SEC`` (1.5 minutes).
"""
from __future__ import annotations

import time
from typing import Any

import streamlit as st

from theme import ATTACK_HOLD_SEC

_K_END = "netaegis_attack_end_ts"
_K_PEAK = "netaegis_attack_peak"
# Client-side simulated attacks (CLI ``attack_sim.py`` may not update MySQL before refresh).
K_ACTIVE_THREATS = "active_threats"


def init_attack_session_state() -> None:
    if _K_END not in st.session_state:
        st.session_state[_K_END] = None
    if _K_PEAK not in st.session_state:
        st.session_state[_K_PEAK] = 0
    if K_ACTIVE_THREATS not in st.session_state:
        st.session_state[K_ACTIVE_THREATS] = 0


def get_simulated_threat_count() -> int:
    init_attack_session_state()
    return max(0, int(st.session_state.get(K_ACTIVE_THREATS) or 0))


def increment_simulated_attack(*, delta: int = 1) -> int:
    """Bump session threat count (used by sidebar demo + optional CLI hooks)."""
    init_attack_session_state()
    n = max(0, int(st.session_state.get(K_ACTIVE_THREATS) or 0)) + max(1, int(delta))
    st.session_state[K_ACTIVE_THREATS] = n
    return n


def merge_session_into_active_threats_metric(
    metrics: dict[str, tuple[Any, int | float | str | None]],
) -> dict[str, tuple[Any, int | float | str | None]]:
    """Combine DB KPI with ``st.session_state.active_threats`` for the Active Threats tile."""
    out = dict(metrics)
    t = out["active_threats"]
    raw = t[0]
    db_int = int(raw) if isinstance(raw, (int, float)) else 0
    merged = max(db_int, get_simulated_threat_count())
    out["active_threats"] = (merged, t[1])
    return out


def sync_attack_hold(db_malicious_rolling_count: int) -> tuple[bool, int]:
    """
    Returns (show_amber_banner, active_threats_display_value).

    ``db_malicious_rolling_count`` should match your SQL window (e.g. malicious rows
    in the last 90s), the same basis as the raw Active Threats KPI.
    """
    init_attack_session_state()
    now = time.time()
    n = max(0, int(db_malicious_rolling_count))

    end_ts = st.session_state.get(_K_END)
    if end_ts is not None and now >= float(end_ts):
        st.session_state[_K_END] = None
        st.session_state[_K_PEAK] = 0
        st.session_state[K_ACTIVE_THREATS] = 0

    if n > 0:
        if st.session_state.get(_K_END) is None:
            st.session_state[_K_END] = now + ATTACK_HOLD_SEC
            st.session_state[_K_PEAK] = n
        else:
            st.session_state[_K_PEAK] = max(int(st.session_state.get(_K_PEAK) or 0), n)

    end_ts = st.session_state.get(_K_END)
    peak = int(st.session_state.get(_K_PEAK) or 0)
    in_hold = end_ts is not None and now < float(end_ts)

    if in_hold:
        return (True, max(peak, n))

    return (False, n)


def apply_attack_hold_to_metrics(
    metrics: dict[str, tuple[Any, int | float | str | None]],
    held_threat_value: int,
    in_hold: bool,
) -> dict[str, tuple[Any, int | float | str | None]]:
    out = dict(metrics)
    if in_hold:
        t = out["active_threats"]
        out["active_threats"] = (held_threat_value, t[1])
    return out
