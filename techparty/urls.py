#encoding=utf-8

from django.conf.urls import patterns, include, url
from techparty.wechat.views import TechpartyView

from django.contrib import admin
admin.autodiscover()

handler500 = 'techparty.website.views.handler500'

urlpatterns = \
    patterns('',
                  url(r'^$', 'techparty.website.views.home'),
                  url(r'^event/$', include('techparty.event.urls', namespace="event")),
                  url(r'^topic/$', include('techparty.topic.urls', namespace="topic")),
                  url(r'^about/$', 'techparty.website.views.about'),
                  url(r'^admin/', include(admin.site.urls)),
                  url(r'^wechat/$', TechpartyView.as_view()),
                  url(r'^reg_confirm/(?P<eid>\d+)/(?P<key>\w+)/$', 'techparty.website.views.confirm_event'),
                  url(r'^lecturer/', include('techparty.lecturer.urls', namespace="lecturer")),
                  url(r'^member/', include('techparty.member.urls', namespace="member")),
                  url(r'^comments/$', include('django.contrib.comments.urls')),
             )
