"""
🎨 محرك رسم SVG المتكامل
────────────────────────
• SVGRenderer: كلاس static methods يتوافق مع streamlit_app.py
• رصف الحجارة بالترتيب البصري الصحيح
• تموضع ديناميكي يتسع مع عدد الأحجار
"""

import streamlit.components.v1 as components
from typing import List, Optional

# ─── إحداثيات النقاط داخل نصف الحجر ───────────
PIP_POSITIONS = {
    0: [],
    1: [(0.5, 0.5)],
    2: [(0.25, 0.25), (0.75, 0.75)],
    3: [(0.25, 0.25), (0.5, 0.5), (0.75, 0.75)],
    4: [(0.25, 0.25), (0.25, 0.75), (0.75, 0.25), (0.75, 0.75)],
    5: [(0.25, 0.25), (0.25, 0.75), (0.5, 0.5), (0.75, 0.25), (0.75, 0.75)],
    6: [(0.25, 0.25), (0.25, 0.5), (0.25, 0.75),
        (0.75, 0.25), (0.75, 0.5), (0.75, 0.75)],
}


class SVGRenderer:
    """Static methods لرسم عناصر الدومينو بـ SVG"""

    # ── أبعاد ثابتة ──
    TW = 100       # عرض الحجر
    TH = 50        # ارتفاع الحجر
    PR = 6         # نصف قطر النقطة
    SP = 8         # فراغ بين الأحجار
    HW = TW // 2   # نصف العرض

    # ════════════════════════════════════
    #  أدوات داخلية
    # ════════════════════════════════════

    @staticmethod
    def _html(svg_code: str, height: int = 200):
        html = (
            '<div style="display:flex;justify-content:center;'
            'width:100%;overflow-x:auto;padding:10px 0;">'
            f'{svg_code}</div>'
        )
        components.html(html, height=height, scrolling=True)

    @staticmethod
    def _draw_pips(count, ox, oy, aw, ah, is_double=False):
        """ارسم نقاط نصف الحجر"""
        pts = PIP_POSITIONS.get(count, [])
        clr = "#CC0000" if is_double else "#1a1a2e"
        pad = 8
        s = ""
        for px, py in pts:
            cx = ox + pad + px * (aw - 2 * pad)
            cy = oy + pad + py * (ah - 2 * pad)
            s += f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{SVGRenderer.PR}" fill="{clr}"/>\n'
        return s

    @staticmethod
    def _draw_tile(tile, x=0, y=0, hl=False, glow=False):
        """
        ارسم حجر دومينو واحد.
        tile: كائن Tile مع .a و .b
        hl: تمييز (highlight)
        glow: وهج أخضر (قابل للعب)
        """
        TW = SVGRenderer.TW
        TH = SVGRenderer.TH
        HW = SVGRenderer.HW

        if glow:
            fill, stroke, sw = "#E8F5E9", "#4CAF50", 3
        elif hl:
            fill, stroke, sw = "#FFF8E1", "#FF9800", 3
        else:
            fill, stroke, sw = "#FFFFFF", "#455A64", 2

        is_dbl = tile.a == tile.b
        s = f'<g transform="translate({x},{y})">\n'

        # ── ظل ──
        s += (f'<rect x="3" y="3" width="{TW}" height="{TH}" '
              f'rx="8" fill="rgba(0,0,0,0.15)"/>\n')

        # ── جسم الحجر ──
        s += (f'<rect width="{TW}" height="{TH}" rx="8" '
              f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>\n')

        # ── خط الفاصل ──
        s += (f'<line x1="{HW}" y1="5" x2="{HW}" y2="{TH-5}" '
              f'stroke="#90A4AE" stroke-width="1.5" stroke-dasharray="3,2"/>\n')

        # ── النقاط ──
        s += SVGRenderer._draw_pips(tile.a, 0, 0, HW, TH, is_dbl)
        s += SVGRenderer._draw_pips(tile.b, HW, 0, HW, TH, is_dbl)

        # ── تأثير الوهج ──
        if glow:
            s += (f'<rect width="{TW}" height="{TH}" rx="8" '
                  f'fill="none" stroke="#66BB6A" stroke-width="2">\n'
                  f'  <animate attributeName="opacity" '
                  f'values="0.3;0.9;0.3" dur="1.4s" repeatCount="indefinite"/>\n'
                  f'</rect>\n')

        s += '</g>\n'
        return s

    # ════════════════════════════════════
    #  الدوال العامة (API)
    # ════════════════════════════════════

    @staticmethod
    def hand(tiles, glowing=None, title="يدك"):
        """
        ━━━ رسم يد اللاعب ━━━
        tiles:   list[Tile]
        glowing: list[int]  — فهارس الأحجار القابلة للعب
        """
        if not tiles:
            return
        glowing = glowing or []

        TW, TH, SP = SVGRenderer.TW, SVGRenderer.TH, SVGRenderer.SP
        n = len(tiles)
        svg_w = n * (TW + SP) + 40
        svg_h = TH + 50

        svg = f'<svg viewBox="0 0 {svg_w} {svg_h}" width="{svg_w}" height="{svg_h}">\n'

        # ── خلفية شفافة ──
        svg += (f'<rect width="{svg_w}" height="{svg_h}" rx="12" '
                f'fill="rgba(255,255,255,0.03)" stroke="rgba(255,255,255,0.08)" '
                f'stroke-width="1"/>\n')

        # ── عنوان ──
        svg += (f'<text x="{svg_w//2}" y="18" text-anchor="middle" '
                f'font-size="12" fill="#888">{title}</text>\n')

        for i, tile in enumerate(tiles):
            x = 20 + i * (TW + SP)
            svg += SVGRenderer._draw_tile(tile, x, 25, glow=(i in glowing))

        svg += '</svg>'
        SVGRenderer._html(svg, svg_h + 10)

    @staticmethod
    def board(board, w=900, h=180):
        """
        ━━━ رسم الطاولة مع الرصف الديناميكي ━━━
        board: كائن Board من game_engine.state
        """
        TW = SVGRenderer.TW
        TH = SVGRenderer.TH
        SP = SVGRenderer.SP

        # ── طاولة فارغة ──
        if board.is_empty:
            svg = (
                f'<svg width="{w}" height="{h}">'
                f'<rect width="100%" height="100%" rx="16" '
                f'fill="#1B5E20" stroke="#2E7D32" stroke-width="3"/>'
                f'<text x="50%" y="50%" text-anchor="middle" '
                f'fill="white" font-size="15" opacity="0.4">'
                f'🎲 الطاولة فارغة — ابدأ اللعب</text></svg>'
            )
            SVGRenderer._html(svg, h)
            return

        # ── حساب الأبعاد ──
        played = board.played_tiles          # [(Tile, Direction), ...]
        n = len(played)
        step = TW + SP
        needed_w = n * step + 120
        full_w = max(w, needed_w)

        svg = (f'<svg viewBox="0 0 {full_w} {h}" '
               f'width="{full_w}" height="{h}">\n')

        # ── خلفية خضراء ──
        svg += (f'<rect width="{full_w}" height="{h}" rx="16" '
                f'fill="#1B5E20" stroke="#2E7D32" stroke-width="3"/>\n')

        # ── خط مرجعي ──
        svg += (f'<line x1="30" y1="{h//2}" x2="{full_w-30}" y2="{h//2}" '
                f'stroke="#2E7D32" stroke-width="1" opacity="0.25"/>\n')

        # ── رصف الحجارة بالترتيب البصري ──
        start_x = (full_w - n * step) // 2
        mid_y = (h - TH) // 2

        for i, item in enumerate(played):
            # ندعم كلا الشكلين: (Tile, Direction) أو Tile وحده
            tile = item[0] if isinstance(item, (tuple, list)) else item
            tx = start_x + i * step
            svg += SVGRenderer._draw_tile(tile, tx, mid_y)

        # ── مؤشرات الأطراف المفتوحة ──
        left_end = board.left if board.left is not None else "?"
        right_end = board.right if board.right is not None else "?"

        # يسار
        svg += (f'<rect x="8" y="{h-38}" width="60" height="28" rx="6" '
                f'fill="rgba(0,0,0,0.3)"/>\n')
        svg += (f'<text x="38" y="{h-19}" text-anchor="middle" '
                f'fill="#A5D6A7" font-size="13" font-weight="bold">'
                f'⬅️ {left_end}</text>\n')

        # يمين
        svg += (f'<rect x="{full_w-68}" y="{h-38}" width="60" height="28" rx="6" '
                f'fill="rgba(0,0,0,0.3)"/>\n')
        svg += (f'<text x="{full_w-38}" y="{h-19}" text-anchor="middle" '
                f'fill="#A5D6A7" font-size="13" font-weight="bold">'
                f'{right_end} ➡️</text>\n')

        # ── عدّاد الأحجار ──
        svg += (f'<text x="{full_w//2}" y="18" text-anchor="middle" '
                f'fill="#66BB6A" font-size="11" opacity="0.7">'
                f'🎴 {n} حجر على الطاولة</text>\n')

        svg += '</svg>'
        SVGRenderer._html(svg, h + 20)

    @staticmethod
    def players(state, w=700, h=400):
        """
        ━━━ خريطة اللاعبين حول الطاولة ━━━
        state: كائن GameState
        """
        from game_engine.state import Pos

        cx, cy = w // 2, h // 2

        svg = f'<svg viewBox="0 0 {w} {h}" width="{w}" height="{h}">\n'

        # ── طاولة بيضاوية ──
        svg += (f'<ellipse cx="{cx}" cy="{cy}" rx="{w//3}" ry="{h//4}" '
                f'fill="#1B5E20" stroke="#2E7D32" stroke-width="2" opacity="0.6"/>\n')

        # ── مواقع اللاعبين ──
        layout = {
            Pos.ME:      (cx, h - 55,  "🟢 أنت",       "#4CAF50"),
            Pos.RIGHT:   (w - 95, cy,  "🔴 خصم يمين",  "#F44336"),
            Pos.PARTNER: (cx, 55,      "🔵 شريكك",     "#2196F3"),
            Pos.LEFT:    (95, cy,      "🟠 خصم يسار",  "#FF9800"),
        }

        for pos, (px, py, name, clr) in layout.items():
            p = state.players[pos]
            is_current = (pos == state.turn)
            sw = "3" if is_current else "1.5"

            # ── بطاقة اللاعب ──
            card_w, card_h = 130, 64
            rx, ry = px - card_w // 2, py - card_h // 2

            svg += (f'<rect x="{rx}" y="{ry}" width="{card_w}" height="{card_h}" '
                    f'rx="12" fill="#0d1117" stroke="{clr}" stroke-width="{sw}"/>\n')

            # ── وهج الدور ──
            if is_current:
                svg += (f'<rect x="{rx}" y="{ry}" width="{card_w}" height="{card_h}" '
                        f'rx="12" fill="none" stroke="{clr}" stroke-width="3">\n'
                        f'  <animate attributeName="opacity" '
                        f'values="0.2;0.8;0.2" dur="1.5s" repeatCount="indefinite"/>\n'
                        f'</rect>\n')

            # ── الاسم ──
            svg += (f'<text x="{px}" y="{py - 6}" text-anchor="middle" '
                    f'fill="white" font-size="13" font-weight="bold">{name}</text>\n')

            # ── عدد الأحجار ──
            remaining = p.count
            tile_text = "🎴" * min(remaining, 7)
            svg += (f'<text x="{px}" y="{py + 14}" text-anchor="middle" '
                    f'fill="{clr}" font-size="10">{remaining} أحجار</text>\n')

            # ── باس ──
            if p.passes > 0:
                svg += (f'<text x="{px}" y="{py + 26}" text-anchor="middle" '
                        f'fill="#FF5722" font-size="9">🚫 دق {p.passes}×</text>\n')

        svg += '</svg>'
        SVGRenderer._html(svg, h + 10)

    @staticmethod
    def analysis_chart(all_moves):
        """
        ━━━ رسم بياني لتحليل الحركات ━━━
        all_moves: list[dict] — كل dict فيه 'move'/'tile' و 'win_rate'
        """
        if not all_moves:
            return

        w, h = 650, 260
        bar_zone = 160
        n = min(len(all_moves), 8)
        bar_w = max(35, (w - 120) // n - 12)

        max_wr = max((m.get('win_rate', 0) for m in all_moves), default=1)
        if max_wr <= 0:
            max_wr = 1

        svg = f'<svg viewBox="0 0 {w} {h}" width="{w}" height="{h}">\n'

        # خلفية
        svg += (f'<rect width="{w}" height="{h}" rx="14" '
                f'fill="#0d1117" stroke="#222" stroke-width="1"/>\n')
        svg += (f'<text x="{w//2}" y="24" text-anchor="middle" '
                f'fill="#aaa" font-size="13" font-weight="bold">'
                f'📊 تحليل الحركات المتاحة</text>\n')

        for i, md in enumerate(all_moves[:n]):
            wr = md.get('win_rate', 0)
            bar_h = max(6, (wr / max_wr) * bar_zone)

            x = 70 + i * (bar_w + 12)
            y = h - 55 - bar_h

            # لون حسب نسبة الفوز
            if wr >= 0.6:
                color = "#4CAF50"
            elif wr >= 0.4:
                color = "#FFC107"
            else:
                color = "#F44336"

            # العمود
            svg += (f'<rect x="{x}" y="{y}" width="{bar_w}" height="{bar_h}" '
                    f'rx="4" fill="{color}" opacity="0.85"/>\n')

            # النسبة
            svg += (f'<text x="{x + bar_w//2}" y="{y - 6}" text-anchor="middle" '
                    f'fill="white" font-size="10" font-weight="bold">'
                    f'{wr:.0%}</text>\n')

            # اسم الحركة
            mv = md.get('move', md.get('tile', '?'))
            label = str(mv)[:8]
            svg += (f'<text x="{x + bar_w//2}" y="{h - 35}" text-anchor="middle" '
                    f'fill="#888" font-size="9">{label}</text>\n')

        svg += '</svg>'
        SVGRenderer._html(svg, h + 10)
