"""
🎨 محرك رسم SVG المتكامل - نسخة مُحصّنة
─────────────────────────────────────────
• فحص آمن لجميع خصائص كائن Player
• رصف بصري متصل للحجارة
• تمييز الطرفين المفتوحين
"""

import streamlit.components.v1 as components
from typing import List, Optional, Any

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


# ══════════════════════════════════════════════
#  أدوات آمنة لقراءة خصائص كائن Player
# ══════════════════════════════════════════════

def _safe_count(player) -> int:
    """عدد الأحجار المتبقية - يجرب جميع الأسماء الممكنة"""
    for attr in ('count', 'tile_count', 'num_tiles', 'tiles_count'):
        val = getattr(player, attr, None)
        if val is not None:
            return int(val)
    # آخر حل: طول اليد
    hand = getattr(player, 'hand',
           getattr(player, 'tiles',
           getattr(player, 'my_tiles', None)))
    if hand is not None:
        return len(hand)
    return 0


def _safe_passes(player) -> int:
    """عدد مرات الباس - يجرب جميع الأسماء الممكنة"""
    for attr in ('passes', 'pass_count', 'num_passes',
                 'consecutive_passes', 'skips', 'pass_counter'):
        val = getattr(player, attr, None)
        if val is not None:
            return int(val)
    return 0


def _safe_total(player) -> int:
    """مجموع النقاط"""
    for attr in ('total', 'score', 'points', 'total_score'):
        val = getattr(player, attr, None)
        if val is not None:
            return int(val)
    return 0


class SVGRenderer:
    """Static methods لرسم عناصر الدومينو بـ SVG"""

    # ── أبعاد ثابتة ──
    TW  = 96        # عرض الحجر الأفقي
    TH  = 48        # ارتفاع الحجر الأفقي
    PR  = 5         # نصف قطر النقطة
    SP  = 2         # فراغ بين الحجارة (صغير لإيهام الاتصال)
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
        """ارسم نقاط نصف الحجر"""
        pts  = PIP_POSITIONS.get(int(count), [])
        clr  = "#CC0000" if is_double else "#1a1a2e"
        pad  = 7
        s    = ""
        for px, py in pts:
            cx = ox + pad + px * (aw - 2 * pad)
            cy = oy + pad + py * (ah - 2 * pad)
            s += (f'<circle cx="{cx:.1f}" cy="{cy:.1f}" '
                  f'r="{SVGRenderer.PR}" fill="{clr}"/>\n')
        return s

    @staticmethod
    def _draw_tile(tile, x: float = 0, y: float = 0,
                   hl: bool = False, glow: bool = False,
                   open_left: bool = False,
                   open_right: bool = False) -> str:
        """
        ارسم حجر دومينو واحد أفقياً.
        open_left / open_right : شريط ذهبي على الحافة المفتوحة
        """
        TW = SVGRenderer.TW
        TH = SVGRenderer.TH
        HW = SVGRenderer.HW

        # ── ألوان الحالة ──
        if glow:
            fill, stroke, sw = "#E8F5E9", "#4CAF50", 3
        elif hl:
            fill, stroke, sw = "#FFF8E1", "#FF9800", 3
        else:
            fill, stroke, sw = "#FAFAFA", "#455A64", 1.5

        is_dbl = (tile.a == tile.b)

        s = f'<g transform="translate({x:.1f},{y:.1f})">\n'

        # ── ظل ──
        s += (f'<rect x="2" y="2" width="{TW}" height="{TH}" '
              f'rx="7" fill="rgba(0,0,0,0.20)"/>\n')

        # ── جسم الحجر ──
        s += (f'<rect width="{TW}" height="{TH}" rx="7" '
              f'fill="{fill}" stroke="{stroke}" '
              f'stroke-width="{sw}"/>\n')

        # ── خط الفاصل العمودي ──
        s += (f'<line x1="{HW}" y1="5" x2="{HW}" y2="{TH - 5}" '
              f'stroke="#90A4AE" stroke-width="1.5" '
              f'stroke-dasharray="3,2"/>\n')

        # ── النقاط ──
        s += SVGRenderer._draw_pips(tile.a, 0,   0, HW, TH, is_dbl)
        s += SVGRenderer._draw_pips(tile.b, HW,  0, HW, TH, is_dbl)

        # ── شريط الحافة المفتوحة (يسار) ──
        if open_left:
            s += (f'<rect x="0" y="0" width="5" height="{TH}" '
                  f'rx="4" fill="#FFD600" opacity="0.85"/>\n')

        # ── شريط الحافة المفتوحة (يمين) ──
        if open_right:
            s += (f'<rect x="{TW - 5}" y="0" width="5" height="{TH}" '
                  f'rx="4" fill="#FFD600" opacity="0.85"/>\n')

        # ── تأثير الوهج ──
        if glow:
            s += (f'<rect width="{TW}" height="{TH}" rx="7" '
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
        step   = TW + SP + 4      # فراغ أوضح في اليد
        svg_w  = n * step + 40
        svg_h  = TH + 50

        svg = (f'<svg viewBox="0 0 {svg_w} {svg_h}" '
               f'width="{svg_w}" height="{svg_h}" '
               f'xmlns="http://www.w3.org/2000/svg">\n')

        svg += (f'<rect width="{svg_w}" height="{svg_h}" rx="12" '
                f'fill="rgba(255,255,255,0.03)" '
                f'stroke="rgba(255,255,255,0.08)" stroke-width="1"/>\n')

        svg += (f'<text x="{svg_w // 2}" y="18" text-anchor="middle" '
                f'font-size="12" fill="#888">{title}</text>\n')

        for i, tile in enumerate(tiles):
            tx = 20 + i * step
            svg += SVGRenderer._draw_tile(tile, tx, 25, glow=(i in glowing))

        svg += '</svg>'
        SVGRenderer._html(svg, svg_h + 10)

    @staticmethod
    def board(board, w: int = 900, h: int = 180):
        """
        ━━━ رسم الطاولة مع الرصف البصري المتصل ━━━
        board: كائن Board من game_engine.state
        """
        TW = SVGRenderer.TW
        TH = SVGRenderer.TH
        SP = SVGRenderer.SP   # 2 بكسل فقط

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

        # ── قائمة الحجارة ──
        played = board.played_tiles   # [(Tile, Direction), ...] أو [Tile, ...]
        n      = len(played)

        step     = TW + SP
        total_w  = n * step - SP              # العرض الكلي بدون فراغ أخير
        needed_w = total_w + 100              # هامش للمؤشرات
        full_w   = max(w, needed_w)

        svg = (f'<svg viewBox="0 0 {full_w} {h}" '
               f'width="{full_w}" height="{h}" '
               f'xmlns="http://www.w3.org/2000/svg">\n')

        # ── تدرج لوني ──
        svg += (
            '<defs>'
            '<linearGradient id="tbl" x1="0" y1="0" x2="0" y2="1">'
            '<stop offset="0%"   stop-color="#1B5E20"/>'
            '<stop offset="100%" stop-color="#145214"/>'
            '</linearGradient>'
            '</defs>\n'
        )

        # ── خلفية الطاولة ──
        svg += (f'<rect width="{full_w}" height="{h}" rx="16" '
                f'fill="url(#tbl)" stroke="#2E7D32" stroke-width="3"/>\n')

        # ── شريط المحور الخلفي ──
        mid_y  = (h - TH) // 2
        rail_y = mid_y + TH // 2 - 3
        svg += (f'<rect x="20" y="{rail_y}" '
                f'width="{full_w - 40}" height="6" rx="3" '
                f'fill="rgba(0,0,0,0.25)"/>\n')

        # ── توسيط الحجارة ──
        start_x = (full_w - total_w) // 2

        for i, item in enumerate(played):
            tile = item[0] if isinstance(item, (tuple, list)) else item
            tx   = start_x + i * step
            ty   = mid_y

            is_first = (i == 0)
            is_last  = (i == n - 1)

            svg += SVGRenderer._draw_tile(
                tile, tx, ty,
                open_left  = is_first,
                open_right = is_last,
            )

        # ── مؤشرات الطرفين ──
        left_end  = board.left  if board.left  is not None else "?"
        right_end = board.right if board.right is not None else "?"

        # — يسار —
        svg += (f'<rect x="6" y="{h - 36}" width="52" height="26" '
                f'rx="6" fill="rgba(0,0,0,0.45)"/>\n')
        svg += (f'<text x="32" y="{h - 17}" text-anchor="middle" '
                f'fill="#FFD600" font-size="13" font-weight="bold">'
                f'◀ {left_end}</text>\n')

        # — يمين —
        svg += (f'<rect x="{full_w - 58}" y="{h - 36}" '
                f'width="52" height="26" rx="6" '
                f'fill="rgba(0,0,0,0.45)"/>\n')
        svg += (f'<text x="{full_w - 32}" y="{h - 17}" '
                f'text-anchor="middle" '
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
                f'rx="{w // 3}" ry="{h // 4}" '
                f'fill="#1B5E20" stroke="#2E7D32" '
                f'stroke-width="2" opacity="0.6"/>\n')

        # ── مواقع اللاعبين ──
        layout = {
            Pos.ME:      (cx,       h - 55, "🟢 أنت",       "#4CAF50"),
            Pos.RIGHT:   (w - 95,   cy,     "🔴 خصم يمين",  "#F44336"),
            Pos.PARTNER: (cx,       55,     "🔵 شريكك",     "#2196F3"),
            Pos.LEFT:    (95,       cy,     "🟠 خصم يسار",  "#FF9800"),
        }

        for pos, (px, py, name, clr) in layout.items():

            # ── استخراج آمن لبيانات اللاعب ──
            try:
                p = state.players[pos]
            except (KeyError, TypeError, AttributeError):
                continue

            is_current = False
            try:
                is_current = (pos == state.turn)
            except AttributeError:
                pass

            sw         = "3" if is_current else "1.5"
            card_w, card_h = 130, 68
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
                        f'rx="12" fill="none" '
                        f'stroke="{clr}" stroke-width="3">\n'
                        f'  <animate attributeName="opacity" '
                        f'values="0.2;0.8;0.2" dur="1.5s" '
                        f'repeatCount="indefinite"/>\n'
                        f'</rect>\n')

            # ── الاسم ──
            svg += (f'<text x="{px}" y="{py - 10}" '
                    f'text-anchor="middle" fill="white" '
                    f'font-size="13" font-weight="bold">{name}</text>\n')

            # ── عدد الأحجار (آمن) ──
            remaining = _safe_count(p)
            svg += (f'<text x="{px}" y="{py + 10}" '
                    f'text-anchor="middle" fill="{clr}" '
                    f'font-size="11">'
                    f'🎴 {remaining} أحجار</text>\n')

            # ── باس (آمن) ──
            passes = _safe_passes(p)
            if passes > 0:
                svg += (f'<text x="{px}" y="{py + 26}" '
                        f'text-anchor="middle" fill="#FF5722" '
                        f'font-size="10">🚫 دق {passes}×</text>\n')

            # ── مؤشر الدور (نجمة) ──
            if is_current:
                svg += (f'<text x="{rx + card_w - 14}" y="{ry + 16}" '
                        f'font-size="14" fill="#FFD600">★</text>\n')

        svg += '</svg>'
        SVGRenderer._html(svg, h + 10)

    @staticmethod
    def analysis_chart(all_moves):
        """
        ━━━ رسم بياني لتحليل الحركات ━━━
        all_moves: list[dict]
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

        svg += (f'<text x="{w // 2}" y="24" text-anchor="middle" '
                f'fill="#aaa" font-size="13" font-weight="bold">'
                f'📊 تحليل الحركات المتاحة</text>\n')

        for i, md in enumerate(all_moves[:n]):
            wr    = md.get('win_rate', 0)
            bar_h = max(6, (wr / max_wr) * bar_zone)
            x     = 70 + i * (bar_w + 12)
            y     = h - 55 - bar_h

            if wr >= 0.6:
                color = "#4CAF50"
            elif wr >= 0.4:
                color = "#FFC107"
            else:
                color = "#F44336"

            svg += (f'<rect x="{x}" y="{y}" '
                    f'width="{bar_w}" height="{bar_h}" '
                    f'rx="4" fill="{color}" opacity="0.85"/>\n')

            svg += (f'<text x="{x + bar_w // 2}" y="{y - 6}" '
                    f'text-anchor="middle" fill="white" '
                    f'font-size="10" font-weight="bold">'
                    f'{wr:.0%}</text>\n')

            mv    = md.get('move', md.get('tile', '?'))
            label = str(mv)[:8]
            svg += (f'<text x="{x + bar_w // 2}" y="{h - 35}" '
                    f'text-anchor="middle" fill="#888" '
                    f'font-size="9">{label}</text>\n')

        svg += '</svg>'
        SVGRenderer._html(svg, h + 10)
