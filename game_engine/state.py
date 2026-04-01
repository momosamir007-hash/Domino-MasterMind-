"""🎲 حجر الدومينو والاتجاهات"""

from enum import Enum


class Direction(Enum):
    LEFT = "left"
    RIGHT = "right"


class Tile:
    """حجر دومينو واحد [a|b]"""

    __slots__ = ("a", "b")

    def __init__(self, a: int, b: int):
        # التخزين بترتيب موحّد (الأصغر أولاً)
        self.a = min(a, b)
        self.b = max(a, b)

    # ─── خصائص ─────────────────────────
    @property
    def is_double(self) -> bool:
        return self.a == self.b

    @property
    def total(self) -> int:
        return self.a + self.b

    def has(self, n: int) -> bool:
        return self.a == n or self.b == n

    def other(self, n: int):
        """أعطني الرقم الثاني"""
        if self.a == n:
            return self.b
        if self.b == n:
            return self.a
        return None

    # ─── مقارنة وهاش ───────────────────
    def __eq__(self, other):
        if not isinstance(other, Tile):
            return False
        return self.a == other.a and self.b == other.b

    def __hash__(self):
        return hash((self.a, self.b))

    def __repr__(self):
        return f"[{self.a}|{self.b}]"

    def __str__(self):
        return f"[{self.a}|{self.b}]"


# ─── كل الأحجار (28 حجراً) ─────────────
ALL_TILES = [Tile(i, j) for i in range(7) for j in range(i, 7)]
