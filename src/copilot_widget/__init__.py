"""Floating copilot chat widget - a minimal custom Streamlit component."""
from __future__ import annotations

import os
from typing import Any

import streamlit.components.v1 as components

_FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "frontend")

_component = components.declare_component(
    "wisag_copilot",
    path=_FRONTEND_DIR,
)


def copilot_widget(
    *,
    messages: list[dict[str, str]],
    expanded: bool,
    busy: bool,
    lang: str,
    placeholder: str,
    mic_hint: str,
    empty_greeting: str,
    thinking_label: str,
    send_label: str,
    mic_label: str,
    read_aloud_label: str,
    stop_reading_label: str,
    key: str = "wisag_copilot",
) -> Any:
    return _component(
        messages=messages,
        expanded=bool(expanded),
        busy=bool(busy),
        lang=lang,
        placeholder=placeholder,
        mic_hint=mic_hint,
        empty_greeting=empty_greeting,
        thinking_label=thinking_label,
        send_label=send_label,
        mic_label=mic_label,
        read_aloud_label=read_aloud_label,
        stop_reading_label=stop_reading_label,
        default=None,
        key=key,
    )
