"""MySQL-backed fetchers + geo helpers for NetAegis (Streamlit-cached)."""
from __future__ import annotations

import ipaddress
import random
from datetime import datetime, timedelta
from typing import Any

import numpy as np
import pandas as pd
import requests
import streamlit as st
from sqlalchemy import text

from backend.common.db import get_db_session
from theme import ATTACK_ALERT_WINDOW_SEC, SNIFFER_MAX_LAG_SEC


def _mock_metrics() -> dict[str, tuple[Any, int | float | str | None]]:
    return {
        "flows_analyzed": (142, -8),
        "active_threats": (7, +3),
        "compliance_score": ("94%", +2),
        "time_to_remediate": ("18m", -4),
    }


@st.cache_data(ttl=86400, show_spinner=False)
def _resolve_public_ip_geo(ip: str) -> tuple[float, float] | None:
    try:
        resp = requests.get(f"https://ipapi.co/{ip}/json/", timeout=1.8)
        if resp.status_code != 200:
            return None
        body = resp.json()
        lat, lon = body.get("latitude"), body.get("longitude")
        if lat is None or lon is None:
            return None
        return float(lat), float(lon)
    except Exception:
        return None


def _is_private_or_local_ip(ip: str | None) -> bool:
    if not ip:
        return True
    try:
        p = ipaddress.ip_address(ip)
        return bool(
            p.is_private or p.is_loopback or p.is_link_local
            or p.is_multicast or p.is_reserved or p.is_unspecified
        )
    except ValueError:
        return True


_CITY_POOL: list[tuple[float, float]] = [
    (40.7128, -74.0060), (51.5074, -0.1278), (35.6762, 139.6503),
    (48.8566, 2.3522), (-33.8688, 151.2093), (55.7558, 37.6173),
    (28.6139, 77.2090), (31.2304, 121.4737), (1.3521, 103.8198),
    (-23.5505, -46.6333), (19.4326, -99.1332), (6.5244, 3.3792),
    (53.3498, -6.2603), (37.7749, -122.4194), (41.0082, 28.9784),
]


def _mock_latlon_from_ip(ip: str | None) -> tuple[float, float]:
    rng = random.Random(42)
    if not ip:
        return rng.choice(_CITY_POOL)
    parts = ip.split(".")
    if len(parts) == 4 and parts[-1].isdigit():
        seed = int(parts[-1]) % len(_CITY_POOL)
        lat, lon = _CITY_POOL[seed]
        return lat + rng.uniform(-2, 2), lon + rng.uniform(-2, 2)
    seed = abs(hash(ip)) % len(_CITY_POOL)
    lat, lon = _CITY_POOL[seed]
    return lat + rng.uniform(-2, 2), lon + rng.uniform(-2, 2)


def _ip_to_latlon(ip: str | None) -> tuple[float, float]:
    if _is_private_or_local_ip(ip) or not ip:
        return _mock_latlon_from_ip(ip)
    resolved = _resolve_public_ip_geo(ip)
    if resolved is not None:
        return resolved
    return _mock_latlon_from_ip(ip)


@st.cache_data(ttl=2)
def _fetch_metrics_from_db() -> dict[str, tuple[Any, int | float | str | None]] | None:
    with get_db_session() as session:
        total_flows = int(session.execute(text("SELECT COUNT(*) FROM alerts")).scalar() or 0)
        threats_recent = int(
            session.execute(
                text(
                    f"""
                    SELECT COUNT(*) FROM alerts
                    WHERE prediction = 'Malicious'
                      AND event_time > UTC_TIMESTAMP() - INTERVAL {ATTACK_ALERT_WINDOW_SEC} SECOND
                    """
                )
            ).scalar()
            or 0
        )
        row = session.execute(
            text(
                """
                SELECT COUNT(*) AS total,
                       SUM(CASE WHEN prediction = 'Benign' THEN 1 ELSE 0 END) AS benign
                FROM alerts
                WHERE event_time > UTC_TIMESTAMP() - INTERVAL 24 HOUR
                """
            )
        ).one()
        total, benign = int(row[0] or 0), int(row[1] or 0)
        pct = 100 if total == 0 else round(benign * 100.0 / total)

        avg_min = session.execute(
            text(
                """
                SELECT AVG(TIMESTAMPDIFF(MINUTE, created_at, updated_at))
                FROM alerts
                WHERE status = 'Resolved' AND updated_at > created_at
                  AND event_time > UTC_TIMESTAMP() - INTERVAL 7 DAY
                """
            )
        ).scalar()
        remed = "—" if avg_min is None else f"{int(round(float(avg_min)))}m"

        return {
            "flows_analyzed": (total_flows, None),
            "active_threats": (threats_recent, None),
            "compliance_score": (f"{pct}%", None),
            "time_to_remediate": (remed, None),
        }


@st.cache_data(ttl=2)
def fetch_dashboard_metrics() -> tuple[dict[str, tuple[Any, int | float | str | None]], bool]:
    try:
        return (_fetch_metrics_from_db(), True)
    except Exception:
        return (_mock_metrics(), False)


def _mock_threat_origins_fallback() -> list[dict]:
    return [
        {"lat": 39.9, "lon": 116.4, "label": "Beijing", "size": 22},
        {"lat": 55.7, "lon": 37.6, "label": "Moscow", "size": 18},
        {"lat": 28.6, "lon": 77.2, "label": "New Delhi", "size": 14},
        {"lat": 37.6, "lon": -122.4, "label": "San Jose", "size": 10},
        {"lat": 51.5, "lon": -0.1, "label": "London", "size": 8},
    ]


@st.cache_data(ttl=2)
def fetch_threat_origins() -> tuple[list[dict], bool]:
    try:
        with get_db_session() as session:
            rows = session.execute(
                text(
                    """
                    SELECT src_ip, COUNT(*) AS cnt
                    FROM alerts
                    WHERE prediction = 'Malicious'
                      AND event_time > UTC_TIMESTAMP() - INTERVAL 24 HOUR
                      AND src_ip IS NOT NULL AND src_ip <> ''
                    GROUP BY src_ip
                    ORDER BY cnt DESC
                    LIMIT 15
                    """
                )
            ).fetchall()
        if not rows:
            return ([], True)
        out: list[dict] = []
        for src_ip, cnt in rows:
            lat, lon = _ip_to_latlon(str(src_ip))
            label = str(src_ip) if len(str(src_ip)) <= 18 else str(src_ip)[:15] + "…"
            size = min(30, max(6, int(cnt) * 2))
            out.append({"lat": lat, "lon": lon, "label": label, "size": size})
        return (out, True)
    except Exception:
        return (_mock_threat_origins_fallback(), False)


def _mock_top_ports() -> pd.DataFrame:
    return pd.DataFrame({
        "Port": ["443 (HTTPS)", "22 (SSH)", "80 (HTTP)", "3389 (RDP)"],
        "Hits": [384, 271, 198, 154],
    })


@st.cache_data(ttl=2)
def fetch_top_ports() -> tuple[pd.DataFrame, bool]:
    try:
        with get_db_session() as session:
            rows = session.execute(
                text(
                    """
                    SELECT dst_port, COUNT(*) AS hits
                    FROM alerts
                    WHERE prediction = 'Malicious'
                      AND event_time > UTC_TIMESTAMP() - INTERVAL 24 HOUR
                      AND dst_port IS NOT NULL
                    GROUP BY dst_port
                    ORDER BY hits DESC
                    LIMIT 8
                    """
                )
            ).fetchall()
        if not rows:
            return (pd.DataFrame(columns=["Port", "Hits"]), True)
        port_names: dict[int, str] = {
            22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS", 80: "HTTP",
            110: "POP3", 143: "IMAP", 443: "HTTPS", 445: "SMB",
            3306: "MySQL", 3389: "RDP", 8080: "HTTP-Alt",
        }
        data: list[dict[str, Any]] = []
        for port, hits in rows:
            p = int(port) if port is not None else 0
            name = port_names.get(p, "tcp")
            data.append({"Port": f"{p} ({name})", "Hits": int(hits)})
        return (pd.DataFrame(data), True)
    except Exception:
        return (_mock_top_ports(), False)


_QUEUE_COLS: list[str] = [
    "ID",
    "Event Time",
    "Prediction",
    "Confidence",
    "Severity",
    "Src IP",
    "Dst IP",
    "Src Port",
    "Dst Port",
    "Protocol",
    "Pkt Rate",
    "Status",
]


def _proto_label(ip_proto: Any) -> str:
    if ip_proto is None:
        return "—"
    try:
        p = int(ip_proto)
    except (TypeError, ValueError):
        return str(ip_proto)
    names = {6: "TCP", 17: "UDP", 1: "ICMP", 47: "GRE", 132: "SCTP"}
    return names.get(p, str(p))


def _rows_to_alert_queue_df(rows: list[Any]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame(columns=_QUEUE_COLS)
    records: list[dict[str, Any]] = []
    for row in rows:
        (
            rid,
            et,
            pred,
            conf,
            sev,
            sip,
            dip,
            sport,
            dport,
            iproto,
            prate,
            status,
        ) = row
        ts = et.strftime("%Y-%m-%d %H:%M:%S") if hasattr(et, "strftime") else str(et)
        records.append({
            "ID": int(rid),
            "Event Time": ts,
            "Prediction": str(pred or ""),
            "Confidence": float(conf) if conf is not None else None,
            "Severity": str(sev or ""),
            "Src IP": str(sip) if sip not in (None, "") else "—",
            "Dst IP": str(dip) if dip not in (None, "") else "—",
            "Src Port": int(sport) if sport is not None else None,
            "Dst Port": int(dport) if dport is not None else None,
            "Protocol": _proto_label(iproto),
            "Pkt Rate": float(prate) if prate is not None else None,
            "Status": str(status or ""),
        })
    return pd.DataFrame.from_records(records, columns=_QUEUE_COLS)


def _mock_alerts_queue_df(*, malicious_only: bool, n: int = 18) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    now = datetime.utcnow()
    records: list[dict[str, Any]] = []
    for i in range(n):
        pred = "Malicious" if malicious_only else (
            "Malicious" if rng.random() < 0.14 else "Benign"
        )
        sev = (
            rng.choice(["Critical", "High", "Medium", "Info"])
            if pred == "Malicious"
            else "Info"
        )
        conf = float(rng.uniform(0.55, 0.9999) if pred == "Malicious" else rng.uniform(0.92, 0.9999))
        ts = (now - timedelta(minutes=i * 4, seconds=int(rng.integers(0, 50)))).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        sport = int(rng.integers(1024, 65500))
        dport = int(rng.choice([80, 443, 22, 3389, 53522, 8009]))
        records.append({
            "ID": 132000 + i,
            "Event Time": ts,
            "Prediction": pred,
            "Confidence": round(conf, 4),
            "Severity": sev,
            "Src IP": f"192.168.1.{int(rng.integers(2, 220))}",
            "Dst IP": f"151.101.{int(rng.integers(1, 40))}.{int(rng.integers(1, 250))}",
            "Src Port": sport,
            "Dst Port": dport,
            "Protocol": rng.choice(["TCP", "UDP"]),
            "Pkt Rate": float(rng.uniform(0.01, 0.35)),
            "Status": "New",
        })
    return pd.DataFrame.from_records(records, columns=_QUEUE_COLS)


@st.cache_data(ttl=2)
def fetch_malicious_alerts_queue(limit: int = 100) -> tuple[pd.DataFrame, bool]:
    lim = max(1, min(int(limit), 500))
    try:
        with get_db_session() as session:
            rows = session.execute(
                text(
                    """
                    SELECT id, event_time, prediction, confidence, severity,
                           src_ip, dst_ip, src_port, dst_port, ip_proto, packet_rate, status
                    FROM alerts
                    WHERE prediction = 'Malicious'
                    ORDER BY event_time DESC
                    LIMIT :lim
                    """
                ),
                {"lim": lim},
            ).fetchall()
        return (_rows_to_alert_queue_df(list(rows)), True)
    except Exception:
        return (_mock_alerts_queue_df(malicious_only=True, n=min(24, lim)), False)


@st.cache_data(ttl=2)
def fetch_all_alerts_queue(limit: int = 100) -> tuple[pd.DataFrame, bool]:
    lim = max(1, min(int(limit), 500))
    try:
        with get_db_session() as session:
            rows = session.execute(
                text(
                    """
                    SELECT id, event_time, prediction, confidence, severity,
                           src_ip, dst_ip, src_port, dst_port, ip_proto, packet_rate, status
                    FROM alerts
                    ORDER BY event_time DESC
                    LIMIT :lim
                    """
                ),
                {"lim": lim},
            ).fetchall()
        return (_rows_to_alert_queue_df(list(rows)), True)
    except Exception:
        return (_mock_alerts_queue_df(malicious_only=False, n=min(24, lim)), False)


@st.cache_data(ttl=2)
def fetch_mysql_connected() -> bool:
    try:
        with get_db_session() as session:
            session.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


@st.cache_data(ttl=2)
def fetch_attack_active() -> bool:
    try:
        with get_db_session() as session:
            n = session.execute(
                text(
                    f"""
                    SELECT COUNT(*) FROM alerts
                    WHERE prediction = 'Malicious'
                      AND event_time > UTC_TIMESTAMP() - INTERVAL {ATTACK_ALERT_WINDOW_SEC} SECOND
                    """
                )
            ).scalar()
        return (n or 0) > 0
    except Exception:
        return False


@st.cache_data(ttl=2)
def fetch_sniffer_likely_live() -> bool:
    try:
        with get_db_session() as session:
            row = session.execute(
                text(
                    f"""
                    SELECT
                      TIMESTAMPDIFF(
                          SECOND,
                          (SELECT MAX(event_time) FROM alerts),
                          UTC_TIMESTAMP()
                      ) AS lag_sec,
                      (
                        SELECT COUNT(*) FROM alerts
                        WHERE event_time > UTC_TIMESTAMP() - INTERVAL {SNIFFER_MAX_LAG_SEC} SECOND
                      ) AS recent_cnt
                    """
                )
            ).one()
        lag_raw, recent_cnt = row[0], int(row[1] or 0)
        if recent_cnt > 0:
            return True
        if lag_raw is None:
            return False
        lag_sec = int(lag_raw)
        return lag_sec <= SNIFFER_MAX_LAG_SEC or lag_sec < 0
    except Exception:
        return False


def mock_xai_radar() -> dict:
    feats = [
        "Flow Duration", "Packet Rate", "Byte Ratio",
        "IAT Mean", "TCP Flags", "Dst Port", "Payload Entropy",
    ]
    return {
        "features": feats,
        "benign": [0.28, 0.42, 0.55, 0.31, 0.19, 0.22, 0.38],
        "attack": [0.82, 0.91, 0.44, 0.73, 0.87, 0.65, 0.78],
    }


def mock_xai_heatmap() -> pd.DataFrame:
    feats = ["Flow Duration", "Packet Rate", "Byte Ratio", "IAT Mean", "TCP Flags"]
    cats = ["DDoS", "Port Scan", "Brute Force", "Exfiltration", "DNS Tunnel"]
    rng = np.random.default_rng(42)
    return pd.DataFrame(
        rng.uniform(0.1, 1.0, size=(len(cats), len(feats))),
        index=cats, columns=feats,
    )


# ─── Threat Intel ──────────────────────────────────────────────────────────────

@st.cache_data(ttl=30)
def fetch_top_malicious_ips(limit: int = 20) -> tuple[pd.DataFrame, bool]:
    """Top malicious source IPs from the last 7 days."""
    try:
        with get_db_session() as session:
            rows = session.execute(
                text(
                    """
                    SELECT src_ip, COUNT(*) AS hits,
                           MAX(severity) AS top_severity,
                           MAX(confidence) AS max_conf
                    FROM alerts
                    WHERE prediction = 'Malicious'
                      AND src_ip IS NOT NULL AND src_ip <> ''
                      AND event_time > UTC_TIMESTAMP() - INTERVAL 7 DAY
                    GROUP BY src_ip
                    ORDER BY hits DESC
                    LIMIT :lim
                    """
                ),
                {"lim": max(1, int(limit))},
            ).fetchall()
        if not rows:
            return (pd.DataFrame(columns=["IP", "Hits (7d)", "Top Severity", "Max Conf"]), True)
        records = [
            {
                "IP": str(r[0]),
                "Hits (7d)": int(r[1]),
                "Top Severity": str(r[2] or ""),
                "Max Conf": float(r[3]) if r[3] is not None else None,
            }
            for r in rows
        ]
        return (pd.DataFrame.from_records(records), True)
    except Exception:
        return (pd.DataFrame(columns=["IP", "Hits (7d)", "Top Severity", "Max Conf"]), False)


@st.cache_data(ttl=30)
def fetch_recent_malicious_alerts(limit: int = 20) -> tuple[pd.DataFrame, bool]:
    """Recent malicious alerts for the Threat Intel historical table."""
    try:
        with get_db_session() as session:
            rows = session.execute(
                text(
                    """
                    SELECT id, event_time, severity, src_ip, dst_ip, dst_port,
                           ip_proto, confidence, status
                    FROM alerts
                    WHERE prediction = 'Malicious'
                    ORDER BY event_time DESC
                    LIMIT :lim
                    """
                ),
                {"lim": max(1, int(limit))},
            ).fetchall()
        if not rows:
            return (pd.DataFrame(), True)
        records = []
        for r in rows:
            rid, et, sev, sip, dip, dport, iproto, conf, status = r
            ts = et.strftime("%Y-%m-%d %H:%M:%S") if hasattr(et, "strftime") else str(et)
            records.append({
                "ID": int(rid),
                "Time (UTC)": ts,
                "Severity": str(sev or ""),
                "Src IP": str(sip) if sip else "—",
                "Dst IP": str(dip) if dip else "—",
                "Dst Port": int(dport) if dport is not None else None,
                "Protocol": _proto_label(iproto),
                "Confidence": float(conf) if conf is not None else None,
                "Status": str(status or ""),
            })
        return (pd.DataFrame.from_records(records), True)
    except Exception:
        return (pd.DataFrame(), False)


# ─── Analytics (real data from alerts) ────────────────────────────────────────

@st.cache_data(ttl=30)
def fetch_analytics_metrics() -> tuple[dict[str, Any], bool]:
    """24h metrics for the Analytics view — derived from the alerts table."""
    try:
        with get_db_session() as session:
            row = session.execute(
                text(
                    """
                    SELECT
                        COUNT(*)                                          AS total,
                        SUM(CASE WHEN ip_proto = 6  THEN 1 ELSE 0 END)  AS tcp,
                        SUM(CASE WHEN ip_proto = 17 THEN 1 ELSE 0 END)  AS udp,
                        SUM(CASE WHEN ip_proto = 1  THEN 1 ELSE 0 END)  AS icmp,
                        COUNT(DISTINCT CASE WHEN prediction='Malicious'
                              THEN src_ip END)                           AS uniq_bad_ips,
                        SUM(CASE WHEN prediction='Malicious' THEN 1 ELSE 0 END) AS mal_cnt
                    FROM alerts
                    WHERE event_time > UTC_TIMESTAMP() - INTERVAL 24 HOUR
                    """
                )
            ).one()
        total = int(row[0] or 0)
        tcp   = int(row[1] or 0)
        udp   = int(row[2] or 0)
        icmp  = int(row[3] or 0)
        other = max(0, total - tcp - udp - icmp)
        bad_ips = int(row[4] or 0)
        mal_cnt = int(row[5] or 0)
        tcp_pct = round(tcp * 100 / total) if total else 0
        return ({
            "total": total,
            "tcp_pct": tcp_pct,
            "bad_ips": bad_ips,
            "mal_cnt": mal_cnt,
            "proto_counts": {"TCP": tcp, "UDP": udp, "ICMP": icmp, "Other": other},
        }, True)
    except Exception:
        return ({
            "total": 0, "tcp_pct": 0, "bad_ips": 0, "mal_cnt": 0,
            "proto_counts": {"TCP": 0, "UDP": 0, "ICMP": 0, "Other": 0},
        }, False)


@st.cache_data(ttl=30)
def fetch_hourly_alert_counts() -> tuple[pd.DataFrame, bool]:
    """Alert counts grouped by hour for the last 24 hours."""
    try:
        with get_db_session() as session:
            rows = session.execute(
                text(
                    """
                    SELECT
                        DATE_FORMAT(event_time, '%Y-%m-%d %H:00:00') AS hr,
                        COUNT(*) AS total,
                        SUM(CASE WHEN prediction = 'Malicious' THEN 1 ELSE 0 END) AS malicious
                    FROM alerts
                    WHERE event_time > UTC_TIMESTAMP() - INTERVAL 24 HOUR
                    GROUP BY hr
                    ORDER BY hr ASC
                    """
                )
            ).fetchall()
        if not rows:
            return (pd.DataFrame(columns=["Hour", "Total", "Malicious"]), True)
        df = pd.DataFrame(rows, columns=["Hour", "Total", "Malicious"])
        df["Hour"] = pd.to_datetime(df["Hour"])
        df["Total"] = df["Total"].astype(int)
        df["Malicious"] = df["Malicious"].astype(int)
        return (df, True)
    except Exception:
        return (pd.DataFrame(columns=["Hour", "Total", "Malicious"]), False)
