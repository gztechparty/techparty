#encoding=utf-8

from django.db import models
from django.contrib.auth.models import User
from datetime import datetime
import time


class Event(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField()
    slug = models.SlugField(blank=True, null=True)
    hashtag = models.CharField(max_length=20, blank=True, null=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    sponsor = models.ForeignKey(User, blank=True, null=True)
    area = models.IntegerField(choices=((0, u'广州'),
                                        (1, u'深圳'), (2, u'珠海')))
    url = models.URLField(blank=True, null=True)
    image = models.URLField(blank=True, null=True)
    address = models.CharField(max_length=100, blank=True, null=True)
    fee = models.IntegerField(default=0)

    def __unicode__(self):
        return self.name

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
        }

    class Meta:
        verbose_name = u'活动'
        verbose_name_plural = u'活动'


class Participate(models.Model):
    PT_STATUS = ((0, u'已报名'), (1, u'已邀请'),
                 (2, u'已拒绝'), (3, u'已确认'),
                 (4, u'已签到'))
    user = models.ForeignKey(User)
    event = models.ForeignKey(Event)
    status = models.IntegerField(choices=PT_STATUS,
                                 default=0)
    signup_time = models.DateTimeField(auto_now_add=True)
    confirm_time = models.DateTimeField(blank=True, null=True, editable=False)
    pay_time = models.DateTimeField(blank=True, null=True, editable=False)
    checkin_time = models.DateTimeField(blank=True, null=True, editable=False)
    paid = models.BooleanField(default=False, editable=False)
    confirm_key = models.CharField(max_length=50, blank=True, null=True,
                                   editable=False)

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


class Tweet(models.Model):
    user = models.ForeignKey(User)
    event = models.ForeignKey(Event)
    text = models.CharField(max_length=280, blank=True, null=True)
    image = models.URLField(blank=True, null=True)
    add_time = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return self.text or self.image

    class Meta:
        verbose_name = u'直播推文'
        verbose_name_plural = u'直播推文'
