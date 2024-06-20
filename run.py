import os
import subprocess
import sys
import shutil
import requests
import inquirer
import typer
import configparser
from rich.console import Console

# Initialize Typer application and rich console for colored output
app = typer.Typer()
console = Console()

# Function to handle errors and exit the script
def handle_error(message):
    console.print(f"[bold red]Error:[/bold red] {message}")
    sys.exit(1)

# Function to run shell commands and handle errors if the command fails
def run_command(command, error_message):
    result = subprocess.run(command, shell=True, env=os.environ.copy())
    if result.returncode != 0:
        handle_error(error_message)

# Function to create a virtual environment
def create_virtualenv(venv_path):
    run_command(f"python3 -m venv {venv_path}", "Failed to create virtual environment.")

# Function to install Django in the virtual environment
def install_django(venv_bin_path):
    run_command(f"{venv_bin_path}/pip install --upgrade pip", "Failed to upgrade pip.")
    run_command(f"{venv_bin_path}/pip install django", "Failed to install Django.")

# Function to install requirements from a requirements.txt file if it exists
def install_requirements(venv_bin_path, requirements_path):
    if os.path.exists(requirements_path):
        run_command(f"{venv_bin_path}/pip install -r {requirements_path}", "Failed to install requirements from requirements.txt")

# Function to create a new Django project
def create_django_project(project_name, project_path, venv_bin_path):
    os.chdir(project_path)
    run_command(f"{venv_bin_path}/django-admin startproject {project_name} .", "Failed to create Django project.")

# Function to apply a preset by copying files and directories
def apply_preset(project_path, preset, venv_bin_path, project_name):
    # Define preset, global, and project directories
    preset_dir = os.path.join(os.path.dirname(__file__), "presets", preset)
    global_dir = os.path.join(preset_dir, "__global__")
    project_dir = os.path.join(preset_dir, "__project__")
    django_project_dir = os.path.join(project_path, project_name)

    if preset:
        # Create a Django app named after the preset
        run_command(f"{venv_bin_path}/django-admin startapp {preset}", "Failed to create Django app.")
        
        # Define app directory path
        app_dir = os.path.join(project_path, f"{preset}")
        
        if os.path.isdir(preset_dir):
            for item in os.listdir(preset_dir):
                # Skip the __global__ and __project__ directories
                if item in ["__global__", "__project__"]:
                    continue
                s = os.path.join(preset_dir, item)
                d = os.path.join(app_dir, item)
                # Copy directory or file to app directory
                if os.path.isdir(s):
                    shutil.copytree(s, d, dirs_exist_ok=True)
                else:
                    shutil.copy2(s, d)
        else:
            handle_error(f"Preset directory {preset_dir} does not exist.")
        
        # Fetch admin.py from GitHub and save it in the app directory
        github_url = "https://raw.githubusercontent.com/RuchitMicro/django-admin.py/django-unfold-admin/admin.py"
        response = requests.get(github_url)
        if response.status_code == 200:
            admin_py_content = response.text
            # Replace global_app_name = 'web' with the preset name
            admin_py_content = admin_py_content.replace("'web'", f"'{preset}'")
            with open(os.path.join(app_dir, "admin.py"), "w") as f:
                f.write(admin_py_content)
        else:
            handle_error("Failed to fetch admin.py from GitHub.")

        # Install additional requirements if requirements.txt exists in the preset directory
        requirements_path = os.path.join(preset_dir, 'requirements.txt')
        install_requirements(venv_bin_path, requirements_path)

    # Copy the contents of __global__ directory to the root project directory
    if os.path.isdir(global_dir):
        for item in os.listdir(global_dir):
            s = os.path.join(global_dir, item)
            d = os.path.join(project_path, item)
            # Copy directory or file to project root directory
            if os.path.isdir(s):
                shutil.copytree(s, d, dirs_exist_ok=True)
            else:
                shutil.copy2(s, d)

    # Copy the contents of __project__ directory to the main Django project directory
    if os.path.isdir(project_dir):
        for item in os.listdir(project_dir):
            s = os.path.join(project_dir, item)
            d = os.path.join(django_project_dir, item)
            # Copy directory or file to main Django project directory
            if os.path.isdir(s):
                shutil.copytree(s, d, dirs_exist_ok=True)
            else:
                shutil.copy2(s, d)

    # Ensure the preset app is in INSTALLED_APPS
    settings_path = os.path.join(django_project_dir, 'settings.py')
    add_app_to_installed_apps(settings_path, preset)

# Function to add an app to the INSTALLED_APPS setting in settings.py
def add_app_to_installed_apps(settings_path, app_name):
    with open(settings_path, 'r') as file:
        lines = file.readlines()

    # Check if the app is already in INSTALLED_APPS
    if any(app_name in line for line in lines):
        return

    # Find the INSTALLED_APPS line and insert the app
    for i, line in enumerate(lines):
        if line.strip().startswith('INSTALLED_APPS'):
            start = i
            break
    else:
        handle_error(f"INSTALLED_APPS not found in {settings_path}")

    # Insert the app into the list
    for i in range(start, len(lines)):
        if lines[i].strip().startswith(']'):
            lines.insert(i, f"    '{app_name}',\n")
            break

    # Write the modified lines back to settings.py
    with open(settings_path, 'w') as file:
        file.writelines(lines)

# Function to run Django database migrations
def run_migrations(project_path, venv_bin_path):
    os.chdir(project_path)
    run_command(f"{venv_bin_path}/python manage.py makemigrations", "Failed to make migrations.")
    run_command(f"{venv_bin_path}/python manage.py migrate", "Failed to run migrations.")

# Function to create a Django superuser
def create_superuser(project_path, venv_bin_path):
    os.chdir(project_path)
    run_command(
        f'echo "from django.contrib.auth import get_user_model; User = get_user_model(); '
        f'User.objects.create_superuser(\'admin\', \'admin@example.com\', \'admin\')" | '
        f'{venv_bin_path}/python manage.py shell',
        "Failed to create superuser."
    )

# Function to select a directory using inquirer prompts
def select_directory(prompt_message):
    current_dir = os.path.abspath(os.curdir)
    while True:
        # List directories including parent directory
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
            # Confirm the selected directory
            use_dir = inquirer.confirm(f"Use this directory ({current_dir})?", default=True)
            if use_dir:
                return current_dir

# Function to read parameters from params file or prompt the user for missing data
def read_params():
    config = configparser.ConfigParser()
    if os.path.exists('params'):
        config.read('params')
        project_name = config.get('DEFAULT', 'project_name', fallback=None)
        preset = config.get('DEFAULT', 'preset', fallback=None)
        project_path = config.get('DEFAULT', 'project_path', fallback=None)
        env_path = config.get('DEFAULT', 'env_path', fallback=None)
    else:
        project_name = None
        preset = None
        project_path = None
        env_path = None
    
    if not project_name:
        project_name = typer.prompt("Enter the project name")
    if not preset:
        preset = typer.prompt("Enter the preset name (e.g., web)")
    if not project_path:
        console.print("Select the project location:")
        project_path = select_directory("Navigate to the project location")
    if not env_path:
        console.print("Select the environment location:")
        env_path = select_directory("Navigate to the environment location")
    
    return project_name, preset, project_path, env_path

# Main command for the Typer application
@app.command()
def main():
    # Read parameters from params file or prompt the user for missing data
    project_name, preset, project_path, env_path = read_params()

    # Define full paths for the project and virtual environment
    project_full_path = os.path.join(project_path, project_name)
    venv_path = os.path.join(env_path, project_name)
    venv_bin_path = os.path.join(venv_path, 'bin')

    # Validate the existence of selected directories
    if not os.path.exists(project_path):
        handle_error(f"Parent directory {project_path} does not exist or is not accessible.")
    if not os.path.exists(env_path):
        handle_error(f"Environment directory {env_path} does not exist or is not accessible.")
    
    # Create project directory with appropriate permissions
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

    # Apply preset if specified
    if preset:
        console.print(f"[bold green]Applying preset {preset}...[/bold green]")
        apply_preset(project_full_path, preset, venv_bin_path, project_name)

    console.print(f"[bold green]Running database migrations...[/bold green]")
    run_migrations(project_full_path, venv_bin_path)

    console.print(f"[bold green]Creating superuser...[/bold green]")
    create_superuser(project_full_path, venv_bin_path)

    # Final message with instructions to activate the virtual environment
    console.print(f"[bold green]Django project {project_name} created successfully in {project_path}![/bold green]")
    console.print(f"[bold yellow]To activate the virtual environment, use: source {venv_bin_path}/activate[/bold yellow]")

# Entry point for the script
if __name__ == "__main__":
    app()
