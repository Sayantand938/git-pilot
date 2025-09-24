# ai_commit.py
from utils.git_utils import get_repo, get_staged_diff, commit
from utils.ai_utils import generate_commit_message
from rich.console import Console
from rich.panel import Panel
import sys

console = Console()

def prompt_user_choice():
    console.print("\n[A]ccept | [R]egenerate | [E]dit manually", style="bold yellow")
    choice = console.input("Your choice: ").strip().lower()
    return choice

def main():
    # Handle missing Git repo gracefully
    try:
        repo = get_repo()
    except Exception:
        console.print("[red]Error:[/red] This directory is not a Git repository. Run 'git init' first.")
        return

    # Auto-stage all changes
    repo.git.add(A=True)

    # Check staged diff
    diff = get_staged_diff(repo)
    if not diff.strip():
        console.print("[yellow]No changes to commit.[/yellow]")
        return

    while True:
        # Generate AI commit message
        console.print("[bold green]Generating AI commit message...[/bold green]")
        message = generate_commit_message(diff)

        # Show in a Rich panel
        console.print(Panel(message, title="AI Suggested Commit Message", style="cyan"))

        # Ask user for confirmation or regeneration
        choice = prompt_user_choice()
        if choice == "a":
            if "--commit" in sys.argv:
                commit(repo, message)
                console.print("[bold green]Changes committed automatically![/bold green]")
            else:
                console.print("[yellow]Commit not executed. Use '--commit' flag to commit automatically.[/yellow]")
            break
        elif choice == "r":
            console.print("[blue]Regenerating commit message...[/blue]\n")
            continue
        elif choice == "e":
            console.print("[blue]Enter your custom commit message (finish with Enter):[/blue]")
            message = console.input()
            if "--commit" in sys.argv:
                commit(repo, message)
                console.print("[bold green]Changes committed with custom message![/bold green]")
            else:
                console.print("[yellow]Commit not executed. Use '--commit' flag to commit automatically.[/yellow]")
            break
        else:
            console.print("[red]Invalid choice. Please select A, R, or E.[/red]")

if __name__ == "__main__":
    main()
