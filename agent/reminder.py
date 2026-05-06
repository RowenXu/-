"""
Daily Esports Reminder Agent
============================

Entry-point for the agent.  Run directly::

    python agent/reminder.py

or via the GitHub Actions workflow which schedules it every day.

The agent:
1. Fetches today's esports matches (via PandaScore or demo data).
2. Formats a readable digest.
3. Broadcasts the digest to every configured notification channel.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone

from fetcher import fetch_today_matches, Match
from notifiers import build_notifiers


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

_GAME_EMOJI: dict[str, str] = {
    "cs-go": "🔫",   # Counter-Strike 2
    "cs2": "🔫",
    "valorant": "🎯",
    "league-of-legends": "🏆",
    "dota-2": "⚔️",
    "overwatch-2": "🦸",
    "r6-siege": "🛡️",
    "rocket-league": "🚀",
    "starcraft-2": "🛸",
}

# Human-readable display names for the primary games
_GAME_DISPLAY: dict[str, str] = {
    "cs-go": "Counter-Strike 2",
    "cs2": "Counter-Strike 2",
    "valorant": "VALORANT",
}


def _display_name(game: str) -> str:
    return _GAME_DISPLAY.get(game, game.upper().replace("-", " "))


def _group_by_game(matches: list[Match]) -> dict[str, list[Match]]:
    groups: dict[str, list[Match]] = {}
    for m in matches:
        # Normalise CS2 slugs so both appear under one section
        key = "cs-go" if m.game == "cs2" else m.game
        groups.setdefault(key, []).append(m)
    return groups


def format_digest(matches: list[Match]) -> str:
    today_str = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
    lines: list[str] = [
        f"🎮 每日电竞赛事提醒 – {today_str}",
        "=" * 42,
    ]

    if not matches:
        lines.append("今日暂无已排期的赛事。")
        return "\n".join(lines)

    groups = _group_by_game(matches)

    for game, game_matches in groups.items():
        emoji = _GAME_EMOJI.get(game, "🎮")
        lines.append(f"\n{emoji}  {_display_name(game)}")
        lines.append("-" * 36)
        for m in game_matches:
            time_str = (
                m.scheduled_at.strftime("%H:%M UTC")
                if m.scheduled_at
                else "时间待定"
            )
            status_tag = " ▶ 进行中" if m.status == "running" else ""
            lines.append(f"  • {m.team_a} vs {m.team_b}")
            lines.append(f"    🏅 {m.tournament}")
            lines.append(f"    🕐 {time_str}{status_tag}")
            if m.stream_url:
                lines.append(f"    🔴 直播: {m.stream_url}")

    lines.append("\n" + "=" * 42)
    lines.append(f"共 {len(matches)} 场赛事。祝观赛愉快！")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    print("[agent] 正在获取今日赛事 …")
    matches = fetch_today_matches()
    digest = format_digest(matches)

    notifiers = build_notifiers()
    print(f"[agent] 发送提醒至 {len(notifiers)} 个渠道 …\n")
    for notifier in notifiers:
        notifier.send(digest)

    return 0


if __name__ == "__main__":
    sys.exit(main())
