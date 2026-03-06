from __future__ import annotations

import json
import shlex
import sys
import time
import urllib.parse
import urllib.request
import webbrowser
from dataclasses import dataclass, field

from colorama import Fore, Style, init
from ollama import chat

from utils.runCmd import runCmd, validate_command

init(autoreset=True)


SYSTEM_PROMPT = (
    "You are GoofyAi Pro, a professional CLI AI agent focused on software engineering and technical workflows.\n"
    "You can help with coding, debugging, architecture, testing, DevOps, docs, product planning, and research summaries.\n"
    "Default to concise, practical answers.\n\n"
    "Output rules:\n"
    "- For normal requests: provide structured assistant answers.\n"
    "- For shell-execution requests: output ONLY ONE single-line command and nothing else.\n"
    "- Never output destructive commands. If unsafe, return exactly: echo unsafe_request_blocked"
)


@dataclass
class AgentState:
    model: str = "qwen2.5-coder:7b"
    history: list[dict[str, str]] = field(default_factory=list)


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str


def _print_status(message: str, color=Fore.LIGHTBLACK_EX):
    print(color + Style.BRIGHT + message + Style.RESET_ALL)


def _safe_open_url(url: str) -> tuple[bool, str]:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return False, "Only http/https URLs are allowed."

    opened = webbrowser.open(url)
    if opened:
        return True, "Opened URL in your default browser."

    return False, "Browser open request was sent but could not be confirmed."


def _search_web(query: str, max_results: int = 5) -> list[SearchResult]:
    encoded = urllib.parse.urlencode(
        {
            "q": query,
            "format": "json",
            "no_redirect": 1,
            "no_html": 1,
            "skip_disambig": 1,
        }
    )
    url = f"https://api.duckduckgo.com/?{encoded}"

    with urllib.request.urlopen(url, timeout=10) as response:
        payload = json.loads(response.read().decode("utf-8"))

    results: list[SearchResult] = []

    abstract = (payload.get("AbstractText") or "").strip()
    abstract_url = (payload.get("AbstractURL") or "").strip()
    heading = (payload.get("Heading") or "Result").strip()

    if abstract and abstract_url:
        results.append(SearchResult(title=heading, url=abstract_url, snippet=abstract))

    def flatten_related(items: list[dict]) -> list[dict]:
        flat: list[dict] = []
        for item in items:
            if "Topics" in item:
                flat.extend(item["Topics"])
            else:
                flat.append(item)
        return flat

    for item in flatten_related(payload.get("RelatedTopics", [])):
        text = (item.get("Text") or "").strip()
        link = (item.get("FirstURL") or "").strip()
        if not text or not link:
            continue
        title = text.split(" - ")[0].strip()
        results.append(SearchResult(title=title, url=link, snippet=text))
        if len(results) >= max_results:
            break

    return results[:max_results]


def _render_help() -> None:
    print(Fore.LIGHTGREEN_EX + Style.BRIGHT + "\nGoofyAi Pro Commands" + Style.RESET_ALL)
    print("  /help                 Show this help")
    print("  /model <name>         Switch Ollama model")
    print("  /run <command>        Validate + run a shell command")
    print("  /search <query>       Search the web (DuckDuckGo)")
    print("  /open <url>           Open URL in browser")
    print("  /history              Show recent conversation turns")
    print("  /quit                 Exit")
    print("\nTip: normal text prompts go to the AI agent.\n")


def _show_history(history: list[dict[str, str]], limit: int = 8) -> None:
    if not history:
        _print_status("No chat history yet.")
        return

    _print_status("Recent conversation:", Fore.LIGHTBLUE_EX)
    for turn in history[-limit:]:
        role = turn["role"]
        content = turn["content"].strip().replace("\n", " ")
        if len(content) > 120:
            content = content[:117] + "..."
        color = Fore.CYAN if role == "user" else Fore.LIGHTMAGENTA_EX
        print(color + f"- {role}: " + Style.RESET_ALL + content)


def _is_command_candidate(ai_response: str) -> bool:
    cleaned = ai_response.strip()
    if not cleaned or "\n" in cleaned:
        return False

    is_valid, _ = validate_command(cleaned)
    return is_valid


def _run_command_and_render(command: str) -> None:
    _print_status("Running command with safety validation...", Fore.LIGHTBLUE_EX)
    result = runCmd(cmd=command)

    if not result.ok and result.returncode is None:
        _print_status(f"⛔ Blocked: {result.reason}", Fore.LIGHTRED_EX)
        return

    if result.ok:
        _print_status("✅ Command executed successfully.", Fore.LIGHTGREEN_EX)
    else:
        _print_status("⚠️ Command ran but returned an error.", Fore.LIGHTYELLOW_EX)

    _print_status(
        f"Command: {result.command} | Exit: {result.returncode} | Time: {result.duration_s:.2f}s",
        Fore.LIGHTBLACK_EX,
    )

    if result.stdout:
        print(Fore.WHITE + Style.BRIGHT + "stdout:" + Style.RESET_ALL)
        print(result.stdout)

    if result.stderr:
        print(Fore.LIGHTRED_EX + Style.BRIGHT + "stderr:" + Style.RESET_ALL)
        print(result.stderr)


def _handle_slash_command(state: AgentState, user_input: str) -> bool:
    parts = shlex.split(user_input)
    cmd = parts[0].lower()

    if cmd in {"/quit", "/exit"}:
        _print_status("Session ended. Bye.", Fore.LIGHTBLACK_EX)
        raise SystemExit(0)

    if cmd == "/help":
        _render_help()
        return True

    if cmd == "/model":
        if len(parts) < 2:
            _print_status("Usage: /model <ollama-model>", Fore.LIGHTYELLOW_EX)
            return True
        state.model = parts[1]
        _print_status(f"Model switched to: {state.model}", Fore.LIGHTGREEN_EX)
        return True

    if cmd == "/history":
        _show_history(state.history)
        return True

    if cmd == "/run":
        if len(parts) < 2:
            _print_status("Usage: /run <command>", Fore.LIGHTYELLOW_EX)
            return True
        shell_cmd = user_input[len("/run") :].strip()
        _run_command_and_render(shell_cmd)
        return True

    if cmd == "/open":
        if len(parts) < 2:
            _print_status("Usage: /open <url>", Fore.LIGHTYELLOW_EX)
            return True
        ok, message = _safe_open_url(parts[1])
        color = Fore.LIGHTGREEN_EX if ok else Fore.LIGHTYELLOW_EX
        _print_status(message, color)
        return True

    if cmd == "/search":
        query = user_input[len("/search") :].strip()
        if not query:
            _print_status("Usage: /search <query>", Fore.LIGHTYELLOW_EX)
            return True
        _print_status(f"Searching web for: {query}", Fore.LIGHTBLUE_EX)
        try:
            results = _search_web(query)
        except Exception as exc:
            _print_status(f"Search failed: {exc}", Fore.LIGHTRED_EX)
            return True

        if not results:
            _print_status("No results found.", Fore.LIGHTYELLOW_EX)
            return True

        for idx, result in enumerate(results, start=1):
            print(Fore.WHITE + Style.BRIGHT + f"{idx}. {result.title}" + Style.RESET_ALL)
            print(f"   {result.url}")
            print(f"   {result.snippet}\n")
        return True

    _print_status("Unknown command. Use /help.", Fore.LIGHTYELLOW_EX)
    return True


def _chat_with_model(state: AgentState, user_input: str) -> str:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}, *state.history, {"role": "user", "content": user_input}]

    stream = chat(model=state.model, stream=True, messages=messages)

    print()
    print(Fore.LIGHTBLACK_EX + Style.BRIGHT + " thinking..", end="", flush=True)
    time.sleep(0.5)

    sys.stdout.write("\r" + " " * 80 + "\r")
    sys.stdout.write(f"{Fore.LIGHTMAGENTA_EX}{Style.BRIGHT} GoofyAi Pro: {Style.RESET_ALL}")
    sys.stdout.flush()

    ai_response = ""
    for chunk in stream:
        content = chunk["message"]["content"]
        print(content, end="", flush=True)
        ai_response += content

    print("\n")
    return ai_response.strip()


def strtcht() -> None:
    state = AgentState()
    _print_status('GoofyAi Pro is online. Type /help for commands, /quit to exit.', Fore.LIGHTGREEN_EX)

    while True:
        user_input = input(f"{Fore.CYAN}{Style.BRIGHT} You: {Style.RESET_ALL}").strip()
        if not user_input:
            continue

        if user_input.startswith("/"):
            _handle_slash_command(state, user_input)
            print()
            continue

        if user_input.lower() in {"quit", "exit"}:
            _print_status("Session ended. Bye.", Fore.LIGHTBLACK_EX)
            break

        try:
            ai_response = _chat_with_model(state, user_input)
        except Exception as exc:
            _print_status(f"Model call failed: {exc}", Fore.LIGHTRED_EX)
            print()
            continue

        state.history.append({"role": "user", "content": user_input})
        state.history.append({"role": "assistant", "content": ai_response})

        if _is_command_candidate(ai_response):
            _print_status("AI proposed an executable command.", Fore.LIGHTBLUE_EX)
            _run_command_and_render(ai_response)

        print()
