#encoding=utf-8

from django.db import models
from django.contrib.auth.models import User
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

    def __unicode__(self):
        return self.name

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
    user = models.ForeignKey(User)
    event = models.ForeignKey(Event)
    status = models.IntegerField(choices=((0, u'已报名'), (1, u'已确认'),
                                          (2, u'已付费'), (3, u'已签到')),
                                 default=0)
    signup_time = models.DateTimeField(auto_now_add=True)
    confirm_time = models.DateTimeField(blank=True, null=True)
    pay_time = models.DateTimeField(blank=True, null=True)
    checkin_time = models.DateTimeField(blank=True, null=True)

    def __unicode__(self):
        return u'%s@%s' % (self.user.first_name, self.event.name)

    class Meta:
        verbose_name = u'参会纪录'
        verbose_name_plural = u'参会纪录'


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
