# garybot

Welcome to the repo for garybot, an IRC bot built with Python and gevent. Garybot connects to an IRC server, listens to a channel, and responds to commands and triggers with a handful of channel functions.

## How to run

- Install the `uv` Python package manager.
- Drop a `.env` file into the project repo root (details below).
- Run `sh start.sh`.

## Architecture

Garybot uses a three-actor concurrency model built on gevent greenlets:

- **Listener** — sits on the raw SSL socket, reads lines into a buffer, and puts complete lines onto a queue.
- **Dispatcher** — receives raw IRC lines, parses them, and spawns short-lived greenlets to handle commands. Puts responses onto the Writer's inbox.
- **Logger** — drains its inbox into an SQLite database for logging and later retrieval.
- **Writer** — drains its inbox queue to the socket.

Each actor is a `gevent.Greenlet`. The client manages the lifecycle of all three and handles reconnection automagically.

## Features

- SSL/TLS connection
- Auto-rejoin on kick
- Admin exit code for clean remote shutdown
- Per-user message logging to SQLite
- Nick ignore list
- LLM-powered responses
- Custom channel triggers
- Greenlet pool for concurrent handler execution

## Configuration

Garybot is configured via environment variables or a `.env` file in the project root.

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

See COMMANDS.md for a list of available commands and triggers.

## User Logs

Channel messages from users are logged to a SQLite database:

```
data/user-logs/user_logs.db

schema: nick TEXT, target TEXT, message TEXT, timestamp REAL
```

## Cloud environment
The existing project infrastructure code is written with pulumi for a Vultr cloud environment. These steps assume you're generally familiar with both.

- Create a pulumi account and install the CLI: https://www.pulumi.com/docs/iac/download-install/
- Create a Vultr account and generate an API key: https://my.vultr.com/settings/#settingsapi
- Share Vultr access token with pulumi project: `pulumi config set vultr:apiKey --secret <VULTR_API_KEY>`
- Install the `uv` Python package manager.
- Drop a `.env` file into the project repo root.

You'll also need to drop a `.env` file into the `infrastructure` directory with the following variables:

| Variable | Description |
|---|---|
| `VULTR_REGION` | Vultr region code (e.g. `ewr`) |
| `USERNAME` | Username for the provisioned server |
| `HOSTNAME` | Hostname for the provisioned server |
| `PLAN` | Vultr plan code (e.g. `vc2-1c-2gb`) |
| `OS_ID` | Vultr OS ID (e.g. `2076` for Alpine) |
| `SSH_KEY_NAME` | Name of the SSH key you've uploaded to Vultr |
| `REPO_NAME` | Name for the git repo (used in provisioning script) |
| `REPO_URL` | URL for the git repo (used in provisioning script) |
| `HOME_IP` | Your home IP address (used in provisioning script for firewall rules) |
