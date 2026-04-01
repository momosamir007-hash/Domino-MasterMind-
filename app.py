"""🎲 المساعد العبقري للدومينو — النسخة النهائية"""

import streamlit as st
import copy
from game_engine.tiles import Tile, Direction, ALL_TILES
from game_engine.state import GameState, Pos, Move
from ai_engine.xray import XRayEngine
from ai_engine.advisor import GeniusAdvisor
from ui.svg import SVGRenderer as SVG
from ui.helpers import show_message, format_move
from config import Config

# ─── إعداد الصفحة ───
st.set_page_config(page_title="🎲 دومينو عبقري", page_icon="🎲", layout="wide")

st.markdown("""
<style>
    .stApp{background:linear-gradient(135deg,#0a0a1a,#111128)}
    #MainMenu,footer{visibility:hidden}
    .stButton>button{border-radius:10px!important;font-weight:600!important;
        transition:all .2s!important}
    .stButton>button:hover{transform:translateY(-2px)!important;
        box-shadow:0 4px 15px rgba(0,0,0,.3)!important}
    [data-testid="stMetric"]{background:rgba(255,255,255,.04);
        border-radius:10px;padding:14px;border:1px solid rgba(255,255,255,.08)}
    .glow-card{background:linear-gradient(135deg,#1B5E20,#2E7D32);
        border-radius:14px;padding:18px;color:#fff;text-align:center;
        margin:10px 0;box-shadow:0 6px 25px rgba(46,125,50,.3)}
</style>
""", unsafe_allow_html=True)

# ─── Session State ───
DEFAULTS = {
    'state': None,
    'phase': 'setup',
    'hand_input': [],
    'advice': None,
    'log': [],
    'msg': '',
    'msg_type': 'info',
    'sims': 1500,
    'time_limit': 3.0,
    'show_xray': True,
    'all_played': [],
    'pending_tile': None,
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = copy.deepcopy(v) if isinstance(v, (list, dict)) else v


def S(k, v=None):
    if v is not None:
        st.session_state[k] = v
    return st.session_state.get(k)


def reset():
    for k, v in DEFAULTS.items():
        st.session_state[k] = copy.deepcopy(v) if isinstance(v, (list, dict)) else v


# ════════════════════════════════════
#  دوال ذكية للإدخال الأوتوماتيكي
# ════════════════════════════════════

def tile_key(t):
    if isinstance(t, Tile):
        return (min(t.a, t.b), max(t.a, t.b))
    return (min(t[0], t[1]), max(t[0], t[1]))


def get_remaining_tiles(gs):
    """كل الأحجار المتبقية (ليست في يدي ولا ملعوبة)"""
    used = set()
    for t in gs.my_hand:
        used.add(tile_key(t))
    for ab in S('all_played'):
        used.add(tile_key(ab))
    return [t for t in ALL_SORTED if tile_key(t) not in used]


def get_possible_directions(gs, tile):
    """أين يمكن وضع هذا الحجر؟"""
    if gs.board.is_empty:
        return [Direction.LEFT]
    dirs = []
    if tile.has(gs.board.left):
        dirs.append(Direction.LEFT)
    if tile.has(gs.board.right):
        dirs.append(Direction.RIGHT)
    return dirs


def track_played(tile):
    ap = S('all_played')
    ap.append((tile.a, tile.b))
    S('all_played', ap)


def apply_opponent_move(gs, turn, tile, direction):
    """تطبيق حركة خصم/شريك"""
    m = Move(turn, tile, direction)
    gs.players[turn].count -= 1
    gs.players[turn].played.append(tile)
    gs.apply(m)
    track_played(tile)
    S('log', S('log') + [format_move(m)])
    S('advice', None)
    S('pending_tile', None)
    d_label = "⬅️ يسار" if direction == Direction.LEFT else "➡️ يمين"
    S('msg', f"✅ {turn.label} لعب {tile} {d_label}")
    S('msg_type', 'info')
    if gs.game_over:
        S('phase', 'over')


# ─── ترتيب الأحجار ───
ALL_SORTED = sorted(ALL_TILES, key=lambda t: (t.a, t.b))

# ═══ الشريط الجانبي ═══
with st.sidebar:
    st.markdown("## 🧠 المساعد العبقري")
    st.markdown("---")
    S('sims', st.slider("محاكاات AI", 200, 5000, 1500, 100))
    S('time_limit', st.slider("⏱️ وقت التحليل", 1.0, 8.0, 3.0, 0.5))
    S('show_xray', st.checkbox("🔬 عرض X-Ray", True))
    st.markdown("---")
    if st.button("🔄 لعبة جديدة", use_container_width=True, type="primary"):
        reset()
        st.rerun()
    with st.expander("📖 القواعد"):
        st.markdown("""
        - 4 لاعبين (فريقين)
        - 7 أحجار لكل لاعب
        - الكل يدق = قفل
        - أول من يخلّص = فوز
        """)

# ═══ العنوان ═══
st.markdown(
    '<h1 style="text-align:center;background:linear-gradient(90deg,#00d2ff,#3a7bd5);'
    '-webkit-background-clip:text;-webkit-text-fill-color:transparent;'
    'font-size:2.2em">🎲 المساعد العبقري للدومينو</h1>',
    unsafe_allow_html=True,
)

phase = S('phase')

# ═══════════════════════════════════
#  📝 مرحلة الإعداد
# ═══════════════════════════════════
if phase == 'setup':
    st.markdown("### 📝 اختر أحجارك السبعة")
    hand = S('hand_input')

    if hand:
        SVG.hand(hand, title="المختارة")
        st.success(f"✅ {len(hand)}/7")

    for row_start in range(0, len(ALL_SORTED), 7):
        cols = st.columns(7)
        for i, t in enumerate(ALL_SORTED[row_start:row_start + 7]):
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
            if st.button("🎮 ابدأ اللعب!", use_container_width=True, type="primary"):
                gs = GameState()
                gs.set_my_hand(hand.copy())
                S('state', gs)
                S('phase', 'playing')
                st.rerun()

# ═══════════════════════════════════
#  🎮 مرحلة اللعب
# ═══════════════════════════════════
elif phase == 'playing':
    gs: GameState = S('state')
    if not gs:
        st.error("خطأ في حالة اللعبة!")
        st.stop()

    if S('msg'):
        show_message(S('msg'), S('msg_type'))
        S('msg', '')

    # ─── الطاولة ───
    st.markdown("### 🎯 الطاولة")
    SVG.board(gs.board, w=900, h=170)

    # ─── اللاعبون ───
    with st.expander("👥 اللاعبون", expanded=True):
        SVG.players(gs, w=700, h=380)

    st.markdown("---")
    turn = gs.turn

    # ═══════════════════════════════
    #  🎯 دوري
    # ═══════════════════════════════
    if turn == Pos.ME:
        st.markdown("### 🎯 دورك!")
        valid = gs.valid_moves(Pos.ME)
        real = [m for m in valid if not m.is_pass]

        # ── زر التحليل + النتيجة ──
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
                wr_color = "#4CAF50" if wr >= .6 else "#FFC107" if wr >= .4 else "#F44336"
                st.markdown(f'''
                <div class="glow-card">
                    <div style="font-size:12px;color:#A5D6A7">🧠 العبقري يقول:</div>
                    <div style="font-size:24px;font-weight:bold;margin:8px 0">⭐ {txt}</div>
                    <div style="font-size:18px;color:{wr_color};margin:4px 0">
                        نسبة الفوز: {wr:.0%}</div>
                    <div style="font-size:13px;color:#C8E6C9;margin-top:6px">💡 {exp}</div>
                </div>
                ''', unsafe_allow_html=True)

                if adv['reasons']:
                    with st.expander("📝 لماذا هذه الحركة؟", expanded=True):
                        for r in adv['reasons']:
                            st.markdown(f"- {r}")
                if adv['all_moves']:
                    SVG.analysis_chart(adv['all_moves'])

        # ── X-Ray ──
        if S('show_xray'):
            with st.expander("🔬 X-Ray: أحجار الخصوم"):
                xray = XRayEngine(gs)
                report = xray.xray_report()
                tabs = st.tabs([p.label for p in [Pos.RIGHT, Pos.PARTNER, Pos.LEFT]])
                for tab, pos in zip(tabs, [Pos.RIGHT, Pos.PARTNER, Pos.LEFT]):
                    with tab:
                        r = report[pos]
                        st.caption(f"أحجار: {r['count']} | مستحيل: {r['impossible_count']}")
                        if r['cant_have']:
                            st.error(f"🚫 ما عنده: {', '.join(map(str, r['cant_have']))}")
                        if r['certain']:
                            st.success(
                                f"✅ مؤكد: {', '.join(str(t) for t in r['certain'])}")
                        for tile, prob in r['likely'][:8]:
                            if prob < 0.01:
                                continue
                            c1, c2 = st.columns([1, 4])
                            with c1:
                                st.write(f"**{tile}**")
                            with c2:
                                st.progress(min(prob, 1.0), text=f"{prob:.0%}")

        # ── أزرار الحركات ──
        st.markdown("#### 👇 اختر حركتك:")
        if real:
            adv = S('advice')
            bcols = st.columns(min(len(real), 4))
            for i, m in enumerate(real):
                with bcols[i % len(bcols)]:
                    d = "⬅️" if m.direction == Direction.LEFT else "➡️"
                    is_rec = (
                        adv and not adv['best_move'].is_pass
                        and adv['best_move'].tile == m.tile
                        and adv['best_move'].direction == m.direction
                    )
                    if st.button(
                        f"{'⭐' if is_rec else ''} [{m.tile.a}|{m.tile.b}] {d}",
                        key=f"m_{i}",
                        use_container_width=True,
                        type="primary" if is_rec else "secondary",
                    ):
                        gs.apply(m)
                        track_played(m.tile)
                        S('log', S('log') + [format_move(m)])
                        S('advice', None)
                        S('msg', f"✅ لعبت {m.tile}")
                        S('msg_type', 'success')
                        if gs.game_over:
                            S('phase', 'over')
                        st.rerun()

        if any(m.is_pass for m in valid):
            if st.button("🚫 دق (باس)", use_container_width=True):
                gs.apply(Move(Pos.ME, None, None))
                S('log', S('log') + ["🟢 أنت: دق 🚫"])
                S('advice', None)
                S('msg', "🚫 دقيت")
                S('msg_type', 'warning')
                if gs.game_over:
                    S('phase', 'over')
                st.rerun()

    # ═══════════════════════════════
    # ★ دور الخصم/الشريك — ذكي
    # ═══════════════════════════════
    else:
        name = turn.label
        icon = turn.icon
        opp_count = gs.players[turn].count
        st.markdown(f"### {icon} دور: **{name}** ({opp_count} أحجار)")

        pending = S('pending_tile')

        # ── حالة 1: حجر ينتظر اتجاه ──
        if pending is not None:
            st.markdown(f"""
            <div style="background:linear-gradient(135deg,#E65100,#FF9800);
                        border-radius:14px;padding:20px;text-align:center;
                        color:#fff;margin:10px 0">
                <div style="font-size:14px">🤔 يركب في الجهتين!</div>
                <div style="font-size:28px;font-weight:bold;margin:8px 0">
                    [{pending.a}|{pending.b}]</div>
                <div style="font-size:13px">وين حطّه {name}؟</div>
            </div>
            """, unsafe_allow_html=True)

            c1, _, c2 = st.columns([2, 1, 2])
            with c1:
                if st.button("⬅️ يسار", key="pend_L", use_container_width=True,
                             type="primary"):
                    apply_opponent_move(gs, turn, pending, Direction.LEFT)
                    st.rerun()
            with c2:
                if st.button("يمين ➡️", key="pend_R", use_container_width=True,
                             type="primary"):
                    apply_opponent_move(gs, turn, pending, Direction.RIGHT)
                    st.rerun()

            if st.button("❌ إلغاء", key="pend_X", use_container_width=True):
                S('pending_tile', None)
                st.rerun()

        # ── حالة 2: اختيار حجر ──
        else:
            remaining = get_remaining_tiles(gs)

            if gs.board.is_empty:
                playable = remaining
            else:
                playable = [t for t in remaining if gs.board.can_play(t)]

            if playable:
                playable.sort(key=lambda t: (t.a, t.b), reverse=True)
                st.caption(
                    f"👇 اضغط الحجر الذي لعبه **{name}** "
                    f"• {len(playable)} متاح من {len(remaining)} متبقي:"
                )

                ncols = min(len(playable), 5)
                for row_start in range(0, len(playable), ncols):
                    row = playable[row_start:row_start + ncols]
                    cols = st.columns(ncols)
                    for j, t in enumerate(row):
                        with cols[j]:
                            if st.button(
                                f"[{t.a}|{t.b}]",
                                key=f"opp_{t.a}_{t.b}_{turn.value}",
                                use_container_width=True,
                            ):
                                dirs = get_possible_directions(gs, t)
                                if len(dirs) == 1:
                                    # ✅ تموضع تلقائي!
                                    apply_opponent_move(gs, turn, t, dirs[0])
                                    st.rerun()
                                elif len(dirs) >= 2:
                                    # 🤔 نسأل
                                    S('pending_tile', t)
                                    st.rerun()
                                else:
                                    st.error("❌ الحجر لا يركب!")
            else:
                st.info("💡 لا أحجار تركب — يجب الباس.")

            st.markdown("---")
            if st.button(
                f"🚫 {name} دق (باس)",
                key=f"ps_{turn.value}",
                type="primary",
                use_container_width=True,
            ):
                gs.apply(Move(turn, None, None))
                S('log', S('log') + [f"{icon} {name}: دق 🚫"])
                S('advice', None)
                S('msg', f"🚫 {name} دق")
                S('msg_type', 'warning')
                if gs.game_over:
                    S('phase', 'over')
                st.rerun()

    # ─── يدي ───
    st.markdown("---")
    st.markdown("### 🃏 أحجارك")
    playable_idx = []
    if turn == Pos.ME and not gs.board.is_empty:
        playable_idx = [i for i, t in enumerate(gs.my_hand) if gs.board.can_play(t)]
    elif turn == Pos.ME and gs.board.is_empty:
        playable_idx = list(range(len(gs.my_hand)))
    SVG.hand(gs.my_hand, glowing=playable_idx, title="يدك")

    # ─── السجل ───
    with st.expander("📜 سجل الحركات"):
        log = S('log')
        for i, e in enumerate(reversed(log[-20:]), 1):
            st.markdown(f"`{len(log) - i + 1}.` {e}")

# ═══════════════════════════════════
#  🏆 النهاية
# ═══════════════════════════════════
elif phase == 'over':
    gs = S('state')
    win = gs.winner and gs.winner.is_friend
    if win:
        st.balloons()
        st.markdown(
            '<div style="text-align:center;padding:40px;'
            'background:linear-gradient(135deg,#1B5E20,#4CAF50);'
            'border-radius:18px;color:#fff;margin:20px 0">'
            '<h1>🏆 مبروك! فريقك فاز!</h1></div>',
            unsafe_allow_html=True,
        )
    elif gs.winner:
        st.markdown(
            '<div style="text-align:center;padding:40px;'
            'background:linear-gradient(135deg,#B71C1C,#E53935);'
            'border-radius:18px;color:#fff;margin:20px 0">'
            '<h1>😔 خسارة</h1></div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div style="text-align:center;padding:40px;'
            'background:linear-gradient(135deg,#E65100,#FF9800);'
            'border-radius:18px;color:#fff;margin:20px 0">'
            '<h1>🤝 تعادل (قفل)</h1></div>',
            unsafe_allow_html=True,
        )

    st.markdown("### 🎯 الطاولة النهائية")
    SVG.board(gs.board)

    c1, c2 = st.columns(2)
    with c1:
        our = gs.players[Pos.ME].total + gs.players[Pos.PARTNER].total
        st.metric("🟢 فريقك", f"{our} نقطة")
    with c2:
        their = gs.players[Pos.RIGHT].total + gs.players[Pos.LEFT].total
        st.metric("🔴 الخصوم", f"{their} نقطة")

    if st.button("🔄 لعبة جديدة", use_container_width=True, type="primary"):
        reset()
        st.rerun()
