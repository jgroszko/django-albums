from django.contrib import admin
from django.core import urlresolvers
from favorites.models import Favorite

class FavoriteAdmin(admin.ModelAdmin):
    def object_link(obj):
        return '<a href=\"%s\">%s</a>' % (obj.to_object.get_absolute_url(),
                                          obj.to_object)
    object_link.allow_tags = True

    list_display = ('from_user', object_link)

admin.site.register(Favorite, FavoriteAdmin)
