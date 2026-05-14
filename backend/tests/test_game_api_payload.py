import json
import unittest

from backend.models.game import Game
from backend.models.player import Player


class FakeClient:
    def yield_roster(self):
        yield (
            Player("Steam|blue-id1|0", 0, "BluePlayer1"),
            Player("Epic|orange-id1|0", 1, "OrangePlayer1"),
            Player("Steam|blue-id2|0", 0, "BluePlayer2"),
            Player("Epic|orange-id2|0", 1, "OrangePlayer2"),
        )


class GameApiPayloadTest(unittest.TestCase):
    def test_run_api_yields_json_serializable_team_payload(self) -> None:
        game = Game()
        game.client = FakeClient()

        def fake_query_tracker() -> None:
            for team in game.teams.values():
                for player in team.players:
                    player.ratings = {
                        "1v1": {
                            "mmr": 900,
                            "rank": "Diamond I",
                            "division": "Division II",
                            "matches_played": 42,
                        },
                        "2v2": {
                            "mmr": 900,
                            "rank": "Diamond I",
                            "division": "Division II",
                            "matches_played": 42,
                        },
                        "3v3": {
                            "mmr": 900,
                            "rank": "Diamond I",
                            "division": "Division II",
                            "matches_played": 42,
                        },
                        "4v4": {
                            "mmr": 900,
                            "rank": "Diamond I",
                            "division": "Division II",
                            "matches_played": 42,
                        }
                    }

        game.query_tracker = fake_query_tracker

        payload = next(game.run_api())

        self.assertEqual(payload["mode"], "2v2")
        self.assertEqual(set(payload["teams"].keys()), {"Team0", "Team1"})
        self.assertEqual(payload["teams"]["Team0"]["name"], "Blue Team")
        self.assertEqual(payload["teams"]["Team1"]["name"], "Orange Team")
        self.assertEqual(payload["teams"]["Team0"]["players"][0]["name"], "BluePlayer1")
        self.assertEqual(
            payload["teams"]["Team0"]["players"][0]["ratings"]["1v1"]["mmr"],
            900,
        )

        json.dumps(payload)


if __name__ == "__main__":
    unittest.main()
