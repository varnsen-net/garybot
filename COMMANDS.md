# Commands

## General

| Trigger | garybot reply |
|---|---|
| begins with `imagine unironically` | REPeatS tHe uSER'S MesSaGe in sPOnGEBOB teXT |
| contains the word `reason` | Replies with `REASON WILL PREVAIL` |
| `.apod` | Return a random Astronomy Picture of the Day from NASA |
| `.ask <nick>` | Return a random line from the given user |
| `<botnick>: <message>` | Chat with the bot directly for an LLM response |
| `.spaghetti` | spaghetti |

Sending the configured exit code as a private message from the admin nick will shut the bot down cleanly.

## Sportsbook

## Admin
These are commands the admin nick can PM to the bot to control it.
| Trigger | garybot reply |
|---|---|
| `reset` | Close the bot with a non-zero exit code, causing it to restart if it's running in a process manager. |
| `goodnight` | Close the bot with a zero exit code, causing it to shut down without restarting. |
