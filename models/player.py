from tracker.tracker_client import fetch_profile

class Player:
    def __init__(self, platform: str, player_id: str) -> None:
        self.platform: str = platform
        self.id: str = player_id
        self.data: dict = {}
        self.ratings: dict = {}
        self.PLAYLISTS = {
            10: "1v1",
            11: "2v2",
            13: "3v3",
        }

    def extract_ranked(self) -> dict:
        self.data = fetch_profile(self.platform, self.id)
        for segment in self.data["data"]["segments"]:
            if segment.get("type") != "playlist":
                continue

            playlist_id = segment.get("attributes", {}).get("playlistId")

            if playlist_id not in self.PLAYLISTS:
                continue

            stats = segment.get("stats", {})
            rating = stats.get("rating", {})
            tier = stats.get("tier", {})
            division = stats.get("division", {})

            self.ratings[self.PLAYLISTS[playlist_id]] = {
                "mmr": rating.get("value"),
                "rank": rating.get("metadata", {}).get("tierName")
                        or tier.get("metadata", {}).get("name"),
                "division": division.get("metadata", {}).get("name"),
                "matches_played": stats.get("matchesPlayed", {}).get("value"),
            }

        return self.ratings

    def update_ratings(self) -> dict:
        self.fetch_profile()
        return self.extract_ranked()



if __name__ == "__main__":
    player1 = Player(platform="steam", player_id="76561198985305791")
    player1.fetch_profile()
    rank = player1.extract_ranked()
    for key, value in rank.items():
        print(f"{key}: {value}")
