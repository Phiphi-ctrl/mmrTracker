from backend.models.player import Player
from backend.models.team import Team
from backend.rl_api.websocket_client import RLWebsocketClient
from collections.abc import Iterator
from typing import Any

class Game:
    def __init__(self) -> None:
        self.teams: dict[int, Team] = {}
        self.client: RLWebsocketClient = RLWebsocketClient()
        self.roster: tuple[Player, ...] = ()
        self.mode: str | None = None

    def _build_teams(self) -> None:
        self.teams.clear()

        is_freeplay = self.mode == "freeplay"

        for player in self.roster:
            team_num = 0 if is_freeplay else player.team_num
            team = self.teams.setdefault(team_num, Team())
            team.players.append(player)


    def get_mode(self) -> None:
        self.mode = {
            1: "freeplay",
            2: "1v1",
            4: "2v2",
            6: "3v3",
            8: "4v4",
        }.get(len(self.roster), "unknown")

    def query_tracker(self) -> None:
        for team in self.teams.values():
            for player in team.players:
                if not player.is_trackable:
                    continue

                try:
                    player.extract_ranked()
                except Exception as exc:
                    player.error = str(exc)

    def update_from_roster(self) -> None:
        self._build_teams()
        self.query_tracker()

    def to_api_payload(self) -> dict[str, Any]:

        payload: dict[str, Any] = {
            "mode": self.mode or "unknown",
            "teams": {},
        }

        for team_num, team in sorted(self.teams.items()):
            team_key = f"Team{team_num}"
            team_name = "Blue Team" if team_num == 0 else "Orange Team"

            payload["teams"][team_key] = {
                "team_num": team_num,
                "name": team_name,
                "players": [
                    self._player_to_api_payload(player)
                    for player in team.players
                ],
            }

        return payload

    def run_api(self) -> Iterator[dict[str, Any]]:
        for roster in self.client.yield_roster():
            self.roster = roster
            self.get_mode()
            self.update_from_roster()
            yield self.to_api_payload()

    def _player_to_api_payload(self, player: Player) -> dict[str, Any]:
        return {
            "name": player.name,
            "primary_id": player.primary_id,
            "team_num": player.team_num,
            "platform": player.platform,
            "platform_raw": player.platform_raw,
            "id": player.id,
            "ratings": player.ratings,
            "error": player.error,
            "is_trackable": player.is_trackable,
        }


if __name__ == "__main__":
    game = Game()
    game.run_api()
