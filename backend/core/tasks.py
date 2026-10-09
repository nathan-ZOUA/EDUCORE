from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail


@shared_task
def deliver_email(subject, message, recipient):
    return send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL if hasattr(settings, "DEFAULT_FROM_EMAIL") else None,
        [recipient],
        fail_silently=False,
    )
