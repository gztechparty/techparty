#encoding=utf-8
from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from jsonfield import JSONField
from tagging.fields import TagField
from uuid import uuid4


class MemberManager(BaseUserManager):
    def create_user(self, username, password, **extra_fields):
        user = self.model(
            name=username,
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
                                self.make_random_password())

    def create_superuser(self, name=None,
                         password=None, **extra_fields):
        user = self.create_user(name,
                                password,
                                **extra_fields
                                )
        user.is_staff = True
        user.is_active = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    name = models.CharField(u'姓名', max_length=100,
                            unique=True, db_index=True)
    nickname = models.CharField(u'昵称', max_length=100, blank=True, null=True)
    email = models.EmailField(u'邮箱', unique=True)
    description = models.TextField(u'个人简介', blank=True, null=True)
    tags = TagField(u'标签')
    
    avatar = models.URLField(u'头像', blank=True, null=True)

    is_lecturer = models.BooleanField(u'讲师', default=False)

    is_staff = models.BooleanField(u'是否组委', default=False,
                                   help_text='flag for log into admin site.')
    is_active = models.BooleanField(u'是否可用', default=True)

    extra_data = JSONField(blank=True, null=True)

    create_time = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'name'
    objects = MemberManager()

    def get_full_name(self):
        return self.nickname

    def get_short_name(self):
        return self.name

    def __unicode__(self):
        return self.nickname or str(self.pk)

    class Meta:
        verbose_name = u'用户'
        verbose_name_plural = u'用户'


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
