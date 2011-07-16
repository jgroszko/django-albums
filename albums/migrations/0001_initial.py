
from south.db import db
from django.db import models
from albums.models import *

class Migration:
    
    def forwards(self, orm):
        
        # Adding model 'AlbumItem'
        db.create_table('albums_albumitem', (
            ('id', orm['albums.AlbumItem:id']),
            ('title', orm['albums.AlbumItem:title']),
            ('slug', orm['albums.AlbumItem:slug']),
            ('parent', orm['albums.AlbumItem:parent']),
            ('created', orm['albums.AlbumItem:created']),
            ('edited', orm['albums.AlbumItem:edited']),
        ))
        db.send_create_signal('albums', ['AlbumItem'])
        
        # Adding model 'Video'
        db.create_table('albums_video', (
            ('albumconvertableitem_ptr', orm['albums.Video:albumconvertableitem_ptr']),
            ('video', orm['albums.Video:video']),
            ('flvFilename', orm['albums.Video:flvFilename']),
        ))
        db.send_create_signal('albums', ['Video'])
        
        # Adding model 'Image'
        db.create_table('albums_image', (
            ('albumconvertableitem_ptr', orm['albums.Image:albumconvertableitem_ptr']),
            ('image', orm['albums.Image:image']),
            ('imageFilename', orm['albums.Image:imageFilename']),
        ))
        db.send_create_signal('albums', ['Image'])
        
        # Adding model 'AlbumConvertableItem'
        db.create_table('albums_albumconvertableitem', (
            ('albumitem_ptr', orm['albums.AlbumConvertableItem:albumitem_ptr']),
            ('thumbFilename', orm['albums.AlbumConvertableItem:thumbFilename']),
            ('converted', orm['albums.AlbumConvertableItem:converted']),
            ('submitter', orm['albums.AlbumConvertableItem:submitter']),
        ))
        db.send_create_signal('albums', ['AlbumConvertableItem'])
        
        # Adding model 'Album'
        db.create_table('albums_album', (
            ('albumitem_ptr', orm['albums.Album:albumitem_ptr']),
            ('highlight', orm['albums.Album:highlight']),
        ))
        db.send_create_signal('albums', ['Album'])
        
        # Adding ManyToManyField 'Album.owners'
        db.create_table('albums_album_owners', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('album', models.ForeignKey(orm.Album, null=False)),
            ('user', models.ForeignKey(orm['auth.User'], null=False))
        ))
        
        # Creating unique_together for [parent, slug] on AlbumItem.
        db.create_unique('albums_albumitem', ['parent_id', 'slug'])
        
    
    
    def backwards(self, orm):
        
        # Deleting unique_together for [parent, slug] on AlbumItem.
        db.delete_unique('albums_albumitem', ['parent_id', 'slug'])
        
        # Deleting model 'AlbumItem'
        db.delete_table('albums_albumitem')
        
        # Deleting model 'Video'
        db.delete_table('albums_video')
        
        # Deleting model 'Image'
        db.delete_table('albums_image')
        
        # Deleting model 'AlbumConvertableItem'
        db.delete_table('albums_albumconvertableitem')
        
        # Deleting model 'Album'
        db.delete_table('albums_album')
        
        # Dropping ManyToManyField 'Album.owners'
        db.delete_table('albums_album_owners')
        
    
    
    models = {
        'albums.album': {
            'albumitem_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['albums.AlbumItem']", 'unique': 'True', 'primary_key': 'True'}),
            'highlight': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'highlight_parent'", 'null': 'True', 'to': "orm['albums.AlbumItem']"}),
            'owners': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.User']"})
        },
        'albums.albumconvertableitem': {
            'albumitem_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['albums.AlbumItem']", 'unique': 'True', 'primary_key': 'True'}),
            'converted': ('django.db.models.fields.NullBooleanField', [], {'null': 'True'}),
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
