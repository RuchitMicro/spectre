
import re
from pathlib import Path
from .errors import handle_error


class SettingsEditor:
    def add_app_to_installed_apps(self, settings_path: Path, app_name: str) -> None:
        text = settings_path.read_text(encoding="utf-8")

        # Find the INSTALLED_APPS list (single block with [...])
        block_re = re.compile(
            r"(^\s*INSTALLED_APPS\s*=\s*\[\s*)(.*?)(\s*\])",
            re.DOTALL | re.MULTILINE
        )
        m = block_re.search(text)
        if not m:
            if app_name == 'saas':
                return
            handle_error(f"INSTALLED_APPS not found in {settings_path}")

        prefix, body, suffix = m.groups()

        # Check for exact presence: 'web' or "web"
        token_re = re.compile(rf"['\"]{re.escape(app_name)}['\"]")
        if token_re.search(body):
            return  # already present exactly

        # Insert a new line with proper indentation
        indent_match = re.search(r"^\s*", m.group(0))
        base_indent = indent_match.group(0) if indent_match else ""
        line_indent = base_indent + "    "

        # if body isn’t empty and not ending with a comma, keep commas clean
        needs_leading_newline = "\n" not in body[-2:] if body.strip() else True
        insertion = ("" if not body.strip() else "\n") + f"{line_indent}'{app_name}',"

        new_body = (body + insertion) if body.strip() else (f"{line_indent}'{app_name}',\n")
        new_text = text[:m.start()] + prefix + new_body + suffix + text[m.end():]

        settings_path.write_text(new_text, encoding="utf-8")
            