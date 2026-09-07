import logging
from contextvars import ContextVar

# Application logs. Everything you write by hand goes here.
logger = logging.getLogger("{{project_name}}")

# One structured line per HTTP request, written by RequestIDMiddleware.
# Separate from `logger` so access traffic never drowns out application logs.
request_logger = logging.getLogger("{{project_name}}.request")

# Set by RequestIDMiddleware for the duration of a request and read by the
# request_id log filter, so every line emitted while handling that request
# carries the same id.
request_id_var = ContextVar("request_id", default="-")
