#encoding=utf-8
from wechat.official import WxApi
from gevent.event import AsyncResult
from gevent.coros import BoundedSemaphore
from django.core.cache import cache
from django.conf import settings
import logging
import random
from redis_cache import get_redis_connection
from . import tasks

log = logging.getLogger('django')

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
    got_global_lock = False

    @classmethod
    def get_access_token(cls, old_token=None):
        """多个进程/线程并发执行此函数。保证只有一条进程去获取access_token。
        其他进程都通过redis的队列来等到新的token
        """
        wxapi._access_token = None
        test = rds.getset(ACCESS_TOKEN_REFRESH_FLAG, '1')
        if not test:
            cls.got_global_lock = True
            # 可能情况，在getset之前一瞬间，前一个并发进程刚发完成并delete key
            # 所以，在此测试一下token是否已经更新，不做无谓的工夫。
            test_token = cache.get(ACCESS_TOKEN_CACHE_KEY)
            if test_token and test_token != old_token:
                rds.delete(ACCESS_TOKEN_REFRESH_FLAG)
                cls.got_global_lock = False
                return test_token

            log.info('you are the one! go get the access token!')
            try:
                token = wxapi.access_token
                cache.set(ACCESS_TOKEN_CACHE_KEY, token, 7000)
            except:
                token = None
                log.error(u'error when obtain access_token', exc_info=True)
            finally:
                rds.delete(ACCESS_TOKEN_REFRESH_FLAG)
                cls.got_global_lock = False
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
        """同一线程里的所有协程并发执行此函数，同一时间只能有一个协程能获取。
        """
        token = cache.get(ACCESS_TOKEN_CACHE_KEY)
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
                try:
                    token = cls.get_access_token(token)
                    cls.token_result.set(token)
                except:
                    log.error(u'获取access_token出错了', exc_info=True)
                    if cls.got_global_lock:
                        rds.delete(ACCESS_TOKEN_REFRESH_FLAG)
                        cls.got_global_lock = False
                finally:
                    cls.is_refreshing_token = None
        return token


def token_guarantee(func):
    """保证微信接口的调用均能够得到有效的access_token。
    如果token失败，则重新获取，然后重试一次。
    """

    def wrapped_func(*args, **kwargs):
        token = cache.get(ACCESS_TOKEN_CACHE_KEY, None)
        log.info('token from cache %s' % token)
        if not token:
            log.info(u'not token found in the cache, grep it again')
            token = TokenRefresher.refresh_wechat_token()
            log.info('new token from wx %s' % token)
            if not token:
                log.error('error when get access token')
                return None
        log.info('token to be use %s' % token)
        wxapi._access_token = token
        data, err = func(*args, **kwargs)
        if err and err.code in (40001, 42001, 40014):
            log.info('error token, flush it!')
            cache.delete(ACCESS_TOKEN_CACHE_KEY)
            token = TokenRefresher.refresh_wechat_token()
            wxapi._access_token = token
            data, err = func(*args, **kwargs)
        return data, err

    return wrapped_func


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

    rs, err = token_guarantee(wxapi.send_message)(user, msg_type, content)
    if not err:
        return
    if err.code == 45015:
        # 用户48小时内无互动, 通过微信号发送
        return send_message_via_account(user, msg_type, content,
                                        msg_id, channel)
    elif err.code == 45002 and msg_type == 'text':
        # 超长消息, 通过微信号发送
        return send_message_via_account(user, msg_type, content,
                                        msg_id, channel)
    else:
        return 'unknow error'


def send_message_via_account(account, msg_type, content):
    if msg_type == 'text':
        content = text_to_article(content)
    elif msg_type == 'news':
        data = {'touser': account, 'news': {'articles': content}}
    else:
        return u'未支持的消息格式'
    rsp, error = token_guarantee(wxapi._post)('message/pictextpreview', data)
    if error:
        log.error(u'发送图文出错了 %s' % error.message)
        log.error(data)
        if error.message == 'check friend failed!':
            return u'输入的微信号有误，请重新输入bd进行绑定。'
        return u'验证过程中出了些问题，请稍后再试...'
    if rsp['errcode'] != 0:
        log.error(u'发送图文出错了 %s' % rsp)
        log.error(data)
        return u'验证过程中出了些问题，请稍后再试...'


common_pic = 'http://techparty.qiniudn.com/images/techparty_bg.jpg'


def text_to_article(text):
    """文本转换成图文, 点击查看详情就可以。
    """
    return [{'title': u'你有新消息',
             'description': u'<pre>%s</pre>' % text,
             'digest': text[:100],
             'picurl': common_pic}]


def get_user_detail(openid):
    return token_guarantee(wxapi.user_info)(openid)
