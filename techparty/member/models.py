#encoding=utf-8
import re
from django.db import models
from django.core import validators
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.utils import timezone
from jsonfield import JSONField
from tagging.fields import TagField
from tagging.models import Tag
from uuid import uuid4


class MemberManager(BaseUserManager):
    def create_user(self, username, password, **extra_fields):
        user = self.model(
            username=username,
            is_staff=False,
            is_active=True,
            is_superuser=False,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_random_user(self):
        return self.create_user(uuid4().get_hex(),
                                None)

    def create_superuser(self, username,
                         password):
        user = self.create_user(username,
                                password
                                )
        user.is_staff = True
        user.is_active = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(
        u'登录名', max_length=30, unique=True,
        validators=[
            validators.RegexValidator(re.compile('^[\w.@+-]+$'),
                                      u'要求英文、数字或及下划线', 'invalid')
        ])
    first_name = models.CharField(u'名字', max_length=30, blank=True)
    last_name = models.CharField(u'姓氏', max_length=30, blank=True)
    email = models.EmailField(u'邮箱', blank=True, unique=True)
    description = models.TextField(u'个人简介', blank=True, null=True)
    tags = TagField(u'标签')

    avatar = models.URLField(u'头像', blank=True, null=True)

    is_lecturer = models.BooleanField(u'讲师', default=False)

    birth_date = models.DateTimeField(null=True, blank=True)
    gendar = models.IntegerField(default=0,
                                 choices=((2, u'女'), (1, u'男'),
                                          (0, u'未知')))
    company = models.CharField(u'公司', max_length=100, blank=True, null=True)
    title = models.CharField(u'职位', max_length=50, blank=True, null=True)

    is_staff = models.BooleanField(u'是否组委', default=False,
                                   help_text='flag for log into admin site.')
    is_active = models.BooleanField(u'是否可用', default=True)

    extra_data = JSONField(blank=True, null=True)

    date_joined = models.DateTimeField(u'加入时间', default=timezone.now)

    USERNAME_FIELD = 'username'
    objects = MemberManager()

    @property
    def name(self):
        return self.username

    @property
    def nickname(self):
        return self.first_name

    def get_full_name(self):
        return self.nickname

    def get_short_name(self):
        return self.name

    def get_tags(self):
        return Tag.objects.get_for_object(self)

    def __unicode__(self):
        return self.nickname or str(self.pk)

    class Meta:
        verbose_name = u'用户'
        verbose_name_plural = u'用户'
        db_table = 'auth_user'


class UserLink(models.Model):
    user = models.ForeignKey(User, verbose_name=u'用户')
    url = models.URLField(u'链接')
    title = models.CharField(u'名称', max_length=50)
    sequence = models.IntegerField(u'顺序', default=0)

    def __unicode__(self):
        return self.title

    class Meta:
        verbose_name = u'用户链接'
        verbose_name_plural = u'用户链接'
