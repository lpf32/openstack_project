from django.conf.urls import patterns, url
from blockmanager import views


urlpatterns = patterns('',
		url(r'^$', views.index, name="index"),
		url(r'^createblock/$', views.create_block, name="create_block"),
		url(r'^get_vms/$', views.get_vms, name="get_vms"),
		url(r'^mount/$', views.mount, name="mount"),
		url(r'^umount/$', views.umount, name="umount"),
		url(r'^delete/$', views.delete, name="delete"),
		url(r'^search/$', views.search, name="search"),
		url(r'^import/$', views.import_block, name="import"),
		)
