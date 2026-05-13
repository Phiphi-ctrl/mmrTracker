__all__ = ["Game", "Player", "Team"]


def __getattr__(name):
    if name == "Game":
        from backend.models.game import Game

        return Game
    if name == "Player":
        from backend.models.player import Player

        return Player
    if name == "Team":
        from backend.models.team import Team

        return Team
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
