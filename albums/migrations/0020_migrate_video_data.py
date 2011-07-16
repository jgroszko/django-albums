
from south.db import db
from django.db import models
from albums.models import *
import shutil

class Migration:
    
    def forwards(self, orm):
        "Write your forwards migration here"
    
        for video in orm.Video.objects.all():
            video_directory = os.path.join('albums',
                                           str(video.albumconvertableitem_ptr.parent.pk),
                                           str(video.pk))
                                           
            video_directory_full = os.path.join(settings.MEDIA_ROOT,
                                                video_directory)

            if(not os.path.exists(video_directory_full)):
                os.makedirs(video_directory_full)

            video_new_path = os.path.join(video_directory, os.path.basename(video.video.path))
            video_new_path_full = os.path.join(settings.MEDIA_ROOT,
                                               video_new_path)

            if(os.path.exists(video.video.path)):
                shutil.move(video.video.path, video_new_path_full)
            else:
                print("WARNING: %s not found (video id %s)" % (video.video.path, video.pk))
            
            video.video = video_new_path
            video.save()

            shutil.rmtree(os.path.join(settings.MEDIA_ROOT, 'albums_videos'))
                
    def backwards(self, orm):
        "Write your backwards migration here"
    
        video_directory = os.path.join(settings.MEDIA_ROOT, 'albums_videos')
        if(not os.path.exists(video_directory)):
            os.makedirs(video_directory)

        def unique_filename(filename):
            filename_parts = os.path.splitext(filename)
            i = 1
            while 1:
                try:
                    fd = os.open(filename, os.O_CREAT | os.O_EXCL | os.O_RDWR)
                    os.close(fd)
                    return filename
                except OSError:
                    pass
                filename = filename_parts[0] + '-' + str(i) + filename_parts[1]
                i += 1

        def move_unique(old_file, new_path):
            old_filename = os.path.basename(old_file)
            
            unique_file = unique_filename(os.path.join(settings.MEDIA_ROOT,
                                                       new_path, old_filename))

            old_path = os.path.join(settings.MEDIA_ROOT,
                                    old_file)
            if(os.path.exists(old_path)):
                shutil.move(os.path.join(settings.MEDIA_ROOT,
                                         old_file),
                            unique_file)
            else:
                print("WARNING: %s not found" % old_path)

            return os.path.join(new_path, os.path.basename(unique_file))


        for video in orm.Video.objects.all():
            video.video = move_unique(video.video.path,
                                      video_directory)[len(settings.MEDIA_ROOT)+1:]
            video.save()

            

    models = {
        'albums.album': {
            'albumitem_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['albums.AlbumItem']", 'unique': 'True', 'primary_key': 'True'}),
            'highlight': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'highlight_parent'", 'null': 'True', 'to': "orm['albums.AlbumConvertableItem']"}),
            'is_profile': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'owners': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.User']"}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'})
        },
        'albums.albumconvertableitem': {
            'Meta': {'unique_together': "(('slug', 'parent'),)"},
            'albumitem_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['albums.AlbumItem']", 'unique': 'True', 'primary_key': 'True'}),
            'allow_comments': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'allow_ratings': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'appearances': ('django.contrib.contenttypes.generic.GenericRelation', [], {'to': "orm['appearances.Appearance']"}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'children'", 'null': 'True', 'to': "orm['albums.Album']"}),
            'preview': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True'}),
            'rating_score': ('django.db.models.fields.IntegerField', [], {'default': '0', 'blank': 'True'}),
            'rating_votes': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'db_index': 'True'}),
            'submitter': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'albums.albumitem': {
            'created': ('django.db.models.fields.DateTimeField', [], {}),
            'edited': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '1000'})
        },
        'albums.image': {
            'albumconvertableitem_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['albums.AlbumConvertableItem']", 'unique': 'True', 'primary_key': 'True'})
        },
        'albums.video': {
            'albumconvertableitem_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['albums.AlbumConvertableItem']", 'unique': 'True', 'primary_key': 'True'}),
            'duration': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'flvFilename': ('django.db.models.fields.CharField', [], {'max_length': '250', 'null': 'True', 'blank': 'True'}),
            'video': ('django.db.models.fields.files.FileField', [], {'max_length': '100'})
        },
        'appearances.appearance': {
            'Meta': {'unique_together': "(('user', 'content_type', 'object_id'),)"},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'created_date': ('django.db.models.fields.DateTimeField', [], {}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'updated_date': ('django.db.models.fields.DateTimeField', [], {}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
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
