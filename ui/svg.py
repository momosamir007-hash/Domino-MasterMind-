"""
🎨 محرك رسم SVG المطور - النسخة الكاملة
تم إصلاح مشكلة ترتيب الحجارة لتظهر كسلسلة متصلة ومنظمة على الطاولة.
"""
import streamlit.components.v1 as components
from typing import List, Optional
from game_engine.domino_board import DominoTile, Board, Direction
from game_engine.game_state import GameState, PlayerPosition

# إحداثيات النقاط (Pips) داخل كل نصف من حجر الدومينو
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
        """
        tw: عرض الحجر
        th: ارتفاع الحجر
        pr: نصف قطر النقطة
        sp: المسافة الفاصلة بين الحجارة
        """
        self.tw = tw
        self.th = th
        self.pr = pr
        self.sp = sp
        self.hw = tw // 2 # نصف عرض الحجر

    @staticmethod
    def display(svg_code: str, height: int = 200):
        """عرض كود SVG داخل مكون Streamlit"""
        html = f"""
        <div style="display:flex; justify-content:center; align-items:center; width:100%; overflow-x:auto; padding:10px 0; background:transparent;">
            {svg_code}
        </div>
        """
        components.html(html, height=height, scrolling=True)

    def _pips(self, count, ox, oy, aw, ah, dbl=False):
        """رسم النقاط (الدوائر) داخل نصف الحجر"""
        pts = PIP_POSITIONS.get(count, [])
        clr = "#CC0000" if dbl else "#1a1a1a" # اللون الأحمر للدبل والأسود للعادي
        pad = 8
        s = ""
        for px, py in pts:
            cx = ox + pad + px * (aw - 2 * pad)
            cy = oy + pad + py * (ah - 2 * pad)
            s += f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{self.pr}" fill="{clr}"/>\n'
        return s

    def tile_svg(self, tile, x=0, y=0, hl=False, label=""):
        """رسم حجر دومينو واحد بصيغة SVG كعنصر مجموعة <g>"""
        fill = "#E8F8F5" if hl else "#FFFFFF"
        stroke = "#27AE60" if hl else "#34495E"
        sw = 3 if hl else 2
        
        s = f'<g transform="translate({x},{y})">\n'
        # ظل الحجر
        s += f'<rect x="2" y="2" width="{self.tw}" height="{self.th}" rx="6" fill="rgba(0,0,0,0.1)"/>\n'
        # جسم الحجر
        s += f'<rect width="{self.tw}" height="{self.th}" rx="6" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>\n'
        # خط المنتصف الفاصل
        s += f'<line x1="{self.hw}" y1="4" x2="{self.hw}" y2="{self.th-4}" stroke="#BDC3C7" stroke-width="1" stroke-dasharray="2,2"/>\n'
        # رسم النقاط في النصفين
        s += self._pips(tile.high, 0, 0, self.hw, self.th, tile.is_double)
        s += self._pips(tile.low, self.hw, 0, self.hw, self.th, tile.is_double)
        
        if label:
            s += f'<text x="{self.tw//2}" y="{self.th+15}" text-anchor="middle" font-family="Arial" font-size="11" fill="#ECF0F1" font-weight="bold">{label}</text>\n'
        
        s += '</g>\n'
        return s

    def board_svg(self, board, width=900, height=200):
        """توليد كود SVG للطاولة مع رصف الحجارة الملعوبة"""
        if board.is_empty:
            return f"""
            <svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
                <rect width="100%" height="100%" rx="15" fill="#1B5E20" stroke="#2E7D32" stroke-width="3"/>
                <text x="50%" y="50%" text-anchor="middle" font-family="Arial" font-size="18" fill="white" opacity="0.4">🎲 الطاولة فارغة - بانتظار الحركة الأولى</text>
            </svg>
            """

        # الحصول على قائمة الحجارة الملعوبة من محرك اللعبة
        played_items = board.all_played_tiles # قائمة الحجارة بالترتيب
        n = len(played_items)
        
        # حساب العرض المطلوب بناءً على عدد الحجارة لمنع التداخل
        total_tile_w = self.tw + self.sp
        content_width = n * total_tile_w + 120
        svg_w = max(width, content_width)
        
        s = f'<svg viewBox="0 0 {svg_w} {height}" width="{svg_w}" height="{height}" xmlns="http://www.w3.org/2000/svg">\n'
        # خلفية الطاولة الخضراء
        s += f'<rect width="{svg_w}" height="{height}" rx="15" fill="#1B5E20" stroke="#2E7D32" stroke-width="3"/>\n'
        
        # حساب إزاحة البداية لتوسيط السلسلة ديناميكياً
        start_x = (svg_w - (n * total_tile_w) + self.sp) // 2
        mid_y = (height - self.th) // 2

        # رسم الحجارة بترتيب رصفها المتسلسل
        for i, tile in enumerate(played_items):
            tx = start_x + (i * total_tile_w)
            s += self.tile_svg(tile, tx, mid_y)

        # رسم أرقام الأطراف المفتوحة (يسار/يمين) للوضوح
        s += f'<rect x="10" y="{height//2 - 20}" width="40" height="40" rx="8" fill="rgba(255,255,255,0.1)"/>'
        s += f'<text x="30" y="{height//2 + 8}" text-anchor="middle" font-family="Arial" font-size="22" font-weight="bold" fill="#A5D6A7">{board.left_end}</text>'
        
        s += f'<rect x="{svg_w - 50}" y="{height//2 - 20}" width="40" height="40" rx="8" fill="rgba(255,255,255,0.1)"/>'
        s += f'<text x="{svg_w - 30}" y="{height//2 + 8}" text-anchor="middle" font-family="Arial" font-size="22" font-weight="bold" fill="#A5D6A7">{board.right_end}</text>'
        
        s += f'<text x="30" y="{height-10}" text-anchor="middle" font-size="10" fill="rgba(255,255,255,0.3)">يسار</text>'
        s += f'<text x="{svg_w-30}" y="{height-10}" text-anchor="middle" font-size="10" fill="rgba(255,255,255,0.3)">يمين</text>'
        
        s += '</svg>'
        return s

    def display_board(self, board, width=900, height=200):
        """عرض الطاولة على الواجهة"""
        svg = self.board_svg(board, width, height)
        self.display(svg, height + 20)

    def hand_svg(self, tiles, highlighted=None, title="يدك"):
        """توليد كود SVG ليد اللاعب"""
        highlighted = highlighted or []
        n = len(tiles)
        if n == 0:
            return f'<svg width="400" height="80"><text x="50%" y="50%" text-anchor="middle" fill="#4CAF50">✨ دومينو! اليد فارغة</text></svg>'
        
        total_w = n * (self.tw + self.sp) + 40
        total_h = self.th + 45
        
        s = f'<svg viewBox="0 0 {total_w} {total_h}" width="{total_w}" height="{total_h}" xmlns="http://www.w3.org/2000/svg">\n'
        s += f'<text x="{total_w//2}" y="15" text-anchor="middle" font-family="Arial" font-size="12" font-weight="bold" fill="#BDC3C7">{title}</text>\n'
        
        for i, tile in enumerate(tiles):
            tx = 20 + i * (self.tw + self.sp)
            s += self.tile_svg(tile, tx, 25, hl=(i in highlighted), label=f"({i+1})")
        
        s += '</svg>'
        return s

    def display_hand(self, tiles, highlighted=None, title="يدك"):
        """عرض يد اللاعب على الواجهة"""
        svg = self.hand_svg(tiles, highlighted, title)
        self.display(svg, self.th + 60)

    def players_svg(self, state, width=700, height=420):
        """رسم خريطة توزيع اللاعبين حول الطاولة"""
        cx, cy = width // 2, height // 2
        
        pos_xy = {
            PlayerPosition.SOUTH: (cx, height - 60),
            PlayerPosition.NORTH: (cx, 60),
            PlayerPosition.WEST: (90, cy),
            PlayerPosition.EAST: (width - 90, cy),
        }
        
        labels = {
            PlayerPosition.SOUTH: "أنت 🟢",
            PlayerPosition.NORTH: "شريكك 🔵",
            PlayerPosition.WEST: "خصم يمين 🔴",
            PlayerPosition.EAST: "خصم يسار 🟠",
        }
        
        clrs = {
            PlayerPosition.SOUTH: "#4CAF50",
            PlayerPosition.NORTH: "#2196F3",
            PlayerPosition.WEST: "#F44336",
            PlayerPosition.EAST: "#FF9800",
        }

        s = f'<svg viewBox="0 0 {width} {height}" width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">\n'
        # الطاولة المركزية
        s += f'<ellipse cx="{cx}" cy="{cy}" rx="{width//3.5}" ry="{height//4.5}" fill="#1B5E20" stroke="#2E7D32" stroke-width="2"/>\n'
        s += f'<text x="{cx}" y="{cy+5}" text-anchor="middle" font-size="14" fill="rgba(255,255,255,0.3)">ساحة اللعب</text>\n'
        
        for pos in PlayerPosition:
            p = state.players[pos]
            px, py = pos_xy[pos]
            clr = clrs[pos]
            is_turn = (pos == state.current_turn)
            
            bw, bh = 130, 75
            bx, by = px - bw // 2, py - bh // 2
            
            # بطاقة اللاعب
            s += f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="12" fill="#111128" stroke="{clr}" stroke-width="{"3" if is_turn else "1"}"/>\n'
            s += f'<rect x="{bx}" y="{by}" width="{bw}" height="24" rx="12" fill="{clr}" opacity="0.9"/>\n'
            s += f'<text x="{px}" y="{by+17}" text-anchor="middle" font-family="Arial" font-size="12" font-weight="bold" fill="white">{labels[pos]}</text>\n'
            
            # عدد الأحجار المتبقية
            count = len(p.hand) if p.is_me else p.tiles_count
            s += f'<text x="{px}" y="{by+45}" text-anchor="middle" font-family="Arial" font-size="13" fill="#ECF0F1">أحجار: {count}</text>\n'
            
            # عرض أيقونات الأحجار المتبقية بشكل رمزي
            icons = "🀫 " * min(count, 7)
            s += f'<text x="{px}" y="{by+62}" text-anchor="middle" font-size="12" fill="{clr}">{icons}</text>\n'
            
            # مؤشر الدور الحالي (نقطة وامضة)
            if is_turn:
                s += f'<circle cx="{bx+bw-10}" cy="{by+10}" r="5" fill="#FFF"><animate attributeName="opacity" values="1;0.2;1" dur="1s" repeatCount="indefinite"/></circle>'
        
        s += '</svg>'
        return s

    def display_players(self, state, width=700, height=420):
        """عرض توزيع اللاعبين على الواجهة"""
        svg = self.players_svg(state, width, height)
        self.display(svg, height + 10)

    def display_big_tile(self, tile, label=""):
        """رسم حجر كبير لعرض التوصيات"""
        tw_orig, th_orig = self.tw, self.th
        self.tw, self.th = 160, 80
        self.hw = 80
        
        svg = f'<svg width="200" height="130" xmlns="http://www.w3.org/2000/svg">\n'
        svg += self.tile_svg(tile, 20, 10, hl=True)
        if label:
            svg += f'<text x="100" y="115" text-anchor="middle" font-family="Arial" font-size="14" font-weight="bold" fill="#4CAF50">{label}</text>'
        svg += '</svg>'
        
        self.tw, self.th = tw_orig, th_orig
        self.hw = tw_orig // 2
        self.display(svg, 140)
