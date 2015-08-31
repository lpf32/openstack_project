from django.conf.urls import patterns, url
from createvm import views


urlpatterns = patterns('',
		url(r'^login/$', views.login, name="login"),
		url(r'^index/$', views.index, name="index"),
		url(r'^logout/$', views.logout, name="logout"),
		url(r'^create/$', views.create, name="create"),
		url(r'^register/$', views.register, name="register"),
		url(r'^$', views.login, name="login"),
		
		)
