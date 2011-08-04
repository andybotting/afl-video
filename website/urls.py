from django.conf.urls.defaults import *
from django.contrib import admin
from django.conf import settings

from app import views
from app import feeds

admin.autodiscover()

handler500 = 'djangotoolbox.errorviews.server_error'

urlpatterns = patterns('',
	('^_ah/warmup$', 'djangoappengine.views.warmup'),
	(r'^admin/', include(admin.site.urls)),

	# Admin tasks I2bmxS2RAfVmt7C3DBeNHh75Ugqfc66xYFc5tT8JYrW53QDq8rYVGADK
	(r'^update_videos_' + settings.SECRET_URL_KEY + '/', views.update_videos_job),
	(r'^process_channel_' + settings.SECRET_URL_KEY + '/', views.process_channel_job),
#	(r'^retag_videos_' + settings.SECRET_URL_KEY + '/', views.retag_videos_job),
#	(r'^update_rounds_' + settings.SECRET_URL_KEY + '/', views.update_rounds_job),
#	(r'^process_round_' + settings.SECRET_URL_KEY + '/', views.process_round),

	# Pages
	(r'^all/$', views.videos),

	(r'^video/match/(?P<match_id>\d+)/$', views.videos_match),
	(r'^video/(?P<video_id>\d+)/$', views.video),
	(r'^video/$', views.videos),
	(r'^videos/$', views.videos),

	(r'^match/(?P<match_id>\d+)$', views.match),
	(r'^matches/$', views.matches),
	#(r'^matches/(?P<team>\w+)/$', views.matches),

	(r'^teams/$', views.teams),
	(r'^teams/(?P<team>\w+)/$', views.team),
	(r'^news/$', views.videos_type, {'type':'news'}),
	(r'^panel/$', views.videos_type, {'type':'panel'}),

	#(r'^json/', views.json),
	(r'^latest/feed/$', feeds.LatestVideoFeed()),

	(r'^thumb/(?P<size>\w+)/', views.get_thumb),
	('^$', 'django.views.generic.simple.direct_to_template', {'template': 'home.html'}),
)
