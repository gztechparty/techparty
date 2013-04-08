#encoding=utf-8
from django.db import models
from django.db.models.signals import post_save, post_delete
from wechat.official import WxTextResponse
from wechat.official import WxMusicResponse
from wechat.official import WxNewsResponse
from wechat.official import WxMusic, WxArticle
from jsonfield import JSONField
import pylibmc
cache = pylibmc.Client()


class Command(models.Model):
    """预定义自动应答
    """
    name = models.CharField(max_length=20)
    alias = models.CharField(max_length=50, blank=True, null=True)
    rsp_type = models.CharField(choices=(('text', '文本'), ('music', '音乐'),
                                         ('news', '图文')), max_length=10)
    precise = models.BooleanField(default=True)
    text = models.TextField(blank=True, null=True)
    music_title = models.CharField(max_length=200, blank=True, null=True)
    music_description = models.CharField(max_length=200, blank=True, null=True)
    music_url = models.URLField(blank=True, null=True)
    music_url_hq = models.URLField(blank=True, null=True)
    create_time = models.DateTimeField(auto_now_add=True)
    fire_times = models.IntegerField(default=0)
    articles = models.ManyToManyField('Article', blank=True, null=True)

    def __unicode__(self):
        return u'%s (%s)' % (self.name, self.alias)

    def as_response(self, req):
        if self.rsp_type == 'text':
            return WxTextResponse(self.text, req)
        elif self.rsp_type == 'music':
            return WxMusicResponse(self.music, req)
        elif self.rsp_type == 'news':
            return WxNewsResponse(self.news, req)

    def music(self):
        return WxMusic(Title=self.music_title,
                       Description=self.music_description,
                       MusicUrl=self.music_url,
                       HQMusicUrl=self.music_url_hq)

    def news(self):
        return [WxArticle(Title=article.title,
                          Description=article.description,
                          Url=article.url,
                          PicUrl=article.image)
                for article in self.articles]

    class Meta:
        verbose_name = u'自动应答'
        verbose_name_plural = u'自动应答'


class Article(models.Model):
    title = models.CharField(max_length=200)
    description = models.CharField(max_length=500)
    image = models.URLField(blank=True, null=True)
    url = models.URLField()
    create_time = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return self.title

    class Meta:
        verbose_name = u'图文资源'
        verbose_name_plural = u'图文资源'


class UserState(models.Model):
    user = models.CharField(max_length=200, db_index=True)
    command = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(blank=True, null=True)
    context = JSONField(blank=True, null=True)

    def __unicode__(self):
        return u'%s@%s' % (self.user, self.state)

    class Meta:
        verbose_name = u'用户状态'
        verbose_name_plural = u'用户状态'


def clean_command_cache(sender, instance, *args, **kwargs):
    cache.delete('buildin_commands')

post_save.connect(clean_command_cache, Command, dispatch_uid='clean_command')
post_delete.connect(clean_command_cache, Command,
                    dispatch_uid='clean_command_2')
