from ollama import chat
from colorama import Fore, init, Style
import sys
import time
from utils.runCmd import runCmd
init(autoreset=True)

def strtcht(ongoing=True):
    while ongoing:
        utxt = f"{Fore.CYAN}{Style.BRIGHT} You: {Style.RESET_ALL}"
        atxt = f"{Fore.LIGHTMAGENTA_EX}{Style.BRIGHT} GoofyAi: {Style.RESET_ALL}"

        usrinpt = input(utxt)

        if usrinpt.lower() == 'quit':
            ongoing = False
        else:
            # Start streaming response
            stream = chat(
                model='qwen2.5-coder:7b',
                stream=True,
                messages = [
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
            
            # Visual Effect, Good spacing
            print()
            # Print thinking message without newline
            print(Fore.LIGHTBLACK_EX + Style.BRIGHT + ' thinking..', end='', flush=True)
            time.sleep(1)  # optional small delay for UX effect

            # Clear the thinking line and start AI response
            sys.stdout.write('\r' + ' ' * 50 + '\r')  # clear line
            sys.stdout.write(atxt)
            sys.stdout.flush()

            ai_response = ''
            # Stream AI response character by character
            for chunk in stream:
                content = chunk['message']['content']
                print(content, end='', flush=True)
                ai_response += content
            
            

            if 'touch' in ai_response or 'rm' in ai_response:
                print()
                succss = f"{Fore.LIGHTGREEN_EX}{Style.BRIGHT} File Created"
                print(Fore.LIGHTMAGENTA_EX, Style.BRIGHT + 'Creating file')
                runCmd(cmd=ai_response)
                sys.stdout.write('\r' + ' ' * 50 + '\r')  # clear line
                sys.stdout.write(succss)
            print('\n')