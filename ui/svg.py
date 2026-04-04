""" ui/svg.py """
import streamlit.components.v1 as components
from typing import List, Optional, Tuple
from game_engine.tiles import Tile, Board, Direction
from game_engine.state import GameState, Pos

# ── إحداثيات النقاط داخل كل مربع (نسب مئوية) ──────────────
PIPS = {
    0: [],
    1: [(50, 50)],
    2: [(25, 75), (75, 25)],
    3: [(25, 75), (50, 50), (75, 25)],
    4: [(25, 25), (25, 75), (75, 25), (75, 75)],
    5: [(25, 25), (25, 75), (50, 50), (75, 25), (75, 75)],
    6: [(25, 25), (25, 50), (25, 75), (75, 25), (75, 50), (75, 75)],
}

# ── ألوان اللاعبين ──────────────────────────────────────────
PLAYER_COLORS = {
    Pos.ME:      "#4CAF50",   # أخضر
    Pos.RIGHT:   "#F44336",   # أحمر
    Pos.PARTNER: "#2196F3",   # أزرق
    Pos.LEFT:    "#FF9800",   # برتقالي
}

# ── أسماء مختصرة للدوائر ────────────────────────────────────
PLAYER_SHORT = {
    Pos.ME:      "أنا",
    Pos.RIGHT:   "يمين",
    Pos.PARTNER: "شريك",
    Pos.LEFT:    "يسار",
}


class SVGRenderer:
    S   = 45     # حجم المربع لنصف الحجر (بكسل)
    GAP = 3      # مسافة التباعد بين الحجارة
    R   = 4.5    # نصف قطر نقطة الدومينو

    # ── ثوابت دائرة التتبع ──────────────────────────────────
    BADGE_R    = 12   # نصف قطر الدائرة
    BADGE_GAP  = 4    # مسافة بين أسفل الحجر والدائرة
    BADGE_ZONE = 45   # ارتفاع المنطقة المخصصة للدوائر

    # ════════════════════════════════════════════════════════
    @staticmethod
    def _show(svg: str, h: int):
        """عرض SVG مع شريط تمرير أفقي"""
        html = f'''
        <div style="width:100%;overflow-x:auto;text-align:center;padding:5px 0;">
            <div style="display:inline-block;min-width:max-content;">
                {svg}
            </div>
        </div>
        '''
        components.html(html, height=h, scrolling=True)

    # ════════════════════════════════════════════════════════
    @classmethod
    def _dots(cls, val: int, ox: float, oy: float,
              s: float, dbl: bool = False) -> str:
        """رسم النقاط داخل مربع محدد"""
        color = "#D32F2F" if dbl else "#1a1a1a"
        svg   = ""
        for px, py in PIPS.get(val, []):
            cx = ox + (px / 100) * s
            cy = oy + (py / 100) * s
            svg += (f'<circle cx="{cx:.1f}" cy="{cy:.1f}" '
                    f'r="{cls.R}" fill="{color}"/>')
        return svg

    # ════════════════════════════════════════════════════════
    @classmethod
    def visual_tile(cls, v1: int, v2: int, is_double: bool,
                    x: float, cy: float,
                    glow: bool = False, label: str = "") -> Tuple[str, float]:
        """
        رسم حجر فردي.
        - الدبل: عمودي  (عرض=S  , ارتفاع=S*2)
        - العادي: أفقي  (عرض=S*2, ارتفاع=S  )
        يُرجع (svg_string, عرض_الحجر)
        """
        bg     = "#C8E6C9" if glow else "#FAFAFA"
        border = "#2E7D32" if glow else "#37474F"
        bw     = 3 if glow else 1.5

        if is_double:
            w = cls.S
            h = cls.S * 2
            y = cy - h / 2

            s  = f'<g transform="translate({x},{y:.1f})">'
            # ظل
            s += (f'<rect x="2" y="3" width="{w}" height="{h}" '
                  f'rx="6" fill="rgba(0,0,0,.2)"/>')
            # الجسم
            s += (f'<rect width="{w}" height="{h}" rx="6" '
                  f'fill="{bg}" stroke="{border}" stroke-width="{bw}"/>')
            # خط المنتصف
            s += (f'<line x1="4" y1="{cls.S}" x2="{w-4}" y2="{cls.S}" '
                  f'stroke="#90A4AE" stroke-width="2"/>')
            # النقاط
            s += cls._dots(v1, 0,     0,     cls.S, True)
            s += cls._dots(v2, 0,     cls.S, cls.S, True)
            s += '</g>'

            if label:
                s += (f'<text x="{x + w/2:.1f}" y="{y + h + 18:.1f}" '
                      f'text-anchor="middle" font-size="12" '
                      f'fill="#aaa" font-weight="bold">{label}</text>')
            return s, float(w)

        else:
            w = cls.S * 2
            h = cls.S
            y = cy - h / 2

            s  = f'<g transform="translate({x},{y:.1f})">'
            s += (f'<rect x="2" y="3" width="{w}" height="{h}" '
                  f'rx="6" fill="rgba(0,0,0,.2)"/>')
            s += (f'<rect width="{w}" height="{h}" rx="6" '
                  f'fill="{bg}" stroke="{border}" stroke-width="{bw}"/>')
            s += (f'<line x1="{cls.S}" y1="4" x2="{cls.S}" y2="{h-4}" '
                  f'stroke="#90A4AE" stroke-width="2"/>')
            s += cls._dots(v1, 0,     0, cls.S, False)
            s += cls._dots(v2, cls.S, 0, cls.S, False)
            s += '</g>'

            if label:
                s += (f'<text x="{x + w/2:.1f}" y="{y + h + 18:.1f}" '
                      f'text-anchor="middle" font-size="12" '
                      f'fill="#aaa" font-weight="bold">{label}</text>')
            return s, float(w)

    # ════════════════════════════════════════════════════════
    @classmethod
    def board(cls, brd: Board, h: int = 220,
              played_by: Optional[List[Tuple]] = None):
        """
        رسم الطاولة الكاملة مع دوائر تتبع اللاعبين.

        played_by : قائمة (Pos, رقم_تسلسلي) بنفس ترتيب brd.played
                    تُمرَّر من GameState.played_by
        """

        # ── طاولة فارغة ─────────────────────────────────
        if brd.is_empty:
            w   = 850
            svg = (f'<svg xmlns="http://www.w3.org/2000/svg" '
                   f'width="{w}" height="{h}" viewBox="0 0 {w} {h}">')
            svg += f'<rect width="{w}" height="{h}" rx="12" fill="#1B5E20"/>'
            svg += (f'<rect x="3" y="3" width="{w-6}" height="{h-6}" rx="10" '
                    f'fill="none" stroke="#4CAF50" stroke-width="2" '
                    f'stroke-dasharray="10,5"/>')
            svg += (f'<text x="{w//2}" y="{h//2 - 5}" text-anchor="middle" '
                    f'font-size="20" fill="rgba(255,255,255,.7)">🎲</text>')
            svg += (f'<text x="{w//2}" y="{h//2 + 20}" text-anchor="middle" '
                    f'font-size="15" fill="rgba(255,255,255,.5)">الطاولة فارغة</text>')
            svg += '</svg>'
            cls._show(svg, h + 10)
            return

        # ── إعادة بناء السلسلة البصرية ──────────────────
        # كل عنصر: {'v1', 'v2', 'dbl', 'idx'}
        # idx = الفهرس الحقيقي في brd.played (لربطه بـ played_by)
        visual_chain = []

        for raw_idx, (tile, direction) in enumerate(brd.played):
            if not visual_chain:
                visual_chain.append({
                    'v1':  tile.a,
                    'v2':  tile.b,
                    'dbl': tile.is_double,
                    'idx': raw_idx,
                })
            else:
                if direction == Direction.LEFT:
                    target = visual_chain[0]['v1']
                    other  = tile.other(target)
                    visual_chain.insert(0, {
                        'v1':  other,
                        'v2':  target,
                        'dbl': tile.is_double,
                        'idx': raw_idx,
                    })
                else:
                    target = visual_chain[-1]['v2']
                    other  = tile.other(target)
                    visual_chain.append({
                        'v1':  target,
                        'v2':  other,
                        'dbl': tile.is_double,
                        'idx': raw_idx,
                    })

        # ── دوال مساعدة لأبعاد الحجر ────────────────────
        def t_width(item):
            return float(cls.S) if item['dbl'] else float(cls.S * 2)

        def t_height(item):
            return float(cls.S * 2) if item['dbl'] else float(cls.S)

        # ── حساب الأبعاد الكلية ──────────────────────────
        total_tile_w = sum(t_width(item) + cls.GAP for item in visual_chain)
        padding      = 160
        aw           = max(850, int(total_tile_w) + padding)

        # الارتفاع الكلي = منطقة الحجارة + منطقة الدوائر
        total_h = h + cls.BADGE_ZONE

        # مركز الحجارة عمودياً (في منتصف منطقة h)
        cy = h / 2

        # ── بداية SVG ────────────────────────────────────
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" '
               f'viewBox="0 0 {aw} {total_h}" '
               f'style="min-width:{aw}px;height:{total_h}px;display:block;">')

        # خلفية خضراء
        svg += (f'<rect width="{aw}" height="{total_h}" '
                f'rx="12" fill="#1B5E20"/>')
        svg += (f'<rect x="3" y="3" width="{aw-6}" height="{total_h-6}" '
                f'rx="10" fill="none" stroke="#2E7D32" stroke-width="2"/>')

        # ── رسم الحجارة ──────────────────────────────────
        # نبدأ من المنتصف الأفقي
        current_x = (aw - total_tile_w) / 2

        # نجمع معلومات كل حجر لرسم الدوائر لاحقاً
        badge_data = []

        for item in visual_chain:
            tw      = t_width(item)
            th_tile = t_height(item)

            tile_svg, _ = cls.visual_tile(
                item['v1'], item['v2'], item['dbl'],
                current_x, cy,
            )
            svg += tile_svg

            # مركز الحجر أفقياً
            tile_cx = current_x + tw / 2
            # أسفل الحجر عمودياً = مركز ± نصف الارتفاع
            tile_bottom = cy + th_tile / 2

            badge_data.append({
                'cx':     tile_cx,
                'bottom': tile_bottom,
                'idx':    item['idx'],
            })

            current_x += tw + cls.GAP

        # ── رسم دوائر التتبع ─────────────────────────────
        if played_by and len(played_by) > 0:
            for info in badge_data:
                raw_idx = info['idx']

                # تحقق أن الفهرس موجود في القائمة
                if raw_idx >= len(played_by):
                    continue

                player, seq = played_by[raw_idx]

                color = PLAYER_COLORS.get(player, "#888888")
                short = PLAYER_SHORT.get(player, "؟")

                bx = info['cx']
                # الدائرة تحت الحجر مباشرة
                by = info['bottom'] + cls.BADGE_GAP + cls.BADGE_R

                # 1) هالة خارجية شفافة
                svg += (f'<circle '
                        f'cx="{bx:.1f}" '
                        f'cy="{by:.1f}" '
                        f'r="{cls.BADGE_R + 4}" '
                        f'fill="{color}" '
                        f'opacity="0.3"/>')

                # 2) الدائرة الرئيسية
                svg += (f'<circle '
                        f'cx="{bx:.1f}" '
                        f'cy="{by:.1f}" '
                        f'r="{cls.BADGE_R}" '
                        f'fill="{color}" '
                        f'stroke="white" '
                        f'stroke-width="2"/>')

                # 3) رقم التسلسل داخل الدائرة
                svg += (f'<text '
                        f'x="{bx:.1f}" '
                        f'y="{by:.1f}" '
                        f'text-anchor="middle" '
                        f'dominant-baseline="central" '
                        f'font-size="10" '
                        f'font-weight="bold" '
                        f'fill="white">'
                        f'{seq}'
                        f'</text>')

                # 4) اسم اللاعب تحت الدائرة
                name_y = by + cls.BADGE_R + 9
                svg += (f'<text '
                        f'x="{bx:.1f}" '
                        f'y="{name_y:.1f}" '
                        f'text-anchor="middle" '
                        f'font-size="9" '
                        f'font-weight="bold" '
                        f'fill="{color}">'
                        f'{short}'
                        f'</text>')

        # ── مؤشرات الأطراف (يسار / يمين) ────────────────
        ey        = cy - 16
        left_val  = visual_chain[0]['v1']
        right_val = visual_chain[-1]['v2']

        # مؤشر الطرف الأيسر
        svg += (f'<g transform="translate(15,{ey:.1f})">'
                f'<rect width="36" height="32" rx="6" '
                f'fill="rgba(0,0,0,0.4)" stroke="#4CAF50" stroke-width="1.5"/>'
                f'<text x="18" y="22" text-anchor="middle" '
                f'font-size="18" font-weight="bold" fill="#fff">'
                f'{left_val}</text>'
                f'</g>')
        svg += (f'<text x="33" y="{h - 12}" text-anchor="middle" '
                f'font-size="11" fill="rgba(255,255,255,.6)">⬅️ يسار</text>')

        # مؤشر الطرف الأيمن
        svg += (f'<g transform="translate({aw - 51},{ey:.1f})">'
                f'<rect width="36" height="32" rx="6" '
                f'fill="rgba(0,0,0,0.4)" stroke="#4CAF50" stroke-width="1.5"/>'
                f'<text x="18" y="22" text-anchor="middle" '
                f'font-size="18" font-weight="bold" fill="#fff">'
                f'{right_val}</text>'
                f'</g>')
        svg += (f'<text x="{aw - 33}" y="{h - 12}" text-anchor="middle" '
                f'font-size="11" fill="rgba(255,255,255,.6)">يمين ➡️</text>')

        svg += '</svg>'
        cls._show(svg, total_h + 25)

    # ════════════════════════════════════════════════════════
    @classmethod
    def hand(cls, tiles, glowing=None, title="يدك"):
        """رسم أحجار اليد"""
        glowing = glowing or []
        n       = len(tiles)

        if n == 0:
            svg = (f'<svg width="350" height="80" '
                   f'xmlns="http://www.w3.org/2000/svg">'
                   f'<rect x="5" y="5" width="340" height="70" rx="10" '
                   f'fill="none" stroke="#4CAF50" '
                   f'stroke-dasharray="8,4" stroke-width="2"/>'
                   f'<text x="175" y="45" text-anchor="middle" '
                   f'font-size="16" fill="#4CAF50">✨ لا يوجد أحجار</text>'
                   f'</svg>')
            cls._show(svg, 90)
            return

        total_w = (
            sum((cls.S if t.is_double else cls.S * 2) for t in tiles)
            + (n - 1) * cls.GAP
        )
        tw = max(400, int(total_w) + 60)
        th = 130
        cy = th // 2 - 5

        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" '
               f'viewBox="0 0 {tw} {th}" '
               f'style="min-width:{tw}px;height:{th}px;">')
        svg += (f'<text x="{tw//2}" y="20" text-anchor="middle" '
                f'font-size="14" fill="#ccc" font-weight="bold">'
                f'🃏 {title} ({n})</text>')

        cx = (tw - total_w) / 2
        for i, t in enumerate(tiles):
            is_glow      = i in glowing
            tile_svg, tw_t = cls.visual_tile(
                t.a, t.b, t.is_double, cx, cy,
                glow=is_glow,
                label=f"({i+1})",
            )
            svg += tile_svg
            cx  += tw_t + cls.GAP

        pts  = sum(t.total for t in tiles)
        svg += (f'<text x="{tw//2}" y="{th - 5}" text-anchor="middle" '
                f'font-size="12" fill="#888">مجموع: {pts} نقطة</text>')
        svg += '</svg>'
        cls._show(svg, th + 25)

    # ════════════════════════════════════════════════════════
    @classmethod
    def players(cls, state: GameState, w: int = 680, h: int = 400):
        """خريطة اللاعبين الأربعة"""
        cx, cy = w // 2, h // 2
        xy = {
            Pos.ME:      (cx,       h - 45),
            Pos.PARTNER: (cx,       45),
            Pos.RIGHT:   (75,       cy),
            Pos.LEFT:    (w - 75,   cy),
        }
        clr = {
            Pos.ME:      "#4CAF50",
            Pos.RIGHT:   "#F44336",
            Pos.PARTNER: "#2196F3",
            Pos.LEFT:    "#FF9800",
        }

        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" '
               f'viewBox="0 0 {w} {h}" width="{w}" height="{h}">')
        svg += (f'<ellipse cx="{cx}" cy="{cy}" '
                f'rx="{w//3}" ry="{h//4}" '
                f'fill="#1B5E20" stroke="#2E7D32" stroke-width="2"/>')
        svg += (f'<text x="{cx}" y="{cy + 5}" text-anchor="middle" '
                f'font-size="14" fill="rgba(255,255,255,.4)">🎲 الطاولة</text>')

        for pos in Pos:
            p       = state.players[pos]
            px, py  = xy[pos]
            c       = clr[pos]
            it      = (pos == state.turn)
            bw_v    = 125
            bh_v    = 72
            bx      = px - bw_v // 2
            by      = py - bh_v // 2

            # إطار اللاعب
            svg += (f'<rect x="{bx}" y="{by}" '
                    f'width="{bw_v}" height="{bh_v}" '
                    f'rx="10" fill="#111128" stroke="{c}" '
                    f'stroke-width="{"3" if it else "1.5"}"/>')
            # رأس ملوّن
            svg += (f'<rect x="{bx}" y="{by}" '
                    f'width="{bw_v}" height="22" rx="10" fill="{c}"/>')
            svg += (f'<rect x="{bx}" y="{by + 13}" '
                    f'width="{bw_v}" height="9" fill="{c}"/>')
            # اسم اللاعب
            svg += (f'<text x="{px}" y="{by + 16}" '
                    f'text-anchor="middle" font-size="11" '
                    f'font-weight="bold" fill="white">{pos.label}</text>')

            # عدد الأحجار
            tc = len(p.hand) if pos == Pos.ME else p.count
            svg += (f'<text x="{px}" y="{by + 40}" '
                    f'text-anchor="middle" font-size="11" '
                    f'fill="#ddd">أحجار: {tc}</text>')
            svg += (f'<text x="{px}" y="{by + 55}" '
                    f'text-anchor="middle" font-size="10">'
                    f'{"🀫" * min(tc, 7)}</text>')

            # الأرقام التي دق عليها
            if p.passed_on:
                ps = ",".join(str(v) for v in sorted(p.passed_on))
                svg += (f'<text x="{px}" y="{by + 68}" '
                        f'text-anchor="middle" font-size="9" '
                        f'fill="#EF5350">🚫 {ps}</text>')

            # مؤشر الدور (نبضة خضراء)
            if it:
                svg += (f'<circle cx="{bx + bw_v - 7}" cy="{by + 7}" '
                        f'r="5" fill="#4CAF50">'
                        f'<animate attributeName="r" '
                        f'values="5;2;5" dur="1.5s" '
                        f'repeatCount="indefinite"/>'
                        f'</circle>')

        svg += '</svg>'
        cls._show(svg, h + 5)

    # ════════════════════════════════════════════════════════
    @classmethod
    def analysis_chart(cls, moves_data, w: int = 580):
        """رسم بياني أفقي لمقارنة الحركات"""
        if not moves_data:
            return

        n      = min(len(moves_data), 6)
        th     = n * 46 + 45
        colors = ["#4CAF50", "#8BC34A", "#FFC107",
                  "#FF9800", "#FF5722", "#9E9E9E"]
        icons  = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣"]

        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" '
               f'viewBox="0 0 {w} {th}" width="{w}" height="{th}">')
        svg += (f'<text x="{w//2}" y="20" text-anchor="middle" '
                f'font-size="14" font-weight="bold" fill="#ddd">'
                f'📊 تحليل الخيارات</text>')

        for i, md in enumerate(moves_data[:n]):
            y   = 32 + i * 46
            wp  = md.get('win_pct', 0)
            bw  = max(8, int((w - 190) * wp))
            c   = colors[i] if i < len(colors) else "#666"
            ic  = icons[i]  if i < len(icons)  else f"{i + 1}."

            svg += f'<g transform="translate(12,{y})">'
            svg += f'<text x="0" y="20" font-size="16">{ic}</text>'
            svg += (f'<text x="30" y="13" font-size="10" fill="#aaa">'
                    f'{md.get("move", "")}</text>')
            svg += (f'<rect x="30" y="18" width="{w - 190}" height="13" '
                    f'rx="6" fill="#1a1a2e"/>')
            svg += (f'<rect x="30" y="18" width="{bw}" height="13" '
                    f'rx="6" fill="{c}" opacity=".85"/>')
            svg += (f'<text x="{w - 148}" y="29" font-size="13" '
                    f'font-weight="bold" fill="#eee">'
                    f'{md.get("win_rate", "")}</text>')
            svg += (f'<text x="{w - 82}" y="29" font-size="9" '
                    f'fill="#888">{md.get("confidence", "")}</text>')
            svg += '</g>'

        svg += '</svg>'
        cls._show(svg, th + 5)
