__all__ = ["Game", "Player", "Team"]


def __getattr__(name):
    if name == "Game":
        from models.game import Game

        return Game
    if name == "Player":
        from models.player import Player

        return Player
    if name == "Team":
        from models.team import Team

        return Team
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
