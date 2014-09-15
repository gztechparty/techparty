#encoding=utf-8

import requests
from social.apps.django_app.default.models import UserSocialAuth
from django.conf import settings
import json


def validate_wechat_account(account, openid):
    body = """您已成功绑定微信号，感谢您对Techparty的关注与支持!
    """
    data = {
        "touser": account.strip().lower(),
        "news": {
            "articles": [{
                "title": u"您已成功绑定微信号！",
                "description": body,
                'digest': body,
                "picurl":
                'http://wxhelper-media.qiniudn.com/sutui_banner.jpg'}]
        }, }
    data = json.dumps(data)
    headers = {'content-type': 'application/json'}
    url = 'http://wechat.toraysoft.com/api/cgi-bin/message/pictextpreview/'
    params = {'access_token': settings.WECHATLIB_ACCESS_TOKEN}
    rsp = requests.post(url, params=params, data=data, headers=headers)

    if rsp.status_code != 200:
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
        # 通过客服接口下发消息。
        dispatch_message(openid, 'text', message)


def dispatch_message(user, msg_type, content,
                     msg_id=None, channel=None):
    from . utils import _dispatch_message
    _dispatch_message(user, msg_type, content,
                      msg_id, channel)
