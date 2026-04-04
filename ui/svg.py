""" svg.py"""
import streamlit.components.v1 as components
from typing import List, Optional, Tuple
from game_engine.tiles import Tile, Board, Direction
from game_engine.state import GameState, Pos

# إحداثيات النقاط داخل المربع
PIPS = {
    0: [],
    1: [(50, 50)],
    2: [(25, 75), (75, 25)],
    3: [(25, 75), (50, 50), (75, 25)],
    4: [(25, 25), (25, 75), (75, 25), (75, 75)],
    5: [(25, 25), (25, 75), (50, 50), (75, 25), (75, 75)],
    6: [(25, 25), (25, 50), (25, 75), (75, 25), (75, 50), (75, 75)],
}

# ألوان وأسماء اللاعبين (احتياطي إن لم يكن Pos متاحاً)
PLAYER_COLORS = {
    Pos.ME:      "#4CAF50",
    Pos.RIGHT:   "#F44336",
    Pos.PARTNER: "#2196F3",
    Pos.LEFT:    "#FF9800",
}

PLAYER_SHORT = {
    Pos.ME:      "أنا",
    Pos.RIGHT:   "يمين",
    Pos.PARTNER: "شريك",
    Pos.LEFT:    "يسار",
}


class SVGRenderer:
    S   = 45      # حجم المربع لنصف الحجر
    GAP = 3       # مسافة التباعد
    R   = 4.5     # نصف قطر نقطة الدومينو

    # ── ثوابت الدائرة المتتبّعة ──────────────────────
    BADGE_R      = 11    # نصف قطر الدائرة
    BADGE_GAP    = 4     # مسافة الدائرة عن أسفل الحجر
    BADGE_FONT   = 8     # حجم الخط داخل الدائرة

    @staticmethod
    def _show(svg: str, h: int):
        html = f'''
        <div style="width:100%;overflow-x:auto;text-align:center;padding:5px 0;">
            <div style="display:inline-block;min-width:max-content;">
                {svg}
            </div>
        </div>
        '''
        components.html(html, height=h, scrolling=True)

    # ─────────────────────────────────────────────────
    @classmethod
    def _dots(cls, val, ox, oy, s, dbl=False):
        color = "#D32F2F" if dbl else "#1a1a1a"
        svg = ""
        for px, py in PIPS.get(val, []):
            cx = ox + (px / 100) * s
            cy = oy + (py / 100) * s
            svg += f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{cls.R}" fill="{color}"/>'
        return svg

    # ─────────────────────────────────────────────────
    @classmethod
    def visual_tile(cls, v1, v2, is_double, x, cy, glow=False, label=""):
        """رسم حجر فردي"""
        bg     = "#C8E6C9" if glow else "#FAFAFA"
        border = "#2E7D32" if glow else "#37474F"
        bw     = 3 if glow else 1.5

        if is_double:
            w, h = cls.S, cls.S * 2
            y = cy - h // 2
            s  = f'<g transform="translate({x},{y})">'
            s += f'<rect x="2" y="3" width="{w}" height="{h}" rx="6" fill="rgba(0,0,0,.2)"/>'
            s += f'<rect width="{w}" height="{h}" rx="6" fill="{bg}" stroke="{border}" stroke-width="{bw}"/>'
            s += f'<line x1="4" y1="{cls.S}" x2="{w-4}" y2="{cls.S}" stroke="#90A4AE" stroke-width="2"/>'
            s += cls._dots(v1, 0, 0,    cls.S, True)
            s += cls._dots(v2, 0, cls.S, cls.S, True)
            s += '</g>'
            if label:
                s += (f'<text x="{x + w//2}" y="{y + h + 18}" '
                      f'text-anchor="middle" font-size="12" fill="#aaa" '
                      f'font-weight="bold">{label}</text>')
            return s, w
        else:
            w, h = cls.S * 2, cls.S
            y = cy - h // 2
            s  = f'<g transform="translate({x},{y})">'
            s += f'<rect x="2" y="3" width="{w}" height="{h}" rx="6" fill="rgba(0,0,0,.2)"/>'
            s += f'<rect width="{w}" height="{h}" rx="6" fill="{bg}" stroke="{border}" stroke-width="{bw}"/>'
            s += f'<line x1="{cls.S}" y1="4" x2="{cls.S}" y2="{h-4}" stroke="#90A4AE" stroke-width="2"/>'
            s += cls._dots(v1, 0,     0, cls.S, False)
            s += cls._dots(v2, cls.S, 0, cls.S, False)
            s += '</g>'
            if label:
                s += (f'<text x="{x + w//2}" y="{y + h + 18}" '
                      f'text-anchor="middle" font-size="12" fill="#aaa" '
                      f'font-weight="bold">{label}</text>')
            return s, w

    # ═════════════════════════════════════════════════
    # ✨ الدائرة المتتبّعة (Badge)
    # ═════════════════════════════════════════════════
    @classmethod
    def _badge(cls, cx: float, cy: float,
               player: Pos, seq: int) -> str:
        """
        ترسم دائرة ملونة حسب اللاعب تحت القطعة.
        cx, cy  = مركز الدائرة (مطلق داخل الـ SVG)
        player  = Pos  (لتحديد اللون والاسم)
        seq     = رقم التسلسل (1، 2، 3 …)
        """
        color  = PLAYER_COLORS.get(player, "#888")
        label  = PLAYER_SHORT.get(player, "?")
        r      = cls.BADGE_R
        font_s = cls.BADGE_FONT

        # ── الدائرة الخارجية (هالة شفافة) ──────────
        svg  = (f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r + 3}" '
                f'fill="{color}" opacity="0.25"/>')

        # ── الدائرة الرئيسية ─────────────────────────
        svg += (f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r}" '
                f'fill="{color}" stroke="white" stroke-width="1.5"/>')

        # ── رقم التسلسل (داخل الدائرة) ───────────────
        svg += (f'<text x="{cx:.1f}" y="{cy - 1:.1f}" '
                f'text-anchor="middle" dominant-baseline="middle" '
                f'font-size="{font_s + 1}" font-weight="bold" fill="white">'
                f'{seq}</text>')

        # ── اسم اللاعب (تحت الدائرة) ─────────────────
        svg += (f'<text x="{cx:.1f}" y="{cy + r + 10:.1f}" '
                f'text-anchor="middle" font-size="{font_s}" '
                f'fill="{color}" font-weight="bold">'
                f'{label}</text>')

        return svg

    # ═════════════════════════════════════════════════
    # ✨ الطاولة مع الدوائر
    # ═════════════════════════════════════════════════
    @classmethod
    def board(cls, brd: Board, h: int = 220,
              played_by: Optional[List[Tuple[Pos, int]]] = None):
        """
        رسم الطاولة + دوائر تتبّع اللاعبين.

        played_by  : قائمة (Pos, رقم_تسلسلي) بنفس ترتيب brd.played
                     تُمرَّر من GameState.played_by
                     إذا كانت None → لا تُرسم دوائر
        """
        # ── طاولة فارغة ─────────────────────────────
        if brd.is_empty:
            w   = 850
            svg = (f'<svg xmlns="http://www.w3.org/2000/svg" '
                   f'width="{w}" height="{h}" viewBox="0 0 {w} {h}">')
            svg += f'<rect width="{w}" height="{h}" rx="12" fill="#1B5E20"/>'
            svg += (f'<rect x="3" y="3" width="{w-6}" height="{h-6}" rx="10" '
                    f'fill="none" stroke="#4CAF50" stroke-width="2" stroke-dasharray="10,5"/>')
            svg += (f'<text x="{w//2}" y="{h//2-5}" text-anchor="middle" '
                    f'font-size="20" fill="rgba(255,255,255,.7)">🎲</text>')
            svg += (f'<text x="{w//2}" y="{h//2+20}" text-anchor="middle" '
                    f'font-size="15" fill="rgba(255,255,255,.5)">الطاولة فارغة</text>')
            svg += '</svg>'
            cls._show(svg, h + 10)
            return

        # ── إعادة بناء السلسلة البصرية ───────────────
        visual_chain = []   # كل عنصر: {'v1','v2','dbl','idx_in_played'}

        for raw_idx, (tile, direction) in enumerate(brd.played):
            if not visual_chain:
                visual_chain.append({
                    'v1': tile.a, 'v2': tile.b,
                    'dbl': tile.is_double,
                    'idx': raw_idx,
                })
            else:
                if direction == Direction.LEFT:
                    target = visual_chain[0]['v1']
                    other  = tile.other(target)
                    visual_chain.insert(0, {
                        'v1': other, 'v2': target,
                        'dbl': tile.is_double,
                        'idx': raw_idx,
                    })
                else:
                    target = visual_chain[-1]['v2']
                    other  = tile.other(target)
                    visual_chain.append({
                        'v1': target, 'v2': other,
                        'dbl': tile.is_double,
                        'idx': raw_idx,
                    })

        # ── حساب الأبعاد ────────────────────────────
        # نحتاج مساحة إضافية في الأسفل للدوائر
        BADGE_AREA = (cls.BADGE_R * 2 + 20) if played_by else 0
        total_tile_w = sum(
            (cls.S if item['dbl'] else cls.S * 2) + cls.GAP
            for item in visual_chain
        )
        padding = 160
        aw = max(850, total_tile_w + padding)

        # الارتفاع الكلي = ارتفاع الطاولة + منطقة الدوائر
        total_h = h + BADGE_AREA

        # مركز الحجارة (عمودياً) يبقى في منتصف المنطقة العليا
        cy = h // 2

        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" '
               f'viewBox="0 0 {aw} {total_h}" '
               f'style="min-width:{aw}px; height:{total_h}px;">')

        # خلفية خضراء تغطي كامل الارتفاع
        svg += f'<rect width="{aw}" height="{total_h}" rx="12" fill="#1B5E20"/>'
        svg += (f'<rect x="3" y="3" width="{aw-6}" height="{total_h-6}" rx="10" '
                f'fill="none" stroke="#2E7D32" stroke-width="2"/>')

        # ── رسم الحجارة ──────────────────────────────
        tile_x_positions = []   # نحفظ x_center لكل حجر للدوائر
        current_x = (aw - total_tile_w) // 2

        for item in visual_chain:
            tile_svg, tw = cls.visual_tile(
                item['v1'], item['v2'], item['dbl'],
                current_x, cy,
            )
            svg += tile_svg

            # حفظ مركز الحجر أفقياً + حافته السفلية
            tile_cx     = current_x + tw / 2
            tile_bottom = cy + (cls.S if item['dbl'] else cls.S // 2)
            tile_x_positions.append({
                'cx':     tile_cx,
                'bottom': tile_bottom,
                'idx':    item['idx'],
            })
            current_x += tw + cls.GAP

        # ── رسم الدوائر المتتبّعة ─────────────────────
        if played_by and len(played_by) == len(brd.played):
            for pos_info in tile_x_positions:
                raw_idx = pos_info['idx']
                if raw_idx < len(played_by):
                    player, seq = played_by[raw_idx]
                    # Y للدائرة: أسفل الحجر + gap + نصف قطر الدائرة
                    badge_cy = (pos_info['bottom']
                                + cls.BADGE_GAP
                                + cls.BADGE_R)
                    svg += cls._badge(
                        pos_info['cx'], badge_cy,
                        player, seq,
                    )

        # ── مؤشرات الأطراف ───────────────────────────
        ey         = cy - 16
        left_val   = visual_chain[0]['v1']
        right_val  = visual_chain[-1]['v2']

        svg += (f'<g transform="translate(15,{ey})">'
                f'<rect width="36" height="32" rx="6" '
                f'fill="rgba(0,0,0,0.4)" stroke="#4CAF50" stroke-width="1.5"/>'
                f'<text x="18" y="22" text-anchor="middle" '
                f'font-size="18" font-weight="bold" fill="#fff">{left_val}</text>'
                f'</g>')
        svg += (f'<text x="33" y="{h-12}" text-anchor="middle" '
                f'font-size="11" fill="rgba(255,255,255,.6)">⬅️ يسار</text>')

        svg += (f'<g transform="translate({aw-51},{ey})">'
                f'<rect width="36" height="32" rx="6" '
                f'fill="rgba(0,0,0,0.4)" stroke="#4CAF50" stroke-width="1.5"/>'
                f'<text x="18" y="22" text-anchor="middle" '
                f'font-size="18" font-weight="bold" fill="#fff">{right_val}</text>'
                f'</g>')
        svg += (f'<text x="{aw-33}" y="{h-12}" text-anchor="middle" '
                f'font-size="11" fill="rgba(255,255,255,.6)">يمين ➡️</text>')

        svg += '</svg>'
        cls._show(svg, total_h + 25)

    # ─────────────────────────────────────────────────
    @classmethod
    def hand(cls, tiles, glowing=None, title="يدك"):
        glowing = glowing or []
        n = len(tiles)
        if n == 0:
            svg = (f'<svg width="350" height="80" xmlns="http://www.w3.org/2000/svg">'
                   f'<rect x="5" y="5" width="340" height="70" rx="10" fill="none" '
                   f'stroke="#4CAF50" stroke-dasharray="8,4" stroke-width="2"/>'
                   f'<text x="175" y="45" text-anchor="middle" font-size="16" '
                   f'fill="#4CAF50">✨ لا يوجد أحجار</text></svg>')
            cls._show(svg, 90)
            return

        total_w = sum(
            (cls.S if t.is_double else cls.S * 2) for t in tiles
        ) + (n - 1) * cls.GAP
        tw = max(400, total_w + 60)
        th = 130
        cy = th // 2 - 5

        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" '
               f'viewBox="0 0 {tw} {th}" '
               f'style="min-width:{tw}px; height:{th}px;">')
        svg += (f'<text x="{tw//2}" y="20" text-anchor="middle" '
                f'font-size="14" fill="#ccc" font-weight="bold">🃏 {title} ({n})</text>')

        cx = (tw - total_w) // 2
        for i, t in enumerate(tiles):
            is_glow  = i in glowing
            tile_svg, tw_t = cls.visual_tile(
                t.a, t.b, t.is_double, cx, cy,
                glow=is_glow,
                label=f"({i+1})",
            )
            svg += tile_svg
            cx  += tw_t + cls.GAP

        pts  = sum(t.total for t in tiles)
        svg += (f'<text x="{tw//2}" y="{th-5}" text-anchor="middle" '
                f'font-size="12" fill="#888">مجموع: {pts} نقطة</text>')
        svg += '</svg>'
        cls._show(svg, th + 25)

    # ─────────────────────────────────────────────────
    @classmethod
    def players(cls, state: GameState, w=680, h=400):
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
        svg += (f'<ellipse cx="{cx}" cy="{cy}" rx="{w//3}" ry="{h//4}" '
                f'fill="#1B5E20" stroke="#2E7D32" stroke-width="2"/>')
        svg += (f'<text x="{cx}" y="{cy+5}" text-anchor="middle" '
                f'font-size="14" fill="rgba(255,255,255,.4)">🎲 الطاولة</text>')

        for pos in Pos:
            p       = state.players[pos]
            px, py  = xy[pos]
            c       = clr[pos]
            it      = pos == state.turn
            bw_v, bh_v = 125, 72
            bx, by  = px - bw_v // 2, py - bh_v // 2

            svg += (f'<rect x="{bx}" y="{by}" width="{bw_v}" height="{bh_v}" '
                    f'rx="10" fill="#111128" stroke="{c}" '
                    f'stroke-width="{"3" if it else "1.5"}"/>')
            svg += (f'<rect x="{bx}" y="{by}" width="{bw_v}" height="22" '
                    f'rx="10" fill="{c}"/>')
            svg += (f'<rect x="{bx}" y="{by+13}" width="{bw_v}" height="9" '
                    f'fill="{c}"/>')
            svg += (f'<text x="{px}" y="{by+16}" text-anchor="middle" '
                    f'font-size="11" font-weight="bold" fill="white">{pos.label}</text>')

            tc = len(p.hand) if pos == Pos.ME else p.count
            svg += (f'<text x="{px}" y="{by+40}" text-anchor="middle" '
                    f'font-size="11" fill="#ddd">أحجار: {tc}</text>')
            svg += (f'<text x="{px}" y="{by+55}" text-anchor="middle" '
                    f'font-size="10">{"🀫" * min(tc, 7)}</text>')

            if p.passed_on:
                ps = ",".join(str(v) for v in sorted(p.passed_on))
                svg += (f'<text x="{px}" y="{by+68}" text-anchor="middle" '
                        f'font-size="9" fill="#EF5350">🚫 {ps}</text>')

            if it:
                svg += (f'<circle cx="{bx+bw_v-7}" cy="{by+7}" r="5" '
                        f'fill="#4CAF50">'
                        f'<animate attributeName="r" values="5;2;5" '
                        f'dur="1.5s" repeatCount="indefinite"/>'
                        f'</circle>')
        svg += '</svg>'
        cls._show(svg, h + 5)

    # ─────────────────────────────────────────────────
    @classmethod
    def analysis_chart(cls, moves_data, w=580):
        if not moves_data:
            return
        n      = min(len(moves_data), 6)
        th     = n * 46 + 45
        colors = ["#4CAF50","#8BC34A","#FFC107","#FF9800","#FF5722","#9E9E9E"]
        icons  = ["🥇","🥈","🥉","4️⃣","5️⃣","6️⃣"]

        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" '
               f'viewBox="0 0 {w} {th}" width="{w}" height="{th}">')
        svg += (f'<text x="{w//2}" y="20" text-anchor="middle" '
                f'font-size="14" font-weight="bold" fill="#ddd">📊 تحليل الخيارات</text>')

        for i, md in enumerate(moves_data[:n]):
            y   = 32 + i * 46
            wp  = md.get('win_pct', 0)
            bw  = max(8, int((w - 190) * wp))
            c   = colors[i] if i < len(colors) else "#666"
            ic  = icons[i]  if i < len(icons)  else f"{i+1}."

            svg += f'<g transform="translate(12,{y})">'
            svg += f'<text x="0" y="20" font-size="16">{ic}</text>'
            svg += (f'<text x="30" y="13" font-size="10" fill="#aaa">'
                    f'{md.get("move","")}</text>')
            svg += (f'<rect x="30" y="18" width="{w-190}" height="13" '
                    f'rx="6" fill="#1a1a2e"/>')
            svg += (f'<rect x="30" y="18" width="{bw}" height="13" '
                    f'rx="6" fill="{c}" opacity=".85"/>')
            svg += (f'<text x="{w-148}" y="29" font-size="13" '
                    f'font-weight="bold" fill="#eee">{md.get("win_rate","")}</text>')
            svg += (f'<text x="{w-82}" y="29" font-size="9" '
                    f'fill="#888">{md.get("confidence","")}</text>')
            svg += '</g>'

        svg += '</svg>'
        cls._show(svg, th + 5)
