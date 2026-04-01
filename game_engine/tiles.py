"""
أحجار الدومينو والطاولة
الملف كامل بدون أي اختصارات - تم إصلاح خطأ الاستنساخ المنطقي (Logic Bug)
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Set, Optional, Tuple
from enum import Enum
import copy

class Direction(Enum):
    LEFT = "left"
    RIGHT = "right"

@dataclass(frozen=True)
class Tile:
    """حجر دومينو واحد"""
    a: int
    b: int

    def __post_init__(self):
        # الحل الرياضي الآمن 100% لمنع خطأ الاستنساخ (Logic Bug)
        # نقوم بتحديد الرقم الأكبر والأصغر في متغيرات منفصلة ومستقلة أولاً
        max_val = max(self.a, self.b)
        min_val = min(self.a, self.b)
        
        # ثم نقوم بإسناد القيم النهائية للحجر 
        # (نستخدم object.__setattr__ لأن الكلاس من نوع frozen)
        object.__setattr__(self, 'a', max_val)
        object.__setattr__(self, 'b', min_val)

    @property
    def is_double(self) -> bool:
        return self.a == self.b

    @property
    def total(self) -> int:
        return self.a + self.b

    def has(self, v: int) -> bool:
        return v in (self.a, self.b)

    def other(self, v: int) -> int:
        if v == self.a:
            return self.b
        if v == self.b:
            return self.a
        raise ValueError(f"{v} غير موجود في الحجر [{self.a}|{self.b}]")

    def __repr__(self):
        return f"[{self.a}|{self.b}]"

    def __eq__(self, o):
        if not isinstance(o, Tile):
            return False
        return self.a == o.a and self.b == o.b

    def __hash__(self):
        return hash((self.a, self.b))


# توليد كل الـ 28 حجر الخاصة بلعبة الدومينو القياسية
ALL_TILES: Set[Tile] = frozenset(
    Tile(i, j) for i in range(7) for j in range(i + 1)
)

@dataclass
class Board:
    """طاولة اللعب"""
    played: List[Tuple[Tile, Direction]] = field(
        default_factory=list
    )
    left: Optional[int] = None
    right: Optional[int] = None

    @property
    def is_empty(self) -> bool:
        return len(self.played) == 0

    @property
    def ends(self) -> Set[int]:
        if self.is_empty:
            return set()
        return {self.left, self.right}

    @property
    def tiles_on_table(self) -> List[Tile]:
        return [t for t, _ in self.played]

    def can_play(self, tile: Tile) -> List[Direction]:
        if self.is_empty:
            return [Direction.LEFT]
        
        dirs = []
        if tile.has(self.left):
            dirs.append(Direction.LEFT)
        if tile.has(self.right):
            # نمنع تكرار الاتجاه إذا كان الحجر دبل والطاولة لها نفس الأطراف
            if self.left != self.right or not dirs:
                dirs.append(Direction.RIGHT)
        return dirs

    def play(self, tile: Tile, d: Direction) -> bool:
        if self.is_empty:
            self.played.append((tile, d))
            self.left = tile.a
            self.right = tile.b
            return True

        if d not in self.can_play(tile):
            return False

        if d == Direction.LEFT:
            self.left = tile.other(self.left)
        else:
            self.right = tile.other(self.right)

        self.played.append((tile, d))
        return True

    def clone(self) -> Board:
        return copy.deepcopy(self)
