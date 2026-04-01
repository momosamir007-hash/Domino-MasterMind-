"""🔧 دوال مساعدة للواجهة"""

import streamlit as st
from game_engine.tiles import Direction


def show_message(msg: str, msg_type: str = "info"):
    """عرض رسالة ملونة"""
    if msg_type == "success":
        st.success(msg)
    elif msg_type == "warning":
        st.warning(msg)
    elif msg_type == "error":
        st.error(msg)
    else:
        st.info(msg)


def format_move(move) -> str:
    """تنسيق حركة للسجل"""
    if move.is_pass:
        return f"{move.pos.icon} {move.pos.label}: دق 🚫"
    d = "⬅️ يسار" if move.direction == Direction.LEFT else "➡️ يمين"
    return f"{move.pos.icon} {move.pos.label}: {move.tile} {d}"
