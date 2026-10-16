# DoBetterBot

A Discord habit-tracking bot where your discipline affects your friends.
Create habits, log them daily, and join a Squad: if one member misses a
required habit, the whole Squad's streak is at risk.

![demo](docs/demo.gif)

## Features

- Personal habits with daily logging and streak tracking
- Squads with shared habits and shared streaks
- Timezone-aware daily reset
- Slash commands with buttons and embeds

> Planned: reminders, achievements, server-scoped leaderboards (see Roadmap)

## Commands

| Command | Description |
|---|---|
| `/habit create` | Create a personal habit |
| `/habit complete` | Log a habit for today |
| `/streak` | View your current streaks |

## Tech stack

Python 3.12 · discord.py · PostgreSQL · asyncpg · Alembic · Docker · pytest

## Architecture

```
cogs/       Discord layer: slash commands and UI only
services/   Business logic: streak rules, squad rules
database/   Models, queries, migrations
config.py   Environment-based configuration
```

Discord-specific code never touches SQL directly. Commands call services,
and services call the database layer. This keeps the rules testable
without a running bot.

### Design decisions
- **PostgreSQL over SQLite:** concurrent writes, proper constraints, and a
  realistic path to many servers.
- **Guild-scoped data:** squads and leaderboards are tied to a guild, so one
  server can never see another's data.
- **Streak rules are configurable:** strict mode, grace period, or
  percentage threshold.

## Getting started

1. Clone the repo
2. Create a bot at the Discord Developer Portal
3. Copy `.env.example` to `.env` and fill in your values
4. Run `docker compose up`

### Environment variables

| Variable | Description |
|---|---|
| `DISCORD_TOKEN` | Your bot token (never commit this) |
| `DATABASE_URL` | PostgreSQL connection string |

## Testing

```
pytest
```

## Roadmap

- [x] Core bot and ping command
- [ ] Personal habits and streaks
- [ ] Squads and shared streaks
- [ ] Reminders
- [ ] Achievements
- [ ] Leaderboards

## License

MIT
