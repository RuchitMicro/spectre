# Conventions

House style for `{{project_name}}`, and the reasoning behind it.

## Why models are heavy

The rule is: **logic belongs on the model unless it needs the request.**

A model method is callable from the admin, an API view, a management command, a
signal handler, a Celery task, and the shell. The same logic written inside a
view is callable from one HTTP route. Every time behavior gets written into a
view, it has to be duplicated the first time someone needs it from the admin or a
script, and the two copies then drift.

Concretely, this is why `Contact.send_mail_notification()` is a model method and
not view code. It can be triggered by the signal on creation, re-triggered from
an admin action, and called from a shell session while debugging, without any of
those three knowing anything about the others.

The test for where code belongs:

- Does it need `request.user`, headers, or the HTTP status? It goes in the view.
- Does it describe what this record *is* or *does*? It goes on the model.

Presentation helpers count as model logic here, because the auto-generated admin
reads them from the model. `BannerImage.image_display()` returns the thumbnail
markup and `admin_meta['list_display']` names it. There is no admin class to put
it in.

## Why views are thin

Views in this project mostly declare a model and a permission posture:

```python
class BlogAPIView(ReadOnlyView):
    model = Blog
```

Filtering, ordering, pagination, depth control, field projection, and error
handling all come from `GenericCRUDView`. Reimplementing any of them inside a
view means losing the consistency the rest of the API has, and means the next
person has to read that view to know how it behaves.

Override a method only for genuinely request-shaped behavior. `ProfileAPIView` is
the reference: it overrides `get_object` because the object is determined by
`request.user`, and blocks POST and DELETE because a profile is created by a
signal and never deleted directly.

## Why the admin is generated

See `docs/architecture.md`. The short version: a hand-written ModelAdmin is a
second description of the model that drifts from the first. `admin_meta` keeps
the description next to the fields it describes.

Write a real ModelAdmin only when the requirement cannot be expressed as
ModelAdmin attributes, for example a custom changelist view or a bespoke form
class. That is rare, and it is worth a comment explaining why.

## Formatting

The codebase aligns assignment operators into columns in two places:

Model fields:

```python
class Testimonial(CommonModel):
    name            =   models.CharField    (max_length=300, null=True)
    designation     =   models.CharField    (max_length=300, null=True)
    image           =   ImageField          (blank=True, null=True, upload_to='testimonial/')
```

Import blocks:

```python
from django.db                  import models
from django.core.exceptions     import ValidationError
from django.utils.safestring    import mark_safe
```

This makes field types and modules scannable in a column. When editing a block
that is already aligned, keep it aligned. Do not reformat blocks that are not,
and do not reflow a file you are only making a small change to.

Imports are grouped with a short comment marking each group, for example
`# Timezone`, `# Signals`, `# DRF`. Follow the existing grouping in the file.

## Naming

- Models are singular: `Blog`, `Testimonial`, `FAQCategory`.
- Views are `<Model>APIView`.
- URL paths are lowercase and hyphenated: `blog-category/`, `password-reset-confirm/`.
- URL names match the path: `name='blog-category'`.
- Ordering fields are called `order_by` and paired with `Meta.ordering`.

## Comments

Comment the *why*, not the *what*. Security decisions, compatibility constraints,
and non-obvious performance behavior are worth a line. Restating the code is not.

Avoid em dashes in comments and documentation.

Section banners are used to group related endpoints in `views.py`:

```python
# ---------------------------------------------------------------------------
# Content
# ---------------------------------------------------------------------------
```

Keep them when adding to an existing group, and add a new one when introducing a
genuinely new area.

## Things not to do

- Do not use `models.ImageField` or `models.FileField`. Use the custom fields from
  `api/fields.py`, which randomize filenames and compress images.
- Do not add a `TextField` without deciding whether it belongs in `rtf_fields`.
  The default is a plain textarea. Opt in only for authored prose, never for
  markup, code, or machine-read data.
- Do not hardcode domains, credentials, or environment URLs. They belong in `.env`.
- Do not call `logging.getLogger` directly. Import `logger` from the project package.
- Do not catch a bare exception and pass silently. Log it with `logger.exception`.
- Do not commit a models.py change without its migration.
- Do not add a dependency without a concrete runtime need.
