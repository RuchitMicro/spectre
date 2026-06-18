
import os
import shutil
import subprocess

from typing     import Iterable, Union
from .errors    import handle_error


Command = Union[str, Iterable[str]]


def run_command(command: Command, error_message: str) -> None:
    """Run a shell command or a list of args.

    - If `command` is a string, it will be executed with `shell=True`.
    - If `command` is an iterable, it will be executed directly.
    """
    try:
        if isinstance(command, str):
            result = subprocess.run(command, shell=True, env=os.environ.copy())
        else:
            result = subprocess.run(list(command), env=os.environ.copy())
    except Exception as exc:  # pragma: no cover - fatal behaviour preserved
        handle_error(f"{error_message} Exception: {exc}")

    if result.returncode != 0:
        handle_error(error_message)


def which(*names: str) -> str | None:
    for n in names:
        p = shutil.which(n)
        if p:
            return p
    return None
