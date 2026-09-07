import re
import time
import uuid

from django.core.signals import request_finished

from .loggers import request_id_var, request_logger

# The incoming value is echoed into log files, so only a bounded, safe token is
# accepted. Without this check a newline in the header would let a caller forge
# log lines.
SAFE_REQUEST_ID = re.compile(r"\A[A-Za-z0-9._-]{1,64}\Z")


class RequestIDMiddleware:
    """Gives each request an id and writes one structured line per request.

    The id is returned as X-Request-ID and stamped on every log line emitted
    while the request is handled, so `grep req=<id> logs/*.log` reconstructs a
    single request out of an interleaved log.

    The access line is written here rather than left to django.server because
    django.server only exists under runserver: under gunicorn it logs nothing.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        incoming = request.headers.get("X-Request-ID", "")
        request_id = incoming if SAFE_REQUEST_ID.match(incoming) else uuid.uuid4().hex[:12]
        request.request_id = request_id
        request_id_var.set(request_id)
        started = time.perf_counter()

        try:
            response = self.get_response(request)
        except Exception:
            self._log(request, 500, started)
            raise

        response["X-Request-ID"] = request_id
        self._log(request, response.status_code, started)
        return response

    def _log(self, request, status, started):
        request_logger.info(
            "%s %s %s", request.method, request.path, status,
            extra={
                "method": request.method,
                # Deliberately not get_full_path(): tokens ride in query strings.
                "path": request.path,
                "status": status,
                "duration_ms": round((time.perf_counter() - started) * 1000, 2),
                "client_ip": request.META.get("REMOTE_ADDR", ""),
            },
        )


def clear_request_id(**kwargs):
    """Clear the id only once the request is completely finished.

    Not done in the middleware itself: Django logs 4xx/5xx responses *after* the
    whole middleware chain returns, and converts uncaught exceptions to
    responses in a wrapper outside it. Clearing any earlier strips the id off
    exactly the "Internal Server Error" lines you need it on. request_finished
    fires after both, when the response is closed.
    """
    request_id_var.set("-")


request_finished.connect(clear_request_id, dispatch_uid="{{project_name}}.clear_request_id")
