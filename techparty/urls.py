from django.conf.urls import patterns, include, url
from techparty.wechat.views import TechpartyView

from django.contrib import admin
admin.autodiscover()

urlpatterns = \
    patterns('',
             url(r'^admin/', include(admin.site.urls)),
             url(r'^wechat/$', TechpartyView.as_view()),
             )
