# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

The architecture, layer rules, API contract, and house style for this project are
in AGENTS.md. It is imported below, so treat it as part of these instructions.

@AGENTS.md

## Deeper references

Read these on demand rather than up front:

- `docs/architecture.md`: how the auto-registering admin, `CommonModel`, and the
  generated serializer layer actually work, and why they are built that way.
- `docs/conventions.md`: the house style, and the reasoning behind heavy models
  with thin views.
- `docs/recipes.md`: step-by-step recipes for the common tasks.

## Skills

Invoke these rather than improvising the steps:

- `/add-model` adds a model end to end, including `admin_meta` and the migration.
- `/add-endpoint` exposes a model through the API with the right base class.
- `/verify` runs the full validation gate and interprets the failures.

## Working agreements

- Before adding a model or endpoint, check whether `CommonModel`, `admin_meta`,
  `ReadOnlyView`, or `CreateOnlyView` already covers it. This codebase is small
  because it leans on those four. Adding a hand-written ModelAdmin or
  ModelSerializer needs a stated reason.
- After changing `api/models.py`, always run `python manage.py makemigrations api`
  and include the generated migration in the same change. A model edit without
  its migration is an incomplete change.
- Run `make verify` before reporting work as finished, and report the real result.
  If tests fail, say so and show the output.
- `.env` holds real local credentials. Never read it into a response, commit it,
  or copy its values into code. `.env.example` is the file to update when a new
  setting is introduced.
- Do not run `migrate` against a non-local database, and do not run destructive
  management commands such as `flush` or `reset_db` without being asked.
- The default superuser is `admin` / `admin`. Mention rotating it when the project
  is being prepared for deployment, and never reuse that password anywhere else.
