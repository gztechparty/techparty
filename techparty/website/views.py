#encoding=utf-8

from datetime import datetime
from techparty.member.models import User
from django.http import HttpResponse
from django.template import loader
from django.template import Context
from django.http import HttpResponseServerError
from django.shortcuts import render
from django.conf import settings
from techparty.event.models import Participate, Event
import logging
import sys
import traceback
from sutui import Sutui
logger = logging.getLogger("django")

sutui_cli = Sutui(settings.SUTUI_APP_KEY, settings.SUTUI_SECRET_KEY)


def notify(message, error=True):
    channel_id = settings.SUTUI_ERROR_CHANNEL_ID
    if not error:
        channel_id = settings.SUTUI_INFO_CHANNEL_ID
    sutui_cli.notify(channel_id, 'text', message)


def log_err(message=None, report=False, description=''):
    if message:
        logger.error(message)
    exc, msg, tb = sys.exc_info()
    logger.error(exc)
    logger.error(msg)
    logger.error(traceback.format_tb(tb))
    content = '%s \n %s \n %s' % (description, msg, traceback.format_tb(tb))
    if report:
        notify(content)


def handler500(request):
    path = request.get_full_path()
    method = request.method
    data = request.REQUEST

    logger.error('unexcpect exception', exc_info=True)
    logger.error(method + ' ' + path)
    logger.error(data)

    tp, msg, tb = sys.exc_info()
    if msg.args:
        logger.error(msg.args)
    trace = '\n'.join(traceback.format_tb(tb))
    content = '\n'.join((': '.join((method, path.encode('utf-8'))),
                         'Data: ' + str(data),
                         'Exception: ' + str(msg.__class__),
                         'Arguments: ' + str(msg.args),
                         'Traceback: ' + trace))
    try:
        notify(content)
        logger.debug(u'已通过速推通知')
    except:
        log_err(u'速推通知失败')

    t = loader.get_template('500.html')
    return HttpResponseServerError(t.render(Context({
        'exception_value': msg,
    })))


def home(request):
    raise Exception('hey')
    context = {}
    context = nav_menu(request, context)

    return render(request, 'home.html', context)


def about(request):
    context = {}

    context = nav_menu(request, context)
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


def nav_menu(request, context):
    """顶部菜单
    """
    url = request.get_full_path()
    menus = (
        {"title": "主页", "url": "/"},
        {"title": "活动", "url": "/event"},
        {"title": "讲师", "url": "/lecturer"},
        {"title": "主题", "url": "/topic"},
        {"title": "关于", "url": "/about"},
    )

    for i in range(len(menus) - 1, -1, -1):
        menu = menus[i]
        logger.debug("nav_menu i: %s", i)

        if i == 0:
            menu["active"] = True
            break

        if url.startswith(menu["url"]):
            menu["active"] = True
            logger.debug("in event_list_view_page active: %s",
                         menu["active"])
            break

    context["menus"] = menus
    return context
