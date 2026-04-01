"""أدوات واجهة بسيطة"""
import streamlit as st
from game_engine.state import Move, Pos
from game_engine.tiles import Direction

def show_message(msg, mtype="info"):
    {
        "info": st.info,
        "success": st.success,
        "warning": st.warning,
        "error": st.error
    }.get(mtype, st.info)(msg)

def format_move(move: Move) -> str:
    icon = move.who.icon
    name = move.who.label
    if move.is_pass:
        return f"{icon} {name}: دق 🚫"
    d = "⬅️" if move.direction == Direction.LEFT else "➡️"
    return f"{icon} {name}: {move.tile} {d}"
