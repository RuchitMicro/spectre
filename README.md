# Spectre

Spectre is a CLI scaffolding tool that generates opinionated Django projects.
It creates a virtualenv, runs `django-admin startproject`, then optionally
layers a "preset" on top: a Django app template with boilerplate files,
project-level settings, and infra files.

## Requirements

- Python 3.9+
- `django-admin` available once the virtualenv is set up (installed automatically)

## Install

```bash
pip install -r requirements.txt
```

## Usage

```bash
python run.py
```

You will be prompted for anything not already set in the `params` file,
including directory pickers for `project_path` and `env_path`.

## Configuration

Spectre reads its settings from a `params` file (INI format) in the repo
root. Any value left out is prompted for interactively.

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

If `preset = saas`, the `[PG_DATABASE]` section must be complete or the run
aborts.

## Presets

Each preset lives in `presets/<name>/` and is applied as a Django app of the
same name.

| Preset | What you get |
|---|---|
| `api` | DRF-based API project: JWT auth, dynamic filtering, logging config, Unfold admin. The most developed preset, with a working test suite and AI-agent onboarding docs (`AGENTS.md`, `docs/`, `.claude/`). |
| `web` | Server-rendered site: Unfold admin, TinyMCE, django-import-export, HTML templates and SCSS for blog, case studies, contact, and FAQ pages. |
| `saas` | Infra and project-only preset: commands, a `communication` package, a `public` app scaffold, `.vscode` launch config. Needs Postgres credentials since it wires up a real database. |
| `user` | Auth and account app: django-allauth-style templates for login, signup, password reset, social account, and OpenID, plus SCSS/CSS for the account UI. |

## What happens when you run it

1. Read or prompt for config (`params`).
2. Create a virtualenv and install Django into it.
3. Run `django-admin startproject <name> .`.
4. Apply the chosen preset, if any.
5. Replace placeholders (`{{project_name}}`, `{{secret_key}}`) across the
   generated project.
6. For `saas`, write DB credentials to `.env` and create the Postgres
   database.
7. Run migrations and create a superuser (`admin` / `admin@example.com` /
   `admin`).
8. Best-effort launch of VS Code (`code` or `code-insiders`) in the new
   project, pointed at the new virtualenv.

## `run.sh`

`run.sh` is a simpler, bash-only equivalent: venv, `django-admin
startproject`, then copy one preset's files into the generated app. It
predates the `__global__` / `__project__` split that `run.py` implements, so
treat `run.py` as the source of truth and `run.sh` as a legacy, minimal
alternative.

## Development

There is no test suite, linter, or build step for this repo itself. The
`api` preset does ship its own test suite; `make verify` should stay green
in a project generated with it.

See [CLAUDE.md](CLAUDE.md) for the full architecture notes.
