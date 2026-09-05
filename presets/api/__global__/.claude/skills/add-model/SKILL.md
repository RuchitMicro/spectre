---
name: add-model
description: Add a Django model to the api app end to end, including CommonModel inheritance, the admin_meta block, the custom file fields, and the migration. Use whenever a new model, table, or entity is being added to this project.
---

# Add a model

In this project the admin is generated from the model, so adding a model is a
change to `api/models.py` plus a migration. There is no admin class to write.

## Steps

1. **Read `api/models.py` first.** Match the alignment style of the surrounding
   field definitions and place the new model near related ones.

2. **Define the model inheriting `CommonModel`**, which supplies the UUID primary
   key, `extra_params`, and the created/updated fields.

```python
class Product(CommonModel):
    name        =   models.CharField    (max_length=300)
    slug        =   models.SlugField    (unique=True)
    image       =   ImageField          (upload_to='product/', blank=True, null=True)
    description =   models.TextField    (blank=True, null=True)
    order_by    =   models.IntegerField (default=0)

    admin_meta = {
        'list_display'  : ['name', 'order_by', 'created_at'],
        'search_fields' : ['name', 'slug'],
        'list_editable' : ['order_by'],
        'ordering'      : ['order_by'],
        'rtf_fields'    : ['description'],
    }

    def __str__(self):
        return str(self.name)

    class Meta:
        ordering = ['order_by']
```

3. **Use the custom file fields.** `ImageField` and `FileField` are imported at
   the top of `models.py` from `api/fields.py`. Never use `models.ImageField` or
   `models.FileField`: the custom ones randomize the stored filename and compress
   images.

4. **Decide `rtf_fields` for every TextField.** Rich text is opt-in: a
   `TextField` is a plain textarea unless listed in `admin_meta['rtf_fields']`.
   Opt in for authored prose. Never opt in a field holding raw HTML, code, a URL
   trace, or machine-read data, because the editor rewrites its contents on save.

   `rtf_exclude` is the older opt-out key. It still works so older `admin_meta`
   dicts keep behaving, but do not use it in new models.

5. **Fill in `admin_meta`.** Keys are ordinary ModelAdmin attributes
   (`list_display`, `search_fields`, `list_filter`, `list_editable`,
   `list_per_page`, `ordering`, `readonly_fields`, `autocomplete_fields`,
   `fieldsets`) plus the special keys: `single_entry`, `rtf_fields`,
   `json_fields`, `inline`, and `actions`. See `docs/architecture.md`.

   A model with no `admin_meta` still registers, it just gets Django defaults.
   Always give at least `list_display` and `__str__`.

6. **Put logic on the model, not in a view.** Display helpers, computed values,
   notifications, and state changes are model methods. See `docs/conventions.md`.

7. **Generate the migration.** This is part of the change, not a follow-up:

```bash
python manage.py makemigrations api
python manage.py migrate
```

8. **Verify:**

```bash
make verify
```

## Do not

- Do not add anything to `api/admin.py`. Registration is automatic.
- Do not write a ModelSerializer. It is generated from the model at request time.
- Do not use `models.ImageField` or `models.FileField`.
- Do not stop before running `makemigrations`.

## If the model also needs an endpoint

Use the `add-endpoint` skill afterwards. Adding a model does not expose it over
the API.
