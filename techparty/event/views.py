#encoding=utf-8

from django.http import HttpResponse
from django.shortcuts import render
from techparty.event.models import Event
from techparty.member.models import User
from techparty.member.views import member_collect_info
from techparty.xsettings import *
from django.core.paginator import Paginator
from techparty.website.views import nav_menu
import logging

logger = logging.getLogger("django")

def event_list_view(request):
    """ 活动列表页面 默认
    """
    return event_list_view_page(request, 1)

def event_list_view_page(request, page_id):
    """ 活动列表页面 第N页
    """
    context = {}

    logger.debug("in event_list_view_page")

    events = Event.objects.filter().order_by('-start_time')

    paginator = Paginator(events, DEFAULT_PAGE_SIZE)
    paged_events = paginator.page(page_id)

    context["events"] = paged_events

    context = nav_menu(request,context)

    return render(request, 'event_list.html', context)





"""
def _page(request, objects, size = DEFAULT_PAGE_SIZE, page = 1):
    #按照分页参数获取相应的查询结果

    # page = request.REQUEST.get("page", 1)

    _page = int(page)
    _size = int(request.REQUEST.get("size", DEFAULT_PAGE_SIZE))


    if not _size:
        _size = size

    logger.debug("get page %s", _page)
    logger.debug("get size %s", _size)

    paginator = Paginator(objects, _size)

    return paginator.page(_page)
"""