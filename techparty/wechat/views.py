#encoding=utf-8

from django.http import HttpResponse
from django.contrib.auth.models import User
from django.views.generic.base import View
from django.conf import settings
from django.core.cache import cache
from wechat.official import WxApplication
from wechat.official import WxTextResponse
from social_auth.models import UserSocialAuth
from techparty.wechat.models import Command
from techparty.wechat.models import UserState


class TechpartyView(View, WxApplication):

    SECRET_TOKEN = settings.TECHPARTY_OFFICIAL_TOKEN

    def get(self, request):
        return HttpResponse(self.process(request.GET))

    def post(self, request):
        return HttpResponse(self.process(request.GET, request.body))

    def get_actions(self):
        actionMap = {}
        commands = cache.get('buildin_commands')
        if not commands:
            commands = Command.objects.all()
            cache.set('buildin_commands', commands)
        for command in commands:
            actionMap[command.name] = command
            for alias in command.alias.split(','):
                actionMap[alias] = command
        return actionMap

    def on_text(self, text):
        """处理用户发来的文本，
        - 先检查用户当前的状态（State）。如果用户带状态，则优先交给状态机处理
        - 用户无状态，则交由命令处理器分配处理。
        """
        if getattr(self, 'wxstate', ''):
            # 先处理状态
            pass
        else:
            command = self.get_actions().get(text.Content)
            if not command:
                return WxTextResponse(u'感谢您的反馈', text)
            if isinstance(command, Command):
                return command.as_response(text)
            else:
                pass

    def pre_process(self):
        """在处理命令前检查用户的状态。
        - 先检查用户是否存在，不存在先保存用户。
        - 再检查用户是否已在某个状态，如有，则把用户状态保存至实例。
        """
        social = UserSocialAuth.objects.filter(provider='weixin',
                                               uid=self.wxreq.FromUserName)
        if social:
            social = social[0]
        else:
            user = User.objects.create_user('wx_' + self.wxreq.FromUserName)
            user.save()
            social = UserSocialAuth(user=user, provider='weixin',
                                    uid=self.wxreq.FromUserName)
            social.save()

        try:
            self.wxstate = UserState.objects.get(user=self.wxreq.FromUserName)
        except:
            self.wxstate = None
