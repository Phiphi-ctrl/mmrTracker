import logging
import os
import time
from copy import deepcopy
from typing import Any

import requests

logger = logging.getLogger(__name__)
PROFILE_CACHE_TTL_SECONDS = float(os.getenv("MMR_TRACKER_PROFILE_CACHE_TTL_SECONDS", "120"))
_profile_cache: dict[tuple[str, str], dict[str, Any]] = {}


def fetch_profile(platform: str | None, player_id: str | None) -> dict:
    if player_id is None or platform is None:
        raise ValueError("Player id and platform cannot be None")

    cache_key = (platform, player_id)
    now = time.monotonic()
    cached_profile = _profile_cache.get(cache_key)

    if cached_profile is not None and now < cached_profile["expires_at"]:
        logger.info(
            "Tracker profile cache hit platform=%s player=%s ttl_remaining_seconds=%.0f",
            platform,
            player_id,
            cached_profile["expires_at"] - now,
        )
        return deepcopy(cached_profile["data"])

    url = (
        "https://api.tracker.gg/api/v2/"
        f"rocket-league/standard/profile/{platform}/{player_id}"
    )

    headers = {
        "Pragma": "no-cache",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-GB,en;q=0.9",
        "Cache-Control": "no-cache",
        "Origin": "https://rocketleague.tracker.network",
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) "
            "Version/26.4 Safari/605.1.15"
        ),
        "Referer": "https://rocketleague.tracker.network/",
        "Accept-Encoding": "gzip, deflate",
    }

    logger.info("Fetching Tracker profile platform=%s player=%s", platform, player_id)
    started_at = time.perf_counter()

    response = requests.get(url, headers=headers, timeout=10)
    elapsed_ms = (time.perf_counter() - started_at) * 1000

    logger.info(
        "Tracker profile response platform=%s player=%s status=%s duration_ms=%.0f",
        platform,
        player_id,
        response.status_code,
        elapsed_ms,
    )

    response.raise_for_status()
    data = response.json()
    _profile_cache[cache_key] = {
        "expires_at": now + PROFILE_CACHE_TTL_SECONDS,
        "data": deepcopy(data),
    }
    return data


def clear_profile_cache() -> None:
    _profile_cache.clear()
