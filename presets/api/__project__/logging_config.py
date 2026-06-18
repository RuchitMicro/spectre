
import logging
import logging.config
from logging.handlers       import RotatingFileHandler
from pathlib                import Path
from django.db              import connection

# BASE_DIR must be fetched dynamically so this file works independently
BASE_DIR    = Path(__file__).resolve().parent.parent
LOG_DIR     = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)



LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,

    "formatters": {
        "standard": {
            "format": "[{asctime}] [{levelname:<8}] {name} | {module}.{funcName}:{lineno} | {message}",
            "style": "{",
        },
        "simple": {
            "format": "[{levelname:<8}] {message}",
            "style": "{",
        },
        "access": {
            "format": "[{asctime}] [{levelname:<8}] {message}",
            "style": "{",
        },
    },

    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "access",
        },
        "access_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOG_DIR / "access.log",
            "maxBytes": 10 * 1024 * 1024,   # 10MB
            "backupCount": 10,             # Keep last 10 files only
            "formatter": "access",
            "level": "INFO",
        },
        "app_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOG_DIR / "app.log",
            "maxBytes": 10 * 1024 * 1024,  # 10MB
            "backupCount": 10,
            "formatter": "standard",
        },

        "error_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOG_DIR / "error.log",
            "maxBytes": 10 * 1024 * 1024, # 10MB
            "backupCount": 10,
            "formatter": "standard",
            "level": "ERROR",
        },
    },

    "loggers": {

        # Your project logger
        "{{project_name}}": {
            "handlers": ["console", "app_file"],
            "level": "INFO",
            "propagate": False,
        },

        # Django request errors (500 errors etc)
        "django.request": {
            "handlers": ["error_file"],
            "level": "ERROR",
            "propagate": False,
        },

        # # Django DB query logging (enable only for debugging)
        # "django.db.backends": {
        #     "handlers": ["console"],
        #     "level": "DEBUG",
        #     "propagate": False,
        # },

        # Default Django logs
        # "django": {
        #     "handlers": ["console"],
        #     "level": "INFO",
        #     "propagate": True,
        # },
        "django.server": {
            "handlers": ["access_file", "console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}


# Optional: Colored console logs (dev only)
try:
    import colorlog

    LOGGING["formatters"]["colored"] = {
        "()": "colorlog.ColoredFormatter",
        "format": "%(log_color)s[%(asctime)s] [%(levelname)-8s] %(name)s | %(module)s:%(lineno)d%(reset)s %(message)s",
        "log_colors": {
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "bold_red",
        },
    }

    LOGGING["handlers"]["console"] = {
        "class": "colorlog.StreamHandler",
        "formatter": "colored",
    }

except ImportError:
    pass


logging.config.dictConfig(LOGGING)


