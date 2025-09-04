
import re
from typing         import Iterable, Tuple, Dict, Type, Set, Union
from django.apps    import apps
from django.urls    import path

ModelT = type

def camel_to_kebab(name: str) -> str:
    # Handle acronyms and normal CamelCase
    s1 = re.sub(r'(.)([A-Z][a-z]+)', r'\1-\2', name)
    return re.sub(r'([a-z0-9])([A-Z])', r'\1-\2', s1).lower()

def _name_set(exclude: Iterable[Union[str, ModelT]]) -> Set[str]:
    out: Set[str] = set()
    for item in exclude or ():
        out.add(item if isinstance(item, str) else item.__name__)
    return out

def generate_api(
    *,
    app_label: str,
    base_view,                        # e.g. your ReadOnlyView
    serializer_factory,               # e.g. create_model_serializer
    permission_classes: Iterable = (),
    exclude: Iterable[Union[str, ModelT]] = (),
    url_name_suffix: str = "",        # optional, appended to the url "name"
) -> Tuple[Dict[str, Type], list]:
    """
    Returns (generated_views_dict, urlpatterns_list).
    - generated_views_dict maps view class names -> classes (e.g., {"BlogAPIView": <class ...>})
    - urlpatterns_list is a list of django.urls.path entries

    Only models from `app_label` are considered. Models listed in `exclude`
    (by class or by class name) are skipped.
    """
    exclude_names = _name_set(exclude)
    generated_views: Dict[str, Type] = {}
    urlpatterns = []

    for model in apps.get_app_config(app_label).get_models():
        model_name = model.__name__
        if model_name in exclude_names:
            continue

        view_name = f"{model_name}APIView"
        kebab = camel_to_kebab(model_name)

        # Build the serializer for this model via your factory
        serializer_cls = serializer_factory(model)

        # Dynamically make a ReadOnly view for the model
        attrs = {
            "model": model,
            "serializer_class": serializer_cls,
            "permission_classes": list(permission_classes) or [],
            "__module__": __name__,  # helps Django introspection / pickling
        }
        view_cls = type(view_name, (base_view,), attrs)
        generated_views[view_name] = view_cls

        url_name = kebab + (f"-{url_name_suffix}" if url_name_suffix else "")
        urlpatterns.append(
            path(f"{kebab}/", view_cls.as_view(), name=url_name)
        )

    return generated_views, urlpatterns
