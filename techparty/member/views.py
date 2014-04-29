from django.shortcuts import render
from django.http import HttpResponse

from techparty.member.models import User

# Create your views here.


def member_info_detail(request, member_name):
    member = User.objects.filter(name=member_name).prefetch_related('userlink_set')
    member = member[0]
    member_dict = {}
    member_dict['name'] = member.name
    member_dict['email'] = member.email
    member_dict['stars'] = 0
    company_str = ''
    if member.company!=None:
        company_str = member.company
    if member.title!=None:
        company_str = company_str + ' ' + member.title
    member_dict['company'] = company_str

    description_str = ''
    if member.description!=None:
        description_str = member.description
    member_dict['description'] = description_str

    tags = ''
    if member.tags!=None:
        tags = member.tags
        print "tags type = ", type(member.tags), '\n', member.tags
    member_dict['tags'] = tags

    user_link_list = []
    for user_link in member.userlink_set.all():
        user_link_list.append({'title':user_link.title, 'url':user_link.url})
        print user_link.url, user_link.title
    member_dict['user_link_list'] = user_link_list

    return render(request, 'member_info_detail.html', member_dict)