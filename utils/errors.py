
import sys
from rich.console import Console

_console = Console()

def handle_error(message: str) -> None:
    """Print an error message and exit the process."""
    _console.print(f"[bold red]Error:[/bold red] {message}")
    sys.exit(1)