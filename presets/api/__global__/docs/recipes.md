# Recipes

Step-by-step for the tasks that come up most. Read `AGENTS.md` first.

## Add a model

1. Define it in `api/models.py`, inheriting `CommonModel`:

```python
class Product(CommonModel):
    name        =   models.CharField    (max_length=300)
    slug        =   models.SlugField    (unique=True)
    price       =   models.DecimalField (max_digits=10, decimal_places=2)
    image       =   ImageField          (upload_to='product/', blank=True, null=True)
    description =   models.TextField    (blank=True, null=True)
    spec_sheet  =   models.TextField    (blank=True, null=True, help_text='Raw HTML')
    order_by    =   models.IntegerField (default=0)

    admin_meta = {
        'list_display'  : ['name', 'price', 'order_by', 'created_at'],
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

Points to get right:

- `ImageField` and `FileField` come from `api/fields.py`, not from `models`.
- Decide `rtf_fields` for every `TextField`. `description` is prose, so it opts
  into the editor. `spec_sheet` holds raw HTML, so it is left out and stays a
  plain textarea. Rich text is opt-in: anything not listed stays plain.
- `__str__` must return a string. It is used in the admin and in logs.

2. Generate and apply the migration:

```bash
python manage.py makemigrations api
python manage.py migrate
```

3. That is the whole admin. The model is registered automatically with the
   `admin_meta` configuration applied. There is nothing to add to `api/admin.py`.

4. If it needs an API endpoint, follow the next recipe.

## Add an API endpoint

1. Add the view to `api/views.py` under the right section banner:

```python
class ProductAPIView(ReadOnlyView):
    model = Product
```

Pick the base class by what the endpoint is for:

| Need | Base class | Notes |
| --- | --- | --- |
| Public read | `ReadOnlyView` | GET only, serializer generated from the model |
| Public write, no read | `CreateOnlyView` | POST only, for form submissions |
| Authenticated CRUD | `GenericCRUDView` | Set `permission_classes` explicitly |

2. Add the route to `api/urls.py`:

```python
path('product/', ProductAPIView.as_view(), name='product'),
```

3. If the model has foreign keys the endpoint will return, avoid the N+1:

```python
class ProductAPIView(ReadOnlyView):
    model                 = Product
    select_related_fields = ('category',)
```

Use `prefetch_related_fields` for reverse and many-to-many relations.

4. The endpoint now supports filtering on every field, `?search=`, `?order_by=`,
   `?pk=`, `?depth=`, `?nested`, pagination, and the `X-Include` / `X-Exclude`
   headers. Do not add any of that yourself.

## Add an authenticated endpoint

```python
class OrderAPIView(GenericCRUDView):
    model              = Order
    permission_classes = [IsAuthenticated]
    serializer_class   = create_model_serializer(Order)
```

Without `bypass_table_permission = True`, this enforces Django model permissions:
GET needs `view_order`, POST needs `add_order`, PATCH `change_order`, DELETE
`delete_order`. Grant them through admin groups.

To scope results to the requesting user, override `get_queryset`:

```python
    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)
```

## Add a side effect

Put the behavior on the model, then trigger it from a signal.

```python
# api/models.py
class Order(CommonModel):
    ...
    def send_confirmation(self):
        ...
```

```python
# api/signals.py
@receiver(post_save, sender=Order)
def confirm_new_order(sender, instance, created, **kwargs):
    if not created:
        return
    try:
        instance.send_confirmation()
    except Exception:
        logger.exception("Failed to send order confirmation for id=%s", instance.pk)
```

The handler decides when, the model method decides what. Wrap the call so a
failing side effect cannot turn a successful write into a 500.

## Add an admin action

Define an ordinary instance method taking `request`, then name it in `admin_meta`:

```python
class Order(CommonModel):
    admin_meta = {
        'list_display' : ['id', 'status'],
        'actions'      : ['mark_as_shipped'],
    }

    def mark_as_shipped(self, request):
        self.status = 'shipped'
        self.save(update_fields=['status'])
    mark_as_shipped.short_description = "Mark selected orders as shipped"
```

The admin calls the method **once per selected object**, as
`obj.mark_as_shipped(request)`. It is not a bulk queryset action, so do the work
for a single instance and let the admin loop. That also keeps the method useful
outside the admin, which is the point of putting logic on the model.

## Add an inline

Declare it on the parent model, mapping the related model name to the foreign key
field on that related model:

```python
class Order(CommonModel):
    admin_meta = {
        'inline': [{'OrderItem': 'order'}],
    }
```

`OrderItem` must live in the same app. Its own `admin_meta` is applied to the
inline, so `list_display` and `rtf_fields` carry over.

## Add a singleton settings model

```python
    admin_meta = {
        'single_entry': True,
        'fieldsets'   : [...],
    }
```

`single_entry` hides the Add button once a row exists. Give the model a `load()`
classmethod like `SiteSetting.load()` so callers have one lookup path, and always
handle the None case since a fresh database has no row yet.

## Add a new setting

1. Read it in `{{project_name}}/settings.py` with a safe default:

```python
PAYMENT_API_KEY = os.getenv("PAYMENT_API_KEY", "")
```

2. Add it to `.env.example` with an empty value and a comment.
3. Add the real value to your local `.env`, which is gitignored.

Use `env_list()` for comma-separated values and `env_bool()` for flags. Both are
defined at the top of `settings.py`.

## Run the checks

```bash
make verify
```

Equivalent to:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
pytest
```

The middle command is the one that catches the most common mistake in this
codebase: editing a model and forgetting the migration. It exits non-zero when a
migration is missing.
