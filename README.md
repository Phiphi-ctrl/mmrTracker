# RL MMR Tracker

Small work-in-progress tool to recover and display Rocket League MMR while in-game rank/MMR visibility is limited by Easy Anti-Cheat.

## Idea

The project reads match/player metadata from Rocket League state updates, extracts `player_id` + `platform`, then queries Tracker Network to retrieve current ranked MMR values.

Current goal: build a live MMR feed during matches.

## Current Data Flow

1. `rl_api/websocket_cllient.py` returns a static example `UpdateState` message (shape of incoming websocket data).
2. `models/game.py` parses `Players[].PrimaryId` (format: `Platform|PlayerId|SplitScreen`) into:
   - `platform` (lowercased)
   - `player_id`
3. `models/player.py` + `tracker/tracker_client.py` call the Tracker API:
   - `https://api.tracker.gg/api/v2/rocket-league/standard/profile/{platform}/{player_id}`
4. Ranked playlists are extracted (`1v1`, `2v2`, `3v3`) with:
   - MMR
   - Rank/Tier
   - Division
   - Matches played

## Project Structure

- `rl_api/websocket_cllient.py`: websocket update payload source (currently static mock export)
- `models/game.py`: match + team + player wiring, `PrimaryId` parsing
- `models/player.py`: ranked playlist extraction logic
- `models/team.py`: team container
- `tracker/tracker_client.py`: Tracker API HTTP client

## Status

- Static websocket payload in place
- Player/platform extraction in place
- Tracker profile fetch in place
- Playlist MMR extraction in place
- Live websocket ingestion and final UI/display layer still to be added

## Development

Double-click one of these Windows launchers from the project root:

```text
Start Fixture.bat
Start Live.bat
```

`Start Fixture.bat` uses the static roster. `Start Live.bat` uses the Rocket League websocket and expects it on `127.0.0.1:49123`.

Start the backend and frontend together from PowerShell:

```powershell
.\scripts\dev.ps1
```

Or from Git Bash/WSL:

```bash
./scripts/dev.sh
```

`dev.sh` uses fixture mode. Use these explicit Bash launchers when you want to choose the source:

```bash
./scripts/dev-fixture.sh
```
```bash
./scripts/dev-live.sh
```

`dev-live.sh` expects the Rocket League websocket to be available on `127.0.0.1:49123`.

The backend runs on `http://127.0.0.1:8000`. The frontend runs on the Vite URL printed in the frontend terminal, usually `http://localhost:5173`.

Useful development environment variables:

```powershell
$env:MMR_TRACKER_CACHE_TTL_SECONDS="1"
$env:MMR_TRACKER_PROFILE_CACHE_TTL_SECONDS="120"
```

`MMR_TRACKER_CACHE_TTL_SECONDS` controls how often the backend rebuilds the lobby payload. `MMR_TRACKER_PROFILE_CACHE_TTL_SECONDS` controls how often the same Tracker profile can be requested again.

## Backend

Run backend with:

```powershell
.\.venv\Scripts\python -m uvicorn backend.api:app --host 127.0.0.1 --port 8000
```

Do not use Uvicorn `--reload` from the sandboxed Windows tool environment; it can hit named-pipe permission errors.

## Notes

This project is intended to surface your own MMR data through external APIs. Use responsibly and make sure your usage follows Rocket League/Epic/Tracker terms of service.
