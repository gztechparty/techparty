#encoding=utf-8

from django.conf.urls import patterns, url

from techparty.member import views

urlpatterns = patterns('',
    url(r'^(?P<member_name>\w+)/$', views.member_info_detail, name='member_info_detail'),
    url(r'^(?P<member_name>\w+)/topiclist/$', views.member_topic_list, name='member_topic_list'),
    url(r'^(?P<member_name>\w+)/collect/$', views.member_collect, name='member_collect'),
)