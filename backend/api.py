import os
import time
import logging
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.models.game import Game
from backend.rl_api.fixture_client import FixtureRosterClient


logging.getLogger("backend").setLevel(logging.INFO)
app = FastAPI(title="RL MMR Tracker API")
LOBBY_CACHE_TTL_SECONDS = float(os.getenv("MMR_TRACKER_CACHE_TTL_SECONDS", "3"))
_lobby_cache: dict[str, Any] = {
    "expires_at": 0.0,
    "payload": None,
}

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/lobby/current")
def current_lobby() -> dict[str, Any]:
    now = time.monotonic()
    cached_payload = _lobby_cache["payload"]

    if cached_payload is not None and now < _lobby_cache["expires_at"]:
        return cached_payload

    payload = _build_current_lobby_payload()
    _lobby_cache["payload"] = payload
    _lobby_cache["expires_at"] = now + LOBBY_CACHE_TTL_SECONDS
    return payload


def _build_current_lobby_payload() -> dict[str, Any]:
    game = Game()

    if os.getenv("MMR_TRACKER_SOURCE", "fixture").lower() != "live":
        roster_path = os.getenv("MMR_TRACKER_FIXTURE_ROSTER")
        game.client = FixtureRosterClient(Path(roster_path)) if roster_path else FixtureRosterClient()

    return next(game.run_api())
