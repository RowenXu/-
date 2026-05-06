# 每日电竞赛事提醒 Agent

每天自动获取 **Counter-Strike 2** 和 **VALORANT**（以及可扩展的其他游戏）的赛事日程，并通过多种渠道发送提醒通知。

## 功能特性

- 🔫 **CS2** + 🎯 **VALORANT** 为主要跟踪游戏（可自定义扩展）
- 📡 数据来源：[PandaScore API](https://developers.pandascore.co/)（免费 tier），无 Token 时自动使用演示数据
- 📣 支持多通知渠道：控制台输出、Telegram Bot、Discord Webhook、Email (SMTP)
- ⏰ 通过 **GitHub Actions** 每天 UTC 08:00（北京时间 16:00）定时运行，也可手动触发

## 快速开始

### 本地运行

```bash
pip install -r requirements.txt
cd agent
python reminder.py
```

无需任何配置即可运行，会输出演示数据。

### 连接真实数据

1. 在 [PandaScore](https://developers.pandascore.co/) 注册免费账号，获取 API Token。
2. 设置环境变量：

```bash
export PANDASCORE_TOKEN=your_token_here
python agent/reminder.py
```

## 通知渠道配置

在 GitHub 仓库 **Settings → Secrets and variables → Actions** 中添加以下密钥：

| 渠道 | 所需密钥 |
|------|---------|
| 数据源 | `PANDASCORE_TOKEN` |
| Telegram | `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` |
| Discord | `DISCORD_WEBHOOK_URL` |
| Email | `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `EMAIL_FROM`, `EMAIL_TO` |

所有渠道均为**可选**，未配置时仅输出到 Actions 日志。

## 自定义跟踪游戏

在仓库 **Settings → Variables** 中设置 `ESPORTS_GAMES`，以逗号分隔游戏 slug：

```
cs-go,valorant,league-of-legends,dota-2
```

默认值为 `cs-go,cs2,valorant`。

## 项目结构

```
agent/
  reminder.py    # 主程序入口
  fetcher.py     # 赛事数据获取（PandaScore / 演示数据）
  notifiers.py   # 通知渠道实现
.github/workflows/
  daily_esports_reminder.yml   # 定时触发的 GitHub Actions 工作流
requirements.txt
```
