from django.contrib.syndication.views import Feed
from app import models

class LatestVideoFeed(Feed):
    title = "AFL Latest Videos"
    link = "/video/"
    description = "Latest Video"

    def items(self):
        return models.Video.objects.order_by('-date')[:10]

    def item_title(self, item):
        return item.name

    def item_description(self, item):
        return "Desc"

    def item_link(self, item):
        return item.urls[2]
