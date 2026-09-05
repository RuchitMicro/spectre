---
description: Generate and apply migrations for the api app, then confirm none are outstanding
---

Generate and apply migrations for this project:

1. Run `python manage.py makemigrations api` and show what it created. Always pass
   the `api` app label so unrelated third-party apps are not swept in.
2. Read the generated migration file. Flag anything destructive before applying:
   a `RemoveField`, a `DeleteModel`, or an `AlterField` that narrows a column type
   or adds a non-nullable field without a default. Ask before continuing if you
   see one.
3. Run `python manage.py migrate`.
4. Confirm with `python manage.py makemigrations --check --dry-run`, which must
   exit clean.

Report what changed. If nothing needed migrating, say that rather than inventing
a summary.
