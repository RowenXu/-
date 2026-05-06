"""
Notification channels for the esports reminder agent.

Each channel reads its configuration from environment variables and exposes a
single ``send(message: str) -> None`` method.

Supported channels
------------------
stdout      – always enabled; prints to the terminal
telegram    – requires TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID
discord     – requires DISCORD_WEBHOOK_URL
email       – requires SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD,
              EMAIL_FROM, EMAIL_TO
"""

from __future__ import annotations

import os
import smtplib
from email.mime.text import MIMEText

import requests


# ---------------------------------------------------------------------------
# Base class
# ---------------------------------------------------------------------------

class BaseNotifier:
    name: str = "base"

    def is_configured(self) -> bool:  # pragma: no cover
        return True

    def send(self, message: str) -> None:  # pragma: no cover
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Stdout
# ---------------------------------------------------------------------------

class StdoutNotifier(BaseNotifier):
    name = "stdout"

    def send(self, message: str) -> None:
        print(message)


# ---------------------------------------------------------------------------
# Telegram
# ---------------------------------------------------------------------------

class TelegramNotifier(BaseNotifier):
    name = "telegram"

    def __init__(self) -> None:
        self.token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()

    def is_configured(self) -> bool:
        return bool(self.token and self.chat_id)

    def send(self, message: str) -> None:
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "HTML",
        }
        try:
            resp = requests.post(url, json=payload, timeout=10)
            resp.raise_for_status()
            print(f"[notifier:telegram] Message sent to chat {self.chat_id}.")
        except requests.RequestException as exc:
            print(f"[notifier:telegram] Failed to send message: {exc}")


# ---------------------------------------------------------------------------
# Discord
# ---------------------------------------------------------------------------

class DiscordNotifier(BaseNotifier):
    name = "discord"

    def __init__(self) -> None:
        self.webhook_url = os.getenv("DISCORD_WEBHOOK_URL", "").strip()

    def is_configured(self) -> bool:
        return bool(self.webhook_url)

    def send(self, message: str) -> None:
        payload = {"content": message}
        try:
            resp = requests.post(self.webhook_url, json=payload, timeout=10)
            resp.raise_for_status()
            print("[notifier:discord] Message sent.")
        except requests.RequestException as exc:
            print(f"[notifier:discord] Failed to send message: {exc}")


# ---------------------------------------------------------------------------
# Email
# ---------------------------------------------------------------------------

class EmailNotifier(BaseNotifier):
    name = "email"

    def __init__(self) -> None:
        self.host = os.getenv("SMTP_HOST", "").strip()
        self.port = int(os.getenv("SMTP_PORT", "587"))
        self.user = os.getenv("SMTP_USER", "").strip()
        self.password = os.getenv("SMTP_PASSWORD", "").strip()
        self.from_addr = os.getenv("EMAIL_FROM", self.user).strip()
        self.to_addr = os.getenv("EMAIL_TO", "").strip()

    def is_configured(self) -> bool:
        return bool(self.host and self.user and self.password and self.to_addr)

    def send(self, message: str) -> None:
        msg = MIMEText(message, "plain", "utf-8")
        msg["Subject"] = "🎮 Today's Esports Schedule"
        msg["From"] = self.from_addr
        msg["To"] = self.to_addr

        try:
            with smtplib.SMTP(self.host, self.port, timeout=15) as smtp:
                smtp.ehlo()
                smtp.starttls()
                smtp.login(self.user, self.password)
                smtp.sendmail(self.from_addr, [self.to_addr], msg.as_string())
            print(f"[notifier:email] Email sent to {self.to_addr}.")
        except Exception as exc:  # noqa: BLE001
            print(f"[notifier:email] Failed to send email: {exc}")


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def build_notifiers() -> list[BaseNotifier]:
    """Return all configured notifiers (stdout is always included)."""
    candidates: list[BaseNotifier] = [
        TelegramNotifier(),
        DiscordNotifier(),
        EmailNotifier(),
    ]
    notifiers: list[BaseNotifier] = [StdoutNotifier()]
    for n in candidates:
        if n.is_configured():
            print(f"[notifier] Enabled: {n.name}")
            notifiers.append(n)
    return notifiers
