import json
import socket
import sys
from json import JSONDecoder
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.models.player import Player

class RLWebsocketClient:
    def __init__(self):
        self.HOST = "127.0.0.1"
        self.PORT = 49123

    @staticmethod
    def _ensure_dict(value):
        if isinstance(value, dict):
            return value

        if isinstance(value, str):
            try:
                parsed = json.loads(value)
            except json.JSONDecodeError:
                return None

            if isinstance(parsed, dict):
                return parsed

        return None

    def _read_rl_events(self):
        decoder = JSONDecoder()
        buffer = ""

        with socket.create_connection((self.HOST, self.PORT), timeout=5) as sock:
            print("Connected to Rocket League Stats API.")
            sock.settimeout(None)

            while True:
                chunk = sock.recv(65536)

                if not chunk:
                    print("Connection closed.")
                    break

                buffer += chunk.decode("utf-8", errors="replace")

                while True:
                    buffer = buffer.lstrip()

                    if not buffer:
                        break

                    try:
                        event, index = decoder.raw_decode(buffer)
                    except json.JSONDecodeError:
                        break

                    buffer = buffer[index:]
                    yield event


    def _normalize_message(self, msg):
        """
        Convert weird decoded values into a dict if possible.
        Some streams may contain JSON strings before/around real JSON objects.
        """
        if isinstance(msg, dict):
            return msg

        if isinstance(msg, str):
            print("Got string message:", repr(msg[:200]))

            # Sometimes APIs send JSON encoded as a string.
            try:
                inner = json.loads(msg)
            except json.JSONDecodeError:
                return None

            if isinstance(inner, dict):
                return inner

        print("Skipping unsupported message type:", type(msg))
        return None

    def yield_roster(self):
        last_roster_key = None

        for raw_msg in self._read_rl_events():
            msg = self._ensure_dict(raw_msg)
            if msg is None or msg.get("Event") != "UpdateState":
                continue

            data = self._ensure_dict(msg.get("Data"))
            if data is None:
                continue

            players = data.get("Players", [])

            roster = tuple(
                Player(
                    primary_id=p.get("PrimaryId"),
                    team=p.get("TeamNum"),
                    name=p.get("Name")
                )
                for p in players
            )

            roster_key = self._make_roster_key(roster)
            if roster_key == last_roster_key:
                continue

            last_roster_key = roster_key

            yield roster

    @staticmethod
    def _make_roster_key(roster: tuple[Player, ...]) -> tuple:
        return tuple(
            sorted(
                (
                    player.primary_id,
                    player.team_num,
                    player.name,
                )
                for player in roster
            )
        )

if __name__ == "__main__":
    client = RLWebsocketClient()
    for roster in client.yield_roster():
        for player in roster:
            print("-" * 60)
            print(player.name, player.team_num, player.primary_id)
