# Architecture

How `{{project_name}}` is put together, and why. Read `AGENTS.md` first for the
rules; this file explains the machinery behind them.

## The core idea

A typical Django project describes the same model three times: once in
`models.py`, once in a `ModelAdmin`, and once in a `ModelSerializer`. Those three
descriptions drift, and the drift is where bugs live.

This project describes each model once. The admin is generated from the model at
import time, and the API serializer is generated from the model at request time.
The model is the only place a field is declared, so there is no drift to manage.

The cost of that choice is indirection: there is no `BlogAdmin` class to open
when the blog admin looks wrong. The answer is always in `Blog.admin_meta`. Once
you know that, the indirection stops being surprising.

## CommonModel

Every model inherits `CommonModel`, an abstract base in `api/models.py`:

- `id` is a UUID primary key, not a sequential integer. IDs appear in URLs and
  API responses, and sequential IDs leak how many records exist and let anyone
  enumerate them. UUIDs cost a little index size and remove that whole class of
  problem.
- `extra_params` is a JSON field for data that does not deserve a column yet.
  Use `get_extra_param`, `set_extra_param`, and `update_extra_params` rather than
  touching the dict directly, since they handle the None case. When a key in
  `extra_params` becomes load-bearing, promote it to a real column.
- `created_at` and `updated_at` are maintained automatically.
- `created_by` and `updated_by` are plain CharFields, not foreign keys, so the
  audit trail survives the deletion of the user who wrote the row.
- `to_dict()`, `to_json()`, and `get_json()` give a plain representation without
  going through DRF. Useful in management commands, shell sessions, and logs.

`admin_meta = {}` is declared on `CommonModel` so `getattr(model, 'admin_meta')`
is always safe.

## How the admin registers itself

The bottom of `api/admin.py` does this:

```python
app = apps.get_app_config(global_app_name)
for model_name, model in app.models.items():
    if model_name not in exempt and 'histor' not in model_name.lower():
        admin.site.register(model, admin_class)
```

Consequences worth knowing:

- **A new model appears in the admin the moment it is defined.** You do not
  register it, and you cannot forget to.
- `global_app_name` is derived from the directory name of `admin.py`, so the file
  works unchanged in any app.
- To keep a model out of the admin, add its lowercase name to the `exempt` list.
- `django-simple-history` shadow models are skipped by the `histor` check.
- `resource_class_mapping` maps a model to a custom import-export Resource. Models
  without an entry get a generated `ModelResource`, so import and export work
  everywhere by default.

`GenericAdmin.__init__` then copies `admin_meta` onto the instance:

```python
for k, v in model.admin_meta.items():
    self.__setattr__(k, v)
```

This is why `admin_meta` keys are just ModelAdmin attribute names. Anything
Django's ModelAdmin understands works, with no wrapper needed.

## Widget substitution

`GenericAdmin.formfield_for_dbfield` rewrites two field types:

- A `TextField` becomes an Unfold `WysiwygWidget` only when the field name is
  listed in `admin_meta['rtf_fields']`. Everything else stays a plain textarea.

  Rich text is opt-in because the editor rewrites its contents on save. A
  TextField holding an HTML `<head>` block, a URL trace, or a CSV blob would be
  silently corrupted the first time someone opened and saved the record. Opting
  in per field means that damage can only happen where it was asked for.

  The resolution order lives in `wants_wysiwyg()` at the top of `admin.py`:

  1. `rtf_fields` declared, so only those fields get the editor.
  2. `rtf_exclude` declared, the legacy opt-out, so every TextField except those.
  3. Neither declared, so plain textareas.

  Rule 2 exists purely for backward compatibility with `admin_meta` dicts written
  before the polarity was reversed. New models should use `rtf_fields`.
  `Blog` is the reference: `featured_text` and `text` are authored prose and get
  the editor, while `head` and `tags` do not.
- A `JSONField` gets a schema-driven JSON editor when `admin_meta['json_fields']`
  declares a schema for it. Without a schema it stays a raw textarea.

## Automatic fieldsets

When `admin_meta` has no `fieldsets` key, `get_fieldsets` builds two tabs: the
model's own editable fields, then a "Meta Data" tab holding the `CommonModel`
bookkeeping fields. That keeps `created_at` and `extra_params` out of the way
without hiding them.

Declaring `fieldsets` yourself replaces this entirely, including the Meta Data
tab, so list every field you still want visible. `SiteSetting` is the reference
example of hand-written tabbed fieldsets.

## The API layer

`django-api-helper` supplies `GenericCRUDView`. On instantiation it:

1. Requires a `model` attribute and raises `TypeError` without one.
2. Builds a filterset from the model with `DynamicFilterSetCreator`, cached per
   model, so every field is filterable with no configuration.

Serializers come from `create_model_serializer(self.model)`, which reads the
model's fields. So, as with the admin, adding a field to a model adds it to the
API automatically.

Two thin base classes in `api/views.py` narrow this down:

- `ReadOnlyView` allows only GET, HEAD, and OPTIONS and returns 405 for the rest.
- `CreateOnlyView` allows only POST.

Both set `permission_classes = [AllowAny]` and `bypass_table_permission = True`,
because they are the public surface. Anything behind authentication should use
`GenericCRUDView` directly with explicit `permission_classes`, which restores the
Django model permission mapping described in `AGENTS.md`.

### `api_meta`

A model may declare `api_meta = {"api_function": ['method_name']}` to expose extra
computed values in API output. `Profile.api_user_data` is the example, flattening
the related user's name and email into the profile response.

## Signals

`ApiConfig.ready()` imports `api.signals`, which is where post_save handlers live.
Two are wired by default:

- Creating a non-superuser `User` creates its `Profile`.
- Creating a `Contact` sends the admin notification and the acknowledgement email.

Handlers stay thin and delegate to model methods. The handler decides *when*, the
model method decides *what*. Both handlers swallow and log exceptions, so a broken
SMTP configuration cannot turn a successful POST into a 500.

## Media handling

`api/fields.py` replaces Django's file fields:

- Uploads are renamed to `uuid4().ext` before hitting storage. User-supplied
  filenames never reach disk, which removes path traversal and collision issues
  and stops the original filename leaking through the media URL.
- Images are resized to `max_width` and re-encoded at `quality`, with animation
  preserved for GIF and WebP. SVG is passed through untouched rather than
  rasterized.
- Every failure path falls back to the original bytes, so an odd upload degrades
  to "stored uncompressed" rather than erroring.

`django-cleanup` is installed, so deleting a row deletes its uploaded files.

## Logging

`logging_config.py` runs `dictConfig` at import and creates `logs/`. Three
rotating handlers split the streams: `app.log` for the project logger,
`error.log` for `django.request` at ERROR and above, and `access.log` for
`django.server`. Console output picks up colors when `colorlog` is installed.

Import the configured logger rather than calling `logging.getLogger` ad hoc:

```python
from {{project_name}}.loggers import logger
```
