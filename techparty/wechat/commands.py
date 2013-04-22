#encoding=utf-8

from wechat.official import WxArticle
from wechat.official import WxNewsResponse
from techparty.event.models import Event
from techparty.event.models import Participate
from techparty.wechat.models import UserState
from datetime import datetime
from wechat.official import WxTextResponse
from django.db import IntegrityError
from django.core.validators import validate_email
from django.core.validators import MaxLengthValidator
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
import sys

interactive_cmds = {}


def register_cmd(command, name=None, alias=None):
    if not name:
        name = command.COMMAND_NAME
    if not alias:
        alias = command.COMMAND_ALIAS
    interactive_cmds[name] = command
    for al in alias.split(','):
        interactive_cmds[al] = command


class ICommand(object):
    """交互式命令的基类
    """
    TRANSIT_MAP = {}
    COMMAND_NAME = 'noname'
    COMMAND_ALIAS = 'nn'

    @classmethod
    def execute(cls, wxreq, user, state=None):
        return cls(wxreq, user, state).process()

    def __init__(self, wxreq, user, state=None):
        self.wxreq = wxreq
        self.user = user
        self.state = state

    def validate_transit_map(self):
        pass

    def process(self):
        if not self.state:
            self.state = UserState(user=self.user, command=self.COMMAND_NAME,
                                   state='start', context={})
            self.start()
        assert self.TRANSIT_MAP, 'No TRANSIT_MAP define!'
        branches = self.TRANSIT_MAP.get(self.state.state, '')
        func = None
        for branch in branches:
            if self.should_transit(branch):
                func = 'enter_%s_state' % branch[0]
                ret = getattr(self, func)()
                if branch[0] in ('end', 'cancel') and self.state.id:
                    self.state.delete()
                elif branch[0] != 'start' and branch[0] not in ('end',
                                                                'cancel'):
                    self.state.state = branch[0]
                    self.state.save()
                return ret
        if not func:
            # 不好意思，原地踏步，继续。
            func = 'enter_%s_state' % self.state.state
            retry = '%s_retry' % self.state.state
            self.state.context[retry] = self.state.context.get(retry, 0) + 1
            self.state.save()
            if self.state.context.get('error', ''):
                return WxTextResponse(self.state.context['error'], self.wxreq)
            return getattr(self, func)()

    def should_transit(self, branch):
        if branch[1]:
            collect_count = 0
            for k, v in branch[1].iteritems():
                if getattr(self.wxreq, k, '') == v:
                    collect_count += 1
            if collect_count == len(branch[1].keys()):
                return True
            return False
        else:
            # 检测有没有should_enter_xx_state方法
            func = 'should_enter_%s_state' % branch[0]
            if getattr(self, func):
                return getattr(self, func)()
            else:
                return False

    def start(self):
        pass

    def end(self):
        pass

    def cancel(self):
        pass

    def enter_start_state(self):
        return self.start()

    def enter_end_state(self):
        return self.end()

    def enter_cancel_state(self):
        return self.cancel()


class RegisterEvent(ICommand):
    """用户状态
    - 等待用户选择活动或确认。
    """
    COMMAND_NAME = u'报名'
    COMMAND_ALIAS = u'er,報名'

    TRANSIT_MAP = {
        'start': (('confirm', {}), ('choose', {}), ('end', {})),
        'confirm': (('end', {'Content': '1'}), ('cancel', {'Content': '0'})),
        'choose': (('end', {}), ('cancel', {'Content': 'c'})),
    }

    def start(self):
        events = Event.objects.filter(start_time__gt=datetime.now())
        self.state.context['events'] = [e.to_dict() for e in events]
        self.state.context['has_info'] = self.user.first_name or \
            self.user.email

    ################ Confirm State ################

    def should_enter_confirm_state(self):
        return len(self.state.context.get('events', [])) == 1 and \
            self.state.context.get('has_info', False)

    def enter_confirm_state(self):
        event = self.state.context['events'][0]
        ct = u'您确认报名参加在%s举行的"%s"？确认请回复1，取消请回复0' % (
            event['start_time'], event['name'])
        return WxTextResponse(ct, self.wxreq)

    ################ Choose State ################

    def should_enter_choose_state(self):
        return len(self.state.context.get('events', [])) > 1 and \
            self.state.context.get('has_info', False)

    def enter_choose_state(self):
        ct = u'目前有多个活动正接受报名，请输入活动序号完成报名,输入c退出:'
        index = 0
        for e in self.state.context['events']:
            ct += u'序号：%d，活动：%s，举办时间：%s' %\
                  (index, e['name'], e['start_time'])
            index += 1
        return WxTextResponse(ct, self.wxreq)

    ################ End State ################

    def should_enter_end_state(self):
        if self.state.state == 'start':
            return (not self.state.context.get('events', [])) or \
                   (not self.state.context.get('has_info', False))
        elif self.state.state == 'choose':
            if self.wxreq.MsgType == 'text':
                try:
                    return int(self.wxreq.Content) in \
                        range(len(self.state.context['events']))
                except:
                    return False
            else:
                self.state.context['error'] = u'请输入文字'
        return False

    def end(self):
        if self.state.state == 'start':
            if self.state.context['has_info']:
                return WxTextResponse(u'近期暂无活动，感谢您的关注',
                                      self.wxreq)
            else:
                return WxTextResponse(u'您的个人资料不齐，请回复ei补全再报名',
                                      self.wxreq)
        elif self.state.state == 'choose' or self.state.state == 'confirm':
            index = int(self.wxreq.Content) if \
                self.state.state == 'choose' else 0
            event = self.state.context['events'][index]
            pt = Participate(user=self.user, event_id=event['id'])
            try:
                pt.save()
            except IntegrityError:
                info = sys.exc_info()
                print info[0], info[1], info[2]
            except:
                return WxTextResponse(u'小子你摊上事儿了，报名不成功，到微博' +
                                      u'找@jeff_kit 帮你搞定吧！', self.wxreq)
            ct = u'您已成功报名"%s",敬请留意邀请邮件。' % event['name']
            return WxTextResponse(ct, self.wxreq)

    def cancel(self):
        return WxTextResponse(u'您已取消报名,感谢关注', self.wxreq)


class RegisterConfirm(ICommand):
    COMMAND_NAME = u'确认报名'
    COMMAND_ALIAS = u'rc'

    TRANSIT_MAP = {
        'start': (('confirm', {}), ('choose', {}), ('end', {})),
        'confirm': (('end', {'Content': '1'}), ('cancel', {'Content': '0'})),
        'choose': (('end', {}), ('cancel', {'Content': 'c'})),
    }

    def pt2dict(self, pt):
        return {
            'id': pt.id,
            'event': pt.event.name
        }

    def start(self):
        pts = Participate.objects.filter(user=self.user, status=1,
                                         event__start_time__gt=datetime.now())
        self.state.context['pts'] = [self.pt2dict(pt) for pt in pts]

    def should_enter_confirm_state(self):
        """如果只有一个活动就直接确认了。
        """
        return len(self.state.context.get('pts', [])) == 1

    def enter_confirm_state(self):
        """让用户确认报名还是取消报名
        """
        print 'enter confirm state'
        pt = self.state.context['pts'][0]
        event = Event.objects.get(id=pt['id'])
        ct = u"""您确认出席“%s”活动吗？
地址：%s
时间：%s
场地人均消费：%d元
出席请回复1，取消请回复0:""" % (event.name, event.address,
                            event.start_time, event.fee)
        return WxTextResponse(ct, self.wxreq)

    def should_enter_choose_state(self):
        return len(self.state.context.get('pts', [])) > 1

    def enter_choose_state(self):
        print 'enter choose state'
        ct = u'目前有多个活动需要确认，请输入序号，回复c退出:'
        index = 0
        for pt in self.state.context['pts']:
            ct += u'序号: %d, 活动：%s' % (index, pt['event'])
            index += 1
        return WxTextResponse(ct, self.wxreq)

    def should_enter_end_state(self):
        print 'should enter end state?'
        if self.state.state == 'start':
            return not self.state.context.get('pts', [])
        elif self.state.state == 'choose':
            if self.wxreq.MsgType == 'text':
                try:
                    return int(self.wxreq.Context) in \
                        range(len(self.state.ontext['pts']))
                except:
                    return False
            else:
                self.state.context['error'] = u'请输入文字'

    def end(self):
        print ''
        if self.state.state == 'start':
            return WxTextResponse(u'未找到需要确认的活动', self.wxreq)
        else:
            index = int(self.wxreq.Content) if \
                self.state.state == 'choose' else 0
            pt = self.state.context['pts'][index]
            name = pt['event']
            pt = Participate.objects.get(id=pt['id'])
            pt.status = 3
            pt.save()

            ct = u'您已确认参加"%s"，届时请准时出席。' % name
            return WxTextResponse(ct, self.wxreq)

    def cancel(self):
        return WxTextResponse(u'已取消确认。', self.wxreq)


class ProfileEdit(ICommand):
    """修改用户的个人资料。
    用户昵称及Email是必填项。
    """
    COMMAND_NAME = u'修改资料'
    COMMAND_ALIAS = u'ei,edit'

    TRANSIT_MAP = {
        'start': (('edit', {}),),
        'edit': (('end', {}), ('cancel', {'Content': 'c'})),
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
        data = self.state.context.get('data', {})
        index = 0
        for field in self.PROFILE_FIELDS:
            if field[0] not in data.keys():
                return index
            index += 1
        return -1

    def start(self):
        self.state.context['original_data'] = {'name': self.user.first_name,
                                               'email': self.user.email}

    def should_enter_edit_state(self):
        return True

    def enter_edit_state(self):
        """
        会有多次进入该状态。每次判断修改到哪个信息了，显示不同的提示。
        """
        data = self.state.context.get('data', {})
        original = self.state.context['original_data']
        for field in self.PROFILE_FIELDS:
            if field[0] not in data.keys():
                ct = u'请输入%s:' % field[1]
                if original.get(field[0], ''):
                    ct = u'请输入%s (原%s，输入s跳过此项):' % \
                         (field[1], original[field[0]])
                return WxTextResponse(ct, self.wxreq)

    def should_enter_end_state(self):
        """
        如果未修改完，则继续，否则结束。
        如果用户选择跳过，则进入结束
        """
        next = self.find_next_field()
        if next < 0:
            return True
        if self.wxreq.MsgType != 'text':
            self.state.context['error'] = u'请输入文字'
            return False
        data = self.state.context.get('data', {})
        field = self.PROFILE_FIELDS[next]
        if self.wxreq.Content == 's':
            value = self.state.context['original_data'].get(field[0], '')
            data[field[0]] = value
        elif len(field) > 2:
            error = self.validate_value_for_field(self.wxreq.Content, field[2])
            if error:
                self.state.context['error'] = error
                return False
        if field[0] not in data:
            data[field[0]] = self.wxreq.Content
        self.state.context['data'] = data
        if len(self.PROFILE_FIELDS) - next == 1:
            return True
        if self.state.context.get('error', ''):
            del self.state.context['error']

    def end(self):
        data = self.state.context.get('data', None)
        if not data:
            return WxTextResponse(u'已取消更改', self.wxreq)
        self.user.first_name = data['name']
        self.user.email = data['email']
        self.user.save()
        return WxTextResponse(u'更改个人资料成功！', self.wxreq)

    def cancel(self):
        return WxTextResponse(u'已取消更改个人资料', self.wxreq)


register_cmd(RegisterEvent)
register_cmd(RegisterConfirm)
register_cmd(ProfileEdit)


############## simple command ############

def events(wxreq, user):
    """返回目前正在举行的活动
    """
    evns = Event.objects.filter(start_time__gt=datetime.now())
    if not evns:
        return WxTextResponse(u'近期暂无活动，感谢您的关注', wxreq)
    articles = [WxArticle(Title=e.name, Description='',
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
        names = u'，'.join([u"%s(%s)" % (pt.event.name,
                                        pt.get_status())for pt in pts])
        ct = u'您已经报名参加了 %s' % names
    else:
        ct = u'您目前未报名任何活动'
    return WxTextResponse(ct, wxreq)


register_cmd(events, u'活动', u'e,event')
register_cmd(user_info, u'我', u'i,me')
register_cmd(register_events, u'我的报名', 'r,mr')
