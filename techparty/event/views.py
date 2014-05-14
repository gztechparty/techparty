#encoding=utf-8
# Create your views here.


from django.shortcuts import render
from django.http import HttpResponse


from techparty.event.models import Event
from techparty.member.models import User
from techparty.member.views import member_collect_info

from techparty.xsettings import *

def event_list_view(request):
    """ 活动列表页面 默认
    """
    return event_list_view_page(request, 1)

def event_list_view_page(request, page_id):
    """ 活动列表页面 第N页
    """
    context = {}
    events_count = Event.objects.filter().count()
    events = Event.objects.filter().order_by('-start_time')

    context["events"] = events
    return render(request, 'event_list.html', context)