"""
🔬 محرك X-Ray — تحليل احتمالات أحجار الخصوم
يعتمد على:
  1. أحجارنا (معروفة)
  2. الأحجار الملعوبة على الطاولة (معروفة)
  3. سجل الباس (إذا دق على رقم = مستحيل عنده هذا الرقم)
"""

from typing import Dict, List, Tuple
from game_engine.tiles import Tile, ALL_TILES
from game_engine.state import GameState, Pos, Board


class XRayEngine:
    def __init__(self, state: GameState):
        self.state = state
        self._compute()

    def _compute(self):
        """حساب الأحجار المستحيلة والمحتملة لكل خصم"""
        # الأحجار المعروفة (يدي + ملعوبة)
        known = set()
        for t in self.state.my_hand:
            known.add(t)
        for t, _ in self.state.board.played_tiles:
            known.add(t)

        self.remaining = [t for t in ALL_TILES if t not in known]

        # تحليل الباس لاستبعاد أرقام
        self.impossible: Dict[Pos, set] = {p: set() for p in Pos if p != Pos.ME}

        board = self.state.board
        for move in self.state.move_history:
            if move.is_pass and move.pos != Pos.ME:
                # عند الباس، الأطراف المفتوحة وقتها = أرقام ما عنده
                # نأخذ الأطراف من الطاولة في تلك اللحظة
                # (تقريب: نستخدم الأطراف الحالية)
                if board.left is not None:
                    self.impossible[move.pos].add(board.left)
                if board.right is not None:
                    self.impossible[move.pos].add(board.right)

    def xray_report(self) -> Dict[Pos, dict]:
        """تقرير X-Ray لكل لاعب"""
        report = {}
        for pos in [Pos.RIGHT, Pos.PARTNER, Pos.LEFT]:
            p = self.state.players[pos]
            imp_nums = self.impossible.get(pos, set())

            # أحجار مستحيلة
            cant_have = [t for t in self.remaining
                         if t.has_any(imp_nums)]

            # أحجار محتملة
            possible = [t for t in self.remaining
                        if t not in cant_have]

            # ترتيب حسب الاحتمالية (تقريب بسيط)
            count = p.count
            total_possible = len(possible) if possible else 1
            likely = [(t, min(count / total_possible, 1.0))
                      for t in possible]
            likely.sort(key=lambda x: -x[1])

            # أحجار مؤكدة (إذا عدد المتبقي = عدد الممكن)
            certain = []
            if len(possible) <= count:
                certain = possible[:]

            report[pos] = {
                'count': count,
                'impossible_count': len(cant_have),
                'cant_have': list(imp_nums),
                'certain': certain,
                'likely': likely,
            }

        return report


def _has_any(tile: Tile, nums: set) -> bool:
    """هل الحجر يحتوي على أي من هذه الأرقام؟"""
    return tile.a in nums or tile.b in nums


# إضافة الدالة للـ Tile
Tile.has_any = lambda self, nums: self.a in nums or self.b in nums
