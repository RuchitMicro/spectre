
from pathlib                    import Path
from django.contrib             import admin
from django.contrib.auth.admin  import UserAdmin as BaseUserAdmin
from django.contrib.auth.admin  import GroupAdmin as BaseGroupAdmin
from django.forms.models        import modelform_factory
from django.utils.translation   import gettext_lazy as _
from django.db                  import models

# Imports for Dynamic app registrations
from django.apps                import apps

# Unfold 
from unfold.admin                       import ModelAdmin, TabularInline, StackedInline
from import_export.admin                import ImportExportModelAdmin
from unfold.contrib.import_export.forms import ExportForm, ImportForm
from unfold.forms                       import AdminPasswordChangeForm, UserChangeForm, UserCreationForm
from django.utils.translation           import gettext_lazy as _
from unfold.contrib.forms.widgets       import ArrayWidget, WysiwygWidget


from django.db.models       import ForeignKey
from import_export          import resources
from import_export.admin    import ImportExportModelAdmin

from .resources     import *
from .models        import *
from .widgets       import JsonEditorWidget

# Common Model
try:
    from .models import CommonModel
    COMMON_MODEL_AVAILABLE = True
except ImportError:
    COMMON_MODEL_AVAILABLE = False

# user / group
try:
    admin.site.unregister(Group)
except admin.sites.AlreadyRegistered:
    pass
except Exception:
    logger.exception("Failed to unregister Group")



# CONFIG CONSTANTS
exempt                  = ['user'] # modelname in this list will not be registered
current_file_path       = Path(__file__).resolve()
global_app_name         = current_file_path.parent.name  # Assumes this file is in the app directory

# It is used to map the models to their Resource models
resource_class_mapping = {
    # User: UserResource,
}



@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    # Forms loaded from `unfold.forms`
    form                    = UserChangeForm
    add_form                = UserCreationForm
    change_password_form    = AdminPasswordChangeForm


@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    pass


class GenericStackedAdmin(TabularInline):
    extra = 0
    tab = True
    show_change_link = True
    collapsible = True
    per_page = 20
    

    def __init__(self, parent_model, admin_site):
        super().__init__(parent_model, admin_site)
        self.filter_horizontal = self.get_many_to_many_fields()
        self.admin_meta = getattr(self.model, 'admin_meta', {})

        # Apply admin_meta attributes dynamically
        try:
            if self.admin_meta:
                for attr, value in self.admin_meta.items():
                    setattr(self, attr, value)
        except Exception as e:
            pass

    def get_many_to_many_fields(self):
        many_to_many_fields = [field.name for field in self.model._meta.many_to_many]
        return many_to_many_fields

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Handle foreign key filters defined in admin_meta
        if self.admin_meta:
            foreignkey_filters = self.admin_meta.get('foreignkey_filters', {})
            if db_field.name in foreignkey_filters:
                parent_obj = self.get_parent_instance(request)
                filter_func = foreignkey_filters[db_field.name]
                if callable(filter_func):
                    kwargs['queryset'] = filter_func(request, parent_obj)

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_parent_instance(self, request):
        """
        Get the parent instance (e.g., Villa) being edited in the admin panel.
        """
        try:
            object_id = request.resolver_match.kwargs.get('object_id')
            if object_id:
                return self.parent_model.objects.get(pk=object_id)
        except Exception:
            return None
    
    def formfield_for_dbfield(self, db_field, request, **kwargs):
        # Check if the field is a TextField and override the widget if not in exclude "rtf_exclude" 
        if isinstance(db_field, models.TextField):
            # Check admin_meta for fields to exclude TinyMCE
            exclude_fields = self.admin_meta.get('rtf_exclude', []) if self.admin_meta else []
            if db_field.name not in exclude_fields:
                kwargs["widget"] = WysiwygWidget()
            
        return super().formfield_for_dbfield(db_field, request, **kwargs)

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        form = formset.form

        if COMMON_MODEL_AVAILABLE:
            exempt_common_model_fields = [field.column for field in CommonModel._meta.fields]
            custom_order = [field for field in form.base_fields if field not in exempt_common_model_fields]
        
        form.base_fields = {field: form.base_fields[field] for field in custom_order}
        return formset


class GenericAdmin(ModelAdmin, ImportExportModelAdmin):
    import_form_class = ImportForm
    export_form_class = ExportForm
    
    def __init__(self, model, admin_site):
        self.model = model
        self.inlines = []
        self.actions = []
        self.admin_meta = getattr(model, 'admin_meta', {})

        # Dynamic admin meta from model
        # Specify a static dictionary in model
        try:
            # Admin Meta
            if model.admin_meta:
                for k,v in model.admin_meta.items():
                    self.__setattr__(k,v)
        except:
            pass
        
        # Dynamic Actions from model
        # Specify a key 'actions' in the admin_meta dictionary in model
        try:
            if 'actions' in model.admin_meta:
                for action_name in model.admin_meta['actions']:
                    # Ensure action_name is a string
                    if isinstance(action_name, str):
                        action_function = getattr(model, action_name, None)
                        if callable(action_function):
                            self.add_action(action_name)
        except Exception as e:
            # Handle or log the exception
            pass
        
        # Register Inlines
        self.register_inlines()  

        super().__init__(model, admin_site)
        
    def get_resource_class(self):
        # Use the custom resource class if specified
        resource_class = resource_class_mapping.get(self.model, None)
        if resource_class:
            return resource_class
        # Fallback for models without a specific resource class
        return type(
            f'{self.model.__name__}Resource',
            (resources.ModelResource,),
            {
                'Meta': type('Meta', (), {'model': self.model})
            }
        )

    def has_add_permission(self, request):
        """
        Hide 'Add' button if 'single_entry' is True and an instance already exists.
        """
        if getattr(self.model, 'admin_meta', {}).get('single_entry') and self.model.objects.exists():
            return False
        return super().has_add_permission(request)

    # Function to get the fieldsets
    def get_fieldsets(self, request, obj=None):
        if 'fieldsets' in self.admin_meta:
            return self.admin_meta['fieldsets']

        common_fields = []
        try:
            if issubclass(self.model, CommonModel):
                common_fields = [field.name for field in CommonModel._meta.fields if field.editable]
        except:
            common_fields = []

        other_fields    = [field.name for field in self.model._meta.fields if field.name not in common_fields and field.editable and field.name != 'id']
        m2m_fields      = [field.name for field in self.model._meta.many_to_many]
        other_fields    += m2m_fields

        fieldsets = [
            (self.model._meta.verbose_name.title(), {
                "classes": ["tab"],
                'fields': other_fields,
            })
        ]

        if common_fields:
            fieldsets.append(
                (_("Meta Data"), {
                    "classes": ["tab"],
                    'fields': common_fields,
                })
            )

        return fieldsets
    
    def formfield_for_dbfield(self, db_field, request, **kwargs):
        # Check if the field is a JSONField
        if isinstance(db_field, models.JSONField) and self.admin_meta:
            # Retrieve the schema configuration for JSON fields
            json_fields_meta = self.model.admin_meta.get('json_fields', {})
            # Retrieve the schema for the specific field, if defined
            json_schema = json_fields_meta.get(db_field.name, {}).get('schema')
            if json_schema:
                # Initialize the custom widget with the specified schema
                kwargs['widget'] = JsonEditorWidget(schema=json_schema)
            
        # Check if the field is a TextField and override the widget if not in exclude "rtf_exclude" 
        if isinstance(db_field, models.TextField):
            # Check admin_meta for fields to exclude WysiwygWidget
            exclude_fields = self.admin_meta.get('rtf_exclude', []) if self.admin_meta else []
            if db_field.name not in exclude_fields:
                kwargs["widget"] = WysiwygWidget()    
            
        
        return super().formfield_for_dbfield(db_field, request, **kwargs)
    
    def get_readonly_fields(self, request, obj=None):
        # Get a list of non-editable fields
        readonly_fields = [field.name for field in self.model._meta.fields if (not field.editable or field.name == 'id')]
        readonly_fields += self.admin_meta.get('readonly_fields', [])
        return readonly_fields
    
    # Function to add actions to the admin class
    def add_action(self, action_name):
        """
        Bind a model method as a Django admin action.

        The model method must accept:
            (modeladmin, request, queryset)
        """
        action_function = getattr(self.model, action_name, None)
        if not callable(action_function):
            return

        def wrapper_action(modeladmin, request, queryset, _action=action_function):
            return _action(modeladmin, request, queryset)

        wrapper_action.__name__ = f"admin_action_{action_name}"
        wrapper_action.short_description = getattr(
            action_function,
            "short_description",
            action_name.replace("_", " ").title(),
        )

        if wrapper_action not in self.actions:
            self.actions.append(wrapper_action)

        setattr(self, wrapper_action.__name__, wrapper_action)
    
    def register_inlines(self):
        if hasattr(self.model, 'admin_meta') and 'inline' in self.model.admin_meta:
            for inline_info in self.model.admin_meta['inline']:
                for related_model, fk_name in inline_info.items():
                    self.add_inline(related_model, fk_name)

    def add_inline(self, related_model_name, fk_name):
        related_model = apps.get_model(app_label=global_app_name, model_name=related_model_name)  # Replace 'your_app_name'
        inline_class_name = f"{related_model.__name__}Inline"
        
        # Retrieve the admin_meta from the related model (Inline model) and get its admin_meta
        # store inline attribute in "inline_admin_meta"
        inline_admin_meta = getattr(related_model, 'admin_meta', {})

        class_attrs = {
            'model': related_model,
            'fk_name': fk_name,
            'form': modelform_factory(related_model, exclude=[]),
            'admin_meta': inline_admin_meta,  # Pass admin_meta to inline
        }

        InlineAdminClass = type(inline_class_name, (GenericStackedAdmin,), class_attrs)
        self.inlines.append(InlineAdminClass)

    # Custom Media so that we can add custom js files
    class Media:
        js = ('https://code.jquery.com/jquery-3.7.0.js', )

# Register all models in the app
app = apps.get_app_config(global_app_name)
for model_name, model in app.models.items():
    if model_name not in exempt and 'histor' not in model_name.lower():
        resource_class = resource_class_mapping.get(model, None)
        if resource_class:
            # Create a custom admin class with the resource_class
            admin_class = type(
                f'{model.__name__}Admin',
                (GenericAdmin,),
                {
                    'resource_class': resource_class,
                }
            )
        else:
            admin_class = GenericAdmin

        admin.site.register(model, admin_class)
    

