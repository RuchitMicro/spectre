
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

    def create_database(self, project_path: Path, db_name: str) -> None:
        cwd = os.getcwd()
        try:
            os.chdir(str(project_path))
            run_command([str(self.venv.bin_path / "python"), "manage.py", "dbshell", "-c", f"CREATE DATABASE {db_name};"],
                        "Failed to create PostgreSQL database. Ensure PostgreSQL is running and you have appropriate permissions.")
        finally:
            os.chdir(cwd)

    def add_database_to_dotenv(self, project_path: Path, project_name: str, db_user: str, db_password: str, db_host: str, db_port: str):
        """
        DB_NAME     =   {{project_name}}
        DB_USER     =   postgres
        DB_PASSWORD =   postgres
        DB_HOST     =   0.0.0.0
        DB_PORT     =   5432
        """
        dotenv_path = project_path / '.env'
        with open(dotenv_path, 'a') as f:
            f.write('\n')
            f.write('# Database configuration\n')
            f.write(f'DB_NAME={project_name}\n')
            f.write(f'DB_USER={db_user}\n')
            f.write(f'DB_PASSWORD={db_password}\n')
            f.write(f'DB_HOST={db_host}\n')
            f.write(f'DB_PORT={db_port}\n')
            f.write('\n')


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
