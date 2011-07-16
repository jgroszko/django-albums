from django.http import Http404
from django.shortcuts import get_object_or_404
from albums.models import Album, AlbumItem, Video, Image, AlbumConvertableItem

def get_item_or_404(album_slug=None, item_slug=None):
    album = get_object_or_404(Album, slug=album_slug)

    if item_slug is None:
        return album

    try:
        item = AlbumConvertableItem.objects.get(parent=album, slug=item_slug)

        try:
            return Video.objects.get(id=item.id)
        except Video.DoesNotExist:
            pass

        return Image.objects.get(id=item.id)
        
    except AlbumConvertableItem.DoesNotExist:
        raise Http404
