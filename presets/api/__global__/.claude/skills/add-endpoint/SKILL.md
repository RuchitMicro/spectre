---
name: add-endpoint
description: Expose a model through the REST API using the right base view class, with correct permissions, relation prefetching, and a URL route. Use whenever an API endpoint, route, or view is being added to this project.
---

# Add an endpoint

Views in this project are thin. Filtering, ordering, pagination, depth control,
field projection, and error handling all come from `GenericCRUDView`. A view
declares which model it exposes and who may call it.

## Steps

1. **Pick the base class.**

| Need | Base class | Behavior |
| --- | --- | --- |
| Public read | `ReadOnlyView` | GET/HEAD/OPTIONS, 405 for the rest, serializer generated from the model |
| Public write only | `CreateOnlyView` | POST only, for contact and enquiry style forms |
| Authenticated CRUD | `GenericCRUDView` | Full CRUD, enforces Django model permissions |

   `ReadOnlyView` and `CreateOnlyView` are defined locally in `api/views.py` and
   already set `AllowAny` and `bypass_table_permission = True`. Note the local
   `ReadOnlyView` shadows the same-named class from `django_api_helper` and does
   not support the library's `?download=1` response.

2. **Add the view** to `api/views.py` under the matching section banner:

```python
class ProductAPIView(ReadOnlyView):
    model = Product
```

   For an authenticated endpoint, be explicit:

```python
class OrderAPIView(GenericCRUDView):
    model              = Order
    permission_classes = [IsAuthenticated]
    serializer_class   = create_model_serializer(Order)
```

   Without `bypass_table_permission = True` this maps to Django model
   permissions: GET needs `view_order`, POST `add_order`, PATCH `change_order`,
   DELETE `delete_order`.

3. **Prevent N+1 queries** whenever the response includes relations:

```python
class ProductAPIView(ReadOnlyView):
    model                   = Product
    select_related_fields   = ('category',)
    prefetch_related_fields = ('tags',)
```

   `select_related_fields` for forward foreign keys, `prefetch_related_fields`
   for reverse and many-to-many.

4. **Scope to the user** where the data is per-user, by overriding `get_queryset`:

```python
    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)
```

5. **Add the route** in `api/urls.py`, keeping it in the right group. The path is
   lowercase and hyphenated and the name matches it:

```python
path('product/', ProductAPIView.as_view(), name='product'),
```

6. **Verify:**

```bash
make verify
python manage.py runserver    # then check the route responds
```

## What you get for free

Do not reimplement any of this:

- `?pk=<uuid>` for a single object
- `?depth=<n>` and `?nested` for relation nesting
- `?order_by=field,-other`, rejected with 400 for unknown fields
- A filter on every model field, plus `?search=`
- Pagination, 20 per page
- `X-Include` and `X-Exclude` headers to project response fields
- The `code` / `detail` / `errors` failure envelope
- Redaction of password-like fields, including through nested relations

## Do not

- Do not write a custom ModelSerializer unless the shape genuinely differs from
  the model. `create_model_serializer(Model)` generates one.
- Do not return raw exception text, tracebacks, or request bodies to clients.
- Do not set `include_sensitive_fields = True` without a stated reason.
- Do not add pagination, filtering, or ordering by hand.
