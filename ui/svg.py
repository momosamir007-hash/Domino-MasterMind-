"""
🎨 محرك رسم SVG المتكامل - نسخة محسّنة
────────────────────────────────────────
• رصف بصري متصل: نهاية كل حجر تلتصق ببداية التالي
• الحجر المزدوج يُرسم عمودياً (تدوير 90°)
• تمييز لوني للحافتين المفتوحتين
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
    TW  = 96    # عرض الحجر الأفقي  (زوجي لضمان القسمة)
    TH  = 48    # ارتفاع الحجر الأفقي
    PR  = 5     # نصف قطر النقطة
    SP  = 2     # فراغ بين الحجارة (صغير جداً لإيهام الاتصال)
    HW  = TW // 2   # نصف العرض

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
    def _draw_pips(count: int, ox: float, oy: float,
                   aw: float, ah: float, is_double: bool = False) -> str:
        """ارسم نقاط نصف الحجر داخل المنطقة (ox,oy)→(ox+aw, oy+ah)"""
        pts  = PIP_POSITIONS.get(count, [])
        clr  = "#CC0000" if is_double else "#1a1a2e"
        pad  = 7
        s    = ""
        for px, py in pts:
            cx = ox + pad + px * (aw - 2 * pad)
            cy = oy + pad + py * (ah - 2 * pad)
            s += (f'<circle cx="{cx:.1f}" cy="{cy:.1f}" '
                  f'r="{SVGRenderer.PR}" fill="{clr}"/>\n')
        return s

    # ─────────────────────────────────────────────────────────
    #  رسم حجر واحد
    #  vertical=True  → الحجر المزدوج يُرسم طولياً (90°)
    #  side_left / side_right → تمييز الحافة المفتوحة
    # ─────────────────────────────────────────────────────────
    @staticmethod
    def _draw_tile(tile, x: float = 0, y: float = 0,
                   hl: bool = False, glow: bool = False,
                   vertical: bool = False,
                   open_left: bool = False,
                   open_right: bool = False) -> str:
        """
        ارسم حجر دومينو واحد.
        tile     : كائن Tile مع .a و .b
        vertical : True → رسم عمودي (للمزدوجات على الأطراف)
        open_left/open_right: تمييز الحافة المفتوحة بإطار ملوّن
        """
        TW = SVGRenderer.TW
        TH = SVGRenderer.TH
        HW = SVGRenderer.HW
        PR = SVGRenderer.PR

        # ── ألوان الحالة ──
        if glow:
            fill, stroke, sw = "#E8F5E9", "#4CAF50", 3
        elif hl:
            fill, stroke, sw = "#FFF8E1", "#FF9800", 3
        else:
            fill, stroke, sw = "#FAFAFA", "#455A64", 1.5

        is_dbl = (tile.a == tile.b)

        # ── أبعاد حسب الاتجاه ──
        if vertical:
            # الحجر العمودي: ارتفاعه = TW، عرضه = TH
            W, H = TH, TW
        else:
            W, H = TW, TH

        s = f'<g transform="translate({x:.1f},{y:.1f})">\n'

        # ── ظل ──
        s += (f'<rect x="2" y="2" width="{W}" height="{H}" '
              f'rx="7" fill="rgba(0,0,0,0.18)"/>\n')

        # ── جسم الحجر ──
        s += (f'<rect width="{W}" height="{H}" rx="7" '
              f'fill="{fill}" stroke="{stroke}" '
              f'stroke-width="{sw}"/>\n')

        # ── خط الفاصل الداخلي ──
        if vertical:
            # خط أفقي في المنتصف
            mid = H // 2
            s += (f'<line x1="5" y1="{mid}" x2="{W-5}" y2="{mid}" '
                  f'stroke="#90A4AE" stroke-width="1.5" '
                  f'stroke-dasharray="3,2"/>\n')
            # النقاط: النصف العلوي = a، النصف السفلي = b
            s += SVGRenderer._draw_pips(tile.a, 0,   0,   W, mid, is_dbl)
            s += SVGRenderer._draw_pips(tile.b, 0, mid,   W, mid, is_dbl)
        else:
            # خط عمودي في المنتصف
            s += (f'<line x1="{HW}" y1="5" x2="{HW}" y2="{H-5}" '
                  f'stroke="#90A4AE" stroke-width="1.5" '
                  f'stroke-dasharray="3,2"/>\n')
            # النقاط: اليسار = a، اليمين = b
            s += SVGRenderer._draw_pips(tile.a, 0,   0, HW, H, is_dbl)
            s += SVGRenderer._draw_pips(tile.b, HW,  0, HW, H, is_dbl)

        # ── تمييز الحافة المفتوحة (يسار) ──
        if open_left and not vertical:
            s += (f'<rect width="6" height="{H}" rx="4" '
                  f'fill="#FFD600" opacity="0.75"/>\n')

        # ── تمييز الحافة المفتوحة (يمين) ──
        if open_right and not vertical:
            s += (f'<rect x="{W-6}" width="6" height="{H}" rx="4" '
                  f'fill="#FFD600" opacity="0.75"/>\n')

        # ── تأثير الوهج (قابل للعب) ──
        if glow:
            s += (f'<rect width="{W}" height="{H}" rx="7" '
                  f'fill="none" stroke="#66BB6A" stroke-width="2">\n'
                  f'  <animate attributeName="opacity" '
                  f'values="0.2;0.9;0.2" dur="1.4s" '
                  f'repeatCount="indefinite"/>\n'
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
        n      = len(tiles)
        step   = TW + SP + 4          # فراغ أوضح في اليد
        svg_w  = n * step + 40
        svg_h  = TH + 50

        svg = (f'<svg viewBox="0 0 {svg_w} {svg_h}" '
               f'width="{svg_w}" height="{svg_h}" '
               f'xmlns="http://www.w3.org/2000/svg">\n')

        # ── خلفية شفافة ──
        svg += (f'<rect width="{svg_w}" height="{svg_h}" rx="12" '
                f'fill="rgba(255,255,255,0.03)" '
                f'stroke="rgba(255,255,255,0.08)" stroke-width="1"/>\n')

        # ── عنوان ──
        svg += (f'<text x="{svg_w//2}" y="18" text-anchor="middle" '
                f'font-size="12" fill="#888">{title}</text>\n')

        for i, tile in enumerate(tiles):
            tx = 20 + i * step
            svg += SVGRenderer._draw_tile(
                tile, tx, 25, glow=(i in glowing)
            )

        svg += '</svg>'
        SVGRenderer._html(svg, svg_h + 10)

    # ─────────────────────────────────────────────────────────
    #  الطاولة — القلب الرئيسي
    # ─────────────────────────────────────────────────────────
    @staticmethod
    def board(board, w: int = 900, h: int = 180):
        """
        ━━━ رسم الطاولة مع الرصف البصري المتصل ━━━
        board: كائن Board من game_engine.state
        """
        TW = SVGRenderer.TW
        TH = SVGRenderer.TH
        SP = SVGRenderer.SP   # = 2 بكسل فقط

        # ── طاولة فارغة ──
        if board.is_empty:
            svg = (
                f'<svg width="{w}" height="{h}" '
                f'xmlns="http://www.w3.org/2000/svg">'
                f'<rect width="100%" height="100%" rx="16" '
                f'fill="#1B5E20" stroke="#2E7D32" stroke-width="3"/>'
                f'<text x="50%" y="50%" text-anchor="middle" '
                f'fill="white" font-size="15" opacity="0.4">'
                f'🎲 الطاولة فارغة — ابدأ اللعب</text></svg>'
            )
            SVGRenderer._html(svg, h)
            return

        # ── قائمة الحجارة المُلعوبة ──
        played = board.played_tiles   # [(Tile, Direction), ...] أو [Tile, ...]

        # ── استخراج بيانات كل حجر ──
        # نحتاج: الحجر + هل هو على الطرف الأيسر + هل على الطرف الأيمن
        tiles_data = []
        for idx, item in enumerate(played):
            tile = item[0] if isinstance(item, (tuple, list)) else item
            is_first = (idx == 0)
            is_last  = (idx == len(played) - 1)
            tiles_data.append((tile, is_first, is_last))

        n    = len(tiles_data)
        step = TW + SP   # خطوة الرصف = عرض الحجر + فراغ 2px فقط

        # ── حساب عرض SVG ──
        needed_w = n * step + SP + 80   # هامش للمؤشرات
        full_w   = max(w, needed_w)

        svg = (f'<svg viewBox="0 0 {full_w} {h}" '
               f'width="{full_w}" height="{h}" '
               f'xmlns="http://www.w3.org/2000/svg">\n')

        # ── تعريف gradient للطاولة ──
        svg += (
            '<defs>'
            '<linearGradient id="table_bg" x1="0" y1="0" x2="0" y2="1">'
            '<stop offset="0%"   stop-color="#1B5E20"/>'
            '<stop offset="100%" stop-color="#145214"/>'
            '</linearGradient>'
            '</defs>\n'
        )

        # ── خلفية الطاولة ──
        svg += (f'<rect width="{full_w}" height="{h}" rx="16" '
                f'fill="url(#table_bg)" '
                f'stroke="#2E7D32" stroke-width="3"/>\n')

        # ── شريط ضوئي خلف الحجارة (يوضح المحور) ──
        mid_y  = (h - TH) // 2
        rail_y = mid_y + TH // 2 - 3
        svg += (f'<rect x="20" y="{rail_y}" '
                f'width="{full_w - 40}" height="6" rx="3" '
                f'fill="rgba(0,0,0,0.25)"/>\n')

        # ── رصف الحجارة ──
        # نبدأ من المنتصف بحيث تكون الحجارة في مركز الطاولة
        total_w  = n * step - SP          # العرض الكلي بدون الفراغ الأخير
        start_x  = (full_w - total_w) // 2

        for i, (tile, is_first, is_last) in enumerate(tiles_data):
            tx = start_x + i * step
            ty = mid_y

            svg += SVGRenderer._draw_tile(
                tile, tx, ty,
                open_left  = is_first,
                open_right = is_last,
            )

        # ── مؤشرات الطرفين (أرقام مفتوحة) ──
        left_end  = board.left  if board.left  is not None else "?"
        right_end = board.right if board.right is not None else "?"

        # — يسار —
        svg += (f'<rect x="6" y="{h - 36}" '
                f'width="52" height="26" rx="6" '
                f'fill="rgba(0,0,0,0.45)"/>\n')
        svg += (f'<text x="32" y="{h - 17}" text-anchor="middle" '
                f'fill="#FFD600" font-size="13" font-weight="bold">'
                f'◀ {left_end}</text>\n')

        # — يمين —
        svg += (f'<rect x="{full_w - 58}" y="{h - 36}" '
                f'width="52" height="26" rx="6" '
                f'fill="rgba(0,0,0,0.45)"/>\n')
        svg += (f'<text x="{full_w - 32}" y="{h - 17}" text-anchor="middle" '
                f'fill="#FFD600" font-size="13" font-weight="bold">'
                f'{right_end} ▶</text>\n')

        # ── عدّاد الأحجار ──
        svg += (f'<text x="{full_w // 2}" y="17" text-anchor="middle" '
                f'fill="#A5D6A7" font-size="11" opacity="0.8">'
                f'🎴 {n} حجر على الطاولة</text>\n')

        svg += '</svg>'
        SVGRenderer._html(svg, h + 20)

    @staticmethod
    def players(state, w: int = 700, h: int = 400):
        """
        ━━━ خريطة اللاعبين حول الطاولة ━━━
        state: كائن GameState
        """
        from game_engine.state import Pos

        cx, cy = w // 2, h // 2

        svg = (f'<svg viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
               f'xmlns="http://www.w3.org/2000/svg">\n')

        # ── طاولة بيضاوية ──
        svg += (f'<ellipse cx="{cx}" cy="{cy}" '
                f'rx="{w//3}" ry="{h//4}" '
                f'fill="#1B5E20" stroke="#2E7D32" '
                f'stroke-width="2" opacity="0.6"/>\n')

        # ── مواقع اللاعبين ──
        layout = {
            Pos.ME:      (cx,      h - 55, "🟢 أنت",       "#4CAF50"),
            Pos.RIGHT:   (w - 95,  cy,     "🔴 خصم يمين",  "#F44336"),
            Pos.PARTNER: (cx,      55,     "🔵 شريكك",     "#2196F3"),
            Pos.LEFT:    (95,      cy,     "🟠 خصم يسار",  "#FF9800"),
        }

        for pos, (px, py, name, clr) in layout.items():
            p          = state.players[pos]
            is_current = (pos == state.turn)
            sw         = "3" if is_current else "1.5"

            card_w, card_h = 130, 64
            rx = px - card_w // 2
            ry = py - card_h // 2

            # ── بطاقة اللاعب ──
            svg += (f'<rect x="{rx}" y="{ry}" '
                    f'width="{card_w}" height="{card_h}" '
                    f'rx="12" fill="#0d1117" '
                    f'stroke="{clr}" stroke-width="{sw}"/>\n')

            # ── وهج الدور ──
            if is_current:
                svg += (f'<rect x="{rx}" y="{ry}" '
                        f'width="{card_w}" height="{card_h}" '
                        f'rx="12" fill="none" stroke="{clr}" stroke-width="3">\n'
                        f'  <animate attributeName="opacity" '
                        f'values="0.2;0.8;0.2" dur="1.5s" '
                        f'repeatCount="indefinite"/>\n'
                        f'</rect>\n')

            # ── الاسم ──
            svg += (f'<text x="{px}" y="{py - 6}" '
                    f'text-anchor="middle" fill="white" '
                    f'font-size="13" font-weight="bold">{name}</text>\n')

            # ── عدد الأحجار ──
            remaining = p.count
            svg += (f'<text x="{px}" y="{py + 14}" '
                    f'text-anchor="middle" fill="{clr}" '
                    f'font-size="10">{remaining} أحجار</text>\n')

            # ── باس ──
            if p.passes > 0:
                svg += (f'<text x="{px}" y="{py + 26}" '
                        f'text-anchor="middle" fill="#FF5722" '
                        f'font-size="9">🚫 دق {p.passes}×</text>\n')

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

        w, h     = 650, 260
        bar_zone = 160
        n        = min(len(all_moves), 8)
        bar_w    = max(35, (w - 120) // n - 12)

        max_wr = max((m.get('win_rate', 0) for m in all_moves), default=1)
        if max_wr <= 0:
            max_wr = 1

        svg = (f'<svg viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
               f'xmlns="http://www.w3.org/2000/svg">\n')

        svg += (f'<rect width="{w}" height="{h}" rx="14" '
                f'fill="#0d1117" stroke="#222" stroke-width="1"/>\n')
        svg += (f'<text x="{w//2}" y="24" text-anchor="middle" '
                f'fill="#aaa" font-size="13" font-weight="bold">'
                f'📊 تحليل الحركات المتاحة</text>\n')

        for i, md in enumerate(all_moves[:n]):
            wr    = md.get('win_rate', 0)
            bar_h = max(6, (wr / max_wr) * bar_zone)
            x     = 70 + i * (bar_w + 12)
            y     = h - 55 - bar_h

            color = "#4CAF50" if wr >= 0.6 else ("#FFC107" if wr >= 0.4 else "#F44336")

            svg += (f'<rect x="{x}" y="{y}" width="{bar_w}" height="{bar_h}" '
                    f'rx="4" fill="{color}" opacity="0.85"/>\n')
            svg += (f'<text x="{x + bar_w//2}" y="{y - 6}" '
                    f'text-anchor="middle" fill="white" '
                    f'font-size="10" font-weight="bold">'
                    f'{wr:.0%}</text>\n')

            mv    = md.get('move', md.get('tile', '?'))
            label = str(mv)[:8]
            svg += (f'<text x="{x + bar_w//2}" y="{h - 35}" '
                    f'text-anchor="middle" fill="#888" '
                    f'font-size="9">{label}</text>\n')

        svg += '</svg>'
        SVGRenderer._html(svg, h + 10)
