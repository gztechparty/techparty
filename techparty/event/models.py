#encoding=utf-8

from django.db import models
from django.conf import settings
from datetime import datetime
import time
from tagging.fields import TagField


class Event(models.Model):
    AREA = ((0, u'广州'),
            (1, u'深圳'), (2, u'珠海'))
    name = models.CharField(u'活动名称', max_length=50)
    description = models.TextField(u'活动内容')
    slug = models.SlugField(u'slug', blank=True, null=True)
    hashtag = models.CharField(u'社交标签', max_length=20,
                               blank=True, null=True)
    tags = TagField(u'标签')
    start_time = models.DateTimeField(u'开始时间')
    end_time = models.DateTimeField(u'结束时间')
    sponsor = models.ForeignKey(settings.AUTH_USER_MODEL,
                                verbose_name=u'发起人',
                                blank=True, null=True)
    area = models.IntegerField(u'城市',
                               choices=AREA)

    # 微信公众号用
    url = models.URLField(u'活动网址', blank=True, null=True)
    image = models.URLField(u'海报', blank=True, null=True)
    address = models.CharField(u'会场', max_length=200, blank=True, null=True)
    fee = models.IntegerField(u'费用', default=0)
    need_subject = models.BooleanField(u'报名需分享主题', default=False)

    create_time = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return self.name

    @property
    def area_name(self):
        return self.AREA[self.area][1]

    def can_confirm(self):
        print type(self.start_time)
        print self.start_time
        print datetime.now()
        return self.start_time > datetime.now()

    def to_dict(self):
        ts = time.strftime('%Y年%m月%d日',
                           self.start_time.timetuple())
        return {
            'name': self.name,
            'description': self.description,
            'id': self.id,
            'start_time': ts.decode('utf-8'),
            'area': self.area,
            'need_subject': self.need_subject,
        }

    class Meta:
        verbose_name = u'活动'
        verbose_name_plural = u'活动'


class Participate(models.Model):
    PT_STATUS = ((0, u'已报名'), (1, u'已邀请'),
                 (2, u'已拒绝'), (3, u'已确认'),
                 (4, u'已签到'))
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=u'用户')
    event = models.ForeignKey(Event, verbose_name=u'活动')
    status = models.IntegerField(u'状态', choices=PT_STATUS,
                                 default=0)
    signup_time = models.DateTimeField(u'报名时间', auto_now_add=True)
    reason = models.TextField(u'理由', blank=True, null=True)
    confirm_time = models.DateTimeField(blank=True, null=True, editable=False)
    pay_time = models.DateTimeField(blank=True, null=True, editable=False)
    checkin_time = models.DateTimeField(blank=True, null=True, editable=False)
    paid = models.BooleanField(default=False, editable=False)
    pay_amount = models.IntegerField(u'费用', default=0)
    confirm_key = models.CharField(max_length=50, blank=True, null=True,
                                   editable=False)
    focus_on = models.CharField(u'分享主题', max_length=128,
                                blank=True, null=True)
    topic = models.CharField(u'分享主题', max_length=128,
                             blank=True, null=True)

    def __unicode__(self):
        return u'%s@%s' % (self.user.first_name, self.event.name)

    def get_status(self):
        return self.PT_STATUS[self.status][1]

    def username(self):
        return self.user.first_name

    class Meta:
        verbose_name = u'参会纪录'
        verbose_name_plural = u'参会纪录'
        unique_together = ('user', 'event')


class Topic(models.Model):
    event = models.ForeignKey(Event, verbose_name=u'活动')
    title = models.CharField(u'标题', max_length=100)
    sub_title = models.CharField(u'副标题', max_length=100)
    tags = TagField(u'标签')

    description = models.TextField(u'简介')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=u'讲师')

    slide_file = models.URLField(u'幻灯文件', blank=True, null=True)
    slide_url = models.URLField(u'在线幻灯', blank=True, null=True)

    def __unicode__(self):
        return self.title

    class Meta:
        verbose_name = u'主题'
        verbose_name_plural = u'主题'


class Photo(models.Model):
    event = models.ForeignKey(Event, verbose_name=u'活动')
    name = models.CharField(u'图片名', max_length=100)
    description = models.CharField(u'描述', max_length=140,
                                   blank=True, null=True)
    uploader = models.ForeignKey(settings.AUTH_USER_MODEL,
                                 verbose_name=u'上传者')
    url = models.URLField(u'地址')
    source = models.IntegerField(u'来源', default=0,
                                 choices=((0, u'后台上传'),
                                          (1, u'直播'),
                                          (2, u'用户上传')))
    is_valid = models.BooleanField(default=1)
    create_time = models.DateTimeField(auto_now_add=True, null=True)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = u'照片'
        verbose_name_plural = u'照片'
