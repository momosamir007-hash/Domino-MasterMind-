from dataclasses import dataclass

@dataclass
class Config:
    MAX_PIP: int = 6
    NUM_PLAYERS: int = 4
    HAND_SIZE: int = 7
    TOTAL_TILES: int = 28
    MCTS_SIMULATIONS: int = 2000
    MCTS_TIME_LIMIT: float = 3.0
    MCTS_EXPLORATION: float = 1.414
