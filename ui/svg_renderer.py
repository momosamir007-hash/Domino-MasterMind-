"""
🎨 محرك رسم SVG المطور - حل مشكلة الترتيب التلقائي
تم تعديله لضمان رصف الحجارة بشكل متسلسل ومنظم على الطاولة.
"""
import streamlit.components.v1 as components
from typing import List, Optional
from game_engine.domino_board import DominoTile, Board, Direction
from game_engine.game_state import GameState, PlayerPosition

# إحداثيات النقاط داخل الحجر
PIP_POSITIONS = {
    0: [],
    1: [(0.5, 0.5)],
    2: [(0.25, 0.75), (0.75, 0.25)],
    3: [(0.25, 0.75), (0.5, 0.5), (0.75, 0.25)],
    4: [(0.25, 0.25), (0.25, 0.75), (0.75, 0.25), (0.75, 0.75)],
    5: [(0.25, 0.25), (0.25, 0.75), (0.5, 0.5), (0.75, 0.25), (0.75, 0.75)],
    6: [(0.25, 0.25), (0.25, 0.5), (0.25, 0.75), (0.75, 0.25), (0.75, 0.5), (0.75, 0.75)],
}

class DominoSVG:
    def __init__(self, tw=100, th=50, pr=6, sp=8):
        self.tw = tw  # عرض الحجر
        self.th = th  # ارتفاع الحجر
        self.pr = pr  # قطر النقطة
        self.sp = sp  # المسافة بين الحجارة
        self.hw = tw // 2

    @staticmethod
    def display(svg_code: str, height: int = 200):
        html = f'<div style="display:flex;justify-content:center;width:100%;overflow-x:auto;padding:10px 0;">{svg_code}</div>'
        components.html(html, height=height, scrolling=True)

    def _pips(self, count, ox, oy, aw, ah, dbl=False):
        pts = PIP_POSITIONS.get(count, [])
        clr = "#CC0000" if dbl else "#1a1a1a"
        pad = 8
        s = ""
        for px, py in pts:
            cx = ox + pad + px * (aw - 2 * pad)
            cy = oy + pad + py * (ah - 2 * pad)
            s += f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{self.pr}" fill="{clr}"/>\n'
        return s

    def tile_svg(self, tile, x=0, y=0, hl=False, label=""):
        fill = "#E8F8F5" if hl else "#FFFFFF"
        stroke = "#27AE60" if hl else "#34495E"
        sw = 3 if hl else 2
        s = f'<g transform="translate({x},{y})">\n'
        s += f'<rect x="2" y="2" width="{self.tw}" height="{self.th}" rx="6" fill="rgba(0,0,0,0.1)"/>\n'
        s += f'<rect width="{self.tw}" height="{self.th}" rx="6" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>\n'
        s += f'<line x1="{self.hw}" y1="4" x2="{self.hw}" y2="{self.th-4}" stroke="#BDC3C7" stroke-width="1" stroke-dasharray="2,2"/>\n'
        s += self._pips(tile.high, 0, 0, self.hw, self.th, tile.is_double)
        s += self._pips(tile.low, self.hw, 0, self.hw, self.th, tile.is_double)
        if label:
            s += f'<text x="{self.tw//2}" y="{self.th+15}" text-anchor="middle" font-size="11" fill="#888" font-weight="bold">{label}</text>\n'
        s += '</g>\n'
        return s

    def display_board(self, board, width=900, height=180):
        if board.is_empty:
            svg = f'<svg width="{width}" height="{height}"><rect width="100%" height="100%" rx="15" fill="#1B5E20"/><text x="50%" y="50%" text-anchor="middle" fill="white" opacity="0.5">الطاولة فارغة - ابدأ اللعب</text></svg>'
            self.display(svg, height)
            return

        # الحل الجذري: ترتيب الحجارة بناءً على "سلسلة اللعب" الفعلية
        played_items = board.played_tiles # قائمة الـ (Tile, Direction)
        n = len(played_items)
        total_tile_w = self.tw + self.sp
        full_width = max(width, n * total_tile_w + 100)
        
        svg = f'<svg viewBox="0 0 {full_width} {height}" width="{full_width}" height="{height}">\n'
        svg += f'<rect width="{full_width}" height="{height}" rx="15" fill="#1B5E20" stroke="#2E7D32" stroke-width="3"/>\n'
        
        # حساب نقطة البداية (المنتصف)
        start_x = (full_width - (n * total_tile_w)) // 2
        mid_y = (height - self.th) // 2

        # رسم الحجارة بترتيب رصفها الحقيقي على الطاولة
        for i, (tile, _) in enumerate(played_items):
            tx = start_x + (i * total_tile_w)
            svg += self.tile_svg(tile, tx, mid_y)

        # إضافة الأطراف المفتوحة
        svg += f'<text x="20" y="{height-20}" fill="#A5D6A7" font-weight="bold">⬅️ {board.left_end}</text>'
        svg += f'<text x="{full_width-60}" y="{height-20}" fill="#A5D6A7" font-weight="bold">{board.right_end} ➡️</text>'
        svg += '</svg>'
        self.display(svg, height + 20)

    def display_hand(self, tiles, highlighted=None, title="يدك"):
        highlighted = highlighted or []
        n = len(tiles)
        tw = n * (self.tw + self.sp) + 40
        th = self.th + 40
        svg = f'<svg viewBox="0 0 {tw} {th}" width="{tw}" height="{th}">\n'
        for i, tile in enumerate(tiles):
            svg += self.tile_svg(tile, 20 + i*(self.tw+self.sp), 10, hl=(i in highlighted))
        svg += '</svg>'
        self.display(svg, th + 10)

    def display_players(self, state, width=700, height=400):
        # الكود الخاص برسم خريطة اللاعبين (يبقى كما هو لسلامة التوزيع)
        svg = self.players_svg(state, width, height)
        self.display(svg, height + 10)

    def players_svg(self, state, width, height):
        cx, cy = width // 2, height // 2
        s = f'<svg viewBox="0 0 {width} {height}" width="{width}" height="{height}">\n'
        s += f'<ellipse cx="{cx}" cy="{cy}" rx="{width//3}" ry="{height//4}" fill="#1B5E20" stroke="#2E7D32" stroke-width="2"/>\n'
        
        pos_map = {
            PlayerPosition.SOUTH: (cx, height - 60),
            PlayerPosition.NORTH: (cx, 60),
            PlayerPosition.WEST: (100, cy),
            PlayerPosition.EAST: (width - 100, cy)
        }
        
        for pos, (px, py) in pos_map.items():
            p = state.players[pos]
            clr = "#4CAF50" if pos == PlayerPosition.SOUTH else "#F44336" if "الخصم" in str(pos) else "#2196F3"
            is_turn = (pos == state.current_turn)
            sw = "4" if is_turn else "1"
            s += f'<rect x="{px-60}" y="{py-30}" width="120" height="60" rx="10" fill="#1a1a2e" stroke="{clr}" stroke-width="{sw}"/>\n'
            s += f'<text x="{px}" y="{py}" text-anchor="middle" fill="white" font-size="12">{p.position.name}</text>\n'
            s += f'<text x="{px}" y="{py+20}" text-anchor="middle" fill="{clr}" font-size="10">أحجار: {p.tiles_count}</text>\n'
        s += '</svg>'
        return s
