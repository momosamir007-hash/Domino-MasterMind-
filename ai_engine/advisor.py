""" 🧠 المستشار العبقري """
from typing import Dict, List, Tuple
from collections import defaultdict
from game_engine.state import GameState, Move, Pos
from game_engine.tiles import Tile, Direction
from ai_engine.xray import XRayEngine
from ai_engine.mcts import MCTSEngine
from config import Config

class GeniusAdvisor:
    """ المستشار: يحلل ← يفكر ← ينصح ← يشرح """

    def __init__(self, state: GameState, cfg: Config = None):
        self.state = state
        self.cfg = cfg or Config()
        self.xray = XRayEngine(state)

    def advise(self, sims: int = None, time_limit: float = None) -> Dict:
        """ النصيحة الكاملة
        Returns: {
            'best_move': Move,
            'win_rate': float,
            'explanation': str,
            'reasons': [str],
            'xray': {...},
            'analysis': {...},
            'all_moves': [...]
        } """
        sims = sims or self.cfg.MCTS_SIMULATIONS
        time_limit = time_limit or self.cfg.MCTS_TIME_LIMIT

        # 1. تحليل X-Ray
        xray_data = self.xray.xray_report()

        # 2. بحث MCTS
        engine = MCTSEngine(self.cfg)
        best_move, analysis = engine.search(self.state, sims, time_limit)

        # 3. شرح الحركة
        reasons = self._explain(best_move, analysis, xray_data)

        # 4. توليد الشرح المبسط
        explanation = self._simple_explanation(best_move, reasons)

        # 5. نسبة الفوز
        win_pct = 0.5
        if analysis['moves']:
            win_pct = analysis['moves'][0].get('win_pct', 0.5)

        return {
            'best_move': best_move,
            'win_rate': win_pct,
            'explanation': explanation,
            'reasons': reasons,
            'xray': xray_data,
            'analysis': analysis,
            'all_moves': analysis['moves'],
        }

    def _explain(self, move: Move, analysis: Dict, xray: Dict) -> List[str]:
        """ لماذا هذه الحركة؟ أسباب ذكية """
        reasons = []
        if move.is_pass:
            reasons.append("🚫 ما عندك حجر مناسب - مجبور تدق")
            return reasons

        tile = move.tile
        direction = move.direction

        # ─── 1. التحكم بالأرقام ───
        sim = self.state.clone()
        sim.apply(move)
        if not sim.board.is_empty:
            remaining = self._count_remaining()
            for end in sim.board.ends:
                my_count = sum(1 for t in self.state.my_hand
                               if t != tile and t.has(end))
                total_left = remaining.get(end, 0)
                if my_count >= 2 and total_left <= 4:
                    reasons.append(
                        f"💪 تسيطر على الرقم {end}: "
                        f"عندك {my_count} أحجار "
                        f"من أصل {total_left} متبقية"
                    )
                elif my_count >= 1 and total_left <= 2:
                    reasons.append(
                        f"🎯 تتحكم بالرقم {end} بالكامل تقريباً"
                    )

        # ─── 2. القفل على الخصم ───
        for pos in [Pos.RIGHT, Pos.LEFT]:
            p = self.state.players[pos]
            if not sim.board.is_empty:
                for end in sim.board.ends:
                    if end in p.passed_on:
                        reasons.append(
                            f"🚫 تقفل على {pos.label}: "
                            f"ما عنده الرقم {end}"
                        )

        # ─── 3. التخلص من حجر ثقيل ───
        if tile.total >= 9:
            reasons.append(
                f"⚖️ تتخلص من حجر ثقيل "
                f"({tile.total} نقطة)"
            )
        if tile.is_double and tile.total >= 8:
            reasons.append(
                f"🎲 تتخلص من دبل ثقيل {tile}"
            )

        # ─── 4. مساعدة الشريك ───
        partner = self.state.players[Pos.PARTNER]
        pref = defaultdict(int)
        for t in partner.played:
            pref[t.a] += 1
            if not t.is_double:
                pref[t.b] += 1
        if not sim.board.is_empty:
            for end in sim.board.ends:
                if pref.get(end, 0) >= 2:
                    reasons.append(
                        f"🤝 تفتح للشريك: لعب من الرقم "
                        f"{end} قبل كذا ({pref[end]} مرات)"
                    )

        # ─── 5. إجبار الخصم على الباس ───
        # تحقق: لو الخصم التالي ما عنده الرقمين
        next_enemy = None
        next_pos = Pos((self.state.turn.value + 1) % 4)
        if next_pos.is_enemy:
            next_enemy = next_pos
        if next_enemy and not sim.board.is_empty:
            enemy = self.state.players[next_enemy]
            both_blocked = all(end in enemy.passed_on
                               for end in sim.board.ends)
            if both_blocked:
                reasons.append(
                    f"⚡ ستجبر {next_enemy.label} "
                    f"على الباس! (ما عنده أي طرف)"
                )

        # ─── 6. تجهيز حركة مستقبلية ───
        if not sim.board.is_empty:
            for end in sim.board.ends:
                future = [t for t in self.state.my_hand
                          if t != tile and t.has(end)]
                if future:
                    next_tile = future[0]
                    reasons.append(
                        f"🔮 يفتح لك: تقدر تلعب "
                        f"{next_tile} الدور الجاي"
                    )
                    break

        if not reasons:
            reasons.append("✅ أفضل حركة متاحة حسب التحليل")
        return reasons

    def _simple_explanation(self, move: Move, reasons: List[str]) -> str:
        """شرح مبسط بسطر واحد"""
        if move.is_pass:
            return "ما عندك حجر مناسب. ادق!"
        d = "اليسار" if move.direction == Direction.LEFT else "اليمين"
        base = f"العب {move.tile} على {d}."

        # أهم سبب
        if reasons:
            # نختار أقوى سبب
            for r in reasons:
                if "تقفل" in r or "تجبر" in r:
                    return f"{base} {r}"
                if "تسيطر" in r or "تتحكم" in r:
                    return f"{base} {r}"
            return f"{base} {reasons[0]}"
        return base

    def _count_remaining(self) -> Dict[int, int]:
        """كم حجر متبقي لكل رقم"""
        from game_engine.tiles import ALL_TILES
        total = defaultdict(int)
        for t in ALL_TILES:
            total[t.a] += 1
            if not t.is_double:
                total[t.b] += 1
        known = defaultdict(int)
        for t in self.state.known:
            known[t.a] += 1
            if not t.is_double:
                known[t.b] += 1
        return {i: total[i] - known[i] for i in range(7)}
