#encoding=utf-8

import os
import qiniu.conf

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

DEFAULT_PAGE_SIZE = 20

DEBUG = True
TEMPLATE_DEBUG = DEBUG
RUN_ON_SAE = False

ADMINS = (
    ('jeff kit', 'jeff@techparty.org'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'techparty.db',
    },
}

ALLOWED_HOSTS = ['2.techparty.sinaapp.com', 'techparty.sinaapp.com',
                 'techparty.org', 'techparty.sutui.me', 'localhost']


# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'Asia/Shanghai'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'zh-cn'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = False

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = ''

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    #"/base/gump_project/techparty/gztechparty/techparty/static",
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    #    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'z&amp;0r%^c_=-%+m-sw4qgdr5)mlc=t&amp;dz@@9^$yk^z(2hn6okica'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'techparty.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'techparty.wsgi.application'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" 
    # or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

INSTALLED_APPS = (
    'suit',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.comments',
    'django.contrib.contenttypes',
    'django.contrib.messages',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.staticfiles',
    'social.apps.django_app.default',
    'techparty.member',
    'techparty.lecturer',
    'techparty.event',
    'techparty.wechat',
    'techparty.website',
    'tagging',
    'favorites',
    'south',
)

AUTH_USER_MODEL = 'member.User'

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'formatters':{
        'verbose':{
            'format':'%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple':{
            'format': '%(levelname)s %(message)s'
        }
    },
    'handlers': {
        'console':{
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'file':{
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'techparty.log',
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django': {
            'handlers': ['console','file'],
            'level': 'DEBUG',
            'propagate': True,
        },

    }
}


#suit
from django.conf.global_settings import TEMPLATE_CONTEXT_PROCESSORS as TCP
TEMPLATE_CONTEXT_PROCESSORS = TCP + (
    'django.core.context_processors.request',
)

DEBUG_SECRET = 'helloworld'
TECHPARTY_OFFICIAL_TOKEN = ''


# REDIS SETTINGS
REDIS_HOST = '127.0.0.1'
REDIS_PORT = 6379
REDIS_DATABASE = 0
REDIS_PASSWORD = ""

# CELERY SETTINGS
CELERY_BROKER = 'redis://:%s@%s:%d/%d' % (REDIS_PASSWORD, REDIS_HOST,
                                          REDIS_PORT, REDIS_DATABASE)

CACHES = {
    'default': {
        'BACKEND': 'redis_cache.cache.RedisCache',
        'LOCATION': ':'.join((REDIS_HOST, str(REDIS_PORT),
                              str(REDIS_DATABASE))),
        'OPTIONS': {
            'CLIENT_CLASS': 'redis_cache.client.DefaultClient',
            'PASSWORD': REDIS_PASSWORD,
            'SOCKET_TIMEOUT': 5,
        }
    }
}

WECHAT_APP_KEY = ''
WECHAT_APP_SECRET = ''

# EMAIL SETTINGS

EMAIL_BACKEND = 'techparty.email.AsyncEmailBackend'
DEFAULT_FROM_EMAIL = 'notice-bot@techparty.org'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_USER = 'theemial'
EMAIL_HOST_PASSWORD = 'thepassword'
EMAIL_PORT = 587
EMAIL_USE_TLS = True

# SUTUI settings

SUTUI_APP_KEY = ''
SUTUI_SECRET_KEY = ''
SUTUI_ERROR_CHANNEL_ID = 24
SUTUI_INFO_CHANNEL_ID = 11

# QINIU settings

qiniu.conf.ACCESS_KEY = "<YOUR_APP_ACCESS_KEY>"
qiniu.conf.SECRET_KEY = "<YOUR_APP_SECRET_KEY>"

INVITE_MSG = """{{user.first_name}}您好：
    您在珠三角技术沙龙的活动“{{event.name}}”中的报名申请已被接受了，现正式通知您。下面是本次活动的详细情况:

    活动名称：{{event.name}}
    举办时间：{{event.start_time}} 至 {{event.end_time}}
    举办地址：{{event.address}}
    活动费用：{{event.fee}}元/人, 主要用于缴纳场地租用及当天茶点费用。

请点击下面的链接确认前往参加活动，或向珠三角技术沙龙微信公众号发送rc命令进行报名的确认。感谢您的配合。
点击这里确认报名：http://techparty.sutui.me/reg_confirm/{{event.id}}/{{participate.confirm_key}}/?m={{user.email}}&i={{user.username}}

附件是活动现场签到用的二维码，入场时请向负责签到的组委出示该二维码。

------------------
祝一切好！
@珠三角技术沙龙 组委
http://techparty.org
"""

INVITE_MSG_WECHAT = """<p>{{user.first_name}}您好：</p>
    <p>您在珠三角技术沙龙的活动“{{event.name}}”中的报名申请已被接受了，现正式通知您。下面是本次活动的详细情况:</p>
<ul>
    <li>活动名称：{{event.name}}</li>
    <li>举办时间：{{event.start_time}} 至 {{event.end_time}}</li>
    <li>举办地址：{{event.address}}</li>
    <li>活动费用：{{event.fee}}元/人, 主要用于缴纳场地租用及当天茶点费用。</li>
</ul>
<p>以下是活动现场签到用的二维码，请妥善保存该二维码，入场时请向负责签到的组委出示它。<p>

<img src="http://techparty.qiniudn.com/qr/{{event.id}}/{{participate.checkin_key}}.png"/>
"""

REJECT_MSG = """{{user.first_name}}您好：
    很遗憾地通知您，您在珠三角技术沙龙活动“{{event.name}}“中的报名没能通过。
    欢迎继续关注珠三角技术沙龙的其他活动。谢谢。
------------------
祝一切好！
@珠三角技术沙龙 组委
http://techparty.org
"""

try:
    from xsettings import *
    if RUN_ON_SAE:
        from sae_settings import *
except:
    pass
