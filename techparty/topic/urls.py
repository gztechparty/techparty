#encoding=utf-8

from django.conf.urls import patterns, url

from techparty.topic import views

urlpatterns = patterns('',
    url(r'^$', views.topic_list_view, name='topic_list_view'),

)