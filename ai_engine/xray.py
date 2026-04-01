""" 🔬 محرك الأشعة السينية المنطقية (X-Ray Engine) """
from typing import Dict, List, Set, Tuple
from collections import defaultdict
import random
from game_engine.tiles import Tile, ALL_TILES
from game_engine.state import GameState, Pos, Player

class XRayEngine:
    """ العقل التحليلي - يرى ما لا تراه العين """

    def __init__(self, state: GameState):
        self.state = state

    # ═══════════════════════════════════
    # 1. الأحجار المستحيلة لكل لاعب
    # ═══════════════════════════════════
    def impossible_tiles(self, pos: Pos) -> Set[Tile]:
        """ الأحجار التي يستحيل أن يملكها هذا اللاعب بناءً على الأرقام التي "باس" عليها """
        player = self.state.players[pos]
        impossible = set()
        for tile in self.state.unknown:
            # لو باس على كلا رقمي الحجر
            if tile.is_double:
                if tile.a in player.passed_on:
                    impossible.add(tile)
            else:
                # حجر عادي: لو باس على أحد أرقامه
                # فعندما كان الرقم على الطاولة ما قدر يلعبه
                # لكن الحجر ممكن يتلعب من الرقم الثاني
                # القاعدة الدقيقة: مستحيل لو باس على كليهما
                if (tile.a in player.passed_on and tile.b in player.passed_on):
                    impossible.add(tile)
        return impossible

    def impossible_values(self, pos: Pos) -> Set[int]:
        """الأرقام التي ما عنده منها أبداً"""
        return self.state.players[pos].passed_on.copy()

    # ═══════════════════════════════════
    # 2. خريطة الاحتمالات الكاملة
    # ═══════════════════════════════════
    def probability_map(self) -> Dict[Pos, Dict[Tile, float]]:
        """ لكل خصم: احتمال امتلاكه لكل حجر مجهول """
        others = [Pos.RIGHT, Pos.PARTNER, Pos.LEFT]
        unknown = list(self.state.unknown)
        if not unknown:
            return {p: {} for p in others}

        # المستحيل لكل لاعب
        imp = {p: self.impossible_tiles(p) for p in others}

        # الاحتمالات الخام
        raw: Dict[Pos, Dict[Tile, float]] = {p: {} for p in others}
        for tile in unknown:
            for pos in others:
                pl = self.state.players[pos]

                # مستحيل؟
                if tile in imp[pos]:
                    raw[pos][tile] = 0.0
                    continue

                # ما عنده أحجار؟
                if pl.count <= 0:
                    raw[pos][tile] = 0.0
                    continue

                # احتمال أساسي
                base = pl.count / len(unknown)

                # عامل "الباس الجزئي"
                # لو باس على أحد رقمي الحجر (مش كليهما)
                factor = 1.0
                if tile.a in pl.passed_on:
                    factor *= 0.05   # شبه مستحيل
                if tile.b in pl.passed_on:
                    factor *= 0.05

                # عامل "كثرة اللعب من رقم"
                played_vals = defaultdict(int)
                for pt in pl.played:
                    played_vals[pt.a] += 1
                    if not pt.is_double:
                        played_vals[pt.b] += 1
                for v in (tile.a, tile.b):
                    times = played_vals.get(v, 0)
                    factor *= 1.0 / (1.0 + times * 0.2)

                raw[pos][tile] = base * factor

        # تطبيع: مجموع كل حجر = 1
        for tile in unknown:
            total = sum(raw[p].get(tile, 0) for p in others)
            if total > 0:
                for p in others:
                    if tile in raw[p]:
                        raw[p][tile] /= total

        return raw

    # ═══════════════════════════════════
    # 3. الأحجار المؤكدة والمرجحة
    # ═══════════════════════════════════
    def certain_tiles(self, pos: Pos) -> List[Tile]:
        """ أحجار مؤكدة 100% عند هذا اللاعب (كل الآخرين مستحيل يملكوها) """
        probs = self.probability_map()
        others = [Pos.RIGHT, Pos.PARTNER, Pos.LEFT]
        certain = []
        for tile in self.state.unknown:
            p = probs.get(pos, {}).get(tile, 0)
            if p >= 0.95:   # شبه مؤكد
                certain.append(tile)
        return certain

    def likely_tiles(self, pos: Pos, threshold: float = 0.5) -> List[Tuple[Tile, float]]:
        """أحجار مرجحة (احتمال > threshold)"""
        probs = self.probability_map()
        likely = []
        for tile, prob in probs.get(pos, {}).items():
            if prob >= threshold:
                likely.append((tile, prob))
        likely.sort(key=lambda x: x[1], reverse=True)
        return likely

    # ═══════════════════════════════════
    # 4. تقرير X-Ray كامل
    # ═══════════════════════════════════
    def xray_report(self) -> Dict:
        """ تقرير شامل عن كل لاعب """
        report = {}
        probs = self.probability_map()
        for pos in [Pos.RIGHT, Pos.PARTNER, Pos.LEFT]:
            pl = self.state.players[pos]
            # ترتيب الأحجار حسب الاحتمال
            sorted_tiles = sorted(
                probs.get(pos, {}).items(),
                key=lambda x: x[1],
                reverse=True,
            )
            report[pos] = {
                'count': pl.count,
                'passed_on': sorted(pl.passed_on),
                'impossible_count': len(self.impossible_tiles(pos)),
                'certain': self.certain_tiles(pos),
                'likely': sorted_tiles[:10],
                'cant_have': sorted(pl.passed_on),
            }
        return report

    # ═══════════════════════════════════
    # 5. توليد أيدي محتملة للمحاكاة
    # ═══════════════════════════════════
    def generate_hands(self, n: int = 50) -> List[Dict[Pos, List[Tile]]]:
        """ توليد n سيناريو محتمل لتوزيع الأحجار مع مراعاة كل القيود (الباس) """
        unknown = list(self.state.unknown)
        others = [Pos.RIGHT, Pos.PARTNER, Pos.LEFT]
        sizes = {p: self.state.players[p].count for p in others}
        imp = {p: self.impossible_tiles(p) for p in others}

        results = []
        attempts = 0
        max_attempts = n * 5
        while len(results) < n and attempts < max_attempts:
            attempts += 1
            sample = self._one_sample(unknown, others, sizes, imp)
            if sample:
                results.append(sample)
        return results

    def _one_sample(self, unknown, others, sizes, imp):
        """توليد توزيع واحد صحيح"""
        pool = list(unknown)
        random.shuffle(pool)
        hands = {p: [] for p in others}
        used = set()
        # ترتيب: اللاعب بقيود أكثر أولاً
        sorted_others = sorted(others, key=lambda p: len(imp[p]), reverse=True)
        for pos in sorted_others:
            need = sizes[pos]
            eligible = [t for t in pool if t not in used and t not in imp[pos]]
            if len(eligible) < need:
                return None
            chosen = random.sample(eligible, need)
            hands[pos] = chosen
            used.update(chosen)
        return hands
