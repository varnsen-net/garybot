# garybot

Welcome to the repo for garybot, an IRC bot built with Python and gevent. Garybot connects to an IRC server, listens to a channel, and responds to commands and triggers with a handful of channel functions.

## How to run
- Install the `uv` Python package manager.
- Drop a `.env` file into the project repo root (details below).
- Run `sh start.sh`.

## Architecture

Gary uses a three-actor concurrency model built on gevent greenlets:

- **Listener** — sits on the raw SSL socket, reads lines into a buffer, and puts complete lines onto a queue.
- **Dispatcher** — receives raw IRC lines, parses them, and spawns short-lived greenlets to handle commands. Puts responses onto the Writer's inbox.
- **Writer** — drains its inbox queue to the socket.

Each actor is a `gevent.Greenlet`. The client manages the lifecycle of all three and handles reconnection automagically.

## Features

- SSL/TLS connection
- Auto-reconnect with configurable delay and max attempts
- Auto-rejoin on kick
- Admin exit code for clean remote shutdown
- Per-user message logging to SQLite
- Nick ignore list
- LLM-powered responses
- Custom channel triggers
- Greenlet pool for concurrent handler execution

## Configuration

Gary is configured via environment variables or a `.env` file in the project root.

| Variable | Description |
|---|---|
| `IRC_NICK` | Bot's IRC nick |
| `IRC_SERVER` | IRC server hostname |
| `IRC_PORT` | IRC server port |
| `IRC_MAIN_CHANNEL` | Channel to join (e.g. `#general`) |
| `IRC_LLM_MODEL` | LLM model identifier |
| `IRC_IGNORE_LIST` | Comma-separated list of nicks to ignore |
| `IRC_ADMIN_NICK` | Bot admin's nick |
| `WOLFRAM_API_KEY` | Wolfram Alpha API key |
| `ODDS_API_KEY` | Odds API key |
| `LLM_API_KEY` | LLM provider API key |

`project_root` and `user_logs_path` are derived automatically from the config file location and can be overridden if needed.

## Commands

| Trigger | Description |
|---|---|
| `.ask <question>` | Ask a question using recent channel context |
| `<botnick>: <message>` | Address the bot directly for an LLM response |
| `.spaghetti` | Spaghetti |
| `imagine unironically` | Triggered response |
| `reason` (as a word) | Triggered response |

Sending the configured exit code as a private message from the admin nick will shut the bot down cleanly.

## User Logs

Channel messages are logged to a SQLite database (excluding lines starting with `.`):

```
data/user-logs/user_logs.db

schema: nick TEXT, target TEXT, message TEXT, timestamp REAL
```
