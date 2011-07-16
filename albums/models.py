import os.path
import datetime
from django.conf import settings
from django.db import models
from django.db.models import signals
from djangoratings.fields import RatingField
from appearances.models import Appearance
from favorites.models import Favorite
from django.contrib.auth.models import User
from django.contrib.contenttypes import generic

from django.utils.translation import ugettext_lazy as _

import tagging
from tagging_ext.models import TagAutocompleteField

from django.conf import settings

import albums.tasks as tasks

class AlbumItem(models.Model):
    title = models.CharField(max_length=1000)

    description = models.TextField(null=True, blank=True)

    created = models.DateTimeField()
    edited = models.DateTimeField()

    def __unicode__(self):
        return self.title

    def can_edit(self, user):
        if user.is_staff:
            return True
        elif(Album.objects.filter(id=self.id).count() == 1):
            return self.album.is_owner(user)
        else:
            return self.parent.album.is_owner(user)

def albumitem_save(sender, instance, **kwargs):
    if(instance.id is None):
        instance.created = datetime.datetime.now()
    instance.edited = datetime.datetime.now()

class AlbumConvertableItem(AlbumItem):
    slug = models.SlugField(unique=False,
                            verbose_name='ID', help_text=_('A unique id for this item\'s URL. Only alphanumeric characters allowed.'))

    def get_directory(self):
        ''' /albums/##/## '''
        return os.path.join('albums', str(self.parent.id), str(self.id))

    def get_preview_path(self, filename):
        ''' /site_media/albums/##/## '''
        result = os.path.join(settings.ALBUMS_UPLOAD_TO, self.get_directory(), filename)
        os.mkdir(os.path.dirname(result))
        return result
    preview = models.FileField(upload_to=get_preview_path, null=True, verbose_name="File")
    preview_ready = models.BooleanField(default=False, null=False)

    submitter = models.ForeignKey(User, blank=False)

    parent = models.ForeignKey('Album', related_name='children', null=True)

    rating = RatingField(range=5, can_change_vote=True)

    tags = TagAutocompleteField(help_text=_("Comma or space separated"))

    appearances = generic.GenericRelation(Appearance)
    favorites = generic.GenericRelation(Favorite)

    allow_ratings = models.BooleanField(default=True)
    allow_comments = models.BooleanField(default=True)

    class Meta:
        unique_together = (('slug', 'parent'),)

    def _resized_path(self, size):
        d, f = os.path.split(self.preview.name)
        return os.path.join(d, 'resized', str(size), f)

    def thumbnail(self, size=80):
        try:
            resized_path = self._resized_path(size)
        except AttributeError:
            return os.path.join(settings.MEDIA_URL,
                                "failed.png")

        if(self.preview_ready):
            return "%s://%s/%s" % (settings.DEFAULT_HTTP_PROTOCOL,
                                   settings.ALBUMS_AWS_CF_DOWNLOAD_DOMAIN,
                                   resized_path)
        else:
            return os.path.join(settings.MEDIA_URL,
                                "waiting.png")

    def get_next(self):
        try:
            return AlbumConvertableItem.objects.filter(
                parent=self.parent,created__gt=self.created
                ).order_by(
                'created'
                )[0:1].get()

        except AlbumConvertableItem.DoesNotExist:
            return None

    def get_previous(self):
        try:
            return AlbumConvertableItem.objects.filter(
                parent=self.parent,created__lt=self.created
                ).order_by(
                '-created'
                )[0:1].get()

        except AlbumConvertableItem.DoesNotExist:
            return None

    @models.permalink
    def get_absolute_url(self):
        return ('albums.views.albumitem', [self.parent.slug, self.slug])

    def delete(self):
        # Make sure the album doesn't get blasted if we're the highlight
        if(self.parent.album.highlight is not None and
           self.parent.album.highlight.id == self.id):
            self.parent.highlight = self.get_next()
            self.parent.save()
            
        tasks.albumitem_delete_directory.delay(self.get_directory())

        return super(AlbumConvertableItem, self).delete()

    def __unicode__(self):
        return self.title

    def get_tags(self):
        return tagging.models.Tag.objects.get_for_object(self)

tagging.register(AlbumConvertableItem, tag_descriptor_attr='tagss')

class Image(AlbumConvertableItem):
    pass
signals.pre_save.connect(albumitem_save, sender=Image)

def generate_image_thumbs(sender, instance, **kwargs):
    if(kwargs['created']):
        tasks.albumitem_generate_thumbnails.delay(instance, settings.ALBUMS_THUMBSIZES)
signals.post_save.connect(generate_image_thumbs, sender=Image)

class Video(AlbumConvertableItem):
    def get_video_path(self, filename):
        return os.path.join(self.get_directory(), filename)
    video = models.FileField(upload_to=get_video_path)
    video_ready = models.BooleanField(default=False, null=False)

    def converted_path(self, format='mp4', extension='mp4', add_extension=True):
        d, f = os.path.split(self.video.name)
        f = os.path.splitext(os.path.basename(f))[0]
        if(add_extension):
            f += "." + extension
        return os.path.join(d, format, f)

    def converted_format(self, extension):
        return self.video.storage.exists(self.converted_path(extension))

    duration = models.IntegerField(null=True)
    def duration_str(self):
        result = str(datetime.timedelta(seconds=self.duration))

        if result[:3] == "0:0":
            return result[3:]
        if result[:2] == "0:":
            return result[2:]
        else:
            return result

signals.pre_save.connect(albumitem_save, sender=Video)

class AlbumManager(models.Manager):
    def browse(self):
        return self.filter(is_profile=False)

    def make_slug_unique(self, slug):
        if(self.filter(slug=slug).count() == 0):
            return slug
        else:
            nums = [int(x.slug[len(slug)+1:]) for x in self.filter(slug__regex="^%s-\d+$" % slug)]
            if(len(nums) == 0):
                return "%s-0" % slug
            else:
                nums.sort()
                return "%s-%d" % (slug, nums[-1]+1)

    def create_profile_album(self, user):
        profile_album = Album()
        profile_album.title = "%s's Profile Pictures" % user.username
        profile_album.is_profile = True

        profile_album.slug = self.make_slug_unique(user.username)

        profile_album.save()

        profile_album.owners.add(user)
        profile_album.save()

        return profile_album

class Album(AlbumItem):
    slug = models.SlugField(unique=True,
                            verbose_name='ID', help_text='A unique id for this item\'s URL. Only alphanumeric characters allowed.')

    highlight = models.ForeignKey(AlbumConvertableItem, related_name='highlight_parent', null=True, blank=True)

    owners = models.ManyToManyField(User, blank=False)

    is_profile = models.BooleanField(blank=False, default=False)

    def is_owner(self, user):
        try:
            self.owners.get(id=user.id)
            return True
        except User.DoesNotExist:
            return False

    def can_delete(self, user):
        return ((not self.is_profile) and
                (user.is_staff or
                 self.is_owner(user)))

    def can_add_video(self, user):
        return ((not self.is_profile) and
                (user.is_staff or
                 self.is_owner(user)))

    @models.permalink
    def get_absolute_url(self):
        return ('albums.views.album', [self.slug])

    def thumbnail(self, size=80):
        if self.highlight is not None:
            return self.highlight.thumbnail(size)
        else:
            return None

    def preview_ready(self):
        return (self.highlight is not None and
                self.highlight.preview_ready)

    def delete(self):
        for child in self.children.all():
            child.delete()

        super(Album, self).delete()

    objects = AlbumManager()

    def bump_highlight(self):
        if self.highlight:
            self.highlight = self.highlight.get_next()
            self.save()
        else:
            self.highlight = self.children.all()[0]
            self.save()

signals.pre_save.connect(albumitem_save, sender=Album)
