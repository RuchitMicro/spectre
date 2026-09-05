# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Spectre is a CLI scaffolding tool that generates opinionated Django projects. It creates a virtualenv, runs `django-admin startproject`, then optionally layers a "preset" (a Django app template with boilerplate files, project-level settings overrides, and infra files) onto the freshly created project.

## Running the tool

```bash
pip install -r requirements.txt
python run.py
```

Configuration is read from the `params` file (INI format, `configparser`) in the repo root:

```ini
[DEFAULT]
admin_preset_url = <url to a Django admin.py template>
project_name     = my_project
preset           = api        # api | web | saas | user
project_path     = /path/to/parent/dir
env_path         = /path/to/venvs/dir

[PG_DATABASE]    # only required when preset = saas
db_name = ...
db_user = ...
db_password = ...
db_host = ...
db_port = ...
```

Any value missing from `params` is prompted for interactively (via `typer`/`inquirer`), including directory pickers for `project_path`/`env_path`. `preset = saas` requires a complete `[PG_DATABASE]` section or the run aborts.

There is also a standalone `run.sh` — a simpler bash-only equivalent (venv + `django-admin startproject` + copy one preset's files directly into a generated app). It predates the `__global__`/`__project__` split in `run.py` and does not implement it; treat `run.py` as the source of truth and `run.sh` as a legacy/minimal alternative.

There is no test suite, linter, or build step for this repo itself — `pyproject.toml` declares a `spectre.cli:app` console-script entry point, but no `spectre/` package exists yet; `run.py` is the actual, current entry point.

## Architecture

### End-to-end flow (`run.py`)

1. `utils/config_loader.read_params()` — load/prompt for project config.
2. `VirtualEnvManager` (`utils/venv_manager.py`) — create the venv, install/upgrade pip, install Django.
3. `DjangoManager.create_project()` (`utils/django_manager.py`) — run `django-admin startproject <name> .` inside the venv.
4. If a preset was chosen, `PresetApplier.apply()` (`utils/presets.py`) layers it on (see below).
5. `PlaceholderReplacer.replace_project_placeholders()` (`utils/placeholders.py`) — walk the generated project and substitute tokens. `{{project_name}}` becomes the real project name and `{{secret_key}}` becomes a freshly generated key (`utils.utils.generate_secret_key`), so no two projects share a secret. Coverage is by suffix (`PLACEHOLDER_SUFFIXES`) plus an explicit filename list (`PLACEHOLDER_FILENAMES`) for extensionless files such as `Dockerfile`, `Makefile`, and `.env`. Add to those constants when a preset introduces a new placeholder-bearing file type, otherwise the token ships to users verbatim.
6. If `preset == 'saas'`, write DB credentials into `.env` and create the Postgres database (`DjangoManager.add_database_to_dotenv` / `create_database`).
7. `DjangoManager.run_migrations()` then `create_superuser()` (hardcoded `admin`/`admin@example.com`/`admin`).
8. `VSCodeLauncher.open()` (`utils/vscode.py`) — best-effort launch of `code`/`code-insiders` with `VIRTUAL_ENV`/`PATH` set to the new venv; silently skipped if the CLI isn't found.

All shell-outs go through `utils/utils.run_command()`, which calls `handle_error()` (`utils/errors.py`, prints and `sys.exit(1)`) on any non-zero exit — there's no exception-based flow control, so preset/venv code doesn't need its own error handling.

### Preset system (`presets/<name>/`, applied by `utils/presets.py`)

Each preset directory maps to a Django app of the same name and is applied via `django-admin startapp <preset>` inside the new project, then merged in three ways:

- **App files** (everything at the top level of `presets/<preset>/`, excluding `__global__`/`__project__`): copied directly into the generated app directory (`<project>/<preset>/`), overwriting the stub files `startapp` created (models.py, views.py, admin.py, etc.).
- **`__global__/`**: copied into the *project root* (sits alongside `manage.py`) — Dockerfile, docker-compose.yml, nginx.conf, `.env`, `.gitignore`, `.vscode/`, and any preset-specific `requirements.txt` (auto-installed into the venv if present).
- **`__project__/`**: copied into the *Django settings package* (`<project>/<project_name>/`) — e.g. `settings.py`, `urls.py`, logging config — overwriting the stubs Django generated.

After copying, two special steps run:
- `admin.py` is **fetched fresh from `admin_preset_url`** (a remote GitHub raw URL, default in `utils/constants.py`), then `'web'` is string-replaced with the actual preset name in its contents. The fetch is best-effort: on a network failure or non-200 it warns and keeps the `admin.py` the preset already copied, so a blip does not abort a scaffold that has already built the venv and project. This means a preset's own `admin.py` must stay working, not just be a placeholder.
- `SettingsEditor.add_app_to_installed_apps()` (`utils/settings_editor.py`) regex-patches the generated `settings.py` to add the preset app to `INSTALLED_APPS` (idempotent; a missing `INSTALLED_APPS` block is tolerated only for the `saas` preset, since `saas` has no app files/`startapp` step, only `__global__`/`__project__` payloads).

Current presets:
- `api` — DRF-based API project (JWT auth, dynamic filtering, logging config, Unfold admin). This is the most developed preset and the reference for the others. It ships **AI-agent onboarding files** in `__global__`: `AGENTS.md` (canonical conventions, imported by `CLAUDE.md` so the two cannot drift), `docs/` (architecture, conventions, recipes), and `.claude/` (three skills, a `/migrate` command, and a permission allowlist). Its architecture is that **the admin and serializers are generated from the models**: `api/admin.py` auto-registers every model in the app and applies the model's `admin_meta` dict as ModelAdmin attributes, while `django-api-helper` generates serializers and filtersets. When editing this preset, update `AGENTS.md` if a layer rule or the API contract changes. It has a working test suite (`presets/api/tests.py`); `make verify` in a generated project must stay green.
- `web` — Server-rendered site (Unfold admin, TinyMCE, django-import-export, HTML templates/SCSS for blog/case-studies/contact/FAQ pages).
- `saas` — Infra/project-only preset (no app code): commands, a `communication` package (adapters/channels/utils), a `public` app scaffold (migrations, email templates), `.vscode` launch config. Requires Postgres credentials since it wires up a real database.
- `user` — Auth/account app (django-allauth-style templates for login/signup/password reset/social account/openid, plus SCSS/CSS for the account UI).

When adding or editing a preset, keep the `__global__` vs `__project__` vs app-root distinction — putting a file in the wrong bucket means it lands in the wrong place in every generated project.
