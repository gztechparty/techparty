
from django.conf.urls import patterns, url

from techparty.lecturer import views

urlpatterns = patterns('',
    url(r'^$', views.lecturer_list_view, name='lecturer_list_view'),
)