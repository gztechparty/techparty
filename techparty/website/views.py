#encoding=utf-8
from django.http import HttpResponse
from django.contrib.auth.models import User
from techparty.event.models import Participate, Event
from datetime import datetime


def confirm_event(request, eid, key):
    """确认参加活动
    """
    username = request.GET.get('i', '')
    if not username:
        return HttpResponse(u'无效的确认请求')
    user = User.objects.filter(username=username)
    if not user:
        return HttpResponse(u'无效的用户')
    user = user[0]
    event = Event.objects.get(id=eid)
    if not event.can_confirm():
        return HttpResponse(u'活动已过期')

    pt = Participate.objects.filter(event=event, confirm_key=key,
                                    user=user)
    if not pt:
        return HttpResponse(u'您并未报名任何活动')
    pt = pt[0]
    pt.confirm_time = datetime.now()
    pt.status = 3
    pt.save()
    return HttpResponse(u'您已经成功确认了参加此活动，请准时出席')
