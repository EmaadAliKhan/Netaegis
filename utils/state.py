"""
NetAegis session-state helpers — 90-second attack hold after a malicious trigger.

Uses monotonic wall time (``time.time()``) for the latch end so Streamlit session
serialization does not break datetime comparisons.

``ATTACK_HOLD_SEC`` matches ``theme.ATTACK_ALERT_WINDOW_SEC`` (1.5 minutes).
"""
from __future__ import annotations

import random
import time
from datetime import datetime, timezone
from typing import Any

import streamlit as st

from theme import ATTACK_HOLD_SEC

_K_END = "netaegis_attack_end_ts"
_K_PEAK = "netaegis_attack_peak"
# Client-side simulated attacks (CLI ``attack_sim.py`` may not update MySQL before refresh).
K_ACTIVE_THREATS = "active_threats"
K_SIM_ALERTS = "netaegis_simulated_alerts"
K_FLOWS_EXTRA = "netaegis_flows_extra"
_K_FLOWS_DISPLAY_PREV = "netaegis_flows_display_prev"
_SIM_ALERT_CAP = 24
DEMO_FLOWS_BASE = 142


def init_attack_session_state() -> None:
    if _K_END not in st.session_state:
        st.session_state[_K_END] = None
    if _K_PEAK not in st.session_state:
        st.session_state[_K_PEAK] = 0
    if K_ACTIVE_THREATS not in st.session_state:
        st.session_state[K_ACTIVE_THREATS] = 0
    if K_SIM_ALERTS not in st.session_state:
        st.session_state[K_SIM_ALERTS] = []
    if K_FLOWS_EXTRA not in st.session_state:
        st.session_state[K_FLOWS_EXTRA] = 0


def get_simulated_threat_count() -> int:
    init_attack_session_state()
    return max(0, int(st.session_state.get(K_ACTIVE_THREATS) or 0))


def increment_simulated_attack(*, delta: int = 1) -> int:
    """Bump session threat count (used by sidebar demo + optional CLI hooks)."""
    init_attack_session_state()
    n = max(0, int(st.session_state.get(K_ACTIVE_THREATS) or 0)) + max(1, int(delta))
    st.session_state[K_ACTIVE_THREATS] = n
    return n


def get_session_flows_extra() -> int:
    init_attack_session_state()
    return max(0, int(st.session_state.get(K_FLOWS_EXTRA) or 0))


def bump_flows_analyzed(n: int = 1) -> int:
    """Increase session flow counter (demo + simulated attacks not yet in MySQL)."""
    init_attack_session_state()
    add = max(1, int(n))
    total = get_session_flows_extra() + add
    st.session_state[K_FLOWS_EXTRA] = total
    return total


def tick_demo_background_flows(*, enabled: bool) -> None:
    """Slowly raise flow count on auto-refresh when MySQL is unavailable."""
    if not enabled:
        return
    bump_flows_analyzed(random.randint(1, 2))


def merge_session_into_flows_metric(
    metrics: dict[str, tuple[Any, int | float | str | None]],
) -> dict[str, tuple[Any, int | float | str | None]]:
    """Add session flow increments to KPI base (mock 142 or DB COUNT)."""
    out = dict(metrics)
    vo, _do = out["flows_analyzed"]
    base = int(vo) if isinstance(vo, (int, float)) else 0
    total = base + get_session_flows_extra()

    prev = st.session_state.get(_K_FLOWS_DISPLAY_PREV)
    delta: int | None = None
    if prev is not None:
        diff = total - int(prev)
        if diff != 0:
            delta = diff
    st.session_state[_K_FLOWS_DISPLAY_PREV] = total

    out["flows_analyzed"] = (total, delta)
    return out


def get_simulated_alert_records() -> list[dict[str, Any]]:
    init_attack_session_state()
    raw = st.session_state.get(K_SIM_ALERTS) or []
    return list(raw) if isinstance(raw, list) else []


def trigger_simulated_attack() -> int:
    """Inject a malicious alert row and latch the 90s attack UI (banner, pulse, KPI).

    Works without MySQL — intended for hosted demo / recruiter walkthroughs.
    """
    init_attack_session_state()
    now_utc = datetime.now(timezone.utc)
    seq = len(get_simulated_alert_records()) + 1
    src_octet = 10 + (seq % 20)
    sport = 42000 + seq
    pkt_rate = round(220.0 + (seq * 8) + random.uniform(0, 4), 4)
    conf = round(min(0.9999, 0.94 + seq * 0.004), 4)
    alert_id = 900_000 + seq

    record: dict[str, Any] = {
        "ID": alert_id,
        "Event Time": now_utc.strftime("%Y-%m-%d %H:%M:%S"),
        "Prediction": "Malicious",
        "Confidence": conf,
        "Severity": "Critical",
        "Src IP": f"203.0.113.{src_octet}",
        "Dst IP": "8.8.8.8",
        "Src Port": sport,
        "Dst Port": 443,
        "Protocol": "UDP",
        "Pkt Rate": pkt_rate,
        "Status": "New",
    }
    alerts = get_simulated_alert_records()
    alerts.insert(0, record)
    st.session_state[K_SIM_ALERTS] = alerts[:_SIM_ALERT_CAP]
    bump_flows_analyzed(1)

    n = increment_simulated_attack(delta=3)
    ts = time.time()
    st.session_state[_K_END] = ts + ATTACK_HOLD_SEC
    st.session_state[_K_PEAK] = max(int(st.session_state.get(_K_PEAK) or 0), n)
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
