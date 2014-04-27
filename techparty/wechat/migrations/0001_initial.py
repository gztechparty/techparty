# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Command'
        db.create_table(u'wechat_command', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('alias', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
            ('rsp_type', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('precise', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('text', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('music_title', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True)),
            ('music_description', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True)),
            ('music_url', self.gf('django.db.models.fields.URLField')(max_length=200, null=True, blank=True)),
            ('music_url_hq', self.gf('django.db.models.fields.URLField')(max_length=200, null=True, blank=True)),
            ('create_time', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('fire_times', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal(u'wechat', ['Command'])

        # Adding M2M table for field articles on 'Command'
        m2m_table_name = db.shorten_name(u'wechat_command_articles')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('command', models.ForeignKey(orm[u'wechat.command'], null=False)),
            ('article', models.ForeignKey(orm[u'wechat.article'], null=False))
        ))
        db.create_unique(m2m_table_name, ['command_id', 'article_id'])

        # Adding model 'Article'
        db.create_table(u'wechat_article', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=500)),
            ('image', self.gf('django.db.models.fields.URLField')(max_length=200, null=True, blank=True)),
            ('url', self.gf('django.db.models.fields.URLField')(max_length=200)),
            ('create_time', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal(u'wechat', ['Article'])

        # Adding model 'UserState'
        db.create_table(u'wechat_userstate', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.CharField')(max_length=200, db_index=True)),
            ('command', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('state', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('create_time', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('update_time', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('context', self.gf('jsonfield.fields.JSONField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'wechat', ['UserState'])


    def backwards(self, orm):
        # Deleting model 'Command'
        db.delete_table(u'wechat_command')

        # Removing M2M table for field articles on 'Command'
        db.delete_table(db.shorten_name(u'wechat_command_articles'))

        # Deleting model 'Article'
        db.delete_table(u'wechat_article')

        # Deleting model 'UserState'
        db.delete_table(u'wechat_userstate')


    models = {
        u'wechat.article': {
            'Meta': {'object_name': 'Article'},
            'create_time': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200'})
        },
        u'wechat.command': {
            'Meta': {'object_name': 'Command'},
            'alias': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'articles': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['wechat.Article']", 'null': 'True', 'blank': 'True'}),
            'create_time': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'fire_times': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'music_description': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'music_title': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'music_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'music_url_hq': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'precise': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'rsp_type': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'text': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'})
        },
        u'wechat.userstate': {
            'Meta': {'object_name': 'UserState'},
            'command': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'context': ('jsonfield.fields.JSONField', [], {'null': 'True', 'blank': 'True'}),
            'create_time': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'update_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.CharField', [], {'max_length': '200', 'db_index': 'True'})
        }
    }

    complete_apps = ['wechat']