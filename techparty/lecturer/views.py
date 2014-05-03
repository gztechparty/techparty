from django.shortcuts import render
from django.http import HttpResponse

from techparty.member.models import User

# Create your views here.

DEFAULT_SIZE = 3
def _page(page, query, size=DEFAULT_SIZE):
    return query[(page - 1) * size: page * size]

def lecturer_list_view(request):
    return lecturer_list_view_page(request, 1)

def lecturer_list_view_page(request, page_id):
    context = {}
    lectures_count = User.objects.filter(is_lecturer=True).count()
    lectures = User.objects.filter(is_lecturer=True).order_by('name')

    (context, page) = get_page_info(context, page_id, lectures_count)

    lectures = _page(page, lectures, size=DEFAULT_SIZE)

    lectures_list = []
    for lecture in lectures:
        lecture_dict = {}
        print lecture.name
        lecture_dict["name"] = lecture.name
        if lecture.avatar==None:
            print "lecture.avatar =", lecture.avatar
            lecture_dict["img_url"] = "http://www.w3school.com.cn/i/w3school_logo_white.gif"
        else:
            lecture_dict["img_url"] = lecture.avatar
            print "lecture.avatar =", lecture.avatar
        lecture_dict["stars"] = 0
        lectures_list.append(lecture_dict)

    context["lectures_list"] = get_lecture_list_in_row(lectures_list)
    return render(request, 'lecturer_list.html', context)

def get_lecture_list_in_row(lectures_list):
    count = 0
    tmp_list = []
    tmp_list_list = []
    for lecture_dict in lectures_list:
        tmp_list_list.append(lecture_dict)
        count = count + 1
        print count
        if count%3==0:
            count = 0
            tmp_list.append(tmp_list_list)
            tmp_list_list = []

    if tmp_list_list:
        tmp_list.append(tmp_list_list)
    return tmp_list

def get_page_info(context, page_id, lectures_count):
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



