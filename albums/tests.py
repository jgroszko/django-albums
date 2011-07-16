import pdb
import uuid
import unittest
from django.contrib.auth.models import User
from albums.models import Album

class AlbumTestCase(unittest.TestCase):
    def test_browse(self):
        Album.objects.create(title='Album', slug=str(uuid.uuid1()), is_profile=False)
        Album.objects.create(title='Profile Album', slug=str(uuid.uuid1()), is_profile=True)

        browse_query = Album.objects.browse()
        self.assertEquals(browse_query.filter(is_profile=True).count(), 0)
        self.assertTrue(browse_query.count() > 0)

    def test_make_slug_unique(self):
        guid = str(uuid.uuid1())
        Album.objects.create(title='TestAlbum', slug=guid)

        slug = Album.objects.make_slug_unique(guid)
        self.assertEquals(Album.objects.filter(slug=slug).count(), 0)
        self.assertEquals(slug, guid+'-0')

        Album.objects.create(title='TestAlbum', slug=guid+'-1')

        slug = Album.objects.make_slug_unique(guid)
        self.assertEquals(Album.objects.filter(slug=slug).count(), 0)
        self.assertEquals(slug, guid+'-2')

        Album.objects.create(title='TestAlbum', slug=guid+'-100')

        slug = Album.objects.make_slug_unique(guid)
        self.assertEquals(Album.objects.filter(slug=slug).count(), 0)
        self.assertEquals(slug, guid+'-101')

        Album.objects.create(title='TestAlbum', slug=guid+'-moo')

        slug = Album.objects.make_slug_unique(guid)
        self.assertEquals(Album.objects.filter(slug=slug).count(), 0)
        self.assertEquals(slug, guid+'-101')
    
    def test_create_profile_album(self):
        unique_username = str(uuid.uuid1())[:30]
        user = User.objects.create(username=unique_username)

        album = user.get_profile().pictures
        self.assertTrue(isinstance(album, Album))
        self.assertEquals(album.title, "%s's Profile Pictures" % unique_username)
        self.assertEquals(album.is_profile, True)
        self.assertEquals(album.slug[:30], unique_username)
        self.assertEquals(Album.objects.filter(slug=album.slug).count(), 1)
