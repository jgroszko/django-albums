import datetime
from models import *
from django.conf import settings
from django.db.models import Count
from django.utils import simplejson
from django.http import HttpResponseRedirect, Http404, HttpResponse, HttpResponseServerError
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.template.loader import render_to_string
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from favorites.models import Favorite
from tagging.models import Tag, TaggedItem
from django.utils.translation import ugettext_lazy as _

from utils import get_item_or_404
from forms import AlbumForm, ImageForm, VideoForm, SmallVideoForm, SelectAlbumForm
from templatetags.video_tags import render_video_player

import tagging.views

def album_edit_required(func):
    def decorate(request, *args, **kwargs):
        item = get_item_or_404(**kwargs)

        if(item.can_edit(request.user)):
            return func(request, *args, **kwargs)
        else:
            return unauthorized(request, item)
    return decorate

def unauthorized(request, album):
    request.user.message_set.create(message="You are not authorized to edit %s" % album.title)
    return HttpResponseRedirect(album.get_absolute_url())

def add_album(request, full_slug=None,
              template='albums/add_album.html',
              template_ajax='albums/add_album_ajax.html'):
    if(request.is_ajax()):
        template = template_ajax
    
    if request.method == 'POST':
        form = AlbumForm(request.POST)

        if form.is_valid():
            album = form.save(commit=False)
            album.save()
            
            album.owners.add(request.user)
            album.save()

            return HttpResponseRedirect(album.get_absolute_url())
    else:
        form = AlbumForm()

    return render_to_response(template, {
            'form': form,
            },
                              context_instance=RequestContext(request))

@album_edit_required
def album_edit(request, album_slug):
    item_from_url = get_item_or_404(album_slug, None)

    if request.method=='POST':
        form = AlbumForm(request.POST, instance=item_from_url)

        if form.is_valid():
            item = form.save()

            return HttpResponseRedirect(item.get_absolute_url())
    else:
        form = AlbumForm(instance=item_from_url)

    return render_to_response('albums/edit_item.html', {
            'item': item_from_url,
            'form': form,
            }, context_instance=RequestContext(request))

@album_edit_required
def albumitem_edit(request, album_slug=None, item_slug=None):
    item_from_url = get_item_or_404(album_slug, item_slug)

    form_class = { Video: VideoForm,
                   Image: ImageForm }[type(item_from_url)]

    show_profile_albums = type(item_from_url) == Image

    if request.method == 'POST':
        form = form_class(request.user, request.POST, instance=item_from_url, show_profile_albums=show_profile_albums)

        if form.is_valid():
            item = form.save(commit=False)

            if(type(item_from_url) is Album and
               'owners' in form.cleaned_data):
                item.owners = form.cleaned_data['owners']

            if(type(item_from_url) is not Album):
                orig = AlbumConvertableItem.objects.get(id=item.id)
                if(orig.parent != item.parent and
                   orig.parent.highlight == orig):
                    orig.parent.bump_highlight()

            item.save()
            
            if item.parent.highlight is None:
                item.parent.highlight = item
                item.parent.save()

            return HttpResponseRedirect(item.get_absolute_url())
    else:
        form = form_class(request.user,
                          instance=item_from_url,
                          show_profile_albums=show_profile_albums)

    return render_to_response('albums/edit_item.html', {
            'form': form,
            'item': item_from_url},
                              context_instance=RequestContext(request))

@album_edit_required
def albumitem_highlight(request, album_slug, item_slug):
    item_from_url = get_item_or_404(album_slug, item_slug)

    album = item_from_url.parent.album
    album.highlight = item_from_url
    album.save()
    
    if request.is_ajax():
        return HttpResponse("Success", mimetype='text/plain')
    else:
        return HttpResponseRedirect(item_from_url.get_absolute_url())

@login_required
def albumitem_toggle_favorite(request, album_slug, item_slug):
    item_from_url = get_item_or_404(album_slug, item_slug)

    favorite = Favorite.objects.toggle(request.user, item_from_url)

    if request.is_ajax():
        return HttpResponse(favorite, mimetype='text/plain')
    else:
        return HttpResponseRedirect(item_from_url.get_absolute_url())

def add_videos(request,
               album_slug=None,
               form_class=SmallVideoForm,
               template='albums/add_videos.html',
               file_field_name='video',
               upload_url='albums_add_videos',
               show_profile_albums=False):
    initial = {}
    if album_slug is not None:
        album = get_item_or_404(album_slug)
        initial['parent'] = album
            
    if request.method == 'POST':
        form = form_class(request.POST, request.FILES)
                
        if(form.is_valid()):
            aci = form.save(commit=False)
            aci.submitter = request.user
            aci.save()
                    
            return HttpResponse(aci.parent.get_absolute_url())        
        else:
            return HttpResponseServerError(form.errors)
                
    else:
        form = form_class()
                
    upload_url_resolved = request.build_absolute_uri(reverse(upload_url))
    if(request.META['SERVER_PORT'] == "443"):
        upload_url_resolved = "https" + upload_url_resolved[4:]
                    
    return render_to_response(template, {
            'album_form': SelectAlbumForm(request.user,
                                          show_profile_albums=show_profile_albums,
                                          initial=initial),
            'form': form,
            'upload_url': upload_url_resolved,
            'file_field_name': file_field_name,
            }, context_instance=RequestContext(request))

@require_POST
def albumconvertableitem_status(request, album_slug, item_slug):
    albumitem = get_item_or_404(album_slug, item_slug)
    
    requested_size = int(request.POST['size'])
    
    data = {'id': '%s_%s' % (album_slug, item_slug),
            'url': reverse('albums_thumbstatus', args=[album_slug, item_slug]),
            'size': requested_size}

    if(albumitem.preview_ready):
        data['thumb'] = render_to_string('albums/albumitem_thumb.html', {'thumb_url': albumitem.thumbnail(requested_size),
                                                                         'size': requested_size,
                                                                         'alt': albumitem.title})

    return HttpResponse(simplejson.dumps(data))

@require_POST
def video_status(request, album_slug, item_slug):
    video = get_item_or_404(album_slug, item_slug)

    if(type(video) is not Video):
        raise Http404

    data = {'url': reverse('albums_video_status', args=[album_slug, item_slug]),}

    if(video.video_ready):
        data['player'] = render_video_player(RequestContext(request), video)

    return HttpResponse(simplejson.dumps(data))

def albums_list(request):
    children = Album.objects.browse().order_by('-created')

    return render_to_response('albums/albums_list.html',
                              {'object_list': children,
                               'title': _("Albums"),
                               },
                              context_instance=RequestContext(request))

def albums_list_user(request, username):
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        raise Http404

    children = Album.objects.browse().filter(owners=user).order_by('created')

    return render_to_response('albums/albums_list.html', 
                              {'object_list': children,
                               'title': _("%s's Albums") % username,
                               'add_album': True,
                               },
                              context_instance=RequestContext(request))

def albums_list_favorites_user(request, username):
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        raise Http404

    favorites = Favorite.objects.for_user(user, [Video, Image])

    return render_to_response('albums/albums_list.html',
                              {'object_list': favorites,
                               'title': _("%s's Favorites") % username,
                               },
                              context_instance=RequestContext(request))

def albums_recent_uploads_user(request, username):
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        raise Http404
    
    items = AlbumConvertableItem.objects.filter(submitter=user).order_by('-created')[:40]

    return render_to_response('albums/albums_list.html',
                              {'object_list': items,
                               'title': _("%s's Recent Uploads") % username,
                               },
                              context_instance=RequestContext(request))

def albums_appearances(request, username):
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        raise Http404

    ctypes = (ContentType.objects.get_for_model(Video),
              ContentType.objects.get_for_model(Image))
    appearances = Appearance.objects.filter(user=user,
                                            content_type__in=ctypes)

    items = [a.to_object for a in appearances]

    return render_to_response('albums/albums_list.html',
                              {'object_list': items,
                               'title': _("%s's Appearances") % username,
                               },
                              context_instance=RequestContext(request))


def album(request, album_slug=None):
    album = get_object_or_404(Album, slug=album_slug)

    children = album.children.order_by('created')

    dictionary = {
        'object': album,
        'can_edit': album.can_edit(request.user),
        'can_add_video': album.can_add_video(request.user),
        'can_delete': album.can_delete(request.user),
        'children': children,
        }

    return render_to_response('albums/album_detail.html', dictionary,
                              context_instance=RequestContext(request))


def albumitem(request, album_slug=None, item_slug=None):
    object = get_item_or_404(album_slug, item_slug)

    template = {Image: 'albums/image_detail.html',
                Video: 'albums/video_detail.html'}[type(object)]

    user_vote = object.rating.get_rating_for_user(request.user, None)
    if user_vote is None:
        user_vote = 0

    dictionary = {
        'object': object,
        'parent': object.parent,
        'is_favorite': Favorite.objects.exists(request.user, object),
        'user_vote': user_vote,
        'can_edit': object.can_edit(request.user),
        'next': object.get_next(),
        'previous': object.get_previous()
        }

    return render_to_response(template, dictionary,
                              context_instance=RequestContext(request))

@album_edit_required
def albumitem_delete(request, album_slug=None, item_slug=None):
    object = get_item_or_404(album_slug, item_slug)

    if(hasattr(object, 'can_delete') and
       not object.can_delete(request.user)):
        raise Http404        

    if(request.method == 'POST' and
        request.POST['action'] == 'delete'):
        if hasattr(object, 'parent'):
            return_url = object.parent.get_absolute_url()
        else:
            return_url = reverse("albums")

        object.delete()

        return HttpResponseRedirect(return_url)

    return render_to_response('albums/albumitem_delete.html',
                              { 'object': object },
                              context_instance=RequestContext(request))

def albumconvertableitem_vote(request, album_slug, item_slug, user_vote):
    object = get_item_or_404(album_slug, item_slug)

    if(request.is_ajax() and
       object.allow_ratings):
        object.rating.add(score=user_vote, user=request.user, ip_address=request.META['REMOTE_ADDR'])

        rating_html = render_to_string('albums/rating_block.html',
                                       {'object': object,
                                        'user_vote': user_vote},
                                       context_instance=RequestContext(request))
        
        return HttpResponse(simplejson.dumps({'success': True,
                                              'user_vote': user_vote,
                                              'rating_html': rating_html}),
                            mimetype="application/json")

    else:
        return HttpResponseRedirect(object.get_absolute_url())

def albums(request, classtype=AlbumConvertableItem, title=None):
    top_rated = classtype.objects.filter(rating_votes__gt=0, allow_ratings=True).order_by('-rating_votes')

    most_recent = classtype.objects.filter(preview_ready=True).order_by('-created')

    ctype = ContentType.objects.get_for_model(classtype)
    top_tags = Tag.objects.filter(items__content_type=ctype).distinct().annotate(Count('items')).order_by('-items__count')

    return render_to_response('albums/albums.html',
                              {'title': title,
                               'top_rated': top_rated,
                               'most_recent': most_recent,
                               'top_tags': top_tags},
                              context_instance=RequestContext(request))

def tagged_object_list(request, tag):
    extra_context = {'title': _("Items tagged %s") % tag
                     }
    
    return tagging.views.tagged_object_list(request, tag=tag,
                                            queryset_or_model=AlbumConvertableItem,
                                            template_name='albums/albums_list.html',
                                            extra_context=extra_context)
