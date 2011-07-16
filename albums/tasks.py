import pexpect
import os
import shutil
import re
import datetime
import Image, ImageFile
from time import sleep
from os.path import dirname
from django.conf import settings
from celery.log import get_default_logger
from celery.decorators import task
import notification.models as notification

import albums.models
from albums.conversion import make_thumbnail, calculate_size_argument, video_convert, file_to_s3, video_to_cloudfront, image_to_cloudfront, s3_delete_folder, key_on_cloudfront

ImageFile.MAXBLOCK = 1000000

@task
def albumitem_generate_thumbnails(image, sizes, send_notifications=True, delete_on_fail=True):
    logger = get_default_logger()

    try:
        old_dir, filename = os.path.split(image.preview.path)
    except ValueError:
        logger.info("Image ID %d has no preview associated with it." % image.id)
        return

    try:
        for size in sizes:
            sized_path = image._resized_path(size)
            new_file = os.path.join(settings.MEDIA_ROOT, sized_path)
            new_dir = os.path.dirname(new_file)
            
            if(image.preview.storage.exists(new_file) and
               key_on_cloudfront(sized_path)):
                logger.info("Skipping conversion of %s" % new_file)
                continue
            
            try:
                os.makedirs(new_dir)
            except OSError as e:
                if(e.errno != 17):
                    raise e
                
            logger.info("About to create %s" % new_file)
                
            thumb = Image.open(image.preview.path)
            thumb.thumbnail([size, size], Image.ANTIALIAS)
            thumb.save(new_file, thumb.format, quality=90, optimize=1)
                
            logger.info("Created thumbnail %s (%d bytes)" % (new_file, os.stat(new_file).st_size))

            image_to_cloudfront(new_file, sized_path)

        if (send_notifications and
            len(albums.models.Video.objects.filter(id=image.id)) == 0):
            notification.send([image.submitter,], "albums_conversion", {'success': True,
                                                                        'object': image})

        image.preview_ready = True
        image.save()
    except Exception as e:
        logger.info("Failed to convert image %s, %s" % (image.title, e))
        if len(albums.models.Video.objects.filter(id=image.id)) == 0:
            if(send_notifications):
                notification.send([image.submitter,], "albums_conversion", {'success': False,
                                                                            'title': image.title})
            if(delete_on_fail):
                image.delete()
                
@task
def albumitem_delete_directory(directory, **kwargs):
    logger = get_default_logger()

    full_path = os.path.join(settings.MEDIA_ROOT, directory)
    if(os.path.exists(full_path)):
        logger.info("Deleting directory %s" % full_path)
        shutil.rmtree(full_path)
    else:
        logger.info("Skipping delete of directory %s" % full_path)

    album_path = full_path[:full_path.rfind(os.path.sep)]
    logger.info("Album path %s %s" % (album_path, os.path.exists(album_path)))
    if(os.path.exists(album_path) and
       len(os.listdir(album_path)) == 0):
        logger.info("Deleting album directory %s" % album_path)
        shutil.rmtree(album_path)

    if hasattr(settings, 'ALBUMS_AWS_S3_BUCKET'):
        s3_delete_folder(directory)
    else:
        logger.info("Skipping delete of AWS keys")

@task
def albums_convert_video(video, send_notifications=True, **kwargs):
    logger = get_default_logger()

    try:
        source_filename = video.video.path

        logger.info("Making thumbnail for %s" % video.video.path)

        # Build path for the preview image
        preview_filename = os.path.splitext(os.path.basename(video.video.path))[0] + ".png"
        preview_path = video.get_preview_path(preview_filename)
        preview_path_full = os.path.join(settings.MEDIA_ROOT, video.get_preview_path(preview_filename))

        duration, resolution = make_thumbnail(os.path.join(settings.MEDIA_ROOT, video.video.path),
                                              preview_path_full)

        # Save what we've done
        video.duration = duration
        video.preview = preview_path
        video.save()

        # Kick off thumbnail generation
        albumitem_generate_thumbnails(video, settings.ALBUMS_THUMBSIZES)
        
        # Figure out size arguments
        size_arg = calculate_size_argument(resolution)

        logger.info("Size arg %s" % size_arg)

        in_file = os.path.join(settings.MEDIA_ROOT, video.video.name)

        for format_key, format in settings.ALBUMS_VIDEO_FORMATS.iteritems():
            format_filename = video.converted_path(format=format_key, extension=format['ext'])

            new_filename = os.path.join(settings.MEDIA_ROOT, format_filename)
            new_dir = os.path.dirname(new_filename)

            try:
                os.makedirs(new_dir)
            except OSError as e:
                if(e.errno != 17):
                    raise e

            out_file = os.path.join(settings.MEDIA_ROOT, format_filename)

            logger.info("Out file %s" % out_file)

            video_convert(format_key, size_arg,
                          in_file,
                          out_file)

            video_to_cloudfront(out_file, format_filename)

        if send_notifications:
            notification.send([video.submitter,], "albums_conversion", {'success': True,
                                                                        'object': video})

        video.video_ready = True
        video.save()

        logger.info("Marked video as ready")

        file_to_s3(in_file, video.video.name)

    except Exception as e:
        if send_notifications:
            notification.send([video.submitter,], "albums_conversion", {'success': False,
                                                                        'title': video.title})
        logger.info("Unable to convert video %s" % (video.title))
        logger.info(e.__str__())
        video.delete()
