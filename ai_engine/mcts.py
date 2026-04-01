"""
🌳 محرك MCTS (Monte Carlo Tree Search)
نسخة مبسطة — يمكن تطويرها لاحقاً
"""

import random
import time
from typing import List, Optional
from game_engine.tiles import Tile, Direction, ALL_TILES
from game_engine.state import GameState, Pos, Move, Board
from config import Config


class MCTSEngine:
    """محاكاة مونت كارلو لتقييم الحركات"""

    def __init__(self, state: GameState, config: Config = None):
        self.state = state
        self.config = config or Config()

    def evaluate_moves(self) -> List[dict]:
        """قيّم كل حركة متاحة وأعطها نسبة فوز"""
        valid = self.state.valid_moves(Pos.ME)
        if not valid:
            return []

        results = []
        sims_per_move = max(
            50,
            self.config.MCTS_SIMULATIONS // max(len(valid), 1)
        )

        start = time.time()

        for move in valid:
            wins = 0
            total = 0

            for _ in range(sims_per_move):
                if time.time() - start > self.config.MCTS_TIME_LIMIT:
                    break
                if self._simulate_random(move):
                    wins += 1
                total += 1

            wr = wins / total if total > 0 else 0.5
            results.append({
                'move': move,
                'tile': move.tile,
                'direction': move.direction,
                'win_rate': wr,
                'simulations': total,
            })

        results.sort(key=lambda x: -x['win_rate'])
        return results

    def _simulate_random(self, first_move: Move) -> bool:
        """محاكاة عشوائية واحدة — هل فاز فريقنا؟"""
        # توزيع عشوائي للأحجار المتبقية
        known = set(self.state.my_hand)
        for t, _ in self.state.board.played_tiles:
            known.add(t)

        remaining = [t for t in ALL_TILES if t not in known]
        random.shuffle(remaining)

        # توزيع على اللاعبين الآخرين
        hands = {}
        for pos in [Pos.RIGHT, Pos.PARTNER, Pos.LEFT]:
            cnt = self.state.players[pos].count
            hands[pos] = remaining[:cnt]
            remaining = remaining[cnt:]

        # محاكاة اللعب
        sim_board = self._copy_board(self.state.board)
        sim_hands = {Pos.ME: list(self.state.my_hand)}
        sim_hands.update(hands)

        # تطبيق الحركة الأولى
        if not first_move.is_pass:
            sim_board.play(first_move.tile, first_move.direction)
            sim_hands[Pos.ME].remove(first_move.tile)

        turn = Pos.ME.next
        passes = 0

        for _ in range(100):  # حد أقصى 100 دور
            hand = sim_hands[turn]

            # أوجد حركة ممكنة
            playable = [t for t in hand if sim_board.can_play(t)]
            if playable:
                t = random.choice(playable)
                dirs = sim_board.get_directions(t)
                d = random.choice(dirs)
                sim_board.play(t, d)
                hand.remove(t)
                passes = 0

                if not hand:
                    return turn.is_friend
            else:
                passes += 1
                if passes >= 4:
                    # قفل — حساب النقاط
                    our = sum(t.total for t in sim_hands[Pos.ME]) + \
                          sum(t.total for t in sim_hands[Pos.PARTNER])
                    their = sum(t.total for t in sim_hands[Pos.RIGHT]) + \
                            sum(t.total for t in sim_hands[Pos.LEFT])
                    return our <= their

            turn = turn.next

        return False

    @staticmethod
    def _copy_board(board: Board) -> Board:
        b = Board()
        b.left = board.left
        b.right = board.right
        b._tiles = list(board._tiles)
        return b
