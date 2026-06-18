
import inquirer
import typer
import configparser
from pathlib        import Path
from typing         import Tuple
from rich.console   import Console
from .constants     import DEFAULT_ADMIN_PRESET_URL


console = Console()


def _select_directory(prompt_message: str) -> Path:
    current_dir = Path.cwd().resolve()
    while True:
        directories = [".. (parent directory)"] + [d.name for d in current_dir.iterdir() if d.is_dir()]
        question = [inquirer.List('directory', message=prompt_message, choices=directories)]
        answer = inquirer.prompt(question)['directory']

        if answer == ".. (parent directory)":
            current_dir = current_dir.parent
        else:
            current_dir = (current_dir / answer).resolve()
            use_dir = inquirer.confirm(f"Use this directory ({current_dir})?", default=True)
            if use_dir:
                return current_dir


def read_params() -> Tuple[str, str, Path, Path, str]:
    config = configparser.ConfigParser()
    if Path('params').exists():
        config.read('params')
        project_name        = config.get('DEFAULT', 'project_name', fallback=None)
        preset              = config.get('DEFAULT', 'preset', fallback=None)
        project_path        = config.get('DEFAULT', 'project_path', fallback=None)
        env_path            = config.get('DEFAULT', 'env_path', fallback=None)
        admin_preset_url    = config.get('DEFAULT', 'admin_preset_url', fallback=DEFAULT_ADMIN_PRESET_URL)

        db_name             = config.get('PG_DATABASE', 'db_name', fallback=None)
        db_user             = config.get('PG_DATABASE', 'db_user', fallback=None)
        db_password         = config.get('PG_DATABASE', 'db_password', fallback=None)
        db_host             = config.get('PG_DATABASE', 'db_host', fallback=None)
        db_port             = config.get('PG_DATABASE', 'db_port', fallback=None)
        db_config           = (db_host and db_port and db_name and db_user and db_password)
    else:
        project_name = preset = project_path = env_path = None
        admin_preset_url = DEFAULT_ADMIN_PRESET_URL

    if not project_name:
        project_name = typer.prompt("Enter the project name")
    if not preset:
        preset = typer.prompt("Enter the preset name (e.g., web)")
    if preset == 'saas' and not db_config:
        console.print("For saas DB is required.")
        raise typer.Abort()

    if not project_path:
        console.print("Select the project location:")
        project_path = _select_directory("Navigate to the project location")
    else:
        project_path = Path(project_path)
    if not env_path:
        console.print("Select the environment location:")
        env_path = _select_directory("Navigate to the environment location")
    else:
        env_path = Path(env_path)

    return {
        "project_name":project_name,
        "preset":preset,
        "project_path":project_path,
        "env_path":env_path,
        "admin_preset_url":admin_preset_url,
        "db" : {
            "db_name":db_name,
            "db_user":db_user,
            "db_password":db_password,
            "db_host":db_host,
            "db_port":db_port
        } if db_config else None
    }