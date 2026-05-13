from backend.tracker.tracker_client import fetch_profile


RL_TO_TRACKER_PLATFORM = {
    "Steam": "steam",
    "Epic": "epic",
    "PS4": "psn",
    "PS5": "psn",
    "XboxOne": "xbl",
    "Switch": "switch",
}


class Player:
    def __init__(self, primary_id: str, team: int, name: str) -> None:
        self.primary_id = primary_id
        self.team_num: int = team
        self.name: str = name

        self.platform_raw: str | None = None
        self.platform: str | None = None
        self.id: str | None = None

        self.data: dict = {}
        self.ratings: dict = {}
        self.error: str | None = None

        self.PLAYLISTS = {
            10: "1v1",
            11: "2v2",
            13: "3v3",
            61: "4v4"
        }

        self._parse_primary_id()

    def _parse_primary_id(self) -> None:
        try:
            platform_raw, player_id, _ = self.primary_id.split("|", maxsplit=2)
        except ValueError:
            self.error = f"Invalid PrimaryId: {self.primary_id}"
            return

        if platform_raw == "Unknown" or player_id == "0":
            self.error = "Bot or unknown player"
            return

        tracker_platform = RL_TO_TRACKER_PLATFORM.get(platform_raw)

        if tracker_platform is None:
            self.error = f"Unsupported platform: {platform_raw}"
            return

        self.platform_raw = platform_raw
        self.platform = tracker_platform
        self.id = player_id

    @property
    def is_trackable(self) -> bool:
        return self.platform is not None and self.id is not None

    def _get_tracker_lookup_id(self) -> str | None:
        if self.platform == "steam":
            return self.id
        return self.name

    def extract_ranked(self, mode: str | None) -> dict:
        if not self.is_trackable:
            return {}

        if mode is None:
            return {}

        mode = mode.lower()

        valid_modes = set(self.PLAYLISTS.values())

        if mode == "freeplay":
            target_modes = valid_modes
        elif mode in valid_modes:
            target_modes = {mode}
        else:
            self.error = f"Unsupported mode: {mode}"
            return {}

        self.data = fetch_profile(self.platform, self._get_tracker_lookup_id())

        self.ratings = {}

        for segment in self.data["data"]["segments"]:
            if segment.get("type") != "playlist":
                continue

            playlist_id = segment.get("attributes", {}).get("playlistId")
            playlist_name = self.PLAYLISTS.get(playlist_id)

            if playlist_name is None:
                continue

            if playlist_name not in target_modes:
                continue

            stats = segment.get("stats", {})
            rating = stats.get("rating", {})
            tier = stats.get("tier", {})
            division = stats.get("division", {})

            self.ratings[playlist_name] = {
                "mmr": rating.get("value"),
                "rank": (
                        rating.get("metadata", {}).get("tierName")
                        or tier.get("metadata", {}).get("name")
                ),
                "division": division.get("metadata", {}).get("name"),
                "matches_played": stats.get("matchesPlayed", {}).get("value"),
            }

        return self.ratings