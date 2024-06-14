import os
import subprocess
import sys
import shutil
import requests
import inquirer
import typer
from rich.console import Console

app = typer.Typer()
console = Console()

def handle_error(message):
    console.print(f"[bold red]Error:[/bold red] {message}")
    sys.exit(1)

def run_command(command, error_message):
    result = subprocess.run(command, shell=True, env=os.environ.copy())
    if result.returncode != 0:
        handle_error(error_message)

def create_virtualenv(venv_path):
    run_command(f"python3 -m venv {venv_path}", "Failed to create virtual environment.")

def install_django(venv_bin_path):
    run_command(f"{venv_bin_path}/pip install --upgrade pip", "Failed to upgrade pip.")
    run_command(f"{venv_bin_path}/pip install django", "Failed to install Django.")

def install_requirements(venv_bin_path, requirements_path):
    if os.path.exists(requirements_path):
        run_command(f"{venv_bin_path}/pip install -r {requirements_path}", "Failed to install requirements from requirements.txt")

def create_django_project(project_name, project_path, venv_bin_path):
    os.chdir(project_path)
    run_command(f"{venv_bin_path}/django-admin startproject {project_name} .", "Failed to create Django project.")

def apply_preset(project_path, preset, venv_bin_path):
    if preset == "web":
        run_command(f"{venv_bin_path}/django-admin startapp web", "Failed to create Django app.")
        
        preset_dir = os.path.join(os.path.dirname(__file__), "presets", preset)
        app_dir = os.path.join(project_path, "web")
        
        if os.path.isdir(preset_dir):
            for item in os.listdir(preset_dir):
                s = os.path.join(preset_dir, item)
                d = os.path.join(app_dir, item)
                if os.path.isdir(s):
                    shutil.copytree(s, d, dirs_exist_ok=True)
                else:
                    shutil.copy2(s, d)
        else:
            handle_error(f"Preset directory {preset_dir} does not exist.")
        
        # Fetch admin.py from GitHub
        github_url = "https://raw.githubusercontent.com/RuchitMicro/django-admin.py/main/admin.py"
        response = requests.get(github_url)
        if response.status_code == 200:
            with open(os.path.join(app_dir, "admin.py"), "w") as f:
                f.write(response.text)
        else:
            handle_error("Failed to fetch admin.py from GitHub.")

        # Install requirements if requirements.txt exists in the preset directory
        requirements_path = os.path.join(preset_dir, 'requirements.txt')
        install_requirements(venv_bin_path, requirements_path)

def run_migrations(project_path, venv_bin_path):
    os.chdir(project_path)
    run_command(f"{venv_bin_path}/python manage.py makemigrations", "Failed to make migrations.")
    run_command(f"{venv_bin_path}/python manage.py migrate", "Failed to run migrations.")

def create_superuser(project_path, venv_bin_path):
    os.chdir(project_path)
    run_command(
        f'echo "from django.contrib.auth import get_user_model; User = get_user_model(); '
        f'User.objects.create_superuser(\'admin\', \'admin@example.com\', \'admin\')" | '
        f'{venv_bin_path}/python manage.py shell',
        "Failed to create superuser."
    )

def select_directory(prompt_message):
    current_dir = os.path.abspath(os.curdir)
    while True:
        directories = [".. (parent directory)"] + [d for d in os.listdir(current_dir) if os.path.isdir(os.path.join(current_dir, d))]
        question = [
            inquirer.List(
                'directory',
                message=prompt_message,
                choices=directories,
            ),
        ]
        answer = inquirer.prompt(question)['directory']
        
        if answer == ".. (parent directory)":
            current_dir = os.path.abspath(os.path.join(current_dir, ".."))
        else:
            current_dir = os.path.abspath(os.path.join(current_dir, answer))
            use_dir = inquirer.confirm(f"Use this directory ({current_dir})?", default=True)
            if use_dir:
                return current_dir

@app.command()
def main(
    project_name: str = typer.Option(..., prompt="Enter the project name"),
    preset: str = typer.Option(None, prompt="Enter the preset name (e.g., web)")
):
    console.print("Select the project location:")
    project_path = select_directory("Navigate to the project location")
    console.print("Select the environment location:")
    env_path = select_directory("Navigate to the environment location")

    project_full_path = os.path.join(project_path, project_name)
    venv_path = os.path.join(env_path, project_name)
    venv_bin_path = os.path.join(venv_path, 'bin')

    if not os.path.exists(project_path):
        handle_error(f"Parent directory {project_path} does not exist or is not accessible.")
    if not os.path.exists(env_path):
        handle_error(f"Environment directory {env_path} does not exist or is not accessible.")
    
    try:
        os.makedirs(project_full_path, exist_ok=True)
    except PermissionError:
        handle_error(f"Permission denied: Unable to create directory {project_full_path}. Please check permissions.")

    console.print(f"[bold green]Creating virtual environment in {env_path}...[/bold green]")
    create_virtualenv(venv_path)

    console.print(f"[bold green]Installing Django...[/bold green]")
    install_django(venv_bin_path)

    console.print(f"[bold green]Creating Django project...[/bold green]")
    create_django_project(project_name, project_full_path, venv_bin_path)

    if preset:
        console.print(f"[bold green]Applying preset {preset}...[/bold green]")
        apply_preset(project_full_path, preset, venv_bin_path)

    console.print(f"[bold green]Running database migrations...[/bold green]")
    run_migrations(project_full_path, venv_bin_path)

    console.print(f"[bold green]Creating superuser...[/bold green]")
    create_superuser(project_full_path, venv_bin_path)

    console.print(f"[bold green]Django project {project_name} created successfully in {project_path}![/bold green]")
    console.print(f"[bold yellow]To activate the virtual environment, use: source {venv_bin_path}/activate[/bold yellow]")

if __name__ == "__main__":
    app()
