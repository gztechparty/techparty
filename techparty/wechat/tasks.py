#encoding=utf-8

from social.apps.django_app.default.models import UserSocialAuth
from techparty.celery import app
from django.core.mail.backends.smtp import EmailBackend
from django.core.mail import EmailMessage
import tempfile
import qrcode


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
    if rsp:
        message = u'验证过程中出了些问题，请稍后再试...'
    else:
        data = rsp.json()
        if data['errcode'] == 0:
            social = UserSocialAuth.objects.get(uid=openid, provider='weixin')
            social.extra_data.update({'wechat_account': account})
            social.save()
            return
        else:
            message = u'您输入的微信帐号不正确，请重新尝试绑定'
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
    email = EmailMessage(u'珠三角技术沙龙活动邀请', message,
                         'techparty.org@gmail.com',
                         [participate.user.email])
    tmp_path = tempfile.mkstemp(suffix='.png')[1]
    image_data.save(tmp_path)
    email.attach_file(tmp_path)
    email.send()
