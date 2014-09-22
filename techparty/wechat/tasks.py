#encoding=utf-8

from social.apps.django_app.default.models import UserSocialAuth
from techparty.celery import app
from django.core.mail.backends.smtp import EmailBackend
from django.template import Template, Context
from django.core.mail import EmailMessage
from django.conf import settings
import tempfile
import qrcode

import qiniu.rs
import qiniu.io


@app.task(name='validate_wechat_account', ignore_result=True)
def validate_wechat_account(account, openid):
    from . utils import send_message_via_account
    body = """您已成功绑定微信号，感谢您对Techparty的关注与支持!
    """
    data = [{
        "title": u"您已成功绑定微信号！",
        "description": body,
        'digest': body,
        "picurl":
        'http://techparty.qiniudn.com/images/techparty_bg.jpg'
        }]
    rsp = send_message_via_account(account, 'news', data)
    message = None
    if rsp:
        message = rsp
    else:
        social = UserSocialAuth.objects.get(uid=openid, provider='weixin')
        social.extra_data.update({'wechat_account': account})
        social.save()
    if message:
        dispatch_message(openid, 'text', message)


@app.task(name='dispatch_message', ignore_result=True)
def dispatch_message(user, msg_type, content,
                     msg_id=None, channel=None):
    from . utils import _dispatch_message
    _dispatch_message(user, msg_type, content,
                      msg_id, channel)


@app.task(name='send_messages', ignore_result=True)
def send_messages(email_messages):
    """创建一个Django的SMTP Email发送器，在队列中发送。
    """
    backend = EmailBackend()
    backend.send_messages(email_messages)


@app.task(name='invite_user', ignore_result=True)
def invite_user(participate, message):
    """生成用户签到二维码，附件发送至用户邮箱。
    上传图片至七牛，通过图文下发至用户微信。
    """
    image_data = qrcode.make('http://techparty.sutui.me/wxcheckin/%s/' %
                             participate.checkin_key)
    if participate.user.email:
        email = EmailMessage(u'珠三角技术沙龙活动邀请', message,
                             'techparty.org@gmail.com',
                             [participate.user.email])
        tmp_path = tempfile.mkstemp(suffix='.png')[1]
        image_data.save(tmp_path)
        email.attach_file(tmp_path)
        email.send()

    try:
        social = UserSocialAuth.objects.get(provider='weixin',
                                            user=participate.user)
    except:
        return

    if 'wechat_account' not in social.extra_data:
        return

    # 上传至七牛
    policy = qiniu.rs.PutPolicy('techparty')
    uptoken = policy.token()
    tmp_path = tempfile.mkstemp(suffix='.png')[1]
    image_data.save(tmp_path)
    key = 'qr/%d/%s.png' % (participate.event.id, participate.checkin_key)
    _, err = qiniu.io.put_file(uptoken, key, tmp_path)
    if err:
        return
    tpl = Template(settings.INVITE_MSG_WECHAT)
    message = tpl.render(Context({'user': participate.user,
                                  'event': participate.event,
                                  'participate': participate}))
    data = [{
        "title": u"%s亲，诚邀您参加%s" %
        (participate.user.first_name, participate.event.name),
        "description": message,
        'digest': u'恭喜您获得珠三角技术沙龙本次沙龙的参与邀请',
        "picurl":
        'http://techparty.qiniudn.com/images/techparty_bg.jpg'
        }]
    from . utils import send_message_via_account
    send_message_via_account(social.extra_data['wechat_account'],
                             'news', data)
