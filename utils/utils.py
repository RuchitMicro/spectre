
import os
import secrets
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


def generate_secret_key(length: int = 50) -> str:
    """Generate a Django-style SECRET_KEY without importing Django.

    Mirrors django.core.management.utils.get_random_secret_key(), but usable
    before the project's virtualenv is on the path. The '$' and '%' characters
    are excluded so the value stays safe to paste into .env and docker-compose,
    where they would otherwise be interpolated.
    """
    alphabet = "abcdefghijklmnopqrstuvwxyz0123456789!@#^&*(-_=+)"
    return "".join(secrets.choice(alphabet) for _ in range(length))
