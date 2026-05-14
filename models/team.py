from dataclasses import dataclass, field
from models.player import Player

@dataclass
class Team:
    players: list[Player] = field(default_factory=list)