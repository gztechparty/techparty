from django.shortcuts import render
from django.http import HttpResponse

from techparty.member.models import User

# Create your views here.


def lecturer_list_view(request):
    lectures = User.objects.filter(is_lecturer=True).order_by('name')

    context = {}
    lectures_list = []
    for lecture in lectures:
        lecture_dict = {}
        print lecture.name
        lecture_dict["name"] = lecture.name
        if lecture.avatar==None:
            print "lecture.avatar =", lecture.avatar, "lecture_dict['img_url'] = "
            lecture_dict["img_url"] = ""
        else:
            lecture_dict["img_url"] = lecture.avatar.url
        lecture_dict["stars"] = 0
        lectures_list.append(lecture_dict)

    count = 0
    tmp_list = []
    tmp_list_list = []
    for lecture_dict in lectures_list:
        tmp_list_list.append(lecture_dict)
        count = count + 1
        print count
        if count%3==0:
            tmp_list.append(tmp_list_list)
            tmp_list_list = []

    if tmp_list_list:
        tmp_list.append(tmp_list_list)

    for tmp_list_list in tmp_list:
        print "----"
        for lecture_dict in tmp_list_list:
            print lecture_dict["name"]

    context["lectures_list"] = tmp_list
    return render(request, 'lecturer_list.html', context)



