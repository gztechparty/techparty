#encoding=utf-8

from django.conf.urls import patterns, url

from techparty.lecturer import views

urlpatterns = patterns('',
    url(r'^$', views.lecturer_list_view, name='lecturer_list_view'),
    url(r'^page/(?P<page_id>\d+)/$', views.lecturer_list_view_page, name='lecturer_list_view_page'),
)