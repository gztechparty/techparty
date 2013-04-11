#encoding=utf-8

from sae.mail import send_mail
from django.core.mail.backends.base import BaseEmailBackend
from django.conf import settings


class SAEEmailBackend(BaseEmailBackend):

    def send_messages(self, email_messages):
        for email in email_messages:
            send_mail(email.to, email.subject, email.body,
                      (settings.EMAIL_HOST, settings.EMAIL_PORT,
                       settings.EMAIL_HOST_USER,
                       settings.EMAIL_HOST_PASSWORD,
                       settings.EMAIL_USE_TLS))
