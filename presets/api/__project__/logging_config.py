"""Logging for {{project_name}}.

Text format for humans in development, JSON for machines in production. The
JSON field names are the contract with the log shipper (Promtail/Alloy into
Loki), so renaming one breaks whatever dashboards read it.

Files, all rotating at 10MB keeping 10 backups:
    logs/app.log       application logs
    logs/access.log    one line per HTTP request
    logs/error.log     500s, with tracebacks
    logs/security.log  blocked/suspicious requests

Everything is driven from .env: LOG_LEVEL, LOG_FORMAT, LOG_TO_FILE, LOG_DIR,
SQL_DEBUG.
"""

import json
import logging
import logging.config
import os
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

from .loggers import request_id_var

# settings.py imports this module before it calls load_dotenv() itself, so
# without this the env knobs below would silently read nothing from .env.
load_dotenv()


def _env_bool(name, default=False):
    return os.getenv(name, str(default)).strip().lower() in ("true", "1", "yes", "on")


# BASE_DIR is resolved here rather than imported so this module stays usable
# on its own, without settings loaded.
BASE_DIR    = Path(__file__).resolve().parent.parent
LOG_DIR     = Path(os.getenv("LOG_DIR") or BASE_DIR / "logs")

LOG_LEVEL   = os.getenv("LOG_LEVEL", "INFO").strip().upper()
JSON_LOGS   = os.getenv("LOG_FORMAT", "text").strip().lower() == "json"
LOG_TO_FILE = _env_bool("LOG_TO_FILE", True)
SQL_DEBUG   = _env_bool("SQL_DEBUG")

MAX_BYTES    = 10 * 1024 * 1024
BACKUP_COUNT = 10

if LOG_TO_FILE:
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        probe = LOG_DIR / ".write-probe"
        probe.touch()
        probe.unlink()
    except OSError:
        # Read-only or root-owned mount, which is normal in a container.
        # Degrade to console rather than killing the process at import time.
        LOG_TO_FILE = False

try:
    import colorlog
    HAS_COLORLOG = True
except ImportError:
    HAS_COLORLOG = False


class RequestIDFilter(logging.Filter):
    """Stamps the current request id (set by RequestIDMiddleware) onto every record."""

    def filter(self, record):
        record.request_id = request_id_var.get()
        return True


class JSONFormatter(logging.Formatter):
    """One JSON object per line, ready for `| json` in a Loki query."""

    # Derived rather than hardcoded so it keeps up with the interpreter:
    # 3.12 added taskName to every record, for instance.
    _STANDARD = frozenset(
        logging.LogRecord("", 0, "", 0, "", (), None).__dict__
    ) | {"asctime", "message", "taskName"}

    def format(self, record):
        payload = {
            "ts": datetime.fromtimestamp(record.created, timezone.utc)
                          .isoformat(timespec="milliseconds")
                          .replace("+00:00", "Z"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "request_id": getattr(record, "request_id", "-"),
            "module": record.module,
            "func": record.funcName,
            "line": record.lineno,
        }
        # Anything the call site passed as extra={...}: method, path, status,
        # duration_ms, and whatever you add later.
        payload.update({
            key: value for key, value in record.__dict__.items()
            if key not in self._STANDARD
        })
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


FILE_FORMATTER    = "json" if JSON_LOGS else "standard"
ACCESS_FORMATTER  = "json" if JSON_LOGS else "access"
CONSOLE_FORMATTER = "json" if JSON_LOGS else ("colored" if HAS_COLORLOG else "standard")


def _file_handler(filename, formatter, level=None):
    handler = {
        "class": "logging.handlers.RotatingFileHandler",
        "filename": LOG_DIR / filename,
        "maxBytes": MAX_BYTES,
        "backupCount": BACKUP_COUNT,
        "formatter": formatter,
        "filters": ["request_id"],
        "encoding": "utf-8",
    }
    if level:
        handler["level"] = level
    return handler


HANDLERS = {
    "console": {
        "class": "colorlog.StreamHandler" if (HAS_COLORLOG and not JSON_LOGS) else "logging.StreamHandler",
        "formatter": CONSOLE_FORMATTER,
        "filters": ["request_id"],
    },
    # Emails ADMINS on unhandled 500s. Defining LOGGING at all disables the
    # copy of this that Django ships by default, so it is re-added here.
    "mail_admins": {
        "class": "django.utils.log.AdminEmailHandler",
        "filters": ["require_debug_false"],
        "level": "ERROR",
    },
}

if LOG_TO_FILE:
    HANDLERS.update({
        "app_file":      _file_handler("app.log", FILE_FORMATTER),
        "access_file":   _file_handler("access.log", ACCESS_FORMATTER, "INFO"),
        "error_file":    _file_handler("error.log", FILE_FORMATTER, "ERROR"),
        "security_file": _file_handler("security.log", FILE_FORMATTER, "WARNING"),
    })


def _handlers(*names):
    """Drop handlers that are not configured, so LOG_TO_FILE=False still boots."""
    return [name for name in names if name in HANDLERS]


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,

    "filters": {
        "request_id": {"()": RequestIDFilter},
        "require_debug_false": {"()": "django.utils.log.RequireDebugFalse"},
    },

    "formatters": {
        "standard": {
            "format": "[{asctime}] [{levelname:<8}] {name} | req={request_id} | {module}.{funcName}:{lineno} | {message}",
            "style": "{",
        },
        "access": {
            "format": "[{asctime}] [{levelname:<8}] req={request_id} | {message}",
            "style": "{",
        },
        "json": {"()": JSONFormatter},
        "colored": {
            "()": "colorlog.ColoredFormatter",
            "format": "%(log_color)s[%(asctime)s] [%(levelname)-8s] %(name)s | req=%(request_id)s | %(module)s:%(lineno)d%(reset)s %(message)s",
            "log_colors": {
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "bold_red",
            },
        },
    },

    "handlers": HANDLERS,

    "loggers": {
        # Your application logs: `from {{project_name}}.loggers import logger`.
        "{{project_name}}": {
            "handlers": _handlers("console", "app_file"),
            "level": LOG_LEVEL,
            "propagate": False,
        },

        # One line per request, written by RequestIDMiddleware.
        "{{project_name}}.request": {
            "handlers": _handlers("console", "access_file"),
            "level": "INFO",
            "propagate": False,
        },

        # Unhandled 500s, with the traceback.
        "django.request": {
            "handlers": _handlers("console", "error_file", "mail_admins"),
            "level": "ERROR",
            "propagate": False,
        },

        # Blocked/suspicious requests: bad Host headers, CSRF failures,
        # disallowed redirects. Security signal, so it gets its own file.
        "django.security": {
            "handlers": _handlers("console", "security_file"),
            "level": "WARNING",
            "propagate": False,
        },

        # runserver's own access line. Quiet, because RequestIDMiddleware
        # already logs every request in a form that also works under gunicorn.
        # WARNING keeps broken static assets (404s) visible.
        "django.server": {
            "handlers": _handlers("console"),
            "level": "WARNING",
            "propagate": False,
        },
    },

    # Catches everything not named above, third-party libraries included, so a
    # dependency's warning cannot vanish silently.
    "root": {
        "handlers": _handlers("console", "app_file"),
        "level": "WARNING",
    },
}

# SQL_DEBUG=True logs every query with its timing. Verbose by design: it is for
# chasing an N+1, not for leaving on.
if SQL_DEBUG:
    LOGGING["loggers"]["django.db.backends"] = {
        "handlers": _handlers("console", "app_file"),
        "level": "DEBUG",
        "propagate": False,
    }

if not HAS_COLORLOG or JSON_LOGS:
    del LOGGING["formatters"]["colored"]

logging.config.dictConfig(LOGGING)
