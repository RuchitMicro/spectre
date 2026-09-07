"""Signal handlers for the api app.

Connected by `ApiConfig.ready()` in apps.py. Keep handlers thin: they decide
*when* something runs, the model method decides *what* it does.
"""

from django.db.models.signals   import post_save
from django.dispatch            import receiver

from {{project_name}}.loggers   import logger

from .models import Contact, Profile, User


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create a Profile for every new non-superuser."""
    if not created or instance.is_superuser:
        return

    try:
        Profile.objects.create(user=instance)
    except Exception:
        logger.exception(
            "Failed to create profile for user: %s (id=%s)",
            instance.username or instance.email,
            instance.id,
        )


@receiver(post_save, sender=Contact)
def notify_on_new_contact(sender, instance, created, **kwargs):
    """Send the enquiry notification and acknowledgement on creation only.

    Both model methods pass fail_silently=True, so a broken SMTP config cannot
    turn a successful POST /api/contact/ into a 500.
    """
    if not created:
        return

    try:
        instance.send_mail_notification()
        instance.send_mail_greeting()
    except Exception:
        logger.exception("Failed to send contact emails for contact id=%s", instance.pk)
