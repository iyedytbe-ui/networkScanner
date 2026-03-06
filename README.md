# GoofyAi Pro CLI Agent

GoofyAi Pro is a coding-focused **CLI AI agent** that can also handle broader technical workflows.

## What it can do

- Interactive AI chat for coding, debugging, architecture, docs, and task planning.
- Safe command execution through an allow-listed command runner.
- Built-in slash commands for common agent tasks.
- Web search from terminal (`/search ...`).
- Open links in your browser (`/open ...`).
- Model switching (`/model ...`) and conversation history (`/history`).

## Run

```bash
python main.py
```

## In-app commands

- `/help` show all commands
- `/model <name>` change Ollama model (default: `qwen2.5-coder:7b`)
- `/run <command>` validate and execute a shell command
- `/search <query>` search the web using DuckDuckGo instant API
- `/open <url>` open URL in default browser
- `/history` show recent messages
- `/quit` exit

## Notes

- AI-generated commands are validated before execution.
- Multi-command pipelines and dangerous operators are blocked.
- If a command is unsafe, execution is denied.
