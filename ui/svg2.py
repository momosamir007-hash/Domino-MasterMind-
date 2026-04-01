""" 🎨 محرك SVG يعمل في Streamlit """
import streamlit.components.v1 as components
from typing import List, Optional
from game_engine.tiles import Tile, Board, Direction
from game_engine.state import GameState, Pos

# مواقع نقاط الدومينو
PIPS = {
    0: [],
    1: [(50, 50)],
    2: [(25, 75), (75, 25)],
    3: [(25, 75), (50, 50), (75, 25)],
    4: [(25, 25), (25, 75), (75, 25), (75, 75)],
    5: [(25, 25), (25, 75), (50, 50), (75, 25), (75, 75)],
    6: [(25, 25), (25, 50), (25, 75), (75, 25), (75, 50), (75, 75)],
}

class SVGRenderer:
    W = 110     # عرض الحجر
    H = 55      # ارتفاع الحجر
    R = 6       # نصف قطر النقطة
    GAP = 10    # فراغ بين الأحجار

    @staticmethod
    def _show(svg: str, h: int):
        """عرض SVG في Streamlit"""
        html = f'<div style="display:flex;justify-content:center;overflow-x:auto;padding:8px 0">{svg}</div>'
        components.html(html, height=h, scrolling=True)

    @classmethod
    def _dots(cls, val, ox, oy, w, h, dbl=False):
        """رسم النقاط"""
        color = "#CC0000" if dbl else "#1a1a1a"
        s = ""
        for px, py in PIPS.get(val, []):
            cx = ox + 8 + (px / 100) * (w - 16)
            cy = oy + 6 + (py / 100) * (h - 12)
            s += f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{cls.R}" fill="{color}"/>'
        return s

    @classmethod
    def tile(cls, t, x=0, y=0, glow=False, label=""):
        """رسم حجر واحد"""
        bg = "#C8E6C9" if glow else "#FFF"
        border = "#2E7D32" if glow else "#34495E"
        bw = 3 if glow else 1.5
        hw = cls.W // 2
        s = f'<g transform="translate({x},{y})">'
        # ظل
        s += f'<rect x="2" y="2" width="{cls.W}" height="{cls.H}" rx="7" fill="rgba(0,0,0,.12)"/>'
        # جسم
        s += f'<rect width="{cls.W}" height="{cls.H}" rx="7" fill="{bg}" stroke="{border}" stroke-width="{bw}"/>'
        # فاصل
        s += f'<line x1="{hw}" y1="4" x2="{hw}" y2="{cls.H-4}" stroke="#B0BEC5" stroke-width="1.5" stroke-dasharray="3,2"/>'
        # نقاط
        s += cls._dots(t.a, 0, 0, hw, cls.H, t.is_double)
        s += cls._dots(t.b, hw, 0, hw, cls.H, t.is_double)
        # تسمية
        if label:
            s += f'<text x="{cls.W//2}" y="{cls.H+15}" text-anchor="middle" font-size="12" fill="#aaa" font-weight="bold">{label}</text>'
        # توهج
        if glow:
            s += f'<rect width="{cls.W}" height="{cls.H}" rx="7" fill="none" stroke="#4CAF50" stroke-width="2"><animate attributeName="opacity" values="1;.3;1" dur="2s" repeatCount="indefinite"/></rect>'
        s += '</g>'
        return s

    @classmethod
    def hand(cls, tiles, glowing=None, title="يدك"):
        """رسم يد كاملة"""
        glowing = glowing or []
        n = len(tiles)
        if n == 0:
            svg = f'<svg width="350" height="70" xmlns="http://www.w3.org/2000/svg"><rect x="5" y="5" width="340" height="60" rx="10" fill="none" stroke="#4CAF50" stroke-dasharray="8,4" stroke-width="2"/><text x="175" y="42" text-anchor="middle" font-size="16" fill="#4CAF50">✨ دومينو!</text></svg>'
            cls._show(svg, 80)
            return
        tw = n * (cls.W + cls.GAP) + 30
        th = cls.H + 55
        svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {tw} {th}" width="{tw}" height="{th}">'
        svg += f'<text x="{tw//2}" y="15" text-anchor="middle" font-size="13" fill="#ccc" font-weight="bold">🃏 {title} ({n})</text>'
        for i, t in enumerate(tiles):
            x = 15 + i * (cls.W + cls.GAP)
            svg += cls.tile(t, x, 22, glow=(i in glowing), label=f"({i+1})")
        pts = sum(t.total for t in tiles)
        svg += f'<text x="{tw//2}" y="{th-2}" text-anchor="middle" font-size="11" fill="#888">مجموع: {pts}</text>'
        svg += '</svg>'
        cls._show(svg, th + 5)

    @classmethod
    def board(cls, brd, w=850, h=170):
        """رسم الطاولة"""
        if brd.is_empty:
            svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
            svg += f'<rect width="{w}" height="{h}" rx="12" fill="#1B5E20"/>'
            svg += f'<rect x="3" y="3" width="{w-6}" height="{h-6}" rx="10" fill="none" stroke="#4CAF50" stroke-width="2" stroke-dasharray="10,5"/>'
            svg += f'<text x="{w//2}" y="{h//2-5}" text-anchor="middle" font-size="20" fill="rgba(255,255,255,.7)">🎲</text>'
            svg += f'<text x="{w//2}" y="{h//2+20}" text-anchor="middle" font-size="15" fill="rgba(255,255,255,.5)">الطاولة فارغة</text>'
            svg += '</svg>'
            cls._show(svg, h + 10)
            return
        tiles = brd.tiles_on_table
        n = len(tiles)
        ttw = cls.W + cls.GAP
        aw = max(w, n * ttw + 100)
        svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {aw} {h}" width="{aw}" height="{h}">'
        svg += f'<rect width="{aw}" height="{h}" rx="12" fill="#1B5E20"/>'
        svg += f'<rect x="2" y="2" width="{aw-4}" height="{h-4}" rx="11" fill="none" stroke="#2E7D32" stroke-width="1.5"/>'
        sx = max(50, (aw - n * ttw) // 2)
        ty = (h - cls.H) // 2
        for i, t in enumerate(tiles):
            svg += cls.tile(t, sx + i * ttw, ty)
        # أطراف
        ey = h // 2 - 16
        svg += f'<g transform="translate(6,{ey})"><rect width="34" height="32" rx="7" fill="rgba(255,255,255,.2)"/><text x="17" y="23" text-anchor="middle" font-size="18" font-weight="bold" fill="#fff">{brd.left}</text></g>'
        svg += f'<g transform="translate({aw-40},{ey})"><rect width="34" height="32" rx="7" fill="rgba(255,255,255,.2)"/><text x="17" y="23" text-anchor="middle" font-size="18" font-weight="bold" fill="#fff">{brd.right}</text></g>'
        svg += f'<text x="23" y="{h-6}" text-anchor="middle" font-size="9" fill="rgba(255,255,255,.4)">⬅️ يسار</text>'
        svg += f'<text x="{aw-23}" y="{h-6}" text-anchor="middle" font-size="9" fill="rgba(255,255,255,.4)">يمين ➡️</text>'
        svg += '</svg>'
        cls._show(svg, h + 10)

    @classmethod
    def players(cls, state, w=680, h=400):
        """خريطة اللاعبين"""
        cx, cy = w // 2, h // 2
        xy = {
            Pos.ME: (cx, h - 45),
            Pos.PARTNER: (cx, 45),
            Pos.RIGHT: (75, cy),
            Pos.LEFT: (w - 75, cy),
        }
        clr = {
            Pos.ME: "#4CAF50",
            Pos.PARTNER: "#2196F3",
            Pos.RIGHT: "#F44336",
            Pos.LEFT: "#FF9800",
        }
        svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">'
        svg += f'<ellipse cx="{cx}" cy="{cy}" rx="{w//3}" ry="{h//4}" fill="#1B5E20" stroke="#2E7D32" stroke-width="2"/>'
        svg += f'<text x="{cx}" y="{cy+5}" text-anchor="middle" font-size="14" fill="rgba(255,255,255,.4)">🎲 الطاولة</text>'
        for pos in Pos:
            p = state.players[pos]
            px, py = xy[pos]
            c = clr[pos]
            it = pos == state.turn
            bw_v, bh_v = 125, 72
            bx, by = px - bw_v // 2, py - bh_v // 2
            svg += f'<rect x="{bx}" y="{by}" width="{bw_v}" height="{bh_v}" rx="10" fill="#111128" stroke="{c}" stroke-width="{"3" if it else "1.5"}"/>'
            svg += f'<rect x="{bx}" y="{by}" width="{bw_v}" height="22" rx="10" fill="{c}"/>'
            svg += f'<rect x="{bx}" y="{by+13}" width="{bw_v}" height="9" fill="{c}"/>'
            svg += f'<text x="{px}" y="{by+16}" text-anchor="middle" font-size="11" font-weight="bold" fill="white">{pos.label}</text>'
            tc = len(p.hand) if pos == Pos.ME else p.count
            svg += f'<text x="{px}" y="{by+40}" text-anchor="middle" font-size="11" fill="#ddd">أحجار: {tc}</text>'
            svg += f'<text x="{px}" y="{by+55}" text-anchor="middle" font-size="10">{"🀫" * min(tc, 7)}</text>'
            if p.passed_on:
                ps = ",".join(str(v) for v in sorted(p.passed_on))
                svg += f'<text x="{px}" y="{by+68}" text-anchor="middle" font-size="9" fill="#EF5350">🚫 {ps}</text>'
            if it:
                svg += f'<circle cx="{bx+bw_v-7}" cy="{by+7}" r="5" fill="#4CAF50"><animate attributeName="r" values="5;2;5" dur="1.5s" repeatCount="indefinite"/></circle>'
        svg += '</svg>'
        cls._show(svg, h + 5)

    @classmethod
    def analysis_chart(cls, moves_data, w=580):
        """رسم بياني للتحليل"""
        if not moves_data:
            return
        n = min(len(moves_data), 6)
        th = n * 46 + 45
        colors = ["#4CAF50", "#8BC34A", "#FFC107", "#FF9800", "#FF5722", "#9E9E9E"]
        icons = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣"]
        svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {th}" width="{w}" height="{th}">'
        svg += f'<text x="{w//2}" y="20" text-anchor="middle" font-size="14" font-weight="bold" fill="#ddd">📊 تحليل الخيارات</text>'
        for i, md in enumerate(moves_data[:n]):
            y = 32 + i * 46
            wp = md.get('win_pct', 0)
            bw = max(8, int((w - 190) * wp))
            c = colors[i] if i < len(colors) else "#666"
            ic = icons[i] if i < len(icons) else f"{i+1}."
            svg += f'<g transform="translate(12,{y})">'
            svg += f'<text x="0" y="20" font-size="16">{ic}</text>'
            svg += f'<text x="30" y="13" font-size="10" fill="#aaa">{md.get("move","")}</text>'
            svg += f'<rect x="30" y="18" width="{w-190}" height="13" rx="6" fill="#1a1a2e"/>'
            svg += f'<rect x="30" y="18" width="{bw}" height="13" rx="6" fill="{c}" opacity=".85"/>'
            svg += f'<text x="{w-148}" y="29" font-size="13" font-weight="bold" fill="#eee">{md.get("win_rate","")}</text>'
            svg += f'<text x="{w-82}" y="29" font-size="9" fill="#888">{md.get("confidence","")}</text>'
            svg += '</g>'
        svg += '</svg>'
        cls._show(svg, th + 5)
