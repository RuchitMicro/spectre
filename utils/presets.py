
import os
import shutil
from pathlib import Path
import requests
from rich.console import Console

from .constants import REQUESTS_TIMEOUT
from .errors import handle_error
from .utils import run_command
from .venv_manager import VirtualEnvManager
from .settings_editor import SettingsEditor


console = Console()


class PresetApplier:
    def __init__(self, venv: VirtualEnvManager) -> None:
        self.venv = venv

    def _install_requirements_if_any(self, requirements_path: Path) -> None:
        if requirements_path.exists():
            run_command([str(self.venv.bin_path / "pip"), "install", "-r", str(requirements_path)],
                        "Failed to install requirements from requirements.txt")

    def apply(self, project_path: Path, preset: str, project_name: str, admin_preset_url: str, base_dir) -> None:
        preset_dir = base_dir / "presets" / preset
        global_dir = preset_dir / "__global__"
        project_dir = preset_dir / "__project__"
        django_project_dir = project_path / project_name

        # create app
        app_dir = project_path / preset
        if not app_dir.exists():
            cwd = os.getcwd()
            try:
                os.chdir(str(project_path))                      # <-- ensure correct location
                run_command(
                    [str(self.venv.bin_path / "django-admin"), "startapp", preset],
                    "Failed to create Django app."
                )
            finally:
                os.chdir(cwd)

        # copy preset files
        if preset_dir.is_dir():
            for item in preset_dir.iterdir():
                if item.name in {"__global__", "__project__"}:
                    continue
                dest = app_dir / item.name
                if item.is_dir():
                    shutil.copytree(item, dest, dirs_exist_ok=True)
                else:
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(item, dest)
        else:
            handle_error(f"Preset directory {preset_dir} does not exist.")

        # Fetch the shared admin.py template and write it into the app, rebinding
        # the hardcoded 'web' app label to this preset's name.
        #
        # This is best-effort: the preset ships its own admin.py (already copied
        # above), so a network failure must not abort a scaffold that has already
        # created the venv and the Django project.
        try:
            response = requests.get(admin_preset_url, timeout=REQUESTS_TIMEOUT)
            if response.status_code == 200:
                admin_py_content = response.text.replace("'web'", f"'{preset}'")
                (app_dir / "admin.py").write_text(admin_py_content)
            else:
                console.print(
                    f"[yellow]Could not fetch admin.py (HTTP {response.status_code}). "
                    f"Keeping the admin.py bundled with the '{preset}' preset.[/yellow]"
                )
        except requests.RequestException as exc:
            console.print(
                f"[yellow]Could not fetch admin.py ({exc}). "
                f"Keeping the admin.py bundled with the '{preset}' preset.[/yellow]"
            )

        # extra requirements from preset global
        self._install_requirements_if_any(global_dir / "requirements.txt")

        # copy global into project root
        if global_dir.is_dir():
            for item in global_dir.iterdir():
                dest = project_path / item.name
                if item.is_dir():
                    shutil.copytree(item, dest, dirs_exist_ok=True)
                else:
                    shutil.copy2(item, dest)

        # copy project-specific files into django package dir
        if project_dir.is_dir():
            for item in project_dir.iterdir():
                dest = django_project_dir / item.name
                if item.is_dir():
                    shutil.copytree(item, dest, dirs_exist_ok=True)
                else:
                    shutil.copy2(item, dest)

        # ensure preset app is registered
        SettingsEditor().add_app_to_installed_apps(django_project_dir / "settings.py", preset)
