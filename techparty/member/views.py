#encoding=utf-8


from django.http import HttpResponse
from django.shortcuts import render
from favorites.models import Favorite
from tagging.models import Tag
from techparty.member.models import User

import json

# Create your views here.

def member_info_detail(request, member_name):
    """ 用户界面详细信息
    """
    member = User.objects.filter(name=member_name).prefetch_related('userlink_set').prefetch_related('topic_set')
    member = member[0]
   
    if member.avatar==None:
        member.avatar = ""

    # 收藏信息
    member.stars = member_collect_info(request, member)

    # 公司信息
    company_str = ''
    if member.company!=None:
        company_str = member.company
    if member.title!=None:
        company_str = company_str + ' ' + member.title
    member.company = company_str

    # 简介
    description_str = ''
    if member.description!=None:
        description_str = member.description
    member.description = description_str

    # 标签
    tags = ''
    tags_list = []
    if member.tags!=None:
        tags = member.tags
        ttags = member.get_tags()
        for item in ttags:
            tags_list.append(item)
    member.tags_list = tags_list

    # 链接
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
    """ 获取讲师的几个topic
    """
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
    """获取讲师的所有topic
    """
    member = User.objects.filter(name=member_name).prefetch_related('userlink_set').prefetch_related('topic_set')
    member = member[0]
    topic_list = member.topic_set.all().order_by('title')
    count = 0
    tmp_list = []
    tmp_list_list = []
    for topic in topic_list:
        tmp_list_list.append(topic)
        count = count + 1
        if count%3==0:
            count = 0
            tmp_list.append(tmp_list_list)
            tmp_list_list = []

    if tmp_list_list:
        tmp_list.append(tmp_list_list)
    member.topic_list = tmp_list

    return render(request, 'member_topic_list.html', {'member':member})


def member_collect_info(request, member):
    """ 讲师的被收藏情况
    """
    response_data = {}
    response_data['stars_color'] = 'black'
    response_data['stars_title'] = '收藏'

    fav_total_user = Favorite.objects.favorites_for_obj(member)
    stars = fav_total_user.count()
    response_data['stars'] = stars

    if not request.user.is_authenticated():
        return response_data

    user = request.user
    fav = Favorite.objects.favorites_obj_of_user(user, member)
    fav_count = fav.count()
    if fav_count>0:
        response_data['stars_color'] = 'gold'
        response_data['stars_title'] = '取消收藏'
    return response_data

def member_collect(request, member_name):
    """ 收藏讲师
    """
    if not request.user.is_authenticated():
        return HttpResponse("")
    
    user = request.user
    member = User.objects.filter(name=member_name)
    member = member[0]    

    fav = Favorite.objects.favorites_obj_of_user(user, member)
    fav_total_user = Favorite.objects.favorites_for_obj(member)
    fav_count = fav.count()
    stars = fav_total_user.count()

    response_data = {}
    response_data['stars_color'] = 'black'
    response_data['stars_title'] = '收藏'
    if fav_count>0:
        Favorite.objects.del_favorite(user, member)
        stars = stars - fav_count
    else:
        Favorite.objects.create_favorite(user, member)
        response_data['stars_color'] = 'gold'
        response_data['stars_title'] = '取消收藏'
        stars = stars + 1
    response_data['stars'] = stars

    return HttpResponse(simplejson.dumps(response_data,ensure_ascii = False)) 



















