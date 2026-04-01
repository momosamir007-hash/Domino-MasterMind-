""" 🌳 Monte Carlo Tree Search موجّه بالاستنتاج من X-Ray Engine """
import math
import time
import random
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
from game_engine.state import GameState, Move, Pos
from game_engine.tiles import Direction
from ai_engine.xray import XRayEngine
from config import Config

@dataclass
class Node:
    state: GameState
    move: Optional[Move] = None
    parent: Optional['Node'] = None
    children: List['Node'] = field(default_factory=list)
    wins: float = 0.0
    visits: int = 0
    untried: List[Move] = field(default_factory=list)

    def __post_init__(self):
        if not self.untried and not self.state.game_over:
            self.untried = self.state.valid_moves(self.state.turn)

    @property
    def expanded(self) -> bool:
        return len(self.untried) == 0

    def ucb1(self, c=1.414) -> float:
        if self.visits == 0:
            return float('inf')
        return (self.wins / self.visits +
                c * math.sqrt(math.log(self.parent.visits) / self.visits))

    def best_child(self, c=1.414) -> 'Node':
        return max(self.children, key=lambda n: n.ucb1(c))

    def most_visited(self) -> 'Node':
        return max(self.children, key=lambda n: n.visits)

class MCTSEngine:
    def __init__(self, cfg: Config = None):
        self.cfg = cfg or Config()

    def search(self, state: GameState,
               sims: int = None, time_limit: float = None) -> Tuple[Move, Dict]:
        """ البحث عن أفضل حركة
        Returns: (أفضل حركة, تحليل مفصل) """
        sims = sims or self.cfg.MCTS_SIMULATIONS
        time_limit = time_limit or self.cfg.MCTS_TIME_LIMIT

        xray = XRayEngine(state)
        root = Node(state=state.clone())
        t0 = time.time()
        done = 0

        while done < sims and (time.time() - t0) < time_limit:
            # 1. Selection
            node = self._select(root)
            # 2. Expansion
            if (not node.state.game_over and not node.expanded):
                node = self._expand(node)
            # 3. Simulation
            result = self._simulate(node, xray)
            # 4. Backpropagation
            self._backprop(node, result)
            done += 1

        best = root.most_visited()
        analysis = self._analyze(root, done, time.time() - t0)
        return best.move, analysis

    def _select(self, node: Node) -> Node:
        while (not node.state.game_over and node.expanded and node.children):
            node = node.best_child(self.cfg.MCTS_EXPLORATION)
        return node

    def _expand(self, node: Node) -> Node:
        idx = random.randint(0, len(node.untried) - 1)
        move = node.untried.pop(idx)
        new_state = node.state.clone()
        new_state.apply(move)
        child = Node(state=new_state, move=move, parent=node)
        node.children.append(child)
        return child

    def _simulate(self, node: Node, xray: XRayEngine) -> float:
        """ محاكاة لعبة كاملة مع توزيع ذكي للأحجار """
        sim = node.state.clone()
        # توزيع الأحجار المجهولة بذكاء
        hands = xray.generate_hands(1)
        if hands:
            for pos, tiles in hands[0].items():
                sim.players[pos].hand = tiles

        # لعب حتى النهاية
        steps = 0
        while not sim.game_over and steps < 80:
            moves = sim.valid_moves(sim.turn)
            real = [m for m in moves if not m.is_pass]
            if real:
                # اختيار ذكي: تفضيل الدبل والثقيل
                weights = []
                for m in real:
                    w = 1.0 + m.tile.total * 0.15
                    if m.tile.is_double:
                        w += 2.0
                    weights.append(w)
                total_w = sum(weights)
                probs = [w / total_w for w in weights]
                idx = random.choices(range(len(real)), weights=probs, k=1)[0]
                move = real[idx]
            else:
                move = moves[0]   # باس
            sim.apply(move)
            steps += 1

        # تقييم النتيجة
        if sim.winner and sim.winner.is_friend:
            return 1.0
        elif sim.winner and sim.winner.is_enemy:
            return 0.0
        return 0.5

    def _backprop(self, node: Node, result: float):
        current = node
        while current:
            current.visits += 1
            # عكس النتيجة للخصم
            if current.state.turn.is_enemy:
                current.wins += (1.0 - result)
            else:
                current.wins += result
            current = current.parent

    def _analyze(self, root: Node, sims: int, elapsed: float) -> Dict:
        analysis = {
            'simulations': sims,
            'time': f"{elapsed:.1f}s",
            'moves': [],
        }
        ranked = sorted(root.children, key=lambda c: c.visits, reverse=True)
        for child in ranked:
            wr = child.wins / child.visits if child.visits > 0 else 0
            if wr >= 0.75:
                conf = "🟢 ممتاز"
            elif wr >= 0.55:
                conf = "🟡 جيد"
            elif wr >= 0.40:
                conf = "🟠 متوسط"
            else:
                conf = "🔴 ضعيف"
            analysis['moves'].append({
                'move': str(child.move),
                'tile': child.move.tile,
                'direction': child.move.direction,
                'visits': child.visits,
                'win_rate': f"{wr:.0%}",
                'win_pct': wr,
                'confidence': conf,
                'is_pass': child.move.is_pass,
            })
        return analysis
