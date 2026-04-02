""" 🎲 المساعد العبقري للدومينو - إصدار واجهة الألعاب 🎮 """

import streamlit as st
import streamlit.components.v1 as components
import copy
import hashlib
import math
import time
from collections import Counter, defaultdict
from game_engine.tiles import Tile, Direction, ALL_TILES
from game_engine.state import GameState, Pos, Move
from ai_engine.xray import XRayEngine
from ai_engine.mcts import MCTSEngine
from ai_engine.advisor import GeniusAdvisor
from ui.svg import SVGRenderer as SVG
from ui.helpers import show_message, format_move
from config import Config

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# ═══════════════════════════════════════════════════════
# إعداد الصفحة والأنماط (Game UI)
# ═══════════════════════════════════════════════════════
st.set_page_config(page_title="🎲 دومينو العرّاف", page_icon="🎮", layout="wide")

st.markdown("""
<style>
.stApp{background:linear-gradient(135deg,#0a0a1a,#111128)}
#MainMenu,footer{visibility:hidden}
.stButton>button{border-radius:8px!important;font-weight:bold!important;border:1px solid rgba(255,255,255,0.1)!important}
.stButton>button:hover{transform:scale(1.02)!important;box-shadow:0 4px 15px rgba(0,210,255,0.3)!important}
.game-hud {display:flex; justify-content:space-between; margin-bottom:15px; gap:10px;}
.hud-box {flex:1; background:linear-gradient(180deg,#16213e,#0f172a); border-radius:12px; padding:12px; text-align:center; transition:0.3s;}
.hud-active {box-shadow: 0 0 20px; transform:translateY(-5px);}
.glow-card{background:linear-gradient(135deg,#1B5E20,#2E7D32);border-radius:12px;padding:15px;color:#fff;text-align:center;margin:10px 0;}
.oracle-card{background:linear-gradient(135deg,#311B92,#512DA8);border-radius:12px;padding:15px;color:#fff;margin:10px 0;}
.partner-card{background:linear-gradient(135deg,#01579B,#0277BD);border-radius:12px;padding:15px;color:#fff;margin:10px 0;}
.danger-card{border-radius:12px;padding:12px;color:#fff;margin:10px 0;text-align:center}
.section-title {font-size:1.2em; color:#00d2ff; border-bottom:2px solid #00d2ff; padding-bottom:5px; margin-bottom:15px;}
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════
# دوال مساعدة آمنة والأنظمة الذكية (مخفية للتبسيط)
# ═══════════════════════════════════════════════════════
def safe_ends(gs):
    if gs.board.is_empty: return []
    try:
        raw = gs.board.ends
        if raw is None: return []
        if isinstance(raw, (list, tuple)): return list(raw)
        if isinstance(raw, set): return sorted(list(raw))
        if isinstance(raw, int): return [raw]
        return list(raw)
    except Exception: return []

def safe_float(val, default=0.0):
    if val is None: return default
    try:
        r = float(val)
        return default if math.isnan(r) or math.isinf(r) else r
    except: return default

def safe_int(val, default=0):
    if val is None: return default
    try: return int(val)
    except: return default

def safe_str(val, default='?'):
    if val is None: return default
    try: return str(val)
    except: return default

class DangerMeter:
    def __init__(self, gs): self.gs = gs
    def calculate(self):
        danger = 45
        warnings = []
        for pos in [Pos.RIGHT, Pos.LEFT]:
            count = self.gs.players[pos].count
            if count <= 1: danger += 30; warnings.append(f"🚨 {pos.label} عنده حجر واحد!")
            elif count <= 2: danger += 20; warnings.append(f"⚠️ {pos.label} عنده {count} حجر!")
        
        partner_count = self.gs.players[Pos.PARTNER].count
        if partner_count <= 1: danger -= 25; warnings.append(f"✅ شريكك على وشك الفوز!")
        
        ends_list = safe_ends(self.gs)
        if ends_list:
            can_play = sum(1 for t in self.gs.my_hand if t.a in ends_list or t.b in ends_list)
            if can_play == 0: danger += 25; warnings.append("🚨 لا تملك أحجاراً تركب!")
            if len(ends_list) >= 2 and ends_list[0] == ends_list[1]: danger += 15
        
        if self.gs.passes >= 3: danger += 10
        danger = max(0, min(100, danger))
        
        if danger < 25: level, color, emoji = "آمن 😊", "#4CAF50", "🟢"
        elif danger < 50: level, color, emoji = "حذر 🤔", "#FFC107", "🟡"
        elif danger < 75: level, color, emoji = "خطر ⚠️", "#FF9800", "🟠"
        else: level, color, emoji = "حرج! 🔴", "#F44336", "🔴"
        return {'score': danger, 'level': level, 'color': color, 'emoji': emoji, 'warnings': warnings}

class RegretTracker:
    @staticmethod
    def record(move_label, win_rate, all_moves_data):
        entry = {'move': safe_str(move_label), 'win_rate': safe_float(win_rate, 0.5), 'regret': 0.0}
        if all_moves_data:
            best = max(all_moves_data, key=lambda x: safe_float(x.get('win_pct', 0)))
            entry['best_available'] = safe_str(best.get('move', '?'))
            entry['best_win_rate'] = safe_float(best.get('win_pct', 0))
            entry['regret'] = max(0.0, entry['best_win_rate'] - entry['win_rate'])
        return entry

class SmartCache:
    @staticmethod
    def board_hash(gs):
        parts = [f"{t.a}{t.b}" for t in sorted(gs.board.tiles_on_table, key=lambda x:(x.a, x.b))]
        parts += [f"h{t.a}{t.b}" for t in sorted(gs.my_hand, key=lambda x:(x.a, x.b))]
        parts.append(f"t{gs.turn.value}")
        ends = safe_ends(gs)
        if ends: parts.append(f"e{''.join(map(str, ends))}")
        return hashlib.md5("_".join(parts).encode()).hexdigest()[:16]

    @staticmethod
    def get(cd, gs):
        if not isinstance(cd, dict): return None
        e = cd.get(SmartCache.board_hash(gs))
        if e and isinstance(e, dict) and 'best_move' in e.get('result', {}): return e
        return None

    @staticmethod
    def put(cd, gs, res):
        if isinstance(cd, dict) and isinstance(res, dict):
            cd[SmartCache.board_hash(gs)] = {'result': res, 'timestamp': time.time()}

# ═══════════════════════════════════════════════════════
# Session State
# ═══════════════════════════════════════════════════════
DEFAULTS = {
    'state': None, 'phase': 'setup', 'hand_input': [], 'advice': None, 'log': [],
    'msg': '', 'msg_type': 'info', 'sims': 2000, 'time_limit': 3.5,
    'pending_tile': None, 'starter': Pos.ME, 'regret_history': [], 'smart_cache': {}
}
for k, v in DEFAULTS.items():
    if k not in st.session_state: st.session_state[k] = copy.deepcopy(v) if isinstance(v, (list, dict)) else v

_NO_VALUE = object()
def S(k, v=_NO_VALUE):
    if v is not _NO_VALUE: st.session_state[k] = v
    return st.session_state.get(k)

def reset():
    for k, v in DEFAULTS.items():
        st.session_state[k] = copy.deepcopy(v) if isinstance(v, (list, dict)) else v

def tile_key(t): return (min(t.a, t.b), max(t.a, t.b))

def get_remaining_tiles(gs):
    used = set(tile_key(t) for t in gs.my_hand) | set(tile_key(t) for t in gs.board.tiles_on_table)
    return [t for t in ALL_TILES if tile_key(t) not in used]

def apply_opponent_move(gs, turn, tile, direction):
    m = Move(turn, tile, direction)
    cb = gs.players[turn].count
    if not gs.apply(m): show_message("❌ حركة غير صالحة!", "error"); return False
    if gs.players[turn].count == cb: gs.players[turn].count -= 1
    if gs.players[turn].count <= 0 and not gs.game_over: gs.game_over = True; gs.winner = turn
    S('log', S('log') + [format_move(m)]); S('advice', None); S('pending_tile', None)
    S('msg', f"✅ {turn.label} لعب [{tile.a}|{tile.b}]"); S('msg_type', 'info')
    if gs.game_over: S('phase', 'over')
    S('state', gs); return True

# ═══════════════════════════════════════════════════════
# الشريط الجانبي
# ═══════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## ⚙️ إعدادات اللعبة")
    S('sims', st.slider("عمق التفكير", 500, 10000, S('sims'), 500))
    S('time_limit', st.slider("زمن الرؤية", 1.0, 10.0, S('time_limit'), 0.5))
    if st.button("🔄 لعبة جديدة", use_container_width=True, type="primary"): reset(); st.rerun()

# ═══════════════════════════════════════════════════════
# 📝 الإعداد (Setup)
# ═══════════════════════════════════════════════════════
phase = S('phase')
if phase == 'setup':
    st.markdown('<h1 style="text-align:center; color:#00d2ff;">🎲 تجهيز الجولة</h1>', unsafe_allow_html=True)
    hand = S('hand_input')
    if hand: SVG.hand(hand, title="المختارة")
    
    ALL_TILES_SORTED = sorted(ALL_TILES, key=lambda t: (t.a, t.b))
    for row in range(0, len(ALL_TILES_SORTED), 7):
        cols = st.columns(7)
        for i, t in enumerate(ALL_TILES_SORTED[row:row + 7]):
            with cols[i]:
                sel = t in hand
                if st.button(f"{'✅' if sel else ' '} [{t.a}|{t.b}]", key=f"s_{t.a}_{t.b}", use_container_width=True, type="primary" if sel else "secondary"):
                    h = S('hand_input')
                    if sel: h.remove(t)
                    elif len(h) < 7: h.append(t)
                    S('hand_input', h); st.rerun()

    if len(hand) == 7:
        st.markdown("### 🎯 من يبدأ اللعب؟")
        sc1, sc2, sc3, sc4 = st.columns(4)
        c_str = S('starter')
        with sc1:
            if st.button(f"{'✅' if c_str==Pos.ME else ''} أنا", use_container_width=True, type="primary" if c_str==Pos.ME else "secondary"): S('starter', Pos.ME); st.rerun()
        with sc2:
            if st.button(f"{'✅' if c_str==Pos.RIGHT else ''} اليمين", use_container_width=True, type="primary" if c_str==Pos.RIGHT else "secondary"): S('starter', Pos.RIGHT); st.rerun()
        with sc3:
            if st.button(f"{'✅' if c_str==Pos.PARTNER else ''} الشريك", use_container_width=True, type="primary" if c_str==Pos.PARTNER else "secondary"): S('starter', Pos.PARTNER); st.rerun()
        with sc4:
            if st.button(f"{'✅' if c_str==Pos.LEFT else ''} اليسار", use_container_width=True, type="primary" if c_str==Pos.LEFT else "secondary"): S('starter', Pos.LEFT); st.rerun()

        if st.button("🎮 ادخل ساحة اللعب!", use_container_width=True, type="primary"):
            gs = GameState(); gs.set_my_hand(hand.copy()); gs.turn = S('starter')
            S('state', gs); S('phase', 'playing'); st.rerun()

# ═══════════════════════════════════════════════════════
# 🎮 اللعب (The Arena)
# ═══════════════════════════════════════════════════════
elif phase == 'playing':
    gs: GameState = S('state')
    turn = gs.turn

    # --- 1. HUD: شريط اللاعبين العلوى ---
    colors = {Pos.LEFT: '#FF9800', Pos.PARTNER: '#2196F3', Pos.RIGHT: '#F44336'}
    hud_html = '<div class="game-hud">'
    for pos in [Pos.LEFT, Pos.PARTNER, Pos.RIGHT]:
        p = gs.players[pos]
        clr = colors[pos]
        active = f"border: 2px solid {clr}; box-shadow: 0 0 15px {clr}; transform:scale(1.05);" if turn == pos else f"border: 1px solid rgba(255,255,255,0.1);"
        hud_html += f'''
        <div class="hud-box" style="{active}">
            <div style="color:{clr}; font-weight:bold; font-size:16px;">{pos.label}</div>
            <div style="font-size:24px; font-weight:bold; color:white; margin:5px 0;">🀫 {p.count}</div>
        </div>
        '''
    hud_html += '</div>'
    st.markdown(hud_html, unsafe_allow_html=True)

    # --- 2. ARENA: الطاولة في المنتصف ---
    st.markdown('<div class="section-title">🎯 ساحة اللعب</div>', unsafe_allow_html=True)
    SVG.board(gs.board, h=220)
    if S('msg'): show_message(S('msg'), S('msg_type'))

    st.markdown("<br>", unsafe_allow_html=True)

    # --- 3. SPLIT SCREEN: لوحة التحكم (يمين) + العرّاف (يسار) ---
    # نستخدم st.columns بحيث يأخذ اللعب مساحة أكبر
    col_game, col_ai = st.columns([1.8, 1.2])

    with col_game:
        st.markdown('<div class="section-title">🎮 لوحة التحكم</div>', unsafe_allow_html=True)
        
        # 1. أوامر اللعب (My Turn / Opponent Turn)
        if turn == Pos.ME:
            valid = gs.valid_moves(Pos.ME)
            real = [m for m in valid if not m.is_pass]
            if gs.board.is_empty and not real: real = [Move(Pos.ME, t, Direction.LEFT) for t in gs.my_hand]
            
            st.info("🟢 دورك للعب:")
            if real:
                adv = S('advice')
                bcols = st.columns(min(len(real), 4))
                for i, m in enumerate(real):
                    with bcols[i % len(bcols)]:
                        d = "⬅️" if m.direction == Direction.LEFT else "➡️"
                        is_rec = False
                        if adv and isinstance(adv, dict) and 'best_move' in adv and not adv['best_move'].is_pass:
                            is_rec = (adv['best_move'].tile == m.tile and adv['best_move'].direction == m.direction)
                        
                        if st.button(f"{'⭐' if is_rec else ''} [{m.tile.a}|{m.tile.b}] {d}", key=f"m_{i}_{m.direction.value}", use_container_width=True, type="primary" if is_rec else "secondary"):
                            gs.apply(m); S('log', S('log') + [format_move(m)])
                            S('advice', None); S('msg', f"✅ لعبت {m.tile}"); S('msg_type', 'success')
                            if gs.game_over: S('phase', 'over')
                            S('state', gs); st.rerun()

            if any(m.is_pass for m in valid):
                if st.button("🚫 دق (تخطي)", use_container_width=True, type="primary"):
                    gs.apply(Move(Pos.ME, None, None)); S('log', S('log') + ["🟢 أنت: دق 🚫"])
                    S('advice', None); S('state', gs)
                    if gs.game_over: S('phase', 'over')
                    st.rerun()
        
        else:
            # دور الخصم
            st.warning(f"⏳ بانتظار حركة {turn.label}...")
            pending = S('pending_tile')
            if pending is not None:
                st.markdown(f"**أين وضع [{pending.a}|{pending.b}]؟**")
                c1, c2 = st.columns(2)
                if c1.button("⬅️ يسار", use_container_width=True): apply_opponent_move(gs, turn, pending, Direction.LEFT); st.rerun()
                if c2.button("يمين ➡️", use_container_width=True): apply_opponent_move(gs, turn, pending, Direction.RIGHT); st.rerun()
                if st.button("❌ إلغاء", use_container_width=True): S('pending_tile', None); st.rerun()
            else:
                remaining = get_remaining_tiles(gs)
                playable = remaining if gs.board.is_empty else [t for t in remaining if gs.board.can_play(t)]
                if playable:
                    playable.sort(key=lambda t: (t.a, t.b), reverse=True)
                    st.caption(f"اختر الحجر الذي لعبه:")
                    ncols = min(len(playable), 5)
                    for row_start in range(0, len(playable), ncols):
                        cols = st.columns(ncols)
                        for j, t in enumerate(playable[row_start:row_start + ncols]):
                            with cols[j]:
                                if st.button(f"[{t.a}|{t.b}]", key=f"o_{t.a}_{t.b}_{turn.value}", use_container_width=True):
                                    if gs.board.is_empty: apply_opponent_move(gs, turn, t, Direction.LEFT); st.rerun()
                                    else:
                                        dirs = gs.board.can_play(t)
                                        if len(dirs) == 1: apply_opponent_move(gs, turn, t, dirs[0]); st.rerun()
                                        elif len(dirs) >= 2: S('pending_tile', t); st.rerun()
                else:
                    st.info("لا توجد أحجار تركب.")
                if st.button("🚫 دق (تخطي)", use_container_width=True, type="primary"):
                    gs.apply(Move(turn, None, None)); S('log', S('log') + [f"🚫 {turn.label} دق"])
                    S('state', gs); st.rerun()

        # 2. يدي في أسفل قسم اللعب
        st.markdown("---")
        st.markdown("**🃏 أحجارك:**")
        SVG.hand(gs.my_hand, glowing=[i for i,t in enumerate(gs.my_hand) if gs.board.is_empty or gs.board.can_play(t)] if turn == Pos.ME else [])


    with col_ai:
        st.markdown('<div class="section-title">🧠 أدوات العرّاف</div>', unsafe_allow_html=True)
        
        # مؤشر الخطر
        if not gs.board.is_empty:
            danger = DangerMeter(gs).calculate()
            st.markdown(f'''
            <div class="danger-card" style="background:linear-gradient(135deg, #1a1a2e, #16213e); border:1px solid {danger['color']};">
                <div style="font-size:18px; font-weight:bold; color:{danger['color']};">{danger['emoji']} مؤشر الخطر: {danger['level']} ({danger['score']}%)</div>
            </div>
            ''', unsafe_allow_html=True)
        
        # زر الذكاء الاصطناعي
        if turn == Pos.ME:
            cached = SmartCache.get(S('smart_cache'), gs)
            if st.button(f"🚀 تشغيل العرّاف (MCTS){' ⚡' if cached else ''}", use_container_width=True, type="primary"):
                if cached: S('advice', cached['result']); st.rerun()
                else:
                    with st.spinner("يحلل..."):
                        adv = GeniusAdvisor(gs, Config(MCTS_SIMULATIONS=S('sims'), MCTS_TIME_LIMIT=S('time_limit'))).advise()
                        S('advice', adv); SmartCache.put(S('smart_cache'), gs, adv); st.rerun()
            
            adv = S('advice')
            if adv and 'best_move' in adv:
                bm = adv['best_move']
                st.markdown(f'''
                <div class="glow-card">
                    <div style="color:#A5D6A7;font-size:12px;">نصيحة العراف:</div>
                    <div style="font-size:20px;font-weight:bold;">{"دق 🚫" if bm.is_pass else f"{bm.tile} {'⬅️' if bm.direction==Direction.LEFT else '➡️'}"}</div>
                    <div style="font-size:14px;margin-top:5px;">فرصة الفوز: {adv.get('win_rate',0):.0%}</div>
                </div>
                ''', unsafe_allow_html=True)

        # استنتاجات سريعة
        xray = XRayEngine(gs)
        rep = xray.xray_report()
        st.markdown('<div class="oracle-card">', unsafe_allow_html=True)
        st.markdown("**🤝 بوصلة الشريك:**")
        partner_passed = gs.players[Pos.PARTNER].passed_on
        if partner_passed: st.write(f"يفتقد: {','.join(map(str, partner_passed))}")
        else: st.write("أوراقه غير مكشوفة.")
        st.markdown('</div>', unsafe_allow_html=True)

        with st.expander("📜 سجل المعركة"):
            for i, e in enumerate(reversed(S('log')[-10:])): st.markdown(f"`{e}`")


# ═══════════════════════════════════════════════════════
# 🏆 النهاية
# ═══════════════════════════════════════════════════════
elif phase == 'over':
    gs = S('state')
    st.markdown('<h1 style="text-align:center; color:#4CAF50;">🏁 انتهت المعركة!</h1>', unsafe_allow_html=True)
    SVG.board(gs.board, h=220)
    
    my_pts = sum(t.total for t in gs.my_hand)
    pts_on_board = sum(t.total for t in gs.board.tiles_on_table)
    others_total = max(0, 168 - pts_on_board - my_pts)
    
    c1, c2 = st.columns(2)
    c1.metric("🟢 نقاط يدك", my_pts)
    c2.metric("❓ مجموع الآخرين", others_total)
    
    if st.button("🔄 العب مباراة جديدة", use_container_width=True, type="primary"): reset(); st.rerun()

