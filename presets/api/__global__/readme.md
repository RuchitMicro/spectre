# {{project_name}}

Django REST API scaffolded from the Spectre `api` preset.

The stack is Django 4.2 + DRF + SimpleJWT, with a self-registering Unfold admin
and `django-api-helper` supplying the generic CRUD layer.

## Quick start

```bash
source /path/to/venv/bin/activate      # the scaffolder printed this path
pip install -r requirements.txt
cp .env.example .env                   # .env is already written for you locally
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

- API root: http://localhost:8000/api/
- Admin: http://localhost:8000/admin/ (default superuser `admin` / `admin`, change it)

A fresh checkout runs with no external services: SQLite for the database and an
in-process cache. Set `DB_NAME` in `.env` to switch to PostgreSQL, and `REDIS_URL`
to switch the cache to Redis.

## Common commands

```bash
make run          # development server
make migrations   # makemigrations api
make migrate      # apply migrations
make test         # pytest
make verify       # checks + missing-migration guard + tests
```

## Working on this project

The conventions for this codebase are documented for humans and AI agents alike:

- `AGENTS.md` is the canonical guide: architecture, layer rules, and the API contract.
- `CLAUDE.md` points Claude Code at the same content and lists available skills.
- `docs/architecture.md` explains how the auto-registering admin and `CommonModel` work.
- `docs/conventions.md` explains the house style and why models carry the logic.
- `docs/recipes.md` has step-by-step recipes for the usual tasks.

Read `AGENTS.md` before adding a model or an endpoint. The admin and the
serializer layer are generated from the model, so most features are a models.py
change plus a URL.

## Deployment

```bash
docker compose up --build
```

Brings up PostgreSQL, Redis, gunicorn, and nginx. `web` runs migrations and
`collectstatic` on boot. Set the production values in `.env` first, in particular
`DEBUG=False`, a rotated `SECRET_KEY`, `ALLOWED_HOSTS`, and `CORS_ALLOWED_ORIGINS`.
