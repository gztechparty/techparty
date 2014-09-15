#encoding=utf-8

from wechat.official import WxArticle
from wechat.official import WxNewsResponse
from techparty.event.models import Event
from techparty.event.models import Participate
from datetime import datetime
from wechat.official import WxTextResponse
from django.db import IntegrityError
from django.core.validators import validate_email
from django.core.validators import MaxLengthValidator
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
import sys
from yafsm import BaseStateMachine
from social.apps.django_app.default.models import UserSocialAuth
from . import tasks

interactive_cmds = {}


def register_cmd(command, name=None, alias=None):
    if not name:
        name = command.COMMAND_NAME
    if not alias:
        alias = command.COMMAND_ALIAS
    interactive_cmds[name] = command
    for al in alias.split(','):
        interactive_cmds[al] = command


class RegisterEvent(BaseStateMachine):
    """用户状态
    - 等待用户选择活动或确认。
    """
    COMMAND_NAME = u'报名'
    COMMAND_ALIAS = u'er,報名,bm'

    TRANSIT_MAP = {
        'start': (('confirm', {}), ('choose', {}), ('end', {})),
        'confirm': (('end', {'Content': '1'}), ('cancel', {'Content': '0'})),
        'choose': (('end', {}), ('cancel', {'Content': 'c'})),
    }

    def init_context(self):
        print self.user.first_name
        events = Event.objects.filter(start_time__gt=datetime.now())
        return {'events': [e.to_dict() for e in events],
                'has_info': self.user.first_name or self.user.email}

    ################ Start State ################

    def should_enter_confirm_from_start(self):
        return len(self.context.get('events', [])) == 1 and \
            self.context.get('has_info', False)

    def should_enter_choose_from_start(self):
        return len(self.context.get('events', [])) > 1 and \
            self.context.get('has_info', False)

    def should_enter_end_from_start(self):
        return (not self.context.get('events', [])) or \
            (not self.context.get('has_info', False))

     ################ Confirm State ################

    def enter_confirm_from_start(self):
        event = self.context['events'][0]
        ct = u'您确认报名参加在%s举行的"%s"？确认请回复1，取消请回复0' % (
            event['start_time'], event['name'])
        return WxTextResponse(ct, self.obj)

    ################ Choose State ################

    def enter_choose_from_start(self):
        ct = u'目前有多个活动正接受报名，请输入活动序号完成报名,输入c退出:'
        index = 0
        for e in self.context['events']:
            ct += u'序号：%d，活动：%s，举办时间：%s' %\
                  (index, e['name'], e['start_time'])
            index += 1
        return WxTextResponse(ct, self.obj)

    def should_enter_end_from_choose(self):
        if self.obj.MsgType == 'text':
            try:
                return int(self.obj.Content) in \
                    range(len(self.context['events']))
            except:
                return False
        else:
            self.error = u'请输入文字'
        return False

    ################ End State ################

    def enter_end_from_start(self):
        if self.context['has_info']:
            return WxTextResponse(u'近期暂无活动，感谢您的关注',
                                  self.obj)
        else:
            return WxTextResponse(u'您的个人资料不齐，请回复ei补全再报名',
                                  self.obj)

    def enter_end_from_confirm(self):
        return self.register_event(self.context['events'][0])

    def enter_end_from_choose(self):
        index = int(self.obj.Content)
        event = self.context['events'][index]
        return self.register_event(event)

    def register_event(self, event):
        pt = Participate(user=self.user, event_id=event['id'])
        try:
            pt.save()
        except IntegrityError:
            info = sys.exc_info()
            print info[0], info[1], info[2]
        except:
            return WxTextResponse(u'小子你摊上事儿了，报名不成功，到微信' +
                                  u'找@jeff_kit 帮你搞定吧！', self.obj)
        ct = u'您已成功报名"%s",敬请留意邀请信息。' % event['name']
        return WxTextResponse(ct, self.obj)

    def cancel(self):
        return WxTextResponse(u'您已取消报名,感谢关注', self.obj)


class RegisterConfirm(BaseStateMachine):
    COMMAND_NAME = u'确认报名'
    COMMAND_ALIAS = u'rc,qr'

    TRANSIT_MAP = {
        'start': (('confirm', {}), ('choose', {}), ('end', {})),
        'confirm': (('end', {'Content': '1'}), ('cancel', {'Content': '0'})),
        'choose': (('end', {}), ('cancel', {'Content': 'c'})),
    }

    def pt2dict(self, pt):
        return {
            'id': pt.id,
            'event': pt.event.name,
            'eid': pt.event.id
        }

    def init_context(self):
        pts = Participate.objects.filter(user=self.user, status=1,
                                         event__start_time__gt=datetime.now())
        return {'pts': [self.pt2dict(pt) for pt in pts]}

    ############## Start State #################

    def should_enter_confirm_from_start(self):
        """如果只有一个活动就直接确认了。
        """
        return len(self.context.get('pts', [])) == 1

    def should_enter_choose_from_start(self):
        return len(self.context.get('pts', [])) > 1

    def should_enter_end_from_start(self):
        return not self.context.get('pts', [])

    ############## Comfirm State ##################

    def enter_confirm_from_start(self):
        """让用户确认报名还是取消报名
        """
        pt = self.context['pts'][0]
        event = Event.objects.get(id=pt['eid'])
        ct = u"""您确认出席"%s"活动吗？
地址：%s
时间：%s
场地人均消费：%d元
出席请回复1，取消请回复0:"""
        ct = ct % (event.name, event.address, event.start_time, event.fee)
        return WxTextResponse(ct, self.obj)

    ############# choose State #####################

    def enter_choose_from_start(self):
        ct = u'目前有多个活动需要确认，请输入序号，回复c退出:'
        index = 0
        for pt in self.context['pts']:
            ct += u'序号: %d, 活动：%s' % (index, pt['event'])
            index += 1
        return WxTextResponse(ct, self.obj)

    def should_enter_end_from_choose(self):
        if self.obj.MsgType == 'text':
            try:
                return int(self.obj.Content) in \
                    range(len(self.context['pts']))
            except:
                return False
        else:
            self.context['error'] = u'请输入文字'
        return False

    ############## End State ##############
    def enter_end_from_start(self):
        return WxTextResponse(u'未找到需要确认的活动', self.obj)

    def enter_end_from_confirm(self):
        pt = self.context['pts'][0]
        return self.confirm_event(pt)

    def enter_end_from_choose(self):
        index = int(self.obj.Content)
        pt = self.context['pts'][index]
        return self.confirm_event(pt)

    def confirm_event(self, pt):
        name = pt['event']
        pt = Participate.objects.get(id=pt['id'])
        pt.status = 3
        pt.save()

        ct = u'您已确认参加"%s"，届时请准时出席。' % name
        return WxTextResponse(ct, self.obj)

    def cancel(self):
        return WxTextResponse(u'已取消确认。', self.obj)


class ProfileEdit(BaseStateMachine):
    """修改用户的个人资料。
    用户昵称及Email是必填项。
    """
    COMMAND_NAME = u'修改资料'
    COMMAND_ALIAS = u'ei,edit'

    TRANSIT_MAP = {
        'start': (('edit', {}),),
        'edit': (('cancel', {'Content': 'c'}), ('end', {})),
    }

    PROFILE_FIELDS = (('name', u'姓名', {'max_length': 10}),
                      ('email', u'邮箱', 'email'),)

    def validate_value_for_field(self, value, rule):
        if isinstance(rule, dict):
            if 'max_length' in rule:
                try:
                    MaxLengthValidator(rule['max_length'])(value)
                except ValidationError:
                    return u'不能超过%d个字符，请重新输入:' % rule['max_length']
        else:
            if rule == 'email':
                try:
                    validate_email(value)
                except ValidationError:
                    return u'请输入正确的邮箱：'
            elif rule == 'url':
                try:
                    URLValidator()(value)
                except ValidationError:
                    return u'请输入正确的网址：'

    def find_next_field(self):
        data = self.context.get('data', {})
        index = 0
        for field in self.PROFILE_FIELDS:
            if field[0] not in data.keys():
                return index
            index += 1
        return -1

    def init_context(self):
        return {'original_data': {'name': self.user.first_name,
                                  'email': self.user.email}}

    ############ start State ###############

    def should_enter_edit_from_start(self):
        return True

    ############ Edit State ################

    def next_field(self):
        """要求用户输入下一个字段
        """
        data = self.context.get('data', {})
        original = self.context['original_data']
        for field in self.PROFILE_FIELDS:
            if field[0] not in data.keys():
                ct = u'请输入%s:' % field[1]
                if original.get(field[0], ''):
                    ct = u'请输入%s (原%s，输入s跳过此项):' % \
                         (field[1], original[field[0]])
                return ct

    def enter_edit_from_start(self):
        """要求用户输入下一个字段
        """
        return WxTextResponse(self.next_field(), self.obj)

    def should_enter_end_from_edit(self):
        """
        1、检查用户输入：
        - s，跳过，
        - 不合法输入，抛异常
        - 合法输入，保存，找下一个字段，无则返回True
        2、判断完成个数，一致则返回True，否则返回False。
        """
        next = self.find_next_field()
        if next < 0:
            return True
        if self.obj.MsgType != 'text':
            self.error = u'请输入文字'
            return False

        data = self.context.get('data', {})
        field = self.PROFILE_FIELDS[next]
        if self.obj.Content.lower() == 's':
            value = self.context['original_data'].get(field[0], '')
            data[field[0]] = value
        elif len(field) > 2:
            error = self.validate_value_for_field(self.obj.Content, field[2])
            if error:
                self.error = error
                return False
        if field[0] not in data:
            data[field[0]] = self.obj.Content
        self.context['data'] = data

        if len(self.PROFILE_FIELDS) - next == 1:
            return True
        self.error = self.next_field()
        return False

    ############## End State ##############

    def end(self):
        data = self.context.get('data', None)
        if not data:
            return WxTextResponse(u'已取消更改', self.obj)
        self.user.first_name = data['name']
        self.user.email = data['email']
        self.user.save()
        return WxTextResponse(u'更改个人资料成功！', self.obj)

    def cancel(self):
        return WxTextResponse(u'已取消更改个人资料', self.obj)


class BindWechat(BaseStateMachine):

    COMMAND_NAME = u'绑定微信号'
    COMMAND_ALIAS = u'bd,绑定,db'

    TRANSIT_MAP = {
        'start': (('input', {}),
                  ('end', {})),
        'input': (('cancel', {'Content': '0'}),
                  ('end', {}))
        }

    def init_context(self):
        # 查询当前用户是否有绑定微信帐号。
        social = UserSocialAuth.objects.filter(provider='weixin',
                                               user=self.user)
        data = social.extra_data
        if 'wechat_account' in data:
            return {'wechat': data['wechat_account']}
        return {}

    def should_enter_input_from_start(self):
        return 'wechat_account' not in self.context

    def enter_input_from_start(self):
        return WxTextResponse(u'请输入您的微信号，回复0取消', self.obj)

    def cancel(self):
        return WxTextResponse(u'已取消绑定微信号', self.obj)

    def should_enter_end_from_start(self):
        """如果用户已绑定帐号，则直接退出。
        """
        return 'wechat_account' in self.context

    def enter_end_from_start(self):
        msg = u'您已经绑定了微信帐号 %s ' % self.user.wechat
        return WxTextResponse(msg, self.obj)

    def should_enter_end_from_input(self):
        return True

    def enter_end_from_input(self):
        """向用户发送一条预览信息，如果不成功则发送错误信息。
        """
        #tasks.validate_wechat_account.delay(self.obj.Content,
        #                                    self.obj.FromUserName)
        return WxTextResponse(u'正在验证您的微信号，请稍候 ...', self.obj)

register_cmd(RegisterEvent)
register_cmd(RegisterConfirm)
register_cmd(ProfileEdit)
register_cmd(BindWechat)


############## simple command ############

def events(wxreq, user):
    """返回目前正在举行的活动
    """
    evns = Event.objects.filter(start_time__gt=datetime.now())
    if not evns:
        return WxTextResponse(u'近期暂无活动，感谢您的关注', wxreq)
    articles = [WxArticle(Title=e.name, Description=e.description,
                          Url=e.url, PicUrl=e.image) for e in evns]
    return WxNewsResponse(articles, wxreq)


def user_info(wxreq, user):
    """查看自己的资料
    """
    if not (user.first_name or user.email):
        return WxTextResponse(u'您未设置个人资料，回复ei来设置吧', wxreq)

    ct = u"""您的姓名：%s
您的邮箱: %s
回复ei可以进行修改。""" % (user.first_name, user.email)
    return WxTextResponse(ct, wxreq)


def register_events(wxreq, user):
    """返回已经报名的活动
    """
    pts = Participate.objects.filter(user=user,
                                     event__start_time__gt=datetime.now())
    if pts:
        ct = u''
        for pt in pts:
            if pt.status not in (1, 3):
                names = u"%s(%s)" % (pt.event.name,
                                     pt.get_status())
                ct = ct + u'您已经报名参加了 %s\n' % names
            else:
                ct = ct + u'%s,您己受邀请参加下面的活动，届时请准时出席！\n' % user.first_name
                event = pt.event
                ct = ct + u"""活动:%s\n地址：%s\n时间：%s\n场地人均消费：%d元\n""" % (event.name, event.address,
                                        event.start_time, event.fee)
    else:
        ct = u'您目前未报名任何活动'
    return WxTextResponse(ct, wxreq)


register_cmd(events, u'活动', u'e,event')
register_cmd(user_info, u'我', u'i,me')
register_cmd(register_events, u'我的报名', 'r,mr')
