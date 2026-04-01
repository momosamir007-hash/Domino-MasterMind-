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
    """
    تنسيق حركة للسجل
    ★ يدعم move.who و move.pos (توافقية) ★
    """
    # ── استخراج اللاعب بأمان ──
    player = getattr(move, 'who', None) or getattr(move, 'pos', None)

    if player is None:
        icon  = "🎲"
        label = "؟"
    else:
        icon  = getattr(player, 'icon',  "🎲")
        label = getattr(player, 'label', "؟")

    # ── باس ──
    if move.is_pass:
        return f"{icon} {label}: دق 🚫"

    # ── حركة عادية ──
    d = "⬅️ يسار" if move.direction == Direction.LEFT else "➡️ يمين"
    return f"{icon} {label}: {move.tile} {d}"
