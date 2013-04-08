#encoding=utf-8

from techparty.event.models import Event
from techparty.event.models import Participate
from techparty.wechat.models import UserState
from datetime import datetime
from wechat.official import WxTextResponse
from django.db import IntegrityError
import sys

interactive_cmds = {}


def register_cmd(command):
    interactive_cmds[command.COMMAND_NAME] = command
    for alias in command.COMMAND_ALIAS.split(','):
        interactive_cmds[alias] = command


class Command(object):

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

    def process(self):
        if not self.state:
            self.state = UserState(user=self.user, command=self.COMMAND_NAME,
                                   state='start', context={})
            self.start()

        assert self.TRANSIT_MAP, 'No TRANSIT_MAP define!'
        branches = self.TRANSIT_MAP.get(self.state.state, '')
        print 'branches of state %s : %s' % (self.state.state, branches)
        if not branches:
            # 做些容错？如果上次的end或cancel没有删除掉。
            return self.end()
        func = None
        for branch in branches:
            if self.should_transit(branch):
                func = 'enter_%s_state' % branch[0]
                print 'check func if exsit: %s' % func
                ret = getattr(self, func)()
                print 'the return result %s ' % ret
                if branch[0] in ('end', 'cancel') and self.state.id:
                    self.state.delete()
                elif branch[0] != 'start':
                    self.state.state = branch[0]
                    self.state.save()
                return ret

        if not func:
            # 不好意思，原地踏步，继续。
            func = 'enter_%s_state' % self.state.state
            retry = '%s_retry' % self.state.state
            self.state.context[retry] = self.state.context.get(retry, 0) + 1
            self.state.save()
            return getattr(self, func)()

    def should_transit(self, branch):
        if branch[1]:
            print u'有对照参数 %s' % branch[1]
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
        print 'enter cancel state'
        return self.cancel()


class RegisterEvent(Command):
    """用户状态
    - 等待用户选择活动或确认。
    """
    COMMAND_NAME = u'报名'
    COMMAND_ALIAS = u'r,reg,報名'

    TRANSIT_MAP = {
        'start': (('confirm', {}), ('choose', {}), ('end', {})),
        'confirm': (('end', {'Content': '1'}), ('cancel', {'Content': '0'})),
        'choose': (('end', {}), ('cancel', {'Content': 'c'})),
        'end': [],
        'cancel': [],
    }

    def start(self):
        events = Event.objects.filter(start_time__gt=datetime.now())
        print 'events %s' % events
        self.state.context['events'] = [e.to_dict() for e in events]

    ################ Confirm State ################

    def should_enter_confirm_state(self):
        return len(self.state.context.get('events', [])) == 1

    def enter_confirm_state(self):
        event = self.state.context['events'][0]
        print event
        ct = u'您确认报名参加在%s举行的"%s"？确认请回复1，取消请回复0' % (
            event['start_time'], event['name'])
        return WxTextResponse(ct, self.wxreq)

    ################ Choose State ################

    def should_enter_choose_state(self):
        return len(self.state.context.get('events', [])) > 1

    def enter_choose_state(self):
        ct = u'目前有两个活动正接受报名，请输入活动序号完成报名:'
        index = 0
        for e in self.state.context['events']:
            ct += u'序号：%d，活动：%s，举办时间：%s' %\
                  (index, e['name'], e['start_time'])
            index += 1
        return WxTextResponse(ct, self.wxreq)

    ################ End State ################

    def should_enter_end_state(self):
        if self.state.state == 'start':
            return not self.state.context.get('events', [])
        elif self.state.state == 'choose':
            if self.wxreq.MsgType == 'text':
                try:
                    return int(self.wxreq.Content) in \
                        range(len(self.state.context['events']))
                except:
                    return False
        return False

    def end(self):
        print 'end this process state: %s' % self.state.state
        if self.state.state == 'start':
            return WxTextResponse(u'近期暂无活动，感谢您的关注', self.wxreq)
        elif self.state.state == 'choose' or self.state.state == 'confirm':
            index = int(self.wxreq.Content) if self.state.state == 'choose' else 0
            event = self.state.context['events'][index]
            pt = Participate(user=self.user, event_id=event['id'])
            try:
                pt.save()
            except IntegrityError:
                print '保存保名出错了？'
                info = sys.exc_info()
                print info[0], info[1], info[2]
            except:
                return WxTextResponse(u'小子你摊上事儿了，报名不成功，到微博' +
                                      u'找@jeff_kit 帮你搞定吧！', self.wxreq)
            ct = u'您已成功报名"%s",敬请留意邀请邮件。' % event['name']
            return WxTextResponse(ct, self.wxreq)

    def cancel(self):
        print 'cancel it!'
        return WxTextResponse(u'您已取消报名,感谢关注', self.wxreq)


register_cmd(RegisterEvent)
