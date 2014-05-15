#encoding=utf-8

from django.shortcuts import render
from django.http import HttpResponse

from techparty.member.models import User
from techparty.member.views import member_collect_info

from techparty.website.views import nav_menu


# Create your views here.

DEFAULT_SIZE = 9

def _page(page, query, size=DEFAULT_SIZE):
    return query[(page - 1) * size: page * size]

def lecturer_list_view(request):
    """ 讲师列表页面 默认
    """
    return lecturer_list_view_page(request, 1)

def lecturer_list_view_page(request, page_id):
    """ 讲师列表页面 第N页
    """
    context = {}
    lectures_count = User.objects.filter(is_lecturer=True).count()
    lectures = User.objects.filter(is_lecturer=True).order_by('name')

    (context, page) = get_page_info(context, page_id, lectures_count)

    lectures = _page(page, lectures, size=DEFAULT_SIZE)

    lectures_list = []
    for lecture in lectures:
        lecture_dict = {}
        lecture_dict["name"] = lecture.name
        if lecture.avatar==None:
            lecture_dict["img_url"] = "http://placehold.it/200x200"
        else:
            lecture_dict["img_url"] = lecture.avatar
        # 收藏的信息
        lecture_dict["stars"] = member_collect_info(request, lecture)
        lectures_list.append(lecture_dict)

    context["lectures_list"] = get_lecture_list_in_row(lectures_list)

    context = nav_menu(request,context)

    return render(request, 'lecturer_list.html', context)

def get_lecture_list_in_row(lectures_list):
    count = 0
    tmp_list = []
    tmp_list_list = []
    for lecture_dict in lectures_list:
        tmp_list_list.append(lecture_dict)
        count = count + 1
        if count%3==0:
            count = 0
            tmp_list.append(tmp_list_list)
            tmp_list_list = []

    if tmp_list_list:
        tmp_list.append(tmp_list_list)
    return tmp_list

def get_page_info(context, page_id, lectures_count):
    """ 底下分页的显示情况 
    """
    page = page_id
    if page==None:
        page = 1;
    page = int(page)
    context["page"] = page
    context["pre_page"]={}
    context["pre_page"]["visible"] = True
    context["pre_page"]["page"] = page - 1
    context["next_page"]={}
    context["next_page"]["visible"] = True
    context["next_page"]["page"] = page + 1

    page_last = lectures_count/DEFAULT_SIZE + 1
    page_beg = 1
    if page==page_beg:
        context["pre_page"]["visible"] = False
    if page==page_last:
        context["next_page"]["visible"] = False
    context["total_page"] = page_last
    return (context, page)




