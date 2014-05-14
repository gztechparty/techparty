#encoding=utf-8

from django.conf.urls import patterns, url

from techparty.event import views

urlpatterns = patterns('',
    url(r'^$', views.event_list_view, name='event_list_view'),
    url(r'^event/(?P<page_id>\d+)/$', views.event_list_view_page, name='event_list_view_page'),
)