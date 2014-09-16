#encoding=utf-8

from social.apps.django_app.default.models import UserSocialAuth
from techparty.celery import app


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
        'http://techparty.qiniudn.com/images/techparty_bg_512.png'
        }]
    rsp = send_message_via_account(account, data)
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
