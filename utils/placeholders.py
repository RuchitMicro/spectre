
from pathlib        import Path
from rich.console   import Console

console = Console()


class PlaceholderReplacer:
    def replace_project_placeholders(self, project_root: Path, project_name: str, token: str = "{{project_name}}") -> None:
        exts = {".py", ".txt", ".md", ".ini", ".cfg", ".json", ".yml", ".yaml"}
        patched = 0
        for p in project_root.rglob("*"):
            if not p.is_file():
                continue
            if any(part in (".venv", "venv", ".git", "__pycache__") for part in p.parts):
                continue
            if p.suffix.lower() in exts:
                try:
                    text = p.read_text(encoding="utf-8")
                except Exception:
                    continue
                if token in text:
                    new_text = text.replace(token, project_name)
                    p.write_text(new_text, encoding="utf-8")
                    patched += 1
        if patched:
            console.print(f"[green]Replaced {token} with '{project_name}' in {patched} files.[/green]")
        else:
            console.print(f"[dim]No {token} placeholders found to replace.[/dim]")
