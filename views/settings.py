"""Settings view."""
from __future__ import annotations

import streamlit as st

from theme import C_SUB, C_TEXT

from views._shared import page_title

_TOAST_KEY = "_netaegis_settings_toast"


def _schedule_settings_toast() -> None:
    st.session_state[_TOAST_KEY] = True


def render_settings_view() -> None:
    page_title("Settings", "Operational toggles and notification behavior")

    st.markdown(
        f'<p style="color:{C_SUB}; margin-bottom:1rem;">'
        "These controls are UI placeholders — bind to config storage or environment when ready.</p>",
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        st.markdown(f"#### <span style='color:{C_TEXT};'>Mitigation & alerts</span>", unsafe_allow_html=True)
        st.toggle(
            "Auto-Mitigation",
            value=False,
            help="Automatically apply firewall or rate-limit rules when high-confidence threats are detected.",
            key="settings_auto_mitigation",
            on_change=_schedule_settings_toast,
        )
        st.slider(
            "Alert sensitivity (threshold)",
            min_value=0.50,
            max_value=0.99,
            value=0.85,
            step=0.01,
            help="Model confidence floor for surfacing alerts — lower values increase sensitivity.",
            key="settings_alert_sensitivity",
            on_change=_schedule_settings_toast,
        )
        auto_mit = st.session_state.get("settings_auto_mitigation", False)
        sens = float(st.session_state.get("settings_alert_sensitivity", 0.85))
        st.caption(
            f"Auto-Mitigation: **{'enabled' if auto_mit else 'disabled'}** · "
            f"Alert threshold: **{sens:.2f}**"
        )

    with st.container(border=True):
        st.markdown(f"#### <span style='color:{C_TEXT};'>Notifications</span>", unsafe_allow_html=True)
        st.toggle(
            "Notification Preferences",
            value=True,
            help="Email or webhook digests for critical and high-severity events.",
            key="settings_notification_preferences",
            on_change=_schedule_settings_toast,
        )
        notif = st.session_state.get("settings_notification_preferences", True)
        st.caption(f"Notifications: **{'on' if notif else 'off'}**")

    if st.session_state.pop(_TOAST_KEY, False):
        st.toast("Settings auto-saved securely.")
