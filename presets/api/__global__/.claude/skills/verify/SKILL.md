---
name: verify
description: Run the full validation gate for this Django project (system checks, missing-migration guard, tests) and interpret the failures. Use before reporting work as finished, or when asked to check, validate, or test the project.
---

# Verify

Run the gate:

```bash
make verify
```

Which is:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
pytest
```

Report the real result. If something fails, say so and show the output. Do not
describe work as finished on the strength of a passing subset.

## Interpreting failures

### `makemigrations --check` exits non-zero

A model was edited without generating its migration. This is the most common
failure in this codebase. Fix it:

```bash
python manage.py makemigrations api
```

Then include the generated migration file in the change.

### `RuntimeError: SECRET_KEY is not set`

`.env` is missing or has no `SECRET_KEY`. Copy the template and generate one:

```bash
cp .env.example .env
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

Never read the contents of an existing `.env` into a response.

### `NameError` or `ImproperlyConfigured` from `api/admin.py`

`api/admin.py` registers every model in the app automatically. A model whose
`admin_meta` names a field that does not exist will fail here, not in `models.py`.
Check that every name in `list_display`, `search_fields`, `list_filter`,
`list_editable`, and `ordering` is a real field or a real model method.

### A TextField is being corrupted on save

The field is listed in `admin_meta['rtf_fields']`, so the admin renders it as a
rich text editor and the editor rewrites the markup. Remove it from that list.

If the model still uses the legacy `rtf_exclude` key, every TextField *except*
the listed ones gets the editor. Migrate it to `rtf_fields`, which is opt-in.

### A rich text editor disappeared from a field

The model was migrated to `rtf_fields` without listing that field. Under the old
`rtf_exclude` key any unlisted TextField got the editor by default; under
`rtf_fields` nothing does unless named. Add the field to `rtf_fields`.

### `django.db.utils.OperationalError` on connect

`DB_NAME` is set in `.env`, so the project expects PostgreSQL. Either start it
(`docker compose up db`) or clear `DB_NAME` to fall back to SQLite.

### Cache errors

`REDIS_URL` is set but Redis is not running. Either start it
(`docker compose up redis`) or clear `REDIS_URL` to fall back to the in-process
cache.

## Checking an endpoint by hand

```bash
python manage.py runserver 0.0.0.0:8000
curl -s localhost:8000/api/ | head
```

`/api/` is the health endpoint and returns `{"message": "Healthy and alive!"}`.

For an authenticated route, get a token first:

```bash
curl -s -X POST localhost:8000/api/token/ \
  -H 'Content-Type: application/json' \
  -d '{"username": "admin", "password": "admin"}'
```
