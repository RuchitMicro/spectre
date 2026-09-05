
from pathlib        import Path
from typing         import Mapping
from rich.console   import Console

console = Console()


# Files that carry placeholders but have no (or an unusual) suffix.
PLACEHOLDER_FILENAMES = {
    "Dockerfile",
    "Makefile",
    ".env",
    ".env.example",
    ".dockerignore",
    "docker-compose.yml",
    "nginx.conf",
}

PLACEHOLDER_SUFFIXES = {
    ".py", ".txt", ".md", ".ini", ".cfg", ".json", ".yml", ".yaml",
    ".conf", ".env", ".sh", ".html", ".toml", ".service",
}

SKIP_PARTS = {".venv", "venv", ".git", "__pycache__", "node_modules", "static", "media"}


class PlaceholderReplacer:
    def replace(self, project_root: Path, tokens: Mapping[str, str]) -> int:
        """Replace every token in `tokens` across the generated project.

        Returns the number of files patched. Binary and unreadable files are skipped.
        """
        tokens = {k: v for k, v in tokens.items() if v is not None}
        if not tokens:
            return 0

        patched = 0
        for p in project_root.rglob("*"):
            if not p.is_file():
                continue
            if any(part in SKIP_PARTS for part in p.parts):
                continue
            if p.suffix.lower() not in PLACEHOLDER_SUFFIXES and p.name not in PLACEHOLDER_FILENAMES:
                continue

            try:
                text = p.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue

            new_text = text
            for token, value in tokens.items():
                if token in new_text:
                    new_text = new_text.replace(token, value)

            if new_text != text:
                p.write_text(new_text, encoding="utf-8")
                patched += 1

        return patched

    def replace_project_placeholders(
        self,
        project_root: Path,
        project_name: str,
        token: str = "{{project_name}}",
        extra_tokens: Mapping[str, str] | None = None,
    ) -> None:
        tokens = {token: project_name}
        if extra_tokens:
            tokens.update(extra_tokens)

        patched = self.replace(project_root, tokens)

        if patched:
            console.print(f"[green]Replaced placeholders in {patched} files.[/green]")
        else:
            console.print(f"[dim]No placeholders found to replace.[/dim]")
