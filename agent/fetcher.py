"""
Esports event fetcher.

Primary source  : PandaScore REST API (https://developers.pandascore.co/)
Fallback / demo : built-in static sample data (no API key needed)

Environment variables
---------------------
PANDASCORE_TOKEN   – PandaScore API token (optional; falls back to demo mode)
ESPORTS_GAMES      – comma-separated game slugs to filter, e.g.
                     "league-of-legends,cs-go,dota-2,valorant,overwatch-2"
                     Defaults to the five above when unset.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

# All times are presented in UTC+8 (Beijing / CST)
TZ_CST = timezone(timedelta(hours=8), name="UTC+8")
from typing import List

import requests

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class Match:
    id: str
    game: str
    tournament: str
    team_a: str
    team_b: str
    scheduled_at: datetime | None
    stream_url: str = ""
    status: str = "not_started"   # not_started | running | finished

    def __str__(self) -> str:
        time_str = (
            self.scheduled_at.astimezone(TZ_CST).strftime("%H:%M (UTC+8)")
            if self.scheduled_at
            else "TBD"
        )
        return (
            f"[{self.game}] {self.tournament}\n"
            f"  {self.team_a} vs {self.team_b}\n"
            f"  🕐 {time_str}"
            + (f"  🔴 {self.stream_url}" if self.stream_url else "")
        )


# ---------------------------------------------------------------------------
# PandaScore fetcher
# ---------------------------------------------------------------------------

_PANDASCORE_BASE = "https://api.pandascore.co"

# Primary games: CS2 and Valorant.
# PandaScore uses "cs-go" as the slug for both CS:GO and CS2; "cs2" is also
# tried for platforms that have migrated to the new slug.
_DEFAULT_GAMES = [
    "cs-go",   # Counter-Strike 2 / CS:GO
    "cs2",     # CS2 on newer PandaScore endpoints (no-op if slug not found)
    "valorant",
]


def _parse_game_slug(match_json: dict) -> str:
    try:
        return match_json["videogame"]["slug"]
    except (KeyError, TypeError):
        return "unknown"


def _parse_team(side: dict | None) -> str:
    if not side:
        return "TBD"
    return side.get("name") or "TBD"


def _parse_dt(raw: str | None) -> datetime | None:
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


def fetch_from_pandascore(token: str, games: list[str]) -> list[Match]:
    """Return today's upcoming / live matches from PandaScore."""
    # "Today" is computed in UTC+8, then converted to UTC for the API filter.
    now_cst = datetime.now(tz=TZ_CST)
    start_cst = now_cst.replace(hour=0, minute=0, second=0, microsecond=0)
    end_cst = now_cst.replace(hour=23, minute=59, second=59, microsecond=0)
    today = start_cst.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    tomorrow = end_cst.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    headers = {"Authorization": f"Bearer {token}"}
    matches: list[Match] = []

    for game in games:
        url = f"{_PANDASCORE_BASE}/{game}/matches"
        params = {
            "filter[status]": "not_started,running",
            "range[scheduled_at]": f"{today},{tomorrow}",
            "sort": "scheduled_at",
            "page[size]": 50,
        }
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=10)
            resp.raise_for_status()
        except requests.RequestException as exc:
            print(f"[fetcher] PandaScore request failed for {game}: {exc}")
            continue

        for item in resp.json():
            opponents = item.get("opponents") or []
            team_a = _parse_team(opponents[0].get("opponent") if len(opponents) > 0 else None)
            team_b = _parse_team(opponents[1].get("opponent") if len(opponents) > 1 else None)
            league = (item.get("league") or {}).get("name", "")
            series = (item.get("serie") or {}).get("full_name", "")
            tournament = f"{league} – {series}" if series else league

            stream_url = ""
            for sv in item.get("streams_list") or []:
                if sv.get("main"):
                    stream_url = sv.get("raw_url", "")
                    break

            matches.append(
                Match(
                    id=str(item.get("id", "")),
                    game=_parse_game_slug(item),
                    tournament=tournament or "Unknown Tournament",
                    team_a=team_a,
                    team_b=team_b,
                    scheduled_at=_parse_dt(item.get("scheduled_at")),
                    stream_url=stream_url,
                    status=item.get("status", "not_started"),
                )
            )

    return matches


# ---------------------------------------------------------------------------
# Demo / fallback data
# ---------------------------------------------------------------------------

_DEMO_MATCHES: list[dict] = [
    # --- Counter-Strike 2 ---
    {
        "id": "demo-cs2-1",
        "game": "cs-go",
        "tournament": "ESL Pro League Season 20",
        "team_a": "NaVi",
        "team_b": "FaZe Clan",
        "scheduled_at": None,
        "stream_url": "https://www.twitch.tv/esl_csgo",
    },
    {
        "id": "demo-cs2-2",
        "game": "cs-go",
        "tournament": "BLAST Premier Spring 2025",
        "team_a": "Team Vitality",
        "team_b": "G2 Esports",
        "scheduled_at": None,
        "stream_url": "https://www.twitch.tv/blastpremier",
    },
    # --- Valorant ---
    {
        "id": "demo-val-1",
        "game": "valorant",
        "tournament": "VCT 2025 EMEA",
        "team_a": "Team Heretics",
        "team_b": "Fnatic",
        "scheduled_at": None,
        "stream_url": "https://www.twitch.tv/valorant",
    },
    {
        "id": "demo-val-2",
        "game": "valorant",
        "tournament": "VCT 2025 Americas",
        "team_a": "Sentinels",
        "team_b": "NRG Esports",
        "scheduled_at": None,
        "stream_url": "https://www.twitch.tv/valorant",
    },
]


def fetch_demo() -> list[Match]:
    return [
        Match(
            id=d["id"],
            game=d["game"],
            tournament=d["tournament"],
            team_a=d["team_a"],
            team_b=d["team_b"],
            scheduled_at=d["scheduled_at"],
            stream_url=d["stream_url"],
        )
        for d in _DEMO_MATCHES
    ]


# ---------------------------------------------------------------------------
# Public entry-point
# ---------------------------------------------------------------------------

def fetch_today_matches() -> list[Match]:
    """Return today's matches, using PandaScore if a token is set."""
    token = os.getenv("PANDASCORE_TOKEN", "").strip()
    games_env = os.getenv("ESPORTS_GAMES", "").strip()
    games = [g.strip() for g in games_env.split(",")] if games_env else _DEFAULT_GAMES

    if token:
        print("[fetcher] Using PandaScore API …")
        matches = fetch_from_pandascore(token, games)
        if matches:
            return matches
        print("[fetcher] PandaScore returned no matches; falling back to demo data.")

    print("[fetcher] Running in demo mode (set PANDASCORE_TOKEN to use live data).")
    return fetch_demo()
