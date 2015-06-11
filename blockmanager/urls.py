from django.conf.urls import patterns, url
from blockmanager import views


urlpatterns = patterns('',
		url(r'^$', views.index, name="index"),
		url(r'^createblock/$', views.create_block, name="create_block"),
		url(r'^get_vms/$', views.get_vms, name="get_vms"),
		)
