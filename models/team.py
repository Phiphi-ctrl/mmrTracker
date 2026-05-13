from dataclasses import dataclass, field

@dataclass
class Team:
    name: str
    team_num: int
    players: list[Player] = field(default_factory=list)