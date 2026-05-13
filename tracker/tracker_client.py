import requests


def fetch_profile(platform: str, player_id: str) -> dict:
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

    response = requests.get(url, headers=headers, timeout=10)

    print("Status:", response.status_code)
    print("Encoding:", response.headers.get("content-encoding"))
    print("Preview:", response.text[:300])

    response.raise_for_status()
    return response.json()