from django.conf.urls.defaults import *

urlpatterns = patterns('',
                       (r'^$', 'appearances.views.list', {}, 'appearances_list'),
                       (r'^(?P<status>confirmed|ignored|pending)$', 'appearances.views.list', {}, 'appearances_list'),
                       (r'^add$', 'appearances.views.add', {}, 'appearances_add'),
                       (r'^update$', 'appearances.views.update', {}, 'appearances_update'),
)
