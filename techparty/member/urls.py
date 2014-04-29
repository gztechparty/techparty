
from django.conf.urls import patterns, url

from techparty.member import views

urlpatterns = patterns('',
    url(r'^(?P<member_name>\w+)/$', views.member_info_detail, name='member_info_detail'),
)