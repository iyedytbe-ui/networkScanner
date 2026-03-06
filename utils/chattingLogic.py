from ollama import chat
from colorama import Fore, init, Style
import sys
import time
from utils.runCmd import runCmd, validate_command

init(autoreset=True)


def _is_command_candidate(ai_response: str) -> bool:
    cleaned = ai_response.strip()
    if not cleaned:
        return False

    if '\n' in cleaned:
        return False

    is_valid, _ = validate_command(cleaned)
    return is_valid


def _print_status(message: str, color=Fore.LIGHTBLACK_EX):
    print(color + Style.BRIGHT + message + Style.RESET_ALL)


def strtcht(ongoing=True):
    _print_status('GoofyAi is online. Type "quit" to exit.', Fore.LIGHTGREEN_EX)

    while ongoing:
        utxt = f"{Fore.CYAN}{Style.BRIGHT} You: {Style.RESET_ALL}"
        atxt = f"{Fore.LIGHTMAGENTA_EX}{Style.BRIGHT} GoofyAi: {Style.RESET_ALL}"

        usrinpt = input(utxt)

        if usrinpt.lower() == 'quit':
            _print_status('Session ended. Bye.', Fore.LIGHTBLACK_EX)
            ongoing = False
            continue

        stream = chat(
            model='qwen2.5-coder:7b',
            stream=True,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a professional coding assistant integrated into a backend system.\n\n"
                        "You operate in TWO MODES:\n\n"
                        "1) COMMAND MODE (for subprocess execution)\n"
                        "- If the user asks to perform an OS action (create file, move file, run program, install package, etc.),\n"
                        "  output ONLY the exact shell command required.\n"
                        "- Output must be a single line.\n"
                        "- No explanations, no markdown, no quotes, no comments.\n"
                        "- Example: touch main.py\n\n"
                        "2) ASSISTANT MODE (default)\n"
                        "- If the user asks for explanations, code, debugging help, architecture advice,\n"
                        "  or anything not requiring OS execution, respond normally.\n"
                        "- Provide clear, professional programming guidance.\n"
                        "- Use clean code examples when helpful.\n\n"
                        "SAFETY RULES:\n"
                        "- Never generate destructive or dangerous commands.\n"
                        "- If a command would be unsafe, output:\n"
                        "  echo unsafe_request_blocked\n\n"
                        "Decide the mode automatically based on the user's intent."
                    ),
                },
                {
                    "role": "user",
                    "content": usrinpt,
                },
            ]
        )

        print()
        print(Fore.LIGHTBLACK_EX + Style.BRIGHT + ' thinking..', end='', flush=True)
        time.sleep(0.8)

        sys.stdout.write('\r' + ' ' * 60 + '\r')
        sys.stdout.write(atxt)
        sys.stdout.flush()

        ai_response = ''
        for chunk in stream:
            content = chunk['message']['content']
            print(content, end='', flush=True)
            ai_response += content

        print('\n')

        cleaned_response = ai_response.strip()
        if not _is_command_candidate(cleaned_response):
            _print_status('No command execution requested. Response shown above.', Fore.LIGHTBLACK_EX)
            print()
            continue

        _print_status('Command detected. Running validation checks...', Fore.LIGHTBLUE_EX)

        result = runCmd(cmd=cleaned_response)

        if not result.ok and result.returncode is None:
            _print_status(f'⛔ Blocked: {result.reason}', Fore.LIGHTRED_EX)
            print()
            continue

        if result.ok:
            _print_status('✅ Command executed successfully.', Fore.LIGHTGREEN_EX)
        else:
            _print_status('⚠️ Command ran but returned an error.', Fore.LIGHTYELLOW_EX)

        _print_status(
            f"Command: {result.command} | Exit: {result.returncode} | Time: {result.duration_s:.2f}s",
            Fore.LIGHTBLACK_EX,
        )

        if result.stdout:
            print(Fore.WHITE + Style.BRIGHT + 'stdout:' + Style.RESET_ALL)
            print(result.stdout)

        if result.stderr:
            print(Fore.LIGHTRED_EX + Style.BRIGHT + 'stderr:' + Style.RESET_ALL)
            print(result.stderr)

        print()
