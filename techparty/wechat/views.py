#encoding=utf-8

from django.http import HttpResponse
from django.contrib.auth.models import User
from django.views.generic.base import View
from django.conf import settings
from wechat.official import WxApplication
from wechat.official import WxTextResponse
from social_auth.models import UserSocialAuth
from techparty.wechat.models import Command
from techparty.wechat.models import UserState
from techparty.wechat.commands import interactive_cmds
from techparty.wechat.commands import ICommand
import random
import pylibmc
import inspect
import traceback
cache = pylibmc.Client()


def log_err():
    import sys
    info = sys.exc_info()
    print 'full exception'
    print info[0]
    print info[1]
    traceback.print_tb(info[2])


class TechpartyView(View, WxApplication):

    SECRET_TOKEN = settings.TECHPARTY_OFFICIAL_TOKEN
    WELCOME_TXT = u"""感谢关注珠三角技术沙龙！本号的职能：
- 线下沙龙活动推送通知
- 支持沙龙报名、签到、直播
- 收看沙龙图文总结
- 收听沙龙录音
- 倾听程序猿/嫒的声音
- 帮工程师找工作
- 为工作推荐工程师
功能正在完善中，欢迎反馈。
更多请惯性地输入help继续吧 :)
    """

    def get(self, request):
        if '__text__' in request.GET and '__code__' in request.GET:
            # Test only！
            if request.GET['__code__'] != settings.DEBUG_SECRET:
                return HttpResponse(u'invalid debug code')
            xml = """<xml>
            <ToUserName><![CDATA[techparty]]></ToUserName>
            <FromUserName><![CDATA[testuser]]></FromUserName>
            <CreateTime>1348831860</CreateTime>
            <MsgType><![CDATA[text]]></MsgType>
            <Content><![CDATA[%s]]></Content>
            <MsgId>1234567890123456</MsgId>
            </xml>
            """ % request.GET['__text__']
            self.debug_mode = True
            try:
                return HttpResponse(self.process(request.GET, xml),
                                    mimetype='text/xml')
            except:
                import sys
                info = sys.exc_info()
                if hasattr(self, 'wxstate') and getattr(self.wxstate,
                                                        'id', ''):
                    self.wxstate.delete()
                error = '%s <br/> %s <br/> %s' % (info[0], info[1],
                                                  traceback.format_tb(info[2]))
                return HttpResponse(error)
        else:
            return HttpResponse(self.process(request.GET))

    def post(self, request):
        try:
            rsp = self.process(request.GET, request.body)
            return HttpResponse(rsp)
        except:
            log_err()
            if hasattr(self, 'wxstate') and self.wxstate.id:
                self.wxstate.delete()
            return HttpResponse('error request')

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
        actionMap.update(interactive_cmds)
        print actionMap
        return actionMap

    def is_valid_params(self, auth_params):
        if getattr(self, 'debug_mode', ''):
            return True
        else:
            return super(TechpartyView, self).is_valid_params(auth_params)

    def resume(self):
        command = interactive_cmds[self.wxstate.command]
        return command.execute(self.wxreq, self.user, self.wxstate)

    def on_text(self, text):
        """处理用户发来的文本，
        - 先检查用户当前的状态（State）。如果用户带状态，则优先交给状态机处理
        - 用户无状态，则交由命令处理器分配处理。
        """
        if self.wxstate:
            return self.resume()
        else:
            command = self.get_actions().get(text.Content.strip().lower())
            if not command:
                # 尝试一下模糊匹配
                blurs = [(k, v) for k, v in self.get_actions().iteritems()
                         if isinstance(v, Command) and not v.precise]
                for blur in blurs:
                    if blur[0] in text.Content.strip().lower():
                        command = blur[1]
                        break
                if not command:
                    return WxTextResponse(u'感谢您的反馈', text)
            if isinstance(command, Command):
                return command.as_response(text)
            elif inspect.isclass(command) and issubclass(command, ICommand):
                return command.execute(self.wxreq, self.user,
                                       self.wxstate)
            else:
                return command(self.wxreq, self.user)

    def on_image(self, image):
        return self.resume() if self.wxstate else \
            WxTextResponse(u'好图！谢谢亲！更多妹子图有请！',
                           self.wxreq)

    def on_link(self, link):
        return self.resume() if self.wxstate else \
            WxTextResponse(u'感谢分享！俺一定会好好学习的！',
                           self.wxreq)

    def on_location(self, location):
        if self.wxstate:
            return self.resume()
        return WxTextResponse(u'请站在原地等候，咱们不见不散！', self.wxreq)

    def pre_process(self):
        """在处理命令前检查用户的状态。
        - 先检查用户是否存在，不存在先保存用户。
        - 再检查用户是否已在某个状态，如有，则把用户状态保存至实例。
        """
        social = UserSocialAuth.objects.filter(provider='weixin',
                                               uid=self.wxreq.FromUserName)
        if social:
            social = social[0]
            self.user = social.user
        else:
            try:
                user = User.objects.create_user('default_' +
                                                str(random.randint(1, 10000)))
                user.save()
                user.username = 'wx_%d' % user.id
                user.save()
                self.user = user
                social = UserSocialAuth(user=user, provider='weixin',
                                        uid=self.wxreq.FromUserName)
                social.save()
            except:
                log_err()
        ss = UserState.objects.filter(user=social.user.username)
        if ss:
            self.wxstate = ss[0]
        else:
            self.wxstate = None
