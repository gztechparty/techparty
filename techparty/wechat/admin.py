#encoding=utf-8

from django.contrib import admin
from techparty.wechat.models import Command, Article, UserState


class CommandAdmin(admin.ModelAdmin):
    list_display = ('name', 'alias', 'rsp_type', 'precise', 'fire_times')
    list_filter = ('rsp_type', 'precise')
    search_fields = ('name', 'alias')


admin.site.register(Command, CommandAdmin)


class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'image', 'url')
    list_filter = ('create_time',)


admin.site.register(Article, ArticleAdmin)


class UserStateAdmin(admin.ModelAdmin):
    list_display = ('user', 'command', 'state', 'context')
    list_filter = ('command',)


admin.site.register(UserState, UserStateAdmin)
