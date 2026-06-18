
import os
from pathlib        import Path
from rich.console   import Console

from .utils         import which
from .venv_manager  import VirtualEnvManager

console = Console()


class VSCodeLauncher:
    def open(self, project_path: Path, venv: VirtualEnvManager) -> None:
        code_cmd = which("code", "code-insiders")
        if not code_cmd:
            console.print("[yellow]VS Code CLI ('code' or 'code-insiders') not found. Skipping opening VS Code.[/yellow]")
            return

        env = os.environ.copy()
        env["VIRTUAL_ENV"] = str(venv.venv_path)
        env["PATH"] = str(venv.bin_path) + os.pathsep + env.get("PATH", "")

        os.spawnve(os.P_NOWAIT, code_cmd, [code_cmd, str(project_path)], env)
        console.print(
            f"[green]Opened VS Code for {project_path} with the virtual environment available in the environment.[/green]"
        )
