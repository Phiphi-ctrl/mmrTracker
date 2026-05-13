import json
import socket
from json import JSONDecoder


HOST = "127.0.0.1"
PORT = 49123


def ensure_dict(value):
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

def read_rl_events():
    decoder = JSONDecoder()
    buffer = ""

    with socket.create_connection((HOST, PORT), timeout=5) as sock:
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


def normalize_message(msg):
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


last_roster = None

for raw_msg in read_rl_events():
    msg = ensure_dict(raw_msg)
    if msg is None or msg.get("Event") != "UpdateState":
        continue

    data = ensure_dict(msg.get("Data"))
    if data is None:
        continue

    players = data.get("Players", [])

    roster = tuple(
        sorted(
            (
                p.get("Name"),
                p.get("PrimaryId"),
                p.get("TeamNum"),
            )
            for p in players
        )
    )

    if roster == last_roster:
        continue

    last_roster = roster

    print("\nRoster changed:")
    for name, primary_id, team_num in roster:
        print(name, primary_id, "Team:", team_num)

    print("-" * 60)