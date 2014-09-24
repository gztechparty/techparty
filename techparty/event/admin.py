#encoding=utf-8

from django.contrib import admin
from django.core.mail import send_mail
from django.template import Template, Context
from django.conf import settings
from techparty.event.models import Event
from techparty.event.models import Participate
from techparty.event.models import Photo
from techparty.event.models import Topic
from datetime import datetime
from uuid import uuid4


class PhotoAdmin(admin.ModelAdmin):
    pass


class TopicInline(admin.StackedInline):
    model = Topic
    extra = 2


class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'area', 'hashtag',
                    'start_time', 'end_time')
    inlines = [TopicInline]
    search_fields = ('name', 'description', 'slug', 'hashtag')
    list_filter = ('start_time', 'area')


class ParticipateAdmin(admin.ModelAdmin):

    def invite_user(modeladmin, request, queryset):
        from techparty.wechat import tasks
        qs = queryset.filter(status__in=(0, 2))
        for pt in qs:
            pt.confirm_key = uuid4().get_hex()
            pt.checkin_key = uuid4().get_hex()
            tasks.invite_user.delay(pt)
            pt.status = 1
            pt.save()

    def reject_user(modeladmin, request, queryset):
        qs = queryset.filter(status__in=(0, 1))

        for pt in qs:
            print 'will send mail'
            send_mail(u'珠三角技术沙龙遗憾地通知您', reject_msg(pt),
                      'techparty.org@gmail.com',
                      [pt.user.email], fail_silently=False)
        qs.update(status=2)

    def markas_checkin(modeladmin, request, queryset):
        queryset.update(status=4, checkin_time=datetime.now())

    def markas_paid(modeladmin, request, queryset):
        queryset.update(paid=True, pay_time=datetime.now())

    invite_user.short_description = u'邀请用户'
    reject_user.short_description = u'拒绝用户'
    markas_checkin.short_description = u'标记为已签到'
    markas_paid.short_description = u'标记为已收费'

    list_display = ('username', 'event', 'reason',
                    'signup_time', 'status', 'paid')
    list_filter = ('event', 'status')
    actions = [invite_user, reject_user, markas_checkin, markas_paid]


admin.site.register(Event, EventAdmin)
admin.site.register(Participate, ParticipateAdmin)
admin.site.register(Photo, PhotoAdmin)


def reject_msg(pt):
    tpl = Template(settings.REJECT_MSG)
    return tpl.render(Context({'user': pt.user, 'event': pt.event,
                               'participate': pt}))
