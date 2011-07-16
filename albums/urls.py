from django.conf.urls.defaults import *
from albums.models import AlbumConvertableItem, Video, Image
from albums.forms import SmallImageForm, AlbumsSearchForm

from django.utils.translation import ugettext_lazy as _

import haystack.views

urlpatterns = patterns('',
                       url(r'^$', 'albums.views.albums', {'classtype': Video}, name='albums'),
                       url(r'^photos', 'albums.views.albums', {'classtype': Image, 'title': "Photos"}, name='albums_photos'),

                       url(r'^list/$', 'albums.views.albums_list', name='albums_list'),
                       url(r'^list/(?P<username>([-\w]+))/$', 'albums.views.albums_list_user', name='albums_list_user'),
                       url(r'^list_favorites/(?P<username>([-\w]+))/$', 'albums.views.albums_list_favorites_user', name='albums_list_favorites_user'),

                       url(r'^recent_uploads/$', 'django.views.generic.list_detail.object_list', {'queryset': AlbumConvertableItem.objects.all().order_by('-created')[:40],
                                                                                                  'template_name': 'albums/albums_list.html',
                                                                                                  'extra_context': {'title': _("Recent Uploads")},
                                                                                                  },
                           name='albums_recent_uploads'),
                       url(r'^recent_uploads/(?P<username>([-\w]+))/$', 'albums.views.albums_recent_uploads_user', name='albums_recent_uploads_user'),

                       url(r'^appearances/(?P<username>([-\w]+))/$', 'albums.views.albums_appearances', name='albums_appearances'),
                       
                       url(r'^search/$', haystack.views.SearchView(form_class=AlbumsSearchForm,
                                                                   template="albums/search.html"),
                           name='albums_search'),
                       
                       url(r'^add_album/$', 'albums.views.add_album', name='albums_add'),

                       url(r'^add_videos$', 'albums.views.add_videos', name='albums_add_videos'),
                       url(r'^a/(?P<album_slug>([-\w]+))/add_videos$', 'albums.views.add_videos', name='albums_add_videos'),
                       url(r'^add_photos$', 'albums.views.add_videos', {'form_class': SmallImageForm,
                                                                        'template': "albums/add_photos.html",
                                                                        'upload_url': 'albums_add_photos',
                                                                        'file_field_name': 'preview',
                                                                        'show_profile_albums': True,}, name='albums_add_photos'),
                       url(r'^a/(?P<album_slug>([-\w]+))/add_photos$', 'albums.views.add_videos', {'form_class': SmallImageForm,
                                                                                                   'template': "albums/add_photos.html",
                                                                                                   'upload_url': 'albums_add_photos',
                                                                                                   'file_field_name': 'preview',
                                                                                                   'show_profile_albums': True,}, name='albums_add_photos'),

                       url(r'^ratings$', 'django.views.generic.list_detail.object_list', {'queryset': AlbumConvertableItem.objects.filter(rating_votes__gt=0, allow_ratings=True)
                                                                                          .extra(select={'score': 'rating_score/rating_votes'},
                                                                                                 order_by = ['-score', '-rating_votes'])[:50],
                                                                                          'template_name': 'albums/albums_list.html',
                                                                                          'extra_context': {'title': _("Top Rated")},
                                                                                          },
                           name='albums_ratings'),

                       url(r'^tags$', 'tagging.views.tags_for_object', { 'model': AlbumConvertableItem, 'order_by': '-created', 'template_name': 'albums/tags.html'}, name='albums_tags'),
                       url(r'^tag/(?P<tag>[^/]+)$','albums.views.tagged_object_list', name='albums_tag'),

                       url(r'^a/(?P<album_slug>([-\w]+))/$', 'albums.views.album', name='albums_album'),
                       url(r'^a/(?P<album_slug>([-\w]+))/edit$', 'albums.views.album_edit', name='albums_album_edit'),
                       url(r'^a/(?P<album_slug>([-\w]+))/delete$', 'albums.views.albumitem_delete', name='albums_album_delete'),

                       url(r'^a/(?P<album_slug>([-\w]+))/(?P<item_slug>([-\w]+))/$', 'albums.views.albumitem', name='albums_item'),
                       url(r'^a/(?P<album_slug>([-\w]+))/(?P<item_slug>([-\w]+))/tstatus$', 'albums.views.albumconvertableitem_status', name='albums_thumbstatus'),
                       url(r'^a/(?P<album_slug>([-\w]+))/(?P<item_slug>([-\w]+))/vstatus$', 'albums.views.video_status', name='albums_video_status'),
                       url(r'^a/(?P<album_slug>([-\w]+))/(?P<item_slug>([-\w]+))/highlight_item$', 'albums.views.albumitem_highlight', name='albums_highlight'),
                       url(r'^a/(?P<album_slug>([-\w]+))/(?P<item_slug>([-\w]+))/favorite$', 'albums.views.albumitem_toggle_favorite', name='albums_favorite'),
                       url(r'^a/(?P<album_slug>([-\w]+))/(?P<item_slug>([-\w]+))/add_vote/(?P<user_vote>\d)$', 'albums.views.albumconvertableitem_vote', name='albums_vote'),
                       url(r'^a/(?P<album_slug>([-\w]+))/(?P<item_slug>([-\w]+))/edit$', 'albums.views.albumitem_edit', name='albums_item_edit'),
                       url(r'^a/(?P<album_slug>([-\w]+))/(?P<item_slug>([-\w]+))/delete$', 'albums.views.albumitem_delete', name='albums_item_delete'),
)
