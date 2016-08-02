from django.conf.urls import patterns, url

from . import views

urlpatterns = patterns('',
  url(r'^$', views.BattleList.as_view(), name='battle_list'),
  url(r'^new$', views.BattleCreate.as_view(), name='battle_new'),
  url(r'^detail/(?P<pk>\d+)$', views.BattleDetailView.as_view(), name='battle_detail'),
  url(r'^edit/(?P<pk>\d+)$', views.BattleUpdate.as_view(), name='battle_edit'),
  url(r'^delete/(?P<pk>\d+)$', views.BattleDelete.as_view(), name='battle_delete'),
)