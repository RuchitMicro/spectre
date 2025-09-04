
import os
from pathlib import Path

from .utils         import run_command
from .venv_manager  import VirtualEnvManager


class DjangoManager:
    def __init__(self, venv: VirtualEnvManager) -> None:
        self.venv = venv

    def create_project(self, project_name: str, project_path: Path) -> None:
        project_path.mkdir(parents=True, exist_ok=True)
        cwd = os.getcwd()
        try:
            os.chdir(str(project_path))
            run_command([str(self.venv.bin_path / "django-admin"), "startproject", project_name, "."],
                        "Failed to create Django project.")
        finally:
            os.chdir(cwd)

    def run_migrations(self, project_path: Path) -> None:
        cwd = os.getcwd()
        try:
            os.chdir(str(project_path))
            run_command([str(self.venv.bin_path / "python"), "manage.py", "makemigrations"],
                        "Failed to make migrations.")
            run_command([str(self.venv.bin_path / "python"), "manage.py", "migrate"],
                        "Failed to run migrations.")
        finally:
            os.chdir(cwd)

    def create_superuser(self, project_path: Path) -> None:
        cwd = os.getcwd()
        try:
            os.chdir(str(project_path))
            cmd = [
                str(self.venv.bin_path / "python"),
                "manage.py",
                "shell",
                "-c",
                ("from django.contrib.auth import get_user_model; "
                 "User = get_user_model(); "
                 "User.objects.create_superuser('admin', 'admin@example.com', 'admin')"),
            ]
            run_command(cmd, "Failed to create superuser.")
        finally:
            os.chdir(cwd)
