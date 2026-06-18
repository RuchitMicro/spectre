
import os
import sys
import typer
from pathlib        import Path
from typing         import Tuple
from rich.console   import Console

# Local imports
from utils.config_loader    import read_params
from utils.constants        import DEFAULT_ADMIN_PRESET_URL
from utils.venv_manager     import VirtualEnvManager
from utils.django_manager   import DjangoManager
from utils.presets          import PresetApplier
from utils.placeholders     import PlaceholderReplacer
from utils.vscode           import VSCodeLauncher
from utils.errors           import handle_error


app     = typer.Typer()
console = Console()


@app.command()
def main() -> None:
    params = read_params()
    project_name    = params['project_name']
    preset          = params['preset']
    project_path    = params['project_path']
    env_path        = params['env_path']
    admin_preset_url = params['admin_preset_url']
    db              = params['db']

    project_full_path = project_path / project_name
    venv_path = env_path / project_name

    if not project_path.exists():
        handle_error(f"Parent directory {project_path} does not exist or is not accessible.")
    if not env_path.exists():
        handle_error(f"Environment directory {env_path} does not exist or is not accessible.")

    try:
        project_full_path.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        handle_error(
            f"Permission denied: Unable to create directory {project_full_path}. Please check permissions."
        )

    # 1) venv & pip/django
    venv = VirtualEnvManager(venv_path)
    console.print(f"[bold green]Creating virtual environment in {env_path}...[/bold green]")
    venv.create()

    console.print(f"[bold green]Installing Django...[/bold green]")
    venv.install_django()

    # 2) Django project
    dj = DjangoManager(venv)
    console.print(f"[bold green]Creating Django project...[/bold green]")
    dj.create_project(project_name, project_full_path)

    # 3) Apply preset (optional)
    if preset:
        console.print(f"[bold green]Applying preset {preset}...[/bold green]")
        PresetApplier(venv).apply(
            project_path=project_full_path,
            preset=preset,
            project_name=project_name,
            admin_preset_url=admin_preset_url or DEFAULT_ADMIN_PRESET_URL,
            base_dir = Path(__file__).resolve().parent
        )

    console.print(f"[bold green]Adding settings.py Config {preset}...[/bold green]")
    PlaceholderReplacer().replace_project_placeholders(project_full_path, project_name)

    if preset == 'saas':
        # create_database
        console.print(f"[bold green]Creating database...[/bold green]")
        dj.add_database_to_dotenv(project_full_path, db['db_name'], db['db_user'], db['db_password'], db['db_host'], db['db_port'])
        dj.create_database(project_full_path, db['db_name'] )
        dj.create_database(project_full_path)
        

    console.print(f"[bold green]Running database migrations...[/bold green]")
    dj.run_migrations(project_full_path)

    console.print(f"[bold green]Creating superuser...[/bold green]")
    dj.create_superuser(project_full_path)

    console.print(
        f"[bold green]Django project {project_name} created successfully in {project_path}![/bold green]"
    )
    console.print(
        f"[bold yellow]To activate the virtual environment, use: source {venv.bin_path}/activate[/bold yellow]"
    )

    # 4) Try opening VS Code with venv path in env
    try:
        VSCodeLauncher().open(project_full_path, venv)
    except Exception as exc:
        console.print(f"[red]Opening VS Code failed: {exc}[/red]")


if __name__ == "__main__":
    app()
