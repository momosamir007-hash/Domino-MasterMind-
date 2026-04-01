"""
🎨 محرك رسم SVG المتكامل
────────────────────────
• حماية كاملة من كل AttributeError
• الأحجار متّصلة بصرياً كسلسلة
• الدبل عمودي
"""

import streamlit.components.v1 as components
from typing import List, Optional

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
    TW = 100
    TH = 50
    HW = TW // 2
    PR = 6
    HAND_GAP = 8
    CHAIN_GAP = 2

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
        """استخراج بيانات اللاعب بأمان"""
        count = getattr(p, 'count', None)
        if count is None:
            count = getattr(p, 'tile_count', 7)

        passes = 0
        if hasattr(p, 'passed_on'):
            passed_on = getattr(p, 'passed_on', set())
            if isinstance(passed_on, set):
                passes = len(passed_on) // 2 if passed_on else 0
            else:
                passes = 0
        elif hasattr(p, 'passes'):
            try:
                passes = p.passes
            except Exception:
                passes = 0

        total = 0
        try:
            total = p.total
        except Exception:
            total = getattr(p, 'score', 0)

        return {'count': count, 'passes': passes, 'total': total}

    # ════════════════════════════════════
    #  ★★★ استخراج أحجار الطاولة بأمان ★★★
    # ════════════════════════════════════

    @staticmethod
    def _get_board_tiles(board):
        """
        يستخرج قائمة الأحجار الملعوبة من Board
        يجرّب كل الأسماء المحتملة ويُرجع list[Tile]
        """
        # ── 1) played_tiles ──
        tiles = getattr(board, 'played_tiles', None)
        if tiles is not None:
            return SVGRenderer._normalize_tiles(tiles)

        # ── 2) chain ──
        tiles = getattr(board, 'chain', None)
        if tiles is not None:
            return SVGRenderer._normalize_tiles(tiles)

        # ── 3) _chain (خاص) ──
        tiles = getattr(board, '_chain', None)
        if tiles is not None:
            return SVGRenderer._normalize_tiles(tiles)

        # ── 4) tiles ──
        tiles = getattr(board, 'tiles', None)
        if tiles is not None:
            return SVGRenderer._normalize_tiles(tiles)

        # ── 5) _tiles ──
        tiles = getattr(board, '_tiles', None)
        if tiles is not None:
            return SVGRenderer._normalize_tiles(tiles)

        # ── 6) tiles_on_table ──
        tiles = getattr(board, 'tiles_on_table', None)
        if tiles is not None:
            return SVGRenderer._normalize_tiles(tiles)

        # ── 7) history ──
        tiles = getattr(board, 'history', None)
        if tiles is not None:
            return SVGRenderer._normalize_tiles(tiles)

        # ── 8) البحث في كل الخصائص ──
        for attr_name in dir(board):
            if attr_name.startswith('__'):
                continue
            try:
                val = getattr(board, attr_name)
                if isinstance(val, (list, tuple)) and len(val) > 0:
                    normalized = SVGRenderer._normalize_tiles(val)
                    if normalized:
                        return normalized
            except Exception:
                continue

        return []

    @staticmethod
    def _normalize_tiles(tiles):
        """
        يحوّل أي شكل من أشكال القائمة إلى list[Tile]
        يدعم: list[Tile], list[(Tile,Dir)], set[Tile], deque, etc.
        """
        result = []
        try:
            items = list(tiles)
        except Exception:
            return []

        for item in items:
            if item is None:
                continue
            # ── (Tile, Direction) tuple ──
            if isinstance(item, (tuple, list)):
                tile = item[0] if len(item) > 0 else None
                if tile is not None and hasattr(tile, 'a') and hasattr(tile, 'b'):
                    result.append(tile)
            # ── Tile مباشر ──
            elif hasattr(item, 'a') and hasattr(item, 'b'):
                result.append(item)

        return result

    # ════════════════════════════════════
    #  رسم النقاط
    # ════════════════════════════════════

    @staticmethod
    def _draw_pips(count, ox, oy, aw, ah, is_double=False):
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
    #  رسم حجر اليد
    # ════════════════════════════════════

    @staticmethod
    def _draw_tile(tile, x=0, y=0, hl=False, glow=False):
        TW, TH, HW = SVGRenderer.TW, SVGRenderer.TH, SVGRenderer.HW

        if glow:
            fill, stroke, sw = "#E8F5E9", "#4CAF50", 3
        elif hl:
            fill, stroke, sw = "#FFF8E1", "#FF9800", 3
        else:
            fill, stroke, sw = "#FFFFFF", "#455A64", 2

        is_dbl = tile.a == tile.b
        s = f'<g transform="translate({x},{y})">\n'
        s += (f'<rect x="3" y="3" width="{TW}" height="{TH}" '
              f'rx="8" fill="rgba(0,0,0,0.15)"/>\n')
        s += (f'<rect width="{TW}" height="{TH}" rx="8" '
              f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>\n')
        s += (f'<line x1="{HW}" y1="5" x2="{HW}" y2="{TH-5}" '
              f'stroke="#90A4AE" stroke-width="1.5" '
              f'stroke-dasharray="3,2"/>\n')
        s += SVGRenderer._draw_pips(tile.a, 0, 0, HW, TH, is_dbl)
        s += SVGRenderer._draw_pips(tile.b, HW, 0, HW, TH, is_dbl)
        if glow:
            s += (f'<rect width="{TW}" height="{TH}" rx="8" '
                  f'fill="none" stroke="#66BB6A" stroke-width="2">\n'
                  f'  <animate attributeName="opacity" '
                  f'values="0.3;0.9;0.3" dur="1.4s" '
                  f'repeatCount="indefinite"/>\n</rect>\n')
        s += '</g>\n'
        return s

    # ════════════════════════════════════
    #  رسم حجر في السلسلة
    # ════════════════════════════════════

    @staticmethod
    def _draw_chain_tile(tile, x, y, vertical=False):
        TW, TH, HW = SVGRenderer.TW, SVGRenderer.TH, SVGRenderer.HW
        fill, stroke, rx = "#FFFFF0", "#37474F", 4

        if vertical:
            vw, vh = TH, TW
            half = vh // 2
            s = f'<g transform="translate({x},{y})">\n'
            s += (f'<rect x="1" y="1" width="{vw}" height="{vh}" '
                  f'rx="{rx}" fill="rgba(0,0,0,0.10)"/>\n')
            s += (f'<rect width="{vw}" height="{vh}" rx="{rx}" '
                  f'fill="{fill}" stroke="{stroke}" '
                  f'stroke-width="1.5"/>\n')
            s += (f'<line x1="4" y1="{half}" x2="{vw-4}" '
                  f'y2="{half}" stroke="#90A4AE" '
                  f'stroke-width="1.5" stroke-dasharray="3,2"/>\n')
            s += SVGRenderer._draw_pips(tile.a, 0, 0, vw, half, True)
            s += SVGRenderer._draw_pips(tile.b, 0, half, vw, half, True)
            s += '</g>\n'
        else:
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

    @staticmethod
    def _draw_connector(x, y):
        return (
            f'<circle cx="{x}" cy="{y}" r="4" '
            f'fill="#8D6E63" stroke="#5D4037" stroke-width="0.8" '
            f'opacity="0.7"/>\n'
        )

    # ════════════════════════════════════
    #  الدوال العامة (API)
    # ════════════════════════════════════

    @staticmethod
    def hand(tiles, glowing=None, title="يدك"):
        if not tiles:
            return
        glowing = glowing or []
        TW, TH = SVGRenderer.TW, SVGRenderer.TH
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
    #  ★★★ الطاولة ★★★
    # ─────────────────────────────────

    @staticmethod
    def board(board, w=900, h=180):
        TW, TH = SVGRenderer.TW, SVGRenderer.TH
        GAP = SVGRenderer.CHAIN_GAP

        # ── طاولة فارغة ──
        is_empty = getattr(board, 'is_empty', True)
        try:
            is_empty = board.is_empty
        except Exception:
            is_empty = True

        if is_empty:
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

        # ── ★ استخراج الأحجار بأمان ★ ──
        played_tiles = SVGRenderer._get_board_tiles(board)
        n = len(played_tiles)

        if n == 0:
            svg = (
                f'<svg width="{w}" height="{h}">'
                f'<rect width="100%" height="100%" rx="16" '
                f'fill="#1B5E20" stroke="#2E7D32" stroke-width="3"/>'
                f'<text x="50%" y="50%" text-anchor="middle" '
                f'fill="white" font-size="15" opacity="0.4">'
                f'🎲 الطاولة فارغة</text></svg>'
            )
            SVGRenderer._html(svg, h)
            return

        # ── بناء السلسلة ──
        chain = []
        total_chain_w = 0
        has_double = False

        for tile in played_tiles:
            is_dbl = (tile.a == tile.b)
            tw = TH if is_dbl else TW
            chain.append((tile, is_dbl, tw))
            total_chain_w += tw + GAP
            if is_dbl:
                has_double = True

        total_chain_w -= GAP
        if total_chain_w < 0:
            total_chain_w = 0

        board_h = max(h, 220) if has_double else h
        full_w = max(w, total_chain_w + 120)
        mid_y = board_h // 2

        svg = (f'<svg viewBox="0 0 {full_w} {board_h}" '
               f'width="{full_w}" height="{board_h}">\n')

        svg += (
            '<defs>\n'
            '  <filter id="chainShadow" x="-2%" y="-2%" '
            'width="104%" height="110%">\n'
            '    <feDropShadow dx="3" dy="4" stdDeviation="3" '
            'flood-opacity="0.25"/>\n'
            '  </filter>\n'
            '</defs>\n'
        )

        # خلفية
        svg += (f'<rect width="{full_w}" height="{board_h}" rx="16" '
                f'fill="#1B5E20" stroke="#2E7D32" stroke-width="3"/>\n')
        svg += (f'<line x1="30" y1="{mid_y}" '
                f'x2="{full_w-30}" y2="{mid_y}" '
                f'stroke="#2E7D32" stroke-width="1" opacity="0.2"/>\n')

        # ── رسم السلسلة ──
        start_x = max(30, (full_w - total_chain_w) // 2)
        svg += '<g filter="url(#chainShadow)">\n'

        cx = start_x
        positions = []

        for tile, is_dbl, tw in chain:
            if is_dbl:
                ty = mid_y - TW // 2
                svg += SVGRenderer._draw_chain_tile(
                    tile, cx, ty, vertical=True
                )
            else:
                ty = mid_y - TH // 2
                svg += SVGRenderer._draw_chain_tile(
                    tile, cx, ty, vertical=False
                )
            positions.append((cx, tw))
            cx += tw + GAP

        svg += '</g>\n'

        # نقاط اتصال
        for i in range(len(positions) - 1):
            px, pw = positions[i]
            jx = px + pw + GAP // 2
            svg += SVGRenderer._draw_connector(jx, mid_y)

        # ── مؤشرات الأطراف ──
        left_end = getattr(board, 'left', "?")
        right_end = getattr(board, 'right', "?")
        if left_end is None:
            left_end = "?"
        if right_end is None:
            right_end = "?"

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

        svg += (f'<text x="{full_w//2}" y="20" '
                f'text-anchor="middle" fill="#66BB6A" '
                f'font-size="11" opacity="0.7">'
                f'🎴 {n} حجر على الطاولة</text>\n')

        svg += '</svg>'
        SVGRenderer._html(svg, board_h + 20)

    # ─────────────────────────────────
    #  خريطة اللاعبين
    # ─────────────────────────────────

    @staticmethod
    def players(state, w=700, h=400):
        from game_engine.state import Pos

        cx, cy = w // 2, h // 2
        svg = (f'<svg viewBox="0 0 {w} {h}" '
               f'width="{w}" height="{h}">\n')

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
            info = SVGRenderer._safe_player(p)
            remaining = info['count']
            passes = info['passes']

            is_current = False
            try:
                is_current = (pos == state.turn)
            except Exception:
                pass

            sw = "3" if is_current else "1.5"
            card_w, card_h = 130, 64
            rx, ry = px - card_w // 2, py - card_h // 2

            svg += (f'<rect x="{rx}" y="{ry}" width="{card_w}" '
                    f'height="{card_h}" rx="12" fill="#0d1117" '
                    f'stroke="{clr}" stroke-width="{sw}"/>\n')

            if is_current:
                svg += (
                    f'<rect x="{rx}" y="{ry}" width="{card_w}" '
                    f'height="{card_h}" rx="12" fill="none" '
                    f'stroke="{clr}" stroke-width="3">\n'
                    f'  <animate attributeName="opacity" '
                    f'values="0.2;0.8;0.2" dur="1.5s" '
                    f'repeatCount="indefinite"/>\n</rect>\n'
                )

            svg += (f'<text x="{px}" y="{py - 6}" '
                    f'text-anchor="middle" fill="white" '
                    f'font-size="13" font-weight="bold">'
                    f'{name}</text>\n')

            svg += (f'<text x="{px}" y="{py + 14}" '
                    f'text-anchor="middle" fill="{clr}" '
                    f'font-size="10">{remaining} أحجار</text>\n')

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
                f'fill="#0d1117" stroke="#222" stroke-width="1"/>\n')
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
