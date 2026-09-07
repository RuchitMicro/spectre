"""Smoke tests for the api app.

These cover the scaffolding itself: the base view classes, CommonModel, the
custom file fields, and the signals. Use them as the pattern for new tests.

Run with `pytest` or `make test`.
"""

import io
import json
import uuid

import pytest
from PIL import Image

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

from .admin import wants_wysiwyg
from .models import Blog, Contact, ImageMaster, Profile, SiteSetting

User = get_user_model()


def make_image(width=3000, height=200, fmt="JPEG"):
    """Build an in-memory upload wider than the 1920px compression threshold."""
    buf = io.BytesIO()
    Image.new("RGB", (width, height), "red").save(buf, format=fmt)
    buf.seek(0)
    return SimpleUploadedFile("original name.jpg", buf.read(), content_type="image/jpeg")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_health_endpoint(client):
    response = client.get("/api/")
    assert response.status_code == 200
    assert response.json() == {"message": "Healthy and alive!"}


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def test_every_response_carries_a_request_id(client):
    response = client.get("/api/")
    assert response["X-Request-ID"]


def test_caller_supplied_request_id_is_reused(client):
    """Lets one id follow a request across services."""
    response = client.get("/api/", headers={"X-Request-ID": "caller-supplied-1"})
    assert response["X-Request-ID"] == "caller-supplied-1"


def test_forged_request_id_is_rejected(client):
    """A newline in the header would otherwise let a caller write fake log lines."""
    response = client.get("/api/", headers={"X-Request-ID": "abc\ninjected ERROR line"})
    assert "\n" not in response["X-Request-ID"]
    assert response["X-Request-ID"] != "abc\ninjected ERROR line"


def test_json_formatter_emits_one_parseable_object_per_line():
    """The field names here are what a Loki query does `| json` on."""
    import logging

    from django.conf import settings

    formatter = settings.LOGGING["formatters"]["json"]["()"]()
    record = logging.LogRecord(
        name="test", level=logging.INFO, pathname=__file__, lineno=1,
        msg="GET %s %s", args=("/api/", 200), exc_info=None,
    )
    record.status = 200
    record.duration_ms = 4.2

    payload = json.loads(formatter.format(record))

    assert payload["msg"] == "GET /api/ 200"
    assert payload["level"] == "INFO"
    assert payload["ts"].endswith("Z"), "Loki parses RFC3339"
    assert payload["status"] == 200
    assert payload["duration_ms"] == 4.2
    assert payload["request_id"] == "-", "no request in flight"


@pytest.mark.django_db
def test_read_only_view_lists_and_paginates(client):
    Blog.objects.create(title="First", slug="first")
    response = client.get("/api/blog/")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_items"] == 1
    assert payload["results"][0]["title"] == "First"


@pytest.mark.django_db
def test_read_only_view_rejects_writes(client):
    response = client.post("/api/blog/", data={"title": "Nope"}, content_type="application/json")
    assert response.status_code in (403, 405)
    assert not Blog.objects.filter(title="Nope").exists()


@pytest.mark.django_db
def test_read_only_view_supports_pk_lookup(client):
    blog = Blog.objects.create(title="Findable", slug="findable")
    response = client.get(f"/api/blog/?pk={blog.pk}")

    assert response.status_code == 200
    assert response.json()["title"] == "Findable"


@pytest.mark.django_db
def test_create_only_view_accepts_contact(client):
    response = client.post(
        "/api/contact/",
        data={
            "full_name": "Test User",
            "email": "test@example.com",
            "phone_number": "1234567890",
            "requirement": "Need a quote",
        },
        content_type="application/json",
    )

    assert response.status_code == 201
    assert Contact.objects.filter(email="test@example.com").exists()


# ---------------------------------------------------------------------------
# CommonModel
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_common_model_uses_uuid_primary_key():
    blog = Blog.objects.create(title="UUID", slug="uuid")
    assert isinstance(blog.pk, uuid.UUID)


@pytest.mark.django_db
def test_extra_params_helpers():
    blog = Blog.objects.create(title="Params", slug="params")

    assert blog.get_extra_param("missing", "fallback") == "fallback"

    blog.set_extra_param("featured", True, save=True)
    blog.update_extra_params({"weight": 3}, save=True)
    blog.refresh_from_db()

    assert blog.extra_params == {"featured": True, "weight": 3}


@pytest.mark.django_db
def test_to_dict_normalises_timestamps():
    blog = Blog.objects.create(title="Dict", slug="dict")
    data = blog.to_dict()

    assert data["id"] == blog.pk
    assert isinstance(data["created_at"], str)


# ---------------------------------------------------------------------------
# Custom file fields
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_image_upload_is_renamed_and_compressed():
    record = ImageMaster.objects.create(name="Banner", image=make_image())

    stored = record.image.name.rsplit("/", 1)[-1]
    assert " " not in stored, "the original filename must not reach storage"
    assert stored.endswith(".jpg")
    uuid.UUID(stored[:-4])  # raises if the stem is not a UUID

    with Image.open(record.image.path) as img:
        assert img.width == 1920, "images wider than max_width should be resized"


# ---------------------------------------------------------------------------
# Signals
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_profile_created_for_new_user():
    user = User.objects.create_user(username="member", email="m@example.com", password="pw")
    assert Profile.objects.filter(user=user).exists()


@pytest.mark.django_db
def test_no_profile_for_superuser():
    admin = User.objects.create_superuser(username="root", email="r@example.com", password="pw")
    assert not Profile.objects.filter(user=admin).exists()


@pytest.mark.django_db
def test_contact_emails_do_not_break_creation(mailoutbox):
    """A missing SiteSetting must not turn a successful write into an error."""
    Contact.objects.create(
        full_name="Nobody",
        email="nobody@example.com",
        phone_number="1",
        requirement="Hello",
    )
    assert Contact.objects.count() == 1


# ---------------------------------------------------------------------------
# Rich text field resolution
# ---------------------------------------------------------------------------

def test_rtf_fields_is_opt_in():
    meta = {"rtf_fields": ["body"]}
    assert wants_wysiwyg(meta, "body") is True
    assert wants_wysiwyg(meta, "raw_html") is False


def test_rtf_exclude_still_works_for_legacy_models():
    """admin_meta copied from an older project keeps its opt-out behavior."""
    meta = {"rtf_exclude": ["raw_html"]}
    assert wants_wysiwyg(meta, "body") is True
    assert wants_wysiwyg(meta, "raw_html") is False


def test_no_declaration_means_plain_textarea():
    assert wants_wysiwyg({}, "body") is False
    assert wants_wysiwyg({"list_display": ["body"]}, "body") is False


def test_rtf_fields_wins_over_rtf_exclude():
    meta = {"rtf_fields": ["body"], "rtf_exclude": ["body"]}
    assert wants_wysiwyg(meta, "body") is True


def test_bare_string_is_not_matched_character_by_character():
    """`('head')` is a string, not a tuple. It must not match 'h' or 'ea'."""
    assert wants_wysiwyg({"rtf_exclude": ("head")}, "head") is False
    assert wants_wysiwyg({"rtf_exclude": ("head")}, "ea") is True
    assert wants_wysiwyg({"rtf_fields": ("body")}, "body") is True
    assert wants_wysiwyg({"rtf_fields": ("body")}, "od") is False


@pytest.mark.django_db
def test_admin_applies_wysiwyg_only_to_declared_fields(rf):
    """Blog declares featured_text and text, so head and tags stay plain."""
    from django.contrib import admin as dj_admin
    from unfold.contrib.forms.widgets import WysiwygWidget

    model_admin = dj_admin.site._registry[Blog]
    request = rf.get("/")

    def widget_for(name):
        field = Blog._meta.get_field(name)
        return type(model_admin.formfield_for_dbfield(field, request).widget)

    assert widget_for("text") is WysiwygWidget
    assert widget_for("featured_text") is WysiwygWidget
    assert widget_for("head") is not WysiwygWidget
    assert widget_for("tags") is not WysiwygWidget


# ---------------------------------------------------------------------------
# Singleton settings
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_site_setting_load_returns_none_when_empty():
    assert SiteSetting.load() is None


@pytest.mark.django_db
def test_site_setting_load_returns_row():
    SiteSetting.objects.create(admin_email="admin@example.com")
    assert SiteSetting.load().admin_email == "admin@example.com"
