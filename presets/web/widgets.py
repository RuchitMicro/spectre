from django.forms import widgets
from django.utils.safestring import mark_safe
import json

# Json Editor Widget
# https://github.com/json-editor/json-editor
class JsonEditorWidget(widgets.Widget):
    template_name = 'json_editor_widget.html'

    def __init__(self, schema, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.schema = schema

    def render(self, name, value, attrs=None, renderer=None):
        # Convert Python dictionary to JSON string
        json_value = value if value else '{}'
        # Render the JSON Editor
        style = '''
        .form-row {
            overflow: visible !important;
        }
        .je-switcher{
            margin-left: 0px !important;
        }
        .je-ready button{
            padding: 5px 10px !important;
            border: 1px solid grey !important;
        }
        .je-ready button i{
            margin-right: 5px !important;
            margin-left: 5px !important;
        }
        .je-indented-panel{
            border-radius: 0px !important;
            padding: 20px 15px !important;
        }
        '''
        return mark_safe(f'''

            <!-- FontAwesome CSS -->
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">

            <!-- JSON Editor CSS -->
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@json-editor/json-editor@latest/dist/jsoneditor.min.css">

            <!-- JSON Editor JS -->
            <script src="https://cdn.jsdelivr.net/npm/@json-editor/json-editor@latest/dist/jsoneditor.min.js"></script>

            <style>{style}</style>
            <script src="https://cdn.jsdelivr.net/npm/@json-editor/json-editor@latest/dist/jsoneditor.min.js"></script>
            <textarea name="{name}" id="tx_{attrs['id']}" style="display:none;">{json_value}</textarea>
            <div id="editor_{attrs['id']}"></div>
            <script>
                document.addEventListener("DOMContentLoaded", function() {{
                    var editor = new JSONEditor(document.getElementById("editor_{attrs['id']}"), {{
                        schema: {self.schema},
                        startval: {json_value},
                        theme: 'html',
                        iconlib: 'fontawesome5',
                    }});
                    editor.on('change', function() {{
                        console.log("Change event triggered");
                        console.log("Editor Value:", editor.getValue());
                        document.getElementById("tx_{attrs['id']}").value = JSON.stringify(editor.getValue());
                    }});
                }});
            </script>
        ''')
