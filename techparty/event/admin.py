#encoding=utf-8

from django.contrib import admin
from django.core.mail import send_mail
from django.template import Template, Context
from techparty.event.models import Event
from techparty.event.models import Participate
from datetime import datetime
from uuid import uuid4


class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'area', 'hashtag',
                    'start_time', 'end_time')
    search_fields = ('name', 'description', 'slug', 'hashtag')
    list_filter = ('start_time', 'area')


class ParticipateAdmin(admin.ModelAdmin):

    def invite_user(modeladmin, request, queryset):
        qs = queryset.filter(status__in=(0, 2))
        for pt in qs:
            pt.confirm_key = uuid4().get_hex()            
            send_mail(u'珠三角技术沙龙活动邀请', invite_msg(pt),
                      'techparty.org@gmail.com',
                      [pt.user.email], fail_silently=False)
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

    list_display = ('username', 'event',
                    'signup_time', 'status', 'paid')
    list_filter = ('event', 'status')
    actions = [invite_user, reject_user, markas_checkin, markas_paid]


admin.site.register(Event, EventAdmin)
admin.site.register(Participate, ParticipateAdmin)


INVITE_MSG = """{{user.first_name}}您好：
    您在珠三角技术沙龙的活动“{{event.name}}”中的报名申请已被接受了，现正式通知您。下面是本次活动的详细情况:

    活动名称：{{event.name}}
    举办时间：{{event.start_time}} 至 {{event.end_time}}
    举办地址：{{event.address}}
    活动费用：{{event.fee}}元/人, 主要用于缴纳场地租用及当天茶点费用。

请点击下面的链接确认前往参加活动，或向珠三角技术沙龙微信公众号发送rc命令进行报名的确认。感谢您的配合。
点击这里确认报名：http://2.techparty.sinaapp.com/reg_confirm/{{event.id}}/{{participate.confirm_key}}/?m={{user.email}}&i={{user.username}}

------------------
祝一切好！
@珠三角技术沙龙 组委
http://techparty.org
"""

REJECT_MSG = """{{user.first_name}}您好：
    很遗憾地通知您，您在珠三角技术沙龙活动“{{event.name}}“中的报名没能通过。
    欢迎继续关注珠三角技术沙龙的其他活动。谢谢。
------------------
祝一切好！
@珠三角技术沙龙 组委
http://techparty.org
"""


def invite_msg(pt):
    tpl = Template(INVITE_MSG)
    return tpl.render(Context({'user': pt.user, 'event': pt.event,
                               'participate': pt}))


def reject_msg(pt):
    tpl = Template(REJECT_MSG)
    return tpl.render(Context({'user': pt.user, 'event': pt.event,
                               'participate': pt}))
