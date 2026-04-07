"""NetAegis design tokens — import from any module."""

C_BG = "#0E0E10"
C_CARD = "#18181B"
C_ACCENT = "#E64833"
C_TEXT = "#F4F4F5"
C_SUB = "#A1A1AA"
C_SUCCESS = "#22C55E"
C_WARN = "#EAB308"
C_AMBER = "#F59E0B"
C_BORDER = "#27272A"

_PLOTLY_WIDTH = "stretch"

# Rolling window for Active Threats KPI, SQL filters, and UI amber hold (1.5 minutes).
ATTACK_ALERT_WINDOW_SEC = 90
ATTACK_HOLD_SEC = ATTACK_ALERT_WINDOW_SEC
SNIFFER_MAX_LAG_SEC = 15 * 60
DASHBOARD_REFRESH_SEC = 2
# Slower Overview polling while threats are active so feeds are easier to read.
DASHBOARD_REFRESH_SEC_UNDER_ATTACK = 5
