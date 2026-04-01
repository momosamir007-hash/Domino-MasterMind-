"""
🎨 محرك رسم SVG المتكامل — نسخة مُصحّحة
────────────────────────
• الأحجار متّصلة بصرياً كسلسلة واحدة
• الدبل يُرسم عمودياً (عمودي على خط السلسلة)
• نقاط اتصال نحاسية بين الأحجار
• حماية من AttributeError
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
    5: [(0.25, 0.25), (0.25, 0.75), (0.5, 0.5),
        (0.75, 0.25), (0.75, 0.75)],
    6: [(0.25, 0.25), (0.25, 0.5), (0.25, 0.75),
        (0.75, 0.25), (0.75, 0.5), (0.75, 0.75)],
}


class SVGRenderer:
    """Static methods لرسم عناصر الدومينو بـ SVG"""

    # ── أبعاد الحجر ──
    TW = 100           # عرض الحجر الأفقي
    TH = 50            # ارتفاع الحجر الأفقي
    HW = TW // 2       # نصف العرض
    PR = 6             # نصف قطر النقطة
    HAND_GAP = 8       # فراغ بين أحجار اليد
    CHAIN_GAP = 2      # ★ فراغ ضئيل جداً في السلسلة (للالتصاق)

    # ════════════════════════════════════
    #  أدوات مساعدة
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
    def _safe_player(p):
        """استخراج بيانات اللاعب بأمان بدون AttributeError"""
        return {
            'count':  getattr(p, 'count', getattr(p, 'tile_count', 7)),
            'passes': getattr(p, 'passes', getattr(p, 'pass_count', 0)),
            'total':  getattr(p, 'total', getattr(p, 'score', 0)),
            'played': getattr(p, 'played', []),
        }

    @staticmethod
    def _draw_pips(count, ox, oy, aw, ah, is_double=False):
        """ارسم نقاط (pips) داخل مستطيل محدد"""
        pts = PIP_POSITIONS.get(count, [])
        clr = "#CC0000" if is_double else "#1a1a2e"
        pad = 7
        s = ""
        for px, py in pts:
            cx = ox + pad + px * (aw - 2 * pad)
            cy = oy + pad + py * (ah - 2 * pad)
            s += (f'<circle cx="{cx:.1f}" cy="{cy:.1f}" '
                  f'r="{SVGRenderer.PR}" fill="{clr}"/>\n')
        return s

    # ════════════════════════════════════
    #  رسم حجر اليد (أفقي دائماً)
    # ════════════════════════════════════

    @staticmethod
    def _draw_tile(tile, x=0, y=0, hl=False, glow=False):
        """ارسم حجراً أفقياً — يُستخدم لعرض يد اللاعب"""
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
        # ظل
        s += (f'<rect x="3" y="3" width="{TW}" height="{TH}" '
              f'rx="8" fill="rgba(0,0,0,0.15)"/>\n')
        # جسم
        s += (f'<rect width="{TW}" height="{TH}" rx="8" '
              f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>\n')
        # فاصل
        s += (f'<line x1="{HW}" y1="5" x2="{HW}" y2="{TH-5}" '
              f'stroke="#90A4AE" stroke-width="1.5" '
              f'stroke-dasharray="3,2"/>\n')
        # نقاط
        s += SVGRenderer._draw_pips(tile.a, 0, 0, HW, TH, is_dbl)
        s += SVGRenderer._draw_pips(tile.b, HW, 0, HW, TH, is_dbl)
        # وهج
        if glow:
            s += (f'<rect width="{TW}" height="{TH}" rx="8" '
                  f'fill="none" stroke="#66BB6A" stroke-width="2">\n'
                  f'  <animate attributeName="opacity" '
                  f'values="0.3;0.9;0.3" dur="1.4s" '
                  f'repeatCount="indefinite"/>\n</rect>\n')
        s += '</g>\n'
        return s

    # ════════════════════════════════════
    #  ★ رسم حجر في سلسلة الطاولة
    # ════════════════════════════════════

    @staticmethod
    def _draw_chain_tile(tile, x, y, vertical=False):
        """
        ارسم حجراً واحداً في سلسلة الطاولة.
        vertical=False → أفقي عادي (TW × TH)
        vertical=True  → دبل عمودي (TH × TW)
        """
        TW = SVGRenderer.TW
        TH = SVGRenderer.TH
        HW = SVGRenderer.HW
        is_dbl = tile.a == tile.b
        fill = "#FFFFF0"
        stroke = "#37474F"
        rx = 4  # ★ زوايا صغيرة للالتصاق النظيف

        if vertical:
            # ── دبل عمودي: عرض=TH  ارتفاع=TW ──
            vw = TH       # 50
            vh = TW       # 100
            half = vh // 2  # 50

            s = f'<g transform="translate({x},{y})">\n'
            # ظل خفيف
            s += (f'<rect x="1" y="1" width="{vw}" height="{vh}" '
                  f'rx="{rx}" fill="rgba(0,0,0,0.10)"/>\n')
            # جسم
            s += (f'<rect width="{vw}" height="{vh}" rx="{rx}" '
                  f'fill="{fill}" stroke="{stroke}" '
                  f'stroke-width="1.5"/>\n')
            # فاصل أفقي
            s += (f'<line x1="4" y1="{half}" x2="{vw-4}" '
                  f'y2="{half}" stroke="#90A4AE" '
                  f'stroke-width="1.5" stroke-dasharray="3,2"/>\n')
            # نقاط: نصف علوي ← tile.a
            s += SVGRenderer._draw_pips(tile.a, 0, 0, vw, half, True)
            # نقاط: نصف سفلي ← tile.b
            s += SVGRenderer._draw_pips(tile.b, 0, half, vw, half, True)
            s += '</g>\n'
            return s
        else:
            # ── عادي أفقي: عرض=TW  ارتفاع=TH ──
            s = f'<g transform="translate({x},{y})">\n'
            s += (f'<rect x="1" y="1" width="{TW}" height="{TH}" '
                  f'rx="{rx}" fill="rgba(0,0,0,0.10)"/>\n')
            s += (f'<rect width="{TW}" height="{TH}" rx="{rx}" '
                  f'fill="{fill}" stroke="{stroke}" '
                  f'stroke-width="1.5"/>\n')
            s += (f'<line x1="{HW}" y1="4" x2="{HW}" y2="{TH-4}" '
                  f'stroke="#90A4AE" stroke-width="1.5" '
                  f'stroke-dasharray="3,2"/>\n')
            s += SVGRenderer._draw_pips(tile.a, 0, 0, HW, TH, False)
            s += SVGRenderer._draw_pips(tile.b, HW, 0, HW, TH, False)
            s += '</g>\n'
            return s

    # ════════════════════════════════════
    #  ★ نقطة الاتصال النحاسية
    # ════════════════════════════════════

    @staticmethod
    def _draw_connector(x, y):
        """نقطة اتصال نحاسية بين حجرين"""
        return (
            f'<circle cx="{x}" cy="{y}" r="4" '
            f'fill="#8D6E63" stroke="#5D4037" stroke-width="0.8" '
            f'opacity="0.7"/>\n'
        )

    # ════════════════════════════════════
    #  الدوال العامة (API)
    # ════════════════════════════════════

    # ─────────────────────────────────
    #  يد اللاعب
    # ─────────────────────────────────

    @staticmethod
    def hand(tiles, glowing=None, title="يدك"):
        """━━━ رسم يد اللاعب ━━━"""
        if not tiles:
            return
        glowing = glowing or []

        TW = SVGRenderer.TW
        TH = SVGRenderer.TH
        GAP = SVGRenderer.HAND_GAP
        n = len(tiles)
        svg_w = n * (TW + GAP) + 40
        svg_h = TH + 50

        svg = (f'<svg viewBox="0 0 {svg_w} {svg_h}" '
               f'width="{svg_w}" height="{svg_h}">\n')
        svg += (f'<rect width="{svg_w}" height="{svg_h}" rx="12" '
                f'fill="rgba(255,255,255,0.03)" '
                f'stroke="rgba(255,255,255,0.08)" '
                f'stroke-width="1"/>\n')
        svg += (f'<text x="{svg_w//2}" y="18" text-anchor="middle" '
                f'font-size="12" fill="#888">{title}</text>\n')

        for i, tile in enumerate(tiles):
            x = 20 + i * (TW + GAP)
            svg += SVGRenderer._draw_tile(
                tile, x, 25, glow=(i in glowing)
            )

        svg += '</svg>'
        SVGRenderer._html(svg, svg_h + 10)

    # ─────────────────────────────────
    #  ★★★ الطاولة — سلسلة متصلة ★★★
    # ─────────────────────────────────

    @staticmethod
    def board(board, w=900, h=180):
        """
        ━━━ رسم سلسلة الطاولة ━━━
        • الأحجار ملتصقة بدون فراغ
        • الدبل عمودي ⊥ السلسلة
        • نقاط اتصال نحاسية عند الالتقاء
        """
        TW = SVGRenderer.TW       # 100
        TH = SVGRenderer.TH       # 50
        GAP = SVGRenderer.CHAIN_GAP  # 2

        # ── طاولة فارغة ──
        if board.is_empty:
            svg = (
                f'<svg width="{w}" height="{h}">'
                f'<rect width="100%" height="100%" rx="16" '
                f'fill="#1B5E20" stroke="#2E7D32" '
                f'stroke-width="3"/>'
                f'<text x="50%" y="50%" text-anchor="middle" '
                f'fill="white" font-size="15" opacity="0.4">'
                f'🎲 الطاولة فارغة — ابدأ اللعب</text></svg>'
            )
            SVGRenderer._html(svg, h)
            return

        # ── تحليل الأحجار الملعوبة ──
        played = board.played_tiles
        n = len(played)

        # بناء معلومات السلسلة
        chain = []
        total_chain_w = 0
        has_double = False

        for item in played:
            tile = item[0] if isinstance(item, (tuple, list)) else item
            is_dbl = (tile.a == tile.b)
            # ★ الدبل عرضه TH(50) على المحور الأفقي
            tw = TH if is_dbl else TW
            chain.append((tile, is_dbl, tw))
            total_chain_w += tw + GAP
            if is_dbl:
                has_double = True

        total_chain_w -= GAP
        if total_chain_w < 0:
            total_chain_w = 0

        # ── أبعاد اللوحة ──
        board_h = max(h, 220) if has_double else h
        full_w = max(w, total_chain_w + 120)
        mid_y = board_h // 2

        svg = (f'<svg viewBox="0 0 {full_w} {board_h}" '
               f'width="{full_w}" height="{board_h}">\n')

        # تعريفات
        svg += '<defs>\n'
        svg += (
            '  <filter id="chainShadow" x="-2%" y="-2%" '
            'width="104%" height="110%">\n'
            '    <feDropShadow dx="3" dy="4" stdDeviation="3" '
            'flood-opacity="0.25"/>\n'
            '  </filter>\n'
        )
        svg += '</defs>\n'

        # ── خلفية الطاولة ──
        svg += (f'<rect width="{full_w}" height="{board_h}" rx="16" '
                f'fill="#1B5E20" stroke="#2E7D32" '
                f'stroke-width="3"/>\n')

        # خط مرجعي خفيف
        svg += (f'<line x1="30" y1="{mid_y}" '
                f'x2="{full_w-30}" y2="{mid_y}" '
                f'stroke="#2E7D32" stroke-width="1" '
                f'opacity="0.2"/>\n')

        # ── رسم السلسلة ──
        start_x = max(30, (full_w - total_chain_w) // 2)
        svg += '<g filter="url(#chainShadow)">\n'

        cx = start_x
        positions = []  # [(x, width, is_dbl)] لحساب نقاط الاتصال

        for i, (tile, is_dbl, tw) in enumerate(chain):
            if is_dbl:
                # ★ الدبل عمودي: يبرز فوق وتحت خط الوسط
                ty = mid_y - TW // 2  # TW=100 هو ارتفاع الدبل
                svg += SVGRenderer._draw_chain_tile(
                    tile, cx, ty, vertical=True
                )
            else:
                # عادي أفقي: متمركز على خط الوسط
                ty = mid_y - TH // 2
                svg += SVGRenderer._draw_chain_tile(
                    tile, cx, ty, vertical=False
                )

            positions.append((cx, tw, is_dbl))
            cx += tw + GAP

        svg += '</g>\n'

        # ── نقاط الاتصال النحاسية ──
        for i in range(len(positions) - 1):
            px, pw, _ = positions[i]
            jx = px + pw + GAP // 2  # نقطة بين الحجرين
            svg += SVGRenderer._draw_connector(jx, mid_y)

        # ── مؤشرات الأطراف ──
        left_end = board.left if board.left is not None else "?"
        right_end = board.right if board.right is not None else "?"

        svg += (f'<rect x="8" y="{board_h-40}" width="62" '
                f'height="28" rx="6" fill="rgba(0,0,0,0.35)"/>\n')
        svg += (f'<text x="39" y="{board_h-21}" '
                f'text-anchor="middle" fill="#A5D6A7" '
                f'font-size="13" font-weight="bold">'
                f'⬅ {left_end}</text>\n')

        svg += (f'<rect x="{full_w-70}" y="{board_h-40}" '
                f'width="62" height="28" rx="6" '
                f'fill="rgba(0,0,0,0.35)"/>\n')
        svg += (f'<text x="{full_w-39}" y="{board_h-21}" '
                f'text-anchor="middle" fill="#A5D6A7" '
                f'font-size="13" font-weight="bold">'
                f'{right_end} ➡</text>\n')

        # عدّاد
        svg += (f'<text x="{full_w//2}" y="20" '
                f'text-anchor="middle" fill="#66BB6A" '
                f'font-size="11" opacity="0.7">'
                f'🎴 {n} حجر على الطاولة</text>\n')

        svg += '</svg>'
        SVGRenderer._html(svg, board_h + 20)

    # ─────────────────────────────────
    #  ★ خريطة اللاعبين — مع حماية الأخطاء ★
    # ─────────────────────────────────

    @staticmethod
    def players(state, w=700, h=400):
        """━━━ خريطة اللاعبين حول الطاولة ━━━"""
        from game_engine.state import Pos

        cx, cy = w // 2, h // 2

        svg = (f'<svg viewBox="0 0 {w} {h}" '
               f'width="{w}" height="{h}">\n')

        # طاولة بيضاوية
        svg += (f'<ellipse cx="{cx}" cy="{cy}" '
                f'rx="{w//3}" ry="{h//4}" fill="#1B5E20" '
                f'stroke="#2E7D32" stroke-width="2" '
                f'opacity="0.6"/>\n')

        layout = {
            Pos.ME:      (cx, h - 55,  "🟢 أنت",       "#4CAF50"),
            Pos.RIGHT:   (w - 95, cy,  "🔴 خصم يمين",  "#F44336"),
            Pos.PARTNER: (cx, 55,      "🔵 شريكك",     "#2196F3"),
            Pos.LEFT:    (95, cy,      "🟠 خصم يسار",  "#FF9800"),
        }

        for pos, (px, py, name, clr) in layout.items():
            p = state.players[pos]

            # ★★★ استخراج آمن — يمنع AttributeError ★★★
            info = SVGRenderer._safe_player(p)
            remaining = info['count']
            passes    = info['passes']

            is_current = (pos == state.turn)
            sw = "3" if is_current else "1.5"

            card_w, card_h = 130, 64
            rx, ry = px - card_w // 2, py - card_h // 2

            # بطاقة اللاعب
            svg += (f'<rect x="{rx}" y="{ry}" width="{card_w}" '
                    f'height="{card_h}" rx="12" fill="#0d1117" '
                    f'stroke="{clr}" stroke-width="{sw}"/>\n')

            # وهج الدور الحالي
            if is_current:
                svg += (
                    f'<rect x="{rx}" y="{ry}" width="{card_w}" '
                    f'height="{card_h}" rx="12" fill="none" '
                    f'stroke="{clr}" stroke-width="3">\n'
                    f'  <animate attributeName="opacity" '
                    f'values="0.2;0.8;0.2" dur="1.5s" '
                    f'repeatCount="indefinite"/>\n</rect>\n'
                )

            # الاسم
            svg += (f'<text x="{px}" y="{py - 6}" '
                    f'text-anchor="middle" fill="white" '
                    f'font-size="13" font-weight="bold">'
                    f'{name}</text>\n')

            # عدد الأحجار
            svg += (f'<text x="{px}" y="{py + 14}" '
                    f'text-anchor="middle" fill="{clr}" '
                    f'font-size="10">{remaining} أحجار</text>\n')

            # ★ باس — بأمان ★
            if passes > 0:
                svg += (f'<text x="{px}" y="{py + 26}" '
                        f'text-anchor="middle" fill="#FF5722" '
                        f'font-size="9">🚫 دق {passes}×</text>\n')

        svg += '</svg>'
        SVGRenderer._html(svg, h + 10)

    # ─────────────────────────────────
    #  تحليل الحركات
    # ─────────────────────────────────

    @staticmethod
    def analysis_chart(all_moves):
        """━━━ رسم بياني لتحليل الحركات ━━━"""
        if not all_moves:
            return

        w, h = 650, 260
        bar_zone = 160
        n = min(len(all_moves), 8)
        bar_w = max(35, (w - 120) // n - 12)

        max_wr = max(
            (m.get('win_rate', 0) for m in all_moves), default=1
        )
        if max_wr <= 0:
            max_wr = 1

        svg = (f'<svg viewBox="0 0 {w} {h}" '
               f'width="{w}" height="{h}">\n')
        svg += (f'<rect width="{w}" height="{h}" rx="14" '
                f'fill="#0d1117" stroke="#222" '
                f'stroke-width="1"/>\n')
        svg += (f'<text x="{w//2}" y="24" text-anchor="middle" '
                f'fill="#aaa" font-size="13" font-weight="bold">'
                f'📊 تحليل الحركات المتاحة</text>\n')

        for i, md in enumerate(all_moves[:n]):
            wr = md.get('win_rate', 0)
            bar_h = max(6, (wr / max_wr) * bar_zone)
            x = 70 + i * (bar_w + 12)
            y = h - 55 - bar_h

            if wr >= 0.6:
                color = "#4CAF50"
            elif wr >= 0.4:
                color = "#FFC107"
            else:
                color = "#F44336"

            svg += (f'<rect x="{x}" y="{y}" width="{bar_w}" '
                    f'height="{bar_h}" rx="4" fill="{color}" '
                    f'opacity="0.85"/>\n')
            svg += (f'<text x="{x + bar_w//2}" y="{y - 6}" '
                    f'text-anchor="middle" fill="white" '
                    f'font-size="10" font-weight="bold">'
                    f'{wr:.0%}</text>\n')

            mv = md.get('move', md.get('tile', '?'))
            label = str(mv)[:8]
            svg += (f'<text x="{x + bar_w//2}" y="{h - 35}" '
                    f'text-anchor="middle" fill="#888" '
                    f'font-size="9">{label}</text>\n')

        svg += '</svg>'
        SVGRenderer._html(svg, h + 10)
