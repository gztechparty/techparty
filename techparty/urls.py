from django.conf.urls import patterns, include, url


from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'techparty.views.home', name='home'),
    # url(r'^techparty/', include('techparty.foo.urls')),

    url(r'^admin/', include(admin.site.urls)),
)
