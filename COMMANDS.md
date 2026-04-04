# Commands

## General

| Trigger | garybot reply |
|---|---|
| begins with `imagine unironically` | REPeatS tHe uSER'S MesSaGe in sPOnGEBOB teXT |
| contains the word `reason` | Replies with `REASON WILL PREVAIL` |
| `.spaghetti` | spaghetti |
| `.ask <nick>` | Return a random line from the given user |
| `.wa <query>` | Return a Wolfram Alpha short response for the given query |
| `.apod` | Return a random Astronomy Picture of the Day from NASA |
| `.haha` | Return a random joke from jokeapi |
| `.tr[ivia] [AaBbCcDd]` | Use `.tr` to get a trivia question, then use `.tr [AaBbCcDd]` to record your answer. |
| `<botnick>: <message>` | Chat with the bot directly for an LLM response |

Sending the configured exit code as a private message from the admin nick will shut the bot down cleanly.

## Sportsbook

## Admin
These are commands the admin nick can PM to the bot to control it.
| Trigger | garybot reply |
|---|---|
| `reset` | Close the bot with a non-zero exit code, causing it to restart if it's running in a process manager. |
| `goodnight` | Close the bot with a zero exit code, causing it to shut down without restarting. |
