
import datetime

from south.db import db
from django.db import models
import albums
from albums.models import *

class Migration:

    no_dry_run = True

    def forwards(self, orm):
        for albumconvertableitem in orm.AlbumConvertableItem.objects.all():
            albumconvertableitem.album = albumconvertableitem.albumitem_ptr.parent.album
            albumconvertableitem.save()
    
        # Get rid of root folder, without blasting everyone away
        try:
            root = orm.AlbumItem.objects.get(id=1)
        except:
            return

        otheralbum = orm.AlbumItem.objects.get(id=orm.Album.objects.all()[1].albumitem_ptr_id)
        for albumitem in orm.AlbumItem.objects.filter(parent=root):
            albumitem.parent = otheralbum
            albumitem.save()
        root.delete()

    def backwards(self, orm):
        for albumconvertableitem in orm.AlbumConvertableItem.objects.all():
            albumitem = orm.AlbumItem.objects.get(id=albumconvertableitem.albumitem_ptr.id)
            albumitem.parent = albumconvertableitem.album.albumitem_ptr
            albumitem.save()

        # Re-create root folder
        root = Album()
        root.id = 1
        root.title = "Root"
        root.slug = ""
        root.created = datetime.datetime.now()
        root.edited = datetime.datetime.now()
        root.save()
        root = orm.AlbumItem.objects.get(id=1)

        for albumitem in orm.AlbumItem.objects.filter(parent__isnull=True):
            albumitem.parent = root
            albumitem.save()
    
    models = {
        'albums.album': {
            'albumitem_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['albums.AlbumItem']", 'unique': 'True', 'primary_key': 'True'}),
            'highlight': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'highlight_parent'", 'null': 'True', 'to': "orm['albums.AlbumItem']"}),
            'owners': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.User']"})
        },
        'albums.albumconvertableitem': {
            'album': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['albums.Album']", 'null': 'True'}),
            'albumitem_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['albums.AlbumItem']", 'unique': 'True', 'primary_key': 'True'}),
            'allow_comments': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'allow_ratings': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'converted': ('django.db.models.fields.NullBooleanField', [], {'null': 'True'}),
            'rating_score': ('django.db.models.fields.IntegerField', [], {'default': '0', 'blank': 'True'}),
            'rating_votes': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'blank': 'True'}),
            'submitter': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'thumbFilename': ('django.db.models.fields.CharField', [], {'max_length': '250', 'null': 'True', 'blank': 'True'})
        },
        'albums.albumitem': {
            'Meta': {'unique_together': "(('parent', 'slug'),)"},
            'created': ('django.db.models.fields.DateTimeField', [], {}),
            'edited': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'children'", 'null': 'True', 'to': "orm['albums.AlbumItem']"}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '1000'})
        },
        'albums.image': {
            'albumconvertableitem_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['albums.AlbumConvertableItem']", 'unique': 'True', 'primary_key': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '100'}),
            'imageFilename': ('django.db.models.fields.CharField', [], {'max_length': '250', 'null': 'True', 'blank': 'True'})
        },
        'albums.video': {
            'albumconvertableitem_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['albums.AlbumConvertableItem']", 'unique': 'True', 'primary_key': 'True'}),
            'flvFilename': ('django.db.models.fields.CharField', [], {'max_length': '250', 'null': 'True', 'blank': 'True'}),
            'video': ('django.db.models.fields.files.FileField', [], {'max_length': '100'})
        },
        'auth.group': {
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'unique_together': "(('content_type', 'codename'),)"},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'unique_together': "(('app_label', 'model'),)", 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }
    
    complete_apps = ['albums']
