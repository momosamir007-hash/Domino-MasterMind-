""" حالة اللعبة الكاملة """
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional
from enum import Enum
import copy
from game_engine.tiles import Tile, Board, Direction, ALL_TILES

class Pos(Enum):
    """مواقع اللاعبين"""
    ME = 0       # أنت (جنوب)
    RIGHT = 1    # يمينك (غرب) - خصم
    PARTNER = 2  # شريكك (شمال)
    LEFT = 3     # يسارك (شرق) - خصم

    @property
    def is_enemy(self) -> bool:
        return self in (Pos.RIGHT, Pos.LEFT)

    @property
    def is_friend(self) -> bool:
        return self in (Pos.ME, Pos.PARTNER)

    @property
    def label(self) -> str:
        return {
            Pos.ME: "أنت 🟢",
            Pos.RIGHT: "خصم يمين 🔴",
            Pos.PARTNER: "شريكك 🔵",
            Pos.LEFT: "خصم يسار 🟠",
        }[self]

    @property
    def icon(self) -> str:
        return {
            Pos.ME: "🟢",
            Pos.RIGHT: "🔴",
            Pos.PARTNER: "🔵",
            Pos.LEFT: "🟠",
        }[self]

@dataclass
class Player:
    pos: Pos
    hand: List[Tile] = field(default_factory=list)
    count: int = 7
    passed_on: Set[int] = field(default_factory=set)
    played: List[Tile] = field(default_factory=list)

    @property
    def total(self) -> int:
        return sum(t.total for t in self.hand)

    def remove(self, tile: Tile):
        if tile in self.hand:
            self.hand.remove(tile)
            self.count = max(0, self.count - 1)

@dataclass
class Move:
    who: Pos
    tile: Optional[Tile]
    direction: Optional[Direction]

    @property
    def is_pass(self) -> bool:
        return self.tile is None

    def __repr__(self):
        if self.is_pass:
            return f"{self.who.label}: دق 🚫"
        d = "⬅️" if self.direction == Direction.LEFT else "➡️"
        return f"{self.who.label}: {self.tile} {d}"

@dataclass
class GameState:
    board: Board = field(default_factory=Board)
    players: Dict[Pos, Player] = field(default_factory=dict)
    turn: Pos = Pos.ME
    history: List[Move] = field(default_factory=list)
    passes: int = 0
    game_over: bool = False
    winner: Optional[Pos] = None

    def __post_init__(self):
        if not self.players:
            for p in Pos:
                self.players[p] = Player(pos=p)

    def set_my_hand(self, tiles: List[Tile]):
        me = self.players[Pos.ME]
        me.hand = list(tiles)
        me.count = len(tiles)

    @property
    def my_hand(self) -> List[Tile]:
        return self.players[Pos.ME].hand

    @property
    def known(self) -> Set[Tile]:
        s = set(self.my_hand)
        s.update(self.board.tiles_on_table)
        return s

    @property
    def unknown(self) -> Set[Tile]:
        return ALL_TILES - self.known

    def valid_moves(self, who: Pos) -> List[Move]:
        p = self.players[who]
        moves = []
        if self.board.is_empty:
            for t in p.hand:
                moves.append(Move(who, t, Direction.LEFT))
        else:
            for t in p.hand:
                for d in self.board.can_play(t):
                    moves.append(Move(who, t, d))
        if not moves:
            moves.append(Move(who, None, None))
        return moves

    def apply(self, move: Move) -> bool:
        p = self.players[move.who]
        if move.is_pass:
            if not self.board.is_empty:
                p.passed_on.update(self.board.ends)
            self.passes += 1
            if self.passes >= 4:
                self.game_over = True
                self._winner_by_points()
        else:
            ok = self.board.play(move.tile, move.direction)
            if not ok:
                return False
            p.remove(move.tile)
            p.played.append(move.tile)
            self.passes = 0
            if p.count <= 0:
                self.game_over = True
                self.winner = move.who
        self.history.append(move)
        self.turn = Pos((self.turn.value + 1) % 4)
        return True

    def _winner_by_points(self):
        best, bp = None, 999
        for pos, pl in self.players.items():
            if pl.total < bp:
                bp = pl.total
                best = pos
        self.winner = best

    def clone(self) -> GameState:
        return copy.deepcopy(self)
