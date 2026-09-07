
import sys
from pathlib import Path

from .utils import run_command


class VirtualEnvManager:
    def __init__(self, venv_path: Path) -> None:
        self.venv_path = venv_path

    @property
    def bin_path(self) -> Path:
        # Cross-platform support: Scripts on Windows
        scripts = self.venv_path / ("Scripts" if sys.platform.startswith("win") else "bin")
        return scripts

    def create(self) -> None:
        run_command([sys.executable, "-m", "venv", str(self.venv_path)], "Failed to create virtual environment.")

    def pip(self, *args: str) -> None:
        run_command([str(self.bin_path / "pip"), *args], "Pip command failed.")

    def install_django(self) -> None:
        self.pip("install", "--upgrade", "pip")
        self.pip("install", "django~=5.2.0")
        