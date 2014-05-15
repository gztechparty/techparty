#encoding=utf-8

from datetime import datetime
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.shortcuts import render
from techparty.event.models import Participate, Event
import logging



logger = logging.getLogger("django")


def home(request):
    context = { }
    context = nav_menu(request,context)

    return render(request, 'home.html', context)

def about(request):
    context = { }

    context = nav_menu(request,context)
    return render(request, 'about.html', context)


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



def nav_menu(request,context):
    """顶部菜单
    """
    url = request.get_full_path()
    menus = (
        {"title":"主页","url":"/"},
        {"title":"活动","url":"/event"},
        {"title":"讲师","url":"/lecturer"},
        {"title":"主题","url":"/topic"},
        {"title":"关于","url":"/about"},
    )


    for i in range(len(menus) - 1, -1, -1):
        menu = menus[i]
        logger.debug("nav_menu i: %s", i)

        if i == 0:
            menu["active"] = True
            break

        if url.startswith(menu["url"]):
            menu["active"] = True
            logger.debug("in event_list_view_page active: %s" ,menu["active"])
            break

            
    context["menus"] = menus
    return context

