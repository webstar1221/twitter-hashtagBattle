from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

from app import settings
from home import views

urlpatterns = patterns('',
    url(r'^$', views.login, name='login'),
    url(r'^home$', views.home, name='home'),
    url(r'^profile', views.profile, name='profile'),
    # url(r'^battle', views.battle, name='battle'),
    url(r'^battle/', include('battle.urls', namespace='battle')),

    url(r'^tweet', views.tweet, name='tweet'),
    url(r'^query', views.query, name='query'),
    url(r'^media/photo', views.media_photo, name='media_photo'),
    url(r'^media/video', views.media_video, name='media_video'),
    url(r'^media/inspector', views.media_inspector, name='media_inspector'),
    url(r'^media', views.media_video, name='media_video'),
    url(r'^logout$', views.logout, name='logout'),
    url('', include('social.apps.django_app.urls', namespace='social')),

    url(r'^admin/', admin.site.urls),
)

urlpatterns += patterns('', (r'^static/(.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_ROOT}), )
