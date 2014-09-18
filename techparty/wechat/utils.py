#encoding=utf-8
from wechat.official import WxApi
from gevent.event import AsyncResult
from gevent.coros import BoundedSemaphore
from django.core.cache import cache
from django.conf import settings
import logging
import random
import sys
import json
import requests
from redis_cache import get_redis_connection
from . import tasks

log = logging.getLogger(__name__)

wxapi = WxApi(settings.WECHAT_APP_KEY,
              settings.WECHAT_APP_SECRET,
              api_entry='http://wxl.diange.fm/api/cgi-bin/')

rds = get_redis_connection('default')

ACCESS_TOKEN_CACHE_KEY = 'techparty_wechat_access_token'
ACCESS_TOKEN_REFRESH_FLAG = 'techparty_wechat_token_refreshing'
TOKEN_CHANNEL_SET = 'techparty_wechat_token_channel_set'
TOKEN_CHANNEL_PREFIX = 'techparty_wechat_token_channel_'


class TokenRefresher(object):

    token_result = AsyncResult()
    token_lock = BoundedSemaphore(1)
    is_refreshing_token = False

    @classmethod
    def get_access_token(cls, old_token=None):
        """多个进程/线程并发执行此函数。保证只有一条进程去获取access_token。
        其他进程都通过redis的队列来等到新的token
        """
        wxapi._access_token = None
        test = rds.getset(ACCESS_TOKEN_REFRESH_FLAG, '1')
        if not test:
            # 可能情况，在getset之前一瞬间，前一个并发进程刚发完成并delete key
            # 所以，在此测试一下token是否已经更新，不做无谓的工夫。
            test_token = cache.get(ACCESS_TOKEN_CACHE_KEY)
            if test_token and test_token != old_token:
                rds.delete(ACCESS_TOKEN_REFRESH_FLAG)
                return test_token

            log.info('you are the one! go get the access token!')
            token = wxapi.access_token
            cache.set(ACCESS_TOKEN_CACHE_KEY, token, 7000)
            rds.delete(ACCESS_TOKEN_REFRESH_FLAG)
            # 通知所有等待中的进程，OK了！
            keys = rds.smembers(TOKEN_CHANNEL_SET)
            for key in keys:
                rds.lpush(key, token)
            rds.delete(TOKEN_CHANNEL_SET)
        else:
            log.info('ok, wait for the redis, wait for the token')
            rand = random.randint(10000, 1000000)
            key = TOKEN_CHANNEL_PREFIX + str(rand)
            rds.sadd(TOKEN_CHANNEL_SET, key)
            token = rds.blpop(key, timeout=20)
            if not token:
                rds.srem(TOKEN_CHANNEL_SET, key)
                token = cache.get(ACCESS_TOKEN_CACHE_KEY)
                if not token:
                    log.info('wait for the access token timeout, so sad!')
        return token

    @classmethod
    def refresh_wechat_token(cls):
        token = None
        if cls.is_refreshing_token:
            log.info('somebody refreshing token now, wait here')
            token = cls.token_result.get()
            log.info('got token! %s' % token)
        else:
            cls.token_lock.acquire()
            if cls.is_refreshing_token:
                log.info('miss the lock, wait for the lock')
                token = cls.token_result.get()
                cls.token_lock.release()
            else:
                log.info('get the lock, for the token!')
                cls.token_result = AsyncResult()
                cls.is_refreshing_token = True
                cls.token_lock.release()
                token = cls.get_access_token()
                cls.token_result.set(token)
                cls.is_refreshing_token = None
        return token


def dispatch_message(users, message):
    # 从cache获取access_token
    msg_type = message.msg_type
    content = message.content['content']
    channel = message.channel.name
    log.info('message id :  %s' % message.pk)
    for user in users:
        tasks.dispatch_message.delay(user, msg_type, content,
                                     message.pk, channel)


def _dispatch_message(user, msg_type, content,
                      msg_id=None, channel=None):
    """把消息发到用户的公众号，是推送的核心。
    """

    log.info('_dispatch_message, channel %s' % channel)
    token = cache.get(ACCESS_TOKEN_CACHE_KEY, None)
    log.info('token from cache %s' % token)
    if not token:
        log.info(u'not token found in the cache, grep it again')
        token = TokenRefresher.refresh_wechat_token()
        log.info('new token from wx %s' % token)
        if not token:
            log.error('error when get access token')
            return 'no access token'
    log.info('token to be use %s' % token)
    wxapi._access_token = token

    try:
        while True:
            rs, err = wxapi.send_message(user, msg_type, content)
            log.info('message sent')
            if err:
                log.error('send wechat message error, code %d' % err.code)
                log.error(err.message)
                log.error(content)
                if err.code in (40001, 42001, 40014):
                    log.info('error token, flush it!')
                    cache.delete('sutui_wx_access_token')
                    token = TokenRefresher.refresh_wechat_token()
                    wxapi._access_token = token
                elif err.code == 45015:
                    # 用户48小时内无互动, 通过微信号发送
                    return send_message_via_account(user, msg_type, content,
                                                    msg_id, channel)
                elif err.code == 45002 and msg_type == 'text':
                    # 超长消息, 通过微信号发送
                    return send_message_via_account(user, msg_type, content,
                                                    msg_id, channel)
                else:
                    return 'unknow error'
            else:
                break
    except:
        tp, msg, tb = sys.exc_info()
        log.error(tp)
        log.error(msg)
        import traceback
        traceback.print_tb(tb)
        log.error('send message fail')
        return u'exception occur'


def send_message_via_account(account, msg_type, content):
    if msg_type == 'text':
        content = text_to_article(content)
    elif msg_type == 'news':
        data = {'touser': account, 'news': {'articles': content}}
    else:
        return u'未支持的消息格式'

    data = json.dumps(data)
    headers = {'content-type': 'application/json'}
    url = 'http://wxl.diange.fm/api/cgi-bin/message/pictextpreview/'
    params = {'access_token': TokenRefresher.refresh_wechat_token()}
    rsp = requests.post(url, params=params, data=data, headers=headers)
    if rsp.status_code != 200:
        log.error(u'发送预览出错了 %s' % rsp.text)
        log.error(data)
        return u'未知错误'
    if rsp.json()['errcode'] != 0:
        log.error(u'发送预览出错了 %s' % rsp.json())
        log.error(data)
        return u'错误代码%d' % rsp.json()['errcode']


common_pic = 'http://techparty.qiniudn.com/images/techparty_bg_512.png'


def text_to_article(text):
    """文本转换成图文, 点击查看详情就可以。
    """
    return [{'title': u'你有新消息',
             'description': u'<pre>%s</pre>' % text,
             'digest': text[:100],
             'picurl': common_pic}]
