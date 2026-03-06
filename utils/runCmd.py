import shlex
import subprocess
import time
from dataclasses import dataclass


@dataclass
class CommandResult:
    ok: bool
    command: str
    returncode: int | None = None
    stdout: str = ""
    stderr: str = ""
    reason: str = ""
    duration_s: float = 0.0


BLOCKED_TOKENS = {
    "rm",
    "reboot",
    "shutdown",
    "mkfs",
    "dd",
    "chmod",
    "chown",
    "sudo",
    "su",
    "kill",
    "killall",
    "poweroff",
    "halt",
    "init",
    "passwd",
    "useradd",
    "usermod",
    "deluser",
}

ALLOWED_COMMANDS = {
    "touch",
    "mkdir",
    "ls",
    "pwd",
    "cat",
    "echo",
    "python",
    "python3",
    "pip",
    "pip3",
    "mv",
    "cp",
    "find",
    "rg",
    "sed",
    "head",
    "tail",
    "wc",
    "git",
    "pytest",
    "node",
    "npm",
    "npx",
    "pnpm",
    "yarn",
    "make",
    "curl",
    "wget",
}


DISALLOWED_PATTERNS = ["&&", "||", ";", "|", ">", "<", "$("]


def validate_command(command: str) -> tuple[bool, str]:
    if not command or not command.strip():
        return False, "Empty command."

    if "\n" in command or "\r" in command:
        return False, "Multi-line commands are not allowed."

    for bad_pattern in DISALLOWED_PATTERNS:
        if bad_pattern in command:
            return False, f"Disallowed shell operator found: {bad_pattern}"

    try:
        tokens = shlex.split(command)
    except ValueError as exc:
        return False, f"Could not parse command safely: {exc}"

    if not tokens:
        return False, "No executable command found."

    executable = tokens[0].lower()

    if executable in BLOCKED_TOKENS:
        return False, f"Blocked potentially destructive command: '{executable}'"

    if executable not in ALLOWED_COMMANDS:
        return (
            False,
            f"Command '{executable}' is not in the safe allow-list. Ask for an approved command.",
        )

    return True, "Validation passed."


def runCmd(cmd: str, timeout_s: int = 45) -> CommandResult:
    is_valid, reason = validate_command(cmd)
    if not is_valid:
        return CommandResult(ok=False, command=cmd, reason=reason)

    start = time.perf_counter()
    try:
        completed = subprocess.run(
            shlex.split(cmd),
            capture_output=True,
            text=True,
            timeout=timeout_s,
            check=False,
        )
    except subprocess.TimeoutExpired:
        duration_s = time.perf_counter() - start
        return CommandResult(
            ok=False,
            command=cmd,
            reason=f"Command timed out after {timeout_s}s.",
            duration_s=duration_s,
        )
    except Exception as exc:
        duration_s = time.perf_counter() - start
        return CommandResult(
            ok=False,
            command=cmd,
            reason=f"Execution failed unexpectedly: {exc}",
            duration_s=duration_s,
        )

    duration_s = time.perf_counter() - start
    return CommandResult(
        ok=completed.returncode == 0,
        command=cmd,
        returncode=completed.returncode,
        stdout=(completed.stdout or "").strip(),
        stderr=(completed.stderr or "").strip(),
        reason="Execution completed." if completed.returncode == 0 else "Command exited with errors.",
        duration_s=duration_s,
    )
