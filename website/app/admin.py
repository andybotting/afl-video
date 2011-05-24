from django.contrib import admin

from app.models import Video
from app.models import Match


class VideoAdmin(admin.ModelAdmin):
	list_display=('name', 'thumbnail', 'date')
	ordering = ['-date']
	search_fields = ['name']

class MatchAdmin(admin.ModelAdmin):
	list_display = ('hometeam', 'awayteam', 'type', 'round', 'date', 'afl_id', 'thumbnail')
	ordering = ['-date']

admin.site.register(Match, MatchAdmin)
admin.site.register(Video, VideoAdmin)
