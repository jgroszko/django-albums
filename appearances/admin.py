from django.core import urlresolvers
from django.contrib import admin
from appearances.models import Appearance

class AppearanceAdmin(admin.ModelAdmin):
    def object_link(obj):
        return '<a href=\"%s\">%s</a>' % (obj.to_object.get_absolute_url(), 
                                          obj.to_object)
    object_link.allow_tags = True

    def user_link(obj):
        return '<a href=\"%s\">%s</a>' % (urlresolvers.reverse('admin:auth_user_change', args=(obj.user.id,)),
                                          obj.user)
    user_link.allow_tags = True
    user_link.short_description = "User"

    list_display = ('status_str', object_link, user_link, 'description', 'created_date', 'updated_date',)
    search_fields = ('user__username',)
    list_filter = ('status', 'created_date', 'updated_date',)
    date_hierarchy = 'updated_date'

admin.site.register(Appearance, AppearanceAdmin)
