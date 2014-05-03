from django.shortcuts import render
from django.http import HttpResponse

from techparty.member.models import User
from tagging.models import Tag

# Create your views here.

def member_info_detail(request, member_name):
    member = User.objects.filter(name=member_name).prefetch_related('userlink_set').prefetch_related('topic_set')
    member = member[0]
   
    if member.avatar==None:
        member.avatar = "http://www.w3school.com.cn/i/w3school_logo_white.gif"
    member.stars = 0
    company_str = ''
    if member.company!=None:
        company_str = member.company
    if member.title!=None:
        company_str = company_str + ' ' + member.title
    member.company = company_str

    description_str = ''
    if member.description!=None:
        description_str = member.description
    member.description = description_str

    tags = ''
    tags_list = []
    if member.tags!=None:
        tags = member.tags
        ttags = member.get_tags()
        for item in ttags:
            tags_list.append(item)
    member.tags_list = tags_list

    user_link_list = []
    for user_link in member.userlink_set.all():
        user_link_list.append({'title':user_link.title, 'url':user_link.url})
    member.user_link_list = user_link_list

    (topic, topic_more_visual, topic_have) = get_topic(member)
    member.topic = topic
    member.topic_more_visual = topic_more_visual
    member.topic_have = topic_have

    return render(request, 'member_info_detail.html', {'member':member})


MemberTopicDefaultSize = 3
def get_topic(member):
    topic_count = member.topic_set.all().order_by('title').count()
    topic_more_visual = False
    topic_have = False
    if topic_count > MemberTopicDefaultSize:
        topic_more_visual = True
    if topic_count > 0:
        topic_have = True
    topic = member.topic_set.all().order_by('title')
    topic = topic[0:3]
    return (topic, topic_more_visual, topic_have)

def member_topic_list(request, member_name):
    member = User.objects.filter(name=member_name).prefetch_related('userlink_set').prefetch_related('topic_set')
    member = member[0]
    topic_list = member.topic_set.all().order_by('title')
    count = 0
    tmp_list = []
    tmp_list_list = []
    for topic in topic_list:
        tmp_list_list.append(topic)
        count = count + 1
        print count
        if count%3==0:
            count = 0
            tmp_list.append(tmp_list_list)
            tmp_list_list = []

    if tmp_list_list:
        tmp_list.append(tmp_list_list)
    member.topic_list = tmp_list

    return render(request, 'member_topic_list.html', {'member':member})


