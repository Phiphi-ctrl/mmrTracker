from dataclasses import dataclass, field
from typing import Any
from player import Player
from team import Team
from rl_api.websocket_cllient import RLWebsocketClient

class Game:
    def __init__(self) -> None:
        self.match_guid: str | None = None
        self.teams: dict[int, Team] = {}
        self.websocket: RLWebsocketClient = RLWebsocketClient()

    @classmethod
    def from_update_state(cls) -> "Game":
        game = cls()
        msg = game.websocket.get_update_state()

        data = msg.get("Data", {})
        game_data = data.get("Game", {})

        game.match_guid = data.get("MatchGuid")

        for team_data in game_data.get("Teams", []):
            team_num = team_data["TeamNum"]

            game.teams[team_num] = Team(
                name=team_data.get("Name", f"Team {team_num}"),
                team_num=team_num,
            )

        for player_data in data.get("Players", []):
            primary_id = player_data.get("PrimaryId")

            if not primary_id:
                continue

            platform, player_id = parse_primary_id(primary_id)

            player = Player(
                platform=platform,
                player_id=player_id,
            )

            team_num = player_data.get("TeamNum", -1)

            if team_num not in game.teams:
                game.teams[team_num] = Team(
                    name=f"Team {team_num}",
                    team_num=team_num,
                )

            game.teams[team_num].players.append(player)

        return game

    def fetch_all_ratings(self) -> None:
        for team in self.teams.values():
            for player in team.players:
                player.fetch_profile()
                player.ratings = player.extract_ranked()


def parse_primary_id(primary_id: str) -> tuple[str, str]:
    platform, player_id, _splitscreen = primary_id.split("|", maxsplit=2)
    return platform.lower(), player_id