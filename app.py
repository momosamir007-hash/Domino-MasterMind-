""" 🎲 المساعد العبقري للدومينو """

import streamlit as st
import streamlit.components.v1 as components
import copy
from game_engine.tiles import Tile, Direction, ALL_TILES
from game_engine.state import GameState, Pos, Move
from ai_engine.xray import XRayEngine
from ai_engine.mcts import MCTSEngine
from ai_engine.advisor import GeniusAdvisor
from ui.svg import SVGRenderer as SVG
from ui.helpers import show_message, format_move
from config import Config

# ─── إعداد ───
st.set_page_config(page_title="🎲 دومينو عبقري", page_icon="🎲", layout="wide")

st.markdown("""
<style>
.stApp{background:linear-gradient(135deg,#0a0a1a,#111128)}
#MainMenu,footer{visibility:hidden}
.stButton>button{border-radius:10px!important;font-weight:600!important}
.stButton>button:hover{transform:translateY(-2px)!important}
[data-testid="stMetric"]{background:rgba(255,255,255,.04);border-radius:10px;padding:14px;border:1px solid rgba(255,255,255,.08)}
.glow-card{background:linear-gradient(135deg,#1B5E20,#2E7D32);border-radius:14px;padding:18px;color:#fff;text-align:center;margin:10px 0;box-shadow:0 6px 25px rgba(46,125,50,.3)}
.dir-btn{font-size:1.3em!important;padding:16px!important;border:2px solid rgba(255,255,255,.2)!important}
</style>
""", unsafe_allow_html=True)


# ─── Session State ───
DEFAULTS = {
    'state': None,
    'phase': 'setup',
    'hand_input': [],
    'rec': None,
    'analysis': None,
    'advice': None,
    'log': [],
    'msg': '',
    'msg_type': 'info',
    'sims': 1500,
    'time_limit': 3.0,
    'show_xray': True,
    'pending_tile': None,
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = copy.deepcopy(v) if isinstance(v, (list, dict)) else v


# 🟢 دالة مساعدة آمنة للقراءة والكتابة في session_state
_NO_VALUE = object()
def S(k, v=_NO_VALUE):
    if v is not _NO_VALUE:
        st.session_state[k] = v
    return st.session_state.get(k)


def reset():
    for k, v in DEFAULTS.items():
        st.session_state[k] = copy.deepcopy(v) if isinstance(v, (list, dict)) else v


# ─── دوال مساعدة ذكية ───
def tile_key(t):
    """مفتاح فريد لكل حجر"""
    if isinstance(t, Tile):
        return (min(t.a, t.b), max(t.a, t.b))
    return (min(t[0], t[1]), max(t[0], t[1]))


def get_remaining_tiles(gs):
    """الأحجار المتبقية = كل الأحجار − يدي − الملعوبة فعلياً على الطاولة"""
    used = set()
    for t in gs.my_hand:
        used.add(tile_key(t))
    for t in gs.board.tiles_on_table:
        used.add(tile_key(t))
    return [t for t in ALL_TILES if tile_key(t) not in used]


def apply_opponent_move(gs, turn, tile, direction):
    """يطبّق حركة خصم/شريك بشكل كامل وآمن"""
    m = Move(turn, tile, direction)
    count_before = gs.players[turn].count
    
    ok = gs.apply(m)
    if not ok:
        show_message("❌ فشل تطبيق الحركة داخلياً!", "error")
        return False
        
    if gs.players[turn].count == count_before:
        gs.players[turn].count -= 1
        
    # 🟢 ✅ إصلاح: التحقق من إعلان الفوز للخصوم والشريك عند انتهاء حجارتهم
    if gs.players[turn].count <= 0 and not gs.game_over:
        gs.game_over = True
        gs.winner = turn
        
    S('log', S('log') + [format_move(m)])
    S('advice', None)
    S('pending_tile', None)
    
    dir_label = "⬅️ يسار" if direction == Direction.LEFT else "➡️ يمين"
    S('msg', f"✅ {turn.label} لعب [{tile.a}|{tile.b}] {dir_label}")
    S('msg_type', 'info')
    
    if gs.game_over:
        S('phase', 'over')
        
    S('state', gs)
    return True


# ═══ الشريط الجانبي ═══
with st.sidebar:
    st.markdown("## 🧠 المساعد العبقري")
    st.markdown("---")
    S('sims', st.slider("محاكاات AI", 200, 5000, 1500, 100))
    S('time_limit', st.slider("وقت التحليل", 1.0, 8.0, 3.0, 0.5))
    S('show_xray', st.checkbox("🔬 عرض X-Ray", True))
    st.markdown("---")
    if st.button("🔄 جديدة", use_container_width=True, type="primary"):
        reset()
        st.rerun()
    with st.expander("📖 القواعد"):
        st.markdown("4 لاعبين • 7 أحجار • الكل يدق = قفل • أول من يخلّص = فوز")

# ═══ العنوان ═══
st.markdown(
    '<h1 style="text-align:center;background:linear-gradient(90deg,#00d2ff,#3a7bd5);'
    '-webkit-background-clip:text;-webkit-text-fill-color:transparent;font-size:2.2em">'
    '🎲 المساعد العبقري للدومينو</h1>',
    unsafe_allow_html=True,
)

phase = S('phase')
ALL_TILES_SORTED = sorted(ALL_TILES, key=lambda t: (t.a, t.b))


# ═══════════════════════════════════
# 📝 الإعداد
# ═══════════════════════════════════
if phase == 'setup':
    st.markdown("### 📝 اختر أحجارك السبعة")
    hand = S('hand_input')
    if hand:
        SVG.hand(hand, title="المختارة")
        st.success(f"✅ {len(hand)}/7")
    for row in range(0, len(ALL_TILES_SORTED), 7):
        cols = st.columns(7)
        for i, t in enumerate(ALL_TILES_SORTED[row:row + 7]):
            with cols[i]:
                sel = t in hand
                if st.button(
                    f"{'✅' if sel else ' '} [{t.a}|{t.b}]",
                    key=f"s_{t.a}_{t.b}",
                    use_container_width=True,
                    type="primary" if sel else "secondary",
                ):
                    h = S('hand_input')
                    if sel:
                        h.remove(t)
                    elif len(h) < 7:
                        h.append(t)
                    S('hand_input', h)
                    st.rerun()
    if len(hand) == 7:
        _, c, _ = st.columns([1, 2, 1])
        with c:
            if st.button("🎮 ابدأ!", use_container_width=True, type="primary"):
                gs = GameState()
                gs.set_my_hand(hand.copy())
                S('state', gs)
                S('phase', 'playing')
                st.rerun()


# ═══════════════════════════════════
# 🎮 اللعب
# ═══════════════════════════════════
elif phase == 'playing':
    gs: GameState = S('state')
    if not gs:
        st.error("خطأ!")
        st.stop()
    if S('msg'):
        show_message(S('msg'), S('msg_type'))

    st.markdown("### 🎯 الطاولة")
    SVG.board(gs.board, h=170)

    with st.expander("👥 اللاعبون", expanded=True):
        SVG.players(gs, w=700, h=380)

    st.markdown("---")
    turn = gs.turn

    # ═══════════════════════════════════
    # 🎯 دوري
    # ═══════════════════════════════════
    if turn == Pos.ME:
        st.markdown("### 🎯 دورك!")
        valid = gs.valid_moves(Pos.ME)
        real = [m for m in valid if not m.is_pass]

        if gs.board.is_empty and not real:
            real = [Move(Pos.ME, t, Direction.LEFT) for t in gs.my_hand]

        ca, cr = st.columns([1, 2])
        with ca:
            if st.button("🧠 حلّل!", use_container_width=True, type="primary"):
                with st.spinner("⏳ العبقري يفكر..."):
                    cfg = Config()
                    cfg.MCTS_SIMULATIONS = S('sims')
                    cfg.MCTS_TIME_LIMIT = S('time_limit')
                    advisor = GeniusAdvisor(gs, cfg)
                    advice = advisor.advise()
                    S('advice', advice)
                    st.rerun()

        with cr:
            adv = S('advice')
            if adv:
                bm = adv['best_move']
                wr = adv['win_rate']
                exp = adv['explanation']
                if bm.is_pass:
                    txt = "دق 🚫"
                else:
                    d = "⬅️ يسار" if bm.direction == Direction.LEFT else "➡️ يمين"
                    txt = f"{bm.tile} {d}"
                wr_color = "#4CAF50" if wr >= 0.6 else "#FFC107" if wr >= 0.4 else "#F44336"
                st.markdown(f'''
                <div class="glow-card">
                    <div style="font-size:12px;color:#A5D6A7">🧠 العبقري يقول:</div>
                    <div style="font-size:24px;font-weight:bold;margin:8px 0">⭐ {txt}</div>
                    <div style="font-size:18px;color:{wr_color};margin:4px 0">نسبة الفوز: {wr:.0%}</div>
                    <div style="font-size:13px;color:#C8E6C9;margin-top:6px">💡 {exp}</div>
                </div>
                ''', unsafe_allow_html=True)
                if adv['reasons']:
                    with st.expander("📝 لماذا هذه الحركة؟", expanded=True):
                        for r in adv['reasons']:
                            st.markdown(f"- {r}")
                if adv['all_moves']:
                    SVG.analysis_chart(adv['all_moves'])

        if S('show_xray'):
            with st.expander("🔬 X-Ray: أحجار الخصوم"):
                xray = XRayEngine(gs)
                report = xray.xray_report()
                tabs = st.tabs([p.label for p in [Pos.RIGHT, Pos.PARTNER, Pos.LEFT]])
                for tab, pos in zip(tabs, [Pos.RIGHT, Pos.PARTNER, Pos.LEFT]):
                    with tab:
                        r = report[pos]
                        st.caption(f"أحجار: {r['count']} | مستحيل: {r['impossible_count']} حجر")
                        if r['cant_have']:
                            st.error(f"🚫 ما عنده: {', '.join(map(str, r['cant_have']))}")
                        if r['certain']:
                            st.success(f"✅ مؤكد عنده: {', '.join(str(t) for t in r['certain'])}")
                        for tile, prob in r['likely'][:8]:
                            if prob < 0.01:
                                continue
                            c1, c2 = st.columns([1, 4])
                            with c1:
                                st.write(f"**{tile}**")
                            with c2:
                                st.progress(min(prob, 1.0), text=f"{prob:.0%}")

        st.markdown("#### 👇 اختر:")
        if real:
            adv = S('advice')
            bcols = st.columns(min(len(real), 4))
            for i, m in enumerate(real):
                with bcols[i % len(bcols)]:
                    d = "⬅️" if m.direction == Direction.LEFT else "➡️"
                    is_rec = (
                        adv and not adv['best_move'].is_pass and
                        adv['best_move'].tile == m.tile and
                        adv['best_move'].direction == m.direction
                    )
                    if st.button(
                        f"{'⭐' if is_rec else ''} [{m.tile.a}|{m.tile.b}] {d}",
                        key=f"m_{i}_{m.direction.value}",
                        use_container_width=True,
                        type="primary" if is_rec else "secondary",
                    ):
                        if gs.turn != Pos.ME:
                            S('msg', "⚠️ ليس دورك الآن!")
                            S('msg_type', 'warning')
                            st.rerun()
                        else:
                            ok = gs.apply(m)
                            if ok:
                                S('log', S('log') + [format_move(m)])
                                S('advice', None)
                                S('msg', f"✅ لعبت {m.tile}")
                                S('msg_type', 'success')
                                if gs.game_over:
                                    S('phase', 'over')
                                S('state', gs)
                                st.rerun()
                            else:
                                S('msg', "❌ فشل تطبيق الحركة!")
                                S('msg_type', 'error')
                                st.rerun()
        if any(m.is_pass for m in valid):
            if st.button("🚫 دق", use_container_width=True):
                if gs.turn == Pos.ME:
                    gs.apply(Move(Pos.ME, None, None))
                    S('log', S('log') + ["🟢 أنت: دق 🚫"])
                    S('advice', None)
                    S('msg', "🚫 دقيت")
                    S('msg_type', 'warning')
                    if gs.game_over:
                        S('phase', 'over')
                    S('state', gs)
                    st.rerun()

    # ═══════════════════════════════════
    # ★ دور الخصم / الشريك
    # ═══════════════════════════════════
    else:
        name = turn.label
        opp_count = gs.players[turn].count
        st.markdown(f"### {turn.icon} دور: **{name}** ({opp_count} أحجار)")

        pending = S('pending_tile')
        if pending is not None:
            st.markdown(f"""
            <div style="background:linear-gradient(135deg,#E65100,#FF9800);border-radius:14px;
            padding:20px;text-align:center;color:#fff;margin:10px 0">
                <div style="font-size:14px">🤔 الحجر يركب في الجهتين!</div>
                <div style="font-size:28px;font-weight:bold;margin:8px 0">[{pending.a}|{pending.b}]</div>
                <div style="font-size:13px">وين حطّه {name}؟</div>
            </div>
            """, unsafe_allow_html=True)
            c1, _, c2 = st.columns([2, 1, 2])
            btn_key = f"{pending.a}_{pending.b}_{turn.value}"
            with c1:
                if st.button("⬅️ في اليسار", key=f"pend_left_{btn_key}", use_container_width=True, type="primary"):
                    if apply_opponent_move(gs, turn, pending, Direction.LEFT):
                        st.rerun()
            with c2:
                if st.button("في اليمين ➡️", key=f"pend_right_{btn_key}", use_container_width=True, type="primary"):
                    if apply_opponent_move(gs, turn, pending, Direction.RIGHT):
                        st.rerun()
            st.markdown("")
            if st.button("❌ إلغاء واختيار حجر آخر", key=f"pend_cancel_{btn_key}", use_container_width=True):
                S('pending_tile', None)
                st.rerun()

        else:
            remaining = get_remaining_tiles(gs)
            if gs.board.is_empty:
                playable = remaining
            else:
                playable = [t for t in remaining if gs.board.can_play(t)]
            if playable:
                playable.sort(key=lambda t: (t.a, t.b), reverse=True)
                st.caption(
                    f"👇 اضغط على الحجر الذي لعبه **{name}** "
                    f"• {len(playable)} حجر متاح من أصل {len(remaining)} متبقي:"
                )
                ncols = min(len(playable), 5)
                for row_start in range(0, len(playable), ncols):
                    row_tiles = playable[row_start:row_start + ncols]
                    cols = st.columns(ncols)
                    for j, t in enumerate(row_tiles):
                        with cols[j]:
                            if st.button(
                                f"[{t.a}|{t.b}]",
                                key=f"opp_{t.a}_{t.b}_{turn.value}",
                                use_container_width=True,
                            ):
                                if gs.board.is_empty:
                                    if apply_opponent_move(gs, turn, t, Direction.LEFT):
                                        st.rerun()
                                else:
                                    dirs = gs.board.can_play(t)
                                    if len(dirs) == 1:
                                        if apply_opponent_move(gs, turn, t, dirs[0]):
                                            st.rerun()
                                    elif len(dirs) >= 2:
                                        S('pending_tile', t)
                                        st.rerun()
                                    else:
                                        S('msg', "❌ خطأ: الحجر لا يركب!")
                                        S('msg_type', 'error')
                                        st.rerun()
            else:
                st.info(
                    "💡 لا توجد أحجار متبقية تركب على أطراف الطاولة الحالية.\n\n"
                    "يجب على هذا اللاعب التخطي (باس)."
                )

            st.markdown("---")
            if st.button(
                f"🚫 {name} دق (باس)",
                key=f"ps_{turn.value}",
                type="primary",
                use_container_width=True,
            ):
                if gs.turn == turn:
                    gs.apply(Move(turn, None, None))
                    S('log', S('log') + [f"{turn.icon} {turn.label}: دق 🚫"])
                    S('advice', None)
                    S('msg', f"🚫 {name} دق")
                    S('msg_type', 'warning')
                    if gs.game_over:
                        S('phase', 'over')
                    S('state', gs)
                    st.rerun()

    st.markdown("---")
    st.markdown("### 🃏 أحجارك")
    playable_idx = []
    if not gs.board.is_empty:
        playable_idx = [i for i, t in enumerate(gs.my_hand) if gs.board.can_play(t)]
    else:
        playable_idx = list(range(len(gs.my_hand)))
    if turn != Pos.ME:
        playable_idx = []
    SVG.hand(gs.my_hand, glowing=playable_idx, title="يدك")

    with st.expander("📜 السجل"):
        log = S('log')
        if log:
            for i, e in enumerate(reversed(log[-20:]), 1):
                st.markdown(f"`{len(log) - i + 1}.` {e}")
        else:
            st.caption("لم تُسجّل حركات بعد.")


# ═══════════════════════════════════
# 🏆 النهاية
# ═══════════════════════════════════
elif phase == 'over':
    gs = S('state')
    
    # 🟢 التحقق مما إذا كانت اللعبة قد انتهت بالقفل
    is_locked = gs.passes >= 4
    
    if not is_locked:
        win = gs.winner and gs.winner.is_friend
        if win:
            st.balloons()
            st.markdown(
                '<div style="text-align:center;padding:40px;background:linear-gradient(135deg,#1B5E20,#4CAF50);'
                'border-radius:18px;color:#fff;margin:20px 0"><h1>🏆 مبروك! فريقك فاز!</h1></div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div style="text-align:center;padding:40px;background:linear-gradient(135deg,#B71C1C,#E53935);'
                'border-radius:18px;color:#fff;margin:20px 0"><h1>😔 خسارة</h1></div>',
                unsafe_allow_html=True,
            )
    else:
        st.markdown(
            '<div style="text-align:center;padding:40px;background:linear-gradient(135deg,#E65100,#FF9800);'
            'border-radius:18px;color:#fff;margin:20px 0"><h1>🔒 اللعبة مقفولة (تعادل)!</h1></div>',
            unsafe_allow_html=True,
        )
        
    st.markdown("### 🎯 الطاولة النهائية")
    SVG.board(gs.board)
    
    # 🟢 ✅ إصلاح نظام عد النقاط الذكي 
    st.markdown("---")
    st.markdown("### 📊 حساب النقاط النهائي")
    
    # حساب مجموع النقاط الإجمالي 168 وطرح الملعوب لمعرفة المتبقي
    my_pts = sum(t.total for t in gs.my_hand)
    pts_on_board = sum(t.total for t in gs.board.tiles_on_table)
    unplayed_total = 168 - pts_on_board
    others_total = unplayed_total - my_pts
    
    st.info(f"💡 بما أن النظام لا يرى أوراق الخصوم، قمنا بحساب النقاط أوتوماتيكياً: **{unplayed_total} نقطة** لم تُلعب في هذه المباراة.")
    
    c1, c2 = st.columns(2)
    with c1:
        st.metric("🟢 نقاط يدك", f"{my_pts}")
    with c2:
        st.metric("❓ نقاط البقية (الخصوم + الشريك)", f"{others_total}")
        
    st.markdown("#### 🔢 لمعرفة النتيجة الدقيقة للمباراة، أدخل ما تبقى في أيديهم:")
    cc1, cc2 = st.columns(2)
    with cc1:
        opp_pts = st.number_input("🔴 مجموع نقاط الخصوم (يمين + يسار):", min_value=0, max_value=others_total, value=min(others_total, 10))
    with cc2:
        # نقاط الشريك هي الباقي تلقائياً
        default_part = max(0, others_total - opp_pts)
        part_pts = st.number_input("🔵 نقاط شريكك:", min_value=0, max_value=others_total, value=default_part)
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    if not is_locked:
        if win:
            st.markdown(f'<div class="glow-card" style="background:linear-gradient(135deg,#1B5E20,#2E7D32);">🎉 فريقك يسجل: <b>{opp_pts}</b> نقطة (من الخصوم)!</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="glow-card" style="background:linear-gradient(135deg,#B71C1C,#E53935);">🔴 الخصوم يسجلون: <b>{my_pts + part_pts}</b> نقطة (من فريقك)!</div>', unsafe_allow_html=True)
    else:
        our_team = my_pts + part_pts
        their_team = opp_pts
        if our_team < their_team:
            st.markdown(f'<div class="glow-card" style="background:linear-gradient(135deg,#1B5E20,#2E7D32);">🏆 فريقك فاز بالقفل! (نقاطكم {our_team} أقل من {their_team}) <br> وسجلتم: <b>{their_team}</b> نقطة!</div>', unsafe_allow_html=True)
        elif their_team < our_team:
            st.markdown(f'<div class="glow-card" style="background:linear-gradient(135deg,#B71C1C,#E53935);">🔴 الخصوم فازوا بالقفل! (نقاطهم {their_team} أقل من {our_team}) <br> وسجلوا: <b>{our_team}</b> نقطة!</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="glow-card" style="background:linear-gradient(135deg,#E65100,#FF9800);">🤝 تعادل تام في النقاط! ({our_team} لكلا الفريقين) - لا أحد يسجل.</div>', unsafe_allow_html=True)

    with st.expander("📜 سجل الحركات المكتمل"):
        log = S('log')
        if log:
            for i, e in enumerate(log, 1):
                st.markdown(f"`{i}.` {e}")

    st.markdown("---")
    if st.button("🔄 لعبة جديدة", use_container_width=True, type="primary"):
        reset()
        st.rerun()
