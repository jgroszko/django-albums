from haystack import site
from haystack.indexes import SearchIndex, CharField, DateTimeField, MultiValueField, IntegerField

from albums.models import AlbumConvertableItem, Album, Video, Image
from tagging.models import Tag

class AlbumItemIndex(SearchIndex):
    text = CharField(document=True, use_template=True)
    title = CharField(model_attr='title')
    created = DateTimeField(model_attr='created')

class AlbumIndex(AlbumItemIndex):
    owners = MultiValueField()
    created = DateTimeField(model_attr='created')

    def prepare_owners(self, object):
        return [u.username for u in object.owners.all()]

site.register(Album, AlbumIndex)

class AlbumConvertableItemIndex(AlbumItemIndex):
    tags = MultiValueField(model_attr='tags')
    submitter = CharField(model_attr='submitter')

    def prepare_tags(self, object):
        return [tag.name for tag in Tag.objects.get_for_object(object)]


class ImageIndex(AlbumConvertableItemIndex):
    def get_queryset(self):
        return Image.objects.filter(preview_ready=True)

site.register(Image, ImageIndex)

class VideoIndex(AlbumConvertableItemIndex):
    length = IntegerField(model_attr='duration')
    
    def get_queryset(self):
        return Video.objects.filter(preview_ready=True, video_ready=True)

site.register(Video, VideoIndex)
