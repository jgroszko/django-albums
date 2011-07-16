from django.core import urlresolvers
from django.contrib import admin
from models import Album, AlbumConvertableItem, Video, Image

class AlbumAdmin(admin.ModelAdmin):
    def owners(obj):
        return ", ".join(['<a href=\"%s\">%s</a>' %
                          (urlresolvers.reverse('admin:profiles_profile_change', args=(x.get_profile().id,)), x.username)
                          for x in obj.owners.all()])
    owners.allow_tags = True

    def items(obj):
        return obj.children.count()

    list_display = ('title', 'highlight', items, 'is_profile', owners, 'created', 'edited')
    search_fields = ('title', 'owners__username',)
    list_filter = ('created', 'edited', 'owners', 'is_profile')
    date_hierarchy = 'created'

admin.site.register(Album, AlbumAdmin)

class AlbumConvertableItemAdmin(admin.ModelAdmin):
    def rating(obj):
        return obj.rating_score/obj.rating_votes if obj.rating_votes != 0 else 0

    def obj_type(obj):
        if Video.objects.filter(id=obj.id).count():
            return "Video"
        else:
            return "Image"

    def parent(obj):
        return '<a href=\"%s\">%s</a>' % (urlresolvers.reverse('admin:albums_album_change', args=(obj.parent.id,)), obj.parent)
    parent.allow_tags = True
    parent.admin_order_field = 'parent'

    def submitter(obj):
        return '<a href=\"%s\">%s</a>' % (urlresolvers.reverse('admin:auth_user_change', args=(obj.submitter.id,)), obj.submitter)
    submitter.allow_tags = True
    submitter.admin_order_field = 'submitter'

    list_display = (obj_type, 'title',parent,submitter,rating,'created','edited')
    list_display_links = ('title',)
    search_fields = ('title', 'parent__title', 'submitter__username')
    date_hierarchy = 'created'
    list_filter = ('parent', 'submitter', 'appearances', 'created', 'edited')

admin.site.register(AlbumConvertableItem, AlbumConvertableItemAdmin)
admin.site.register(Video, AlbumConvertableItemAdmin)
admin.site.register(Image, AlbumConvertableItemAdmin)
