#encoding=utf-8

from django.test import TestCase
from django.test import Client
from django.conf import settings
from django.utils import timezone
from django.core.cache import cache

from techparty.event.models import Event
from techparty.event.models import Participate
from techparty.member.models import User

from social.apps.django_app.default.models import UserSocialAuth
from hashlib import sha1
from datetime import datetime
from datetime import timedelta
import time
import random
from lxml import objectify
import pytz
from mock import Mock


def make_user(name='test_user'):
    user = User.objects.create_user('test_user', None)
    user.first_name = 'test'
    user.save()
        
    social = UserSocialAuth(user=user, provider='weixin',
                            uid=name)
    social.save()
    return user

def make_event(name='Test Event'):
    now = timezone.make_aware(datetime.now(),
                              pytz.timezone(settings.TIME_ZONE))
    tomorrow = timezone.make_aware(datetime.now() + timedelta(days=1),
                                   pytz.timezone(settings.TIME_ZONE))
    event = Event(name=name, description='Hello',
                  start_time=datetime.now() + timedelta(hours=1),
                  end_time=datetime.now() + timedelta(days=1),
                  area=0)
    event.save()
    return event

class WechatTestCase(TestCase):
    """微信测试用例
    """

    def setUp(self):
        cache.get = Mock(return_value=None)
        cache.set = Mock()

    def send_text(self, text, user='test_user',
                  command=None, state=None, context=None):
        xml = self.make_command(text, user, command, state, context)
        cli = Client()
        token = settings.TECHPARTY_OFFICIAL_TOKEN
        timestamp = str(time.time())
        nonce = str(random.randint(1000, 9999))
        sign_ele = [token, timestamp, nonce]
        sign_ele.sort()
        signature = sha1(''.join(sign_ele)).hexdigest()
        params = {'timestamp': timestamp,
                  'nonce': nonce,
                  'signature': signature,
                  'echostr': '234'}
        query_string = '&'.join(['%s=%s' % (k, v) for k, v in params.items()])
        rsp = cli.post('/wechat/?' + query_string,
                       data=xml, content_type='text/xml').content
        return rsp

    def make_command(self, text, user='test_user',
                     command=None, state=None, context=None):
        xml = """<xml>
        <ToUserName><![CDATA[techparty]]></ToUserName>
        <FromUserName><![CDATA[%s]]></FromUserName>
        <CreateTime>1400131860</CreateTime>
        <MsgType><![CDATA[text]]></MsgType>
        <Content><![CDATA[%s]]></Content>
        <MsgId>1234567890123456</MsgId>
        """ % (user, text)
        if command:
            xml += '\n<WechatlibCommand><![CDATA[%s]]></WechatlibCommand>' \
                % command
        if state:
            xml += '\n<WechatlibState><![CDATA[%s]]></WechatlibState>' \
                % state
        if context:
            xml += '\n<WechatlibContext><![CDATA[%s]]></WechatlibContext>' \
                % context
        xml += '\n</xml>'
        return xml


class RegisterTestCase(WechatTestCase):
    """用户报名测试用例
    """

    def test_new_user(self):
        """新用户报名，要求其完善个人信息。
        """
        rsp = self.send_text('er')
        print rsp
        self.assertIn('您的个人资料不齐，请回复ei补全再报名', rsp)

    def test_one_event(self):
        """只有一个活动的情况
        """
        make_user('test_user')
        make_event('Hello Event')
        rsp = self.send_text('er', user='test_user')  # step 1
        obj = objectify.fromstring(rsp)
        self.assertIn('您确认报名参加在', rsp)
        self.assertEqual('er', obj.WechatlibCommand)
        self.assertEqual('confirm', obj.WechatlibState)
        context = obj.WechatlibContext

        rsp = self.send_text('1', command='er', state='confirm',
                             context=context)  #step 2
        obj = objectify.fromstring(rsp)
        self.assertIn('您已成功报名"Hello Event"', rsp)
        self.assertEqual('er', obj.WechatlibCommand)
        self.assertEqual('end', obj.WechatlibState)

    def test_mulitiple_event(self):
        """测试多个活动的情况
        """
        make_user('test_user')
        make_event('Hello Event')
        make_event('Hello Event2')
        rsp = self.send_text('er', user='test_user')
        obj = objectify.fromstring(rsp)
        self.assertIn('目前有多个活动正接受报名', rsp)
        self.assertEqual('er', obj.WechatlibCommand)
        self.assertEqual('choose', obj.WechatlibState)
        context = obj.WechatlibContext

        rsp = self.send_text('0', command='er', state='choose',
                             context=context)
        obj = objectify.fromstring(rsp)
        self.assertIn('您已成功报名"Hello Event"', rsp)
        self.assertEqual('er', obj.WechatlibCommand)
        self.assertEqual('end', obj.WechatlibState)

    def test_no_event(self):
        """测试当前无活动的情况
        """
        make_user('test_user')
        rsp = self.send_text('er')
        self.assertIn('近期暂无活动，感谢您的关注', rsp)

    def test_user_cancel(self):
        """测试用户取消
        """
        make_user('test_user')
        make_event('Hello Event')
        rsp = self.send_text('er', user='test_user')
        obj = objectify.fromstring(rsp)
        self.assertIn('您确认报名参加在', rsp)
        self.assertEqual('er', obj.WechatlibCommand)
        self.assertEqual('confirm', obj.WechatlibState)
        context = obj.WechatlibContext

        rsp = self.send_text('0', command='er', state='confirm',
                             context=context)
        self.assertIn('您已取消报名,感谢关注', rsp)

    def test_wrong_input(self):
        """测试用户输入不符合要求的情况
        """
        make_user('test_user')
        make_event('Hello Event')
        rsp = self.send_text('er', user='test_user')
        obj = objectify.fromstring(rsp)
        self.assertIn('您确认报名参加在', rsp)
        self.assertEqual('er', obj.WechatlibCommand)
        self.assertEqual('confirm', obj.WechatlibState)
        context = obj.WechatlibContext

        rsp = self.send_text('c', command='er', state='confirm',
                             context=context)
        self.assertIn('哟·痛·请以正确的姿势回复嘛 ：）', rsp)

        rsp = self.send_text('0', command='er', state='confirm',
                             context=context)
        self.assertIn('您已取消报名,感谢关注', rsp)

class RegisterConfirmTestCase(WechatTestCase):

    def test_no_event(self):
        """测试无活动需确认
        """
        make_user('test_user')
        rsp = self.send_text('rc', user='test_user')
        self.assertIn('未找到需要确认的活动', rsp)
        obj = objectify.fromstring(rsp)
        self.assertEqual('end', obj.WechatlibState)

    def test_one_event(self):
        """测试只有一个活动的情况
        """
        user = make_user('test_user')
        event = make_event('Hello Event')
        pt = Participate(user=user, event=event, status=1)
        pt.save()
        rsp = self.send_text('rc', user='test_user')
        obj = objectify.fromstring(rsp)
        self.assertIn('您确认出席"Hello Event"活动吗？', rsp)
        self.assertEqual('rc', obj.WechatlibCommand)
        self.assertEqual('confirm', obj.WechatlibState)
        context = obj.WechatlibContext

        rsp = self.send_text('1', command='rc', state='confirm',
                             context=context)
        obj = objectify.fromstring(rsp)
        self.assertIn('您已确认参加"Hello Event"，届时请准时出席。', rsp)
        self.assertEqual('rc', obj.WechatlibCommand)
        self.assertEqual('end', obj.WechatlibState)

    def test_mulitiple_event(self):
        """测试有多个活动需确认的情况
        """
        user = make_user('test_user')
        event = make_event('Hello Event')
        pt = Participate(user=user, event=event, status=1)
        pt.save()
        event = make_event('Hello Event2')
        pt = Participate(user=user, event=event, status=1)
        pt.save()

        rsp = self.send_text('rc', user='test_user')
        obj = objectify.fromstring(rsp)
        print rsp
        self.assertIn('目前有多个活动需要确认，请输入序号，回复c退出:', rsp)
        self.assertEqual('rc', obj.WechatlibCommand)
        self.assertEqual('choose', obj.WechatlibState)
        context = obj.WechatlibContext

        rsp = self.send_text('0', command='rc', state='choose',
                             context=context)
        obj = objectify.fromstring(rsp)
        self.assertIn('届时请准时出席', rsp)
        self.assertEqual('rc', obj.WechatlibCommand)
        self.assertEqual('end', obj.WechatlibState)

    def test_user_cancel(self):
        """测试用户取消
        """
        user = make_user('test_user')
        event = make_event('Hello Event')
        pt = Participate(user=user, event=event, status=1)
        pt.save()
        rsp = self.send_text('rc', user='test_user')
        obj = objectify.fromstring(rsp)
        self.assertIn('您确认出席"Hello Event"活动吗？', rsp)
        self.assertEqual('rc', obj.WechatlibCommand)
        self.assertEqual('confirm', obj.WechatlibState)
        context = obj.WechatlibContext

        rsp = self.send_text('0', command='rc', state='confirm',
                             context=context)
        obj = objectify.fromstring(rsp)
        self.assertIn('已取消确认', rsp)
        self.assertEqual('rc', obj.WechatlibCommand)
        self.assertEqual('end', obj.WechatlibState)


class ProfileEditTestCase(WechatTestCase):

    def test_edit(self):
        """测试正常流程
        """

        make_user('test_user')
        
        rsp = self.send_text('ei', 'test_user')
        obj = objectify.fromstring(rsp)
        self.assertIn('请输入姓名', rsp)
        rsp = self.send_text('jeff', 'test_user', command='ei', state='edit',
                             context=obj.WechatlibContext)
        self.assertIn('请输入邮箱', rsp)

        obj = objectify.fromstring(rsp)
        rsp = self.send_text('jeff@techparty.org', 'test_user',
                             command='ei', state='edit',
                             context=obj.WechatlibContext)

        self.assertIn('更改个人资料成功', rsp)
        
        user = User.objects.get(username='test_user')
        self.assertEqual('jeff', user.first_name)
        self.assertEqual('jeff@techparty.org', user.email)

    def test_skip(self):
        """测试正常流程
        """

        user = make_user('test_user')
        user.first_name = 'jeff'
        user.email = 'bbmyth@gmail.com'
        user.save()
        
        rsp = self.send_text('ei', 'test_user')
        obj = objectify.fromstring(rsp)
        self.assertIn('请输入姓名', rsp)
        rsp = self.send_text('S', 'test_user', command='ei', state='edit',
                             context=obj.WechatlibContext)
        self.assertIn('请输入邮箱', rsp)

        obj = objectify.fromstring(rsp)
        rsp = self.send_text('s', 'test_user',
                             command='ei', state='edit',
                             context=obj.WechatlibContext)

        self.assertIn('更改个人资料成功', rsp)
        
        user = User.objects.get(username='test_user')
        self.assertEqual('jeff', user.first_name)
        self.assertEqual('bbmyth@gmail.com', user.email)

    def test_cancel(self):
        user = make_user('test_user')
                
        rsp = self.send_text('ei', 'test_user')
        obj = objectify.fromstring(rsp)
        self.assertIn('请输入姓名', rsp)
        rsp = self.send_text('c', 'test_user', command='ei', state='edit',
                             context=obj.WechatlibContext)
        self.assertIn('已取消更改个人资料', rsp)
