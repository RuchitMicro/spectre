# AGENTS.md

`{{project_name}}` is a Django REST API scaffolded from the Spectre `api` preset.

Read this file before writing code. The single most important thing to understand
is that **the admin and the serializer layer are generated from the models**. Most
features are a change to `api/models.py` plus one URL line. If you find yourself
hand-writing a ModelAdmin or a ModelSerializer, you are almost certainly working
against the architecture.

## Stack

- Python 3.9+, Django 4.2 LTS, Django REST Framework
- `django-api-helper` for the generic CRUD view, dynamic filters, pagination, and serializers
- `django-unfold` for the admin UI, `django-import-export` for import and export
- SimpleJWT for authentication, with token blacklisting on logout
- SQLite and an in-process cache by default. PostgreSQL and Redis switch on via `.env`

## Project map

- `api/models.py`: every model. This is where the logic lives.
- `api/views.py`: thin endpoint declarations, mostly `model = X`.
- `api/serializers.py`: only hand-written serializers for auth and profile flows.
- `api/urls.py`: one `path()` per endpoint, mounted at `/api/`.
- `api/signals.py`: post_save handlers. Connected by `ApiConfig.ready()`.
- `api/fields.py`: `CustomImageField` and `CustomFileField`. Use these, never Django's.
- `api/admin.py`: the generic auto-registering admin. You should rarely edit this.
- `api/permissions.py`: custom DRF permission classes.
- `{{project_name}}/settings.py`: all configuration, env-driven through `.env`.
- `{{project_name}}/loggers.py`: import `logger` from here, never `logging.getLogger` directly.
- `{{project_name}}/logging_config.py`: handlers writing to `logs/`.

## The layer rules

These are the house rules. They are the reason the codebase stays small.

### Models are heavy

All business logic lives on the model: computed values, formatting, notifications,
state transitions, admin display helpers. A model method is reachable from the
admin, the API, a management command, the shell, and a signal without any glue.
The same logic placed in a view is reachable from exactly one HTTP route.

- Every model inherits `CommonModel` unless there is a specific reason not to.
  That gives it a UUID primary key, `extra_params` JSON, and created/updated
  timestamps and actor fields.
- Every model carries an `admin_meta` dict. That dict *is* the admin configuration.
- Put display helpers on the model and reference them from `admin_meta['list_display']`.
- Put side effects in a model method, then call it from a signal. Do not inline
  side effects into a view.

### Views are thin

A view declares which model it exposes and which HTTP verbs are allowed. Nothing else.

```python
class BlogAPIView(ReadOnlyView):
    model = Blog
```

That is a complete, filterable, paginated, ordered read endpoint. Reach for the
three local base classes in `api/views.py` first:

- `ReadOnlyView`: GET only, public. Serializer is generated from the model.
- `CreateOnlyView`: POST only, public. For forms such as contact submissions.
- `GenericCRUDView` (from `django_api_helper`): full CRUD, permission checked.

Write a custom method on a view only when the behavior is genuinely
request-shaped: reading `request.user`, returning a non-standard status, or
overriding permissions. `ProfileAPIView` is the reference example.

### The admin is not written by hand

`api/admin.py` loops over every model in the app and registers it with
`GenericAdmin`. `GenericAdmin.__init__` copies every key of the model's
`admin_meta` onto the ModelAdmin instance. So `admin_meta` keys are ordinary
ModelAdmin attributes:

```python
admin_meta = {
    'list_display'  : ['title', 'category', 'created_at'],
    'search_fields' : ['title', 'category__category'],
    'list_filter'   : ['category'],
    'list_editable' : ['category'],
    'list_per_page' : 50,
    'ordering'      : ['order_by'],
    'autocomplete_fields': ['category'],
}
```

These keys are not ModelAdmin attributes and get special handling:

- `single_entry: True` hides the Add button once one row exists. Use for singletons.
- `rtf_fields: [...]` opts fields *into* the rich text editor. See below.
- `json_fields: {'field': {'schema': {...}}}` renders a JSON editor for a JSONField.
- `inline: [{'RelatedModel': 'fk_field_name'}]` registers a related model as an inline.
- `actions: ['method_name']` binds a model method as an admin action. The method
  is called once per selected object as `obj.method_name(request)`.

**Rich text is opt-in.** A `TextField` renders as a plain textarea unless the
model lists it in `admin_meta['rtf_fields']`. This default is deliberate: the
editor rewrites its contents on save, so it corrupts raw HTML, script blocks,
URL traces, and anything else machine-read. Opt in only for authored prose.

```python
'rtf_fields': ['description'],   # description gets the editor, nothing else does
```

`rtf_exclude` is the older opt-out key, where every TextField got the editor
*except* the listed ones. It is still honoured so `admin_meta` dicts copied from
older projects keep working, but do not use it in new code. If a model declares
both, `rtf_fields` wins.

To exclude a model from the admin entirely, add its lowercase name to `exempt`
in `api/admin.py`. Models with `histor` in the name are skipped automatically.

## File and image fields

Always import the custom fields, never Django's:

```python
from .fields import CustomImageField as ImageField, CustomFileField as FileField
```

- Both rename uploads to `uuid4().ext`, so user-supplied filenames never reach disk.
- `ImageField` also compresses: resizes to `max_width=1920` and re-encodes at
  `quality=75`, preserving animation for GIF and WebP. Override per field with
  `ImageField(max_width=800, quality=60)` or disable with `do_compress=False`.
- Both fall back to the original bytes on any processing error, so an unusual
  upload degrades rather than 500s.

## The API contract

These behaviors come from `django-api-helper` and apply to every view built on
`GenericCRUDView`. Do not reimplement them.

Query parameters:

- `?pk=<uuid>` returns a single object instead of a list.
- `?depth=<n>` controls relation nesting, clamped to `SERIALIZER_MIN_DEPTH`(1) and `SERIALIZER_MAX_DEPTH`(3).
- `?nested` switches to recursive relation serialization.
- `?order_by=field,-other` orders results. Unknown fields return 400.
- `?aggregate=sum:amount` works only where the view sets `allow_aggregate = True`.
- Any model field is a filter, generated dynamically. `?search=` is available too.
- Pagination is 20 per page by default.

Headers:

- `X-Include` and `X-Exclude` project top-level response fields. Exclude wins.

Rules:

- Errors use a `code` / `detail` / optional `errors` envelope. Never return raw
  exception text, tracebacks, or request bodies to clients.
- Password-like fields are redacted by default, including through nested
  relations. Only a view-level `include_sensitive_fields = True` opts out, and
  that needs a deliberate reason.
- Permissions map to Django model permissions: GET needs `view_*`, POST `add_*`,
  PATCH `change_*`, DELETE `delete_*`. `bypass_table_permission = True` skips
  that check and is already set on the public `ReadOnlyView` and `CreateOnlyView`.
- For known relation paths set `select_related_fields` and `prefetch_related_fields`
  on the view. This is the intended fix for N+1 queries.

Note that `api/views.py` defines its own `ReadOnlyView`, which shadows the
library class of the same name. The local one generates a serializer from the
model but does not support the library's `?download=1` file response.

## Logging

```python
from {{project_name}}.loggers import logger
```

| File | Holds |
|------|-------|
| `logs/app.log` | application logs, plus anything a third-party library logs |
| `logs/access.log` | one line per HTTP request |
| `logs/error.log` | 500s, with tracebacks |
| `logs/security.log` | bad Host headers, CSRF failures, disallowed redirects |

All rotate at 10MB keeping 10 files. Use `logger.exception` inside an `except`
block so the traceback is captured. Never log credentials, tokens, request
bodies, or uploaded file contents.

### Request ids

`RequestIDMiddleware` gives every request a short id, returns it as the
`X-Request-ID` header, and stamps it on every log line written while that
request is handled — including Django's own 500 line and any third-party
library's output. So one request is recoverable from an interleaved log:

```bash
grep req=8745ac80fb2e logs/*.log        # text mode
jq 'select(.request_id=="8745ac80fb2e")' logs/*.log   # json mode
```

A caller may supply its own `X-Request-ID` to trace across services; the value
is rejected unless it matches `[A-Za-z0-9._-]{1,64}`, because it gets echoed
into log files.

The access line is written by the middleware, not by `django.server` — that
logger only exists under `runserver`, so relying on it means an empty
`access.log` in production. `django.server` is therefore pinned to WARNING,
which is why static-asset requests no longer appear in dev.

### Configuration

Set in `.env`: `LOG_LEVEL`, `LOG_FORMAT` (`text` or `json`), `LOG_TO_FILE`,
`LOG_DIR`, `SQL_DEBUG` (logs every query with timing — for chasing an N+1),
`ADMIN_EMAILS` (emailed on unhandled 500s once `DEBUG=False`).

`LOG_FORMAT=json` emits one JSON object per line, for a log shipper
(Promtail/Alloy into Loki) to parse with `| json`. The field names —
`ts, level, logger, msg, request_id, module, func, line, exc` plus
`method, path, status, duration_ms, client_ip` on access lines — are the
contract with whatever queries them, so renaming one breaks dashboards.
Anything passed as `logger.info(..., extra={...})` is included automatically.

In a container, set `LOG_TO_FILE=False` and `LOG_FORMAT=json` to log JSON to
stdout. If the log directory is not writable the file handlers are dropped and
logging falls back to the console rather than failing at import.

## Configuration

Everything is read from `.env` through `settings.py`. Never hardcode a domain, a
credential, or an environment-specific URL in Python.

- `SECRET_KEY` is generated per project at scaffold time. Startup fails if it is missing.
- `DEBUG=True` allows all CORS origins. Production reads `CORS_ALLOWED_ORIGINS`.
- `FRONTEND_URL` is the app the API serves, used to build password reset links.
- Setting `DB_NAME` switches from SQLite to PostgreSQL. Setting `REDIS_URL`
  switches the cache from in-process to Redis.

## Validation

Run these after any change:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run   # fails if a migration is missing
pytest
```

`make verify` runs all three. A model change is not finished until
`makemigrations api` has been run and the generated migration committed.

## Edit style

- Keep changes surgical. Match the surrounding code rather than reformatting it.
- This codebase aligns the `=` in model field definitions and import blocks into
  columns. Preserve that alignment when editing a block that already uses it.
- Comments explain *why*, especially for security, compatibility, or non-obvious
  performance behavior. Do not narrate what the code already says.
- Avoid em dashes in comments and documentation.
- Do not add a dependency without a concrete runtime need for it.
- Update this file when a layer rule, a public behavior, or the API contract changes.
