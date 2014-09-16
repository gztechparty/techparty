#encoding=utf-8

from django.core.mail.backends.base import BaseEmailBackend
from django.conf import settings


class AsyncEmailBackend(BaseEmailBackend):

    def send_messages(self, email_messages):
        from techparty.wechat import tasks
        tasks.send_messages.delay(email_messages)
