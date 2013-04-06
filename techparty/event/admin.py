#encoding=utf-8

from django.contrib import admin
from techparty.event.models import Event
from techparty.event.models import Participate


class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'area', 'hashtag',
                    'start_time', 'end_time')
    search_fields = ('name', 'description', 'slug', 'hashtag')
    list_filter = ('start_time', 'area')


admin.site.register(Event, EventAdmin)


class ParticipateAdmin(admin.ModelAdmin):
    list_display = ('user', 'event', 'status')
    list_filter = ('event', 'status')


admin.site.register(Participate, ParticipateAdmin)
