import pexpect
import os
import re
import datetime

from django.conf import settings

from boto.s3.connection import S3Connection
from boto.cloudfront import CloudFrontConnection
from boto.cloudfront.distribution import Distribution

from celery.log import get_default_logger

def make_thumbnail(in_path, out_path):
    '''
    Generate a thumbnail from a video.

    Returns a tuple: [duration of the video, video resolution]
    '''
    logger = get_default_logger()

    ffmpeg_path = getattr(settings, "FFMPEG_PATH", 'ffmpeg')

    ffmpeg_cmd = '%s %s -i "%s" "%s"' % (ffmpeg_path,
                                         settings.ALBUMS_VIDEO_THUMB_ARGS,
                                         in_path,
                                         out_path)

    logger.info(ffmpeg_cmd)
    ffmpeg_output = pexpect.run(ffmpeg_cmd)
    logger.info(ffmpeg_output)

    # Extract the length of the video
    m = re.search("Duration:.*(\d\d):(\d\d):(\d\d\.\d\d)", ffmpeg_output)
    if(m is None or
       os.stat(out_path).st_size == 0):
        raise Exception("unable to find duration of video")
    groups = m.groups()
    duration = datetime.timedelta(hours=int(groups[0]), minutes=int(groups[1]), seconds=float(groups[2])).seconds

    m = re.search("Stream.*Video.* (\d+)x(\d+)", ffmpeg_output)
    if(m is None):
        raise Exception("Unable to determine resolution of video")
    resolution = [int(x) for x in m.groups()]
    logger.info("Resolution: %s" % resolution)

    return [duration, resolution]

# Video Conversion

def calculate_size_argument(resolution):
    def make_even(i):
        return i if (i % 2) == 0 else (i - 1)

    size_arg = '-s %sx%s' % (settings.ALBUMS_VIDEO_SIZE[0], settings.ALBUMS_VIDEO_SIZE[1])
    ratio = float(settings.ALBUMS_VIDEO_SIZE[0]) / float(settings.ALBUMS_VIDEO_SIZE[1])
    video_ratio = float(resolution[0]) / float(resolution[1])
    if(video_ratio > ratio):
        scaled_video_height = resolution[1] * (float(settings.ALBUMS_VIDEO_SIZE[0])/float(resolution[0]))
        padding = (settings.ALBUMS_VIDEO_SIZE[1] - scaled_video_height) / 2
        size_arg = '-vf "scale=%s:%s,pad=%s:%s:0:%s"' % (make_even(settings.ALBUMS_VIDEO_SIZE[0]),
                                                         int(scaled_video_height),
                                                         make_even(settings.ALBUMS_VIDEO_SIZE[0]),
                                                         make_even(settings.ALBUMS_VIDEO_SIZE[1]),
                                                         make_even(int(padding)))
    if(video_ratio < ratio):
        scaled_video_width = resolution[0] * (float(settings.ALBUMS_VIDEO_SIZE[1])/float(resolution[1]))
        padding = (settings.ALBUMS_VIDEO_SIZE[0] - scaled_video_width) / 2
        size_arg = '-vf "scale=%s:%s,pad=%s:%s:%s:0"' % (int(scaled_video_width),
                                                        make_even(settings.ALBUMS_VIDEO_SIZE[1]),
                                                        make_even(settings.ALBUMS_VIDEO_SIZE[0]),
                                                        make_even(settings.ALBUMS_VIDEO_SIZE[1]),
                                                        make_even(int(padding)))

    return size_arg

def video_convert(format, size_arg, in_path, out_path):
    logger = get_default_logger()
    format_settings = settings.ALBUMS_VIDEO_FORMATS[format]

    logger.info("Starting conversion of %s" % in_path)

    threads_arg = '-threads %s' % settings.ALBUMS_CONVERSION_THREADS

    ffmpeg_path = getattr(settings, "FFMPEG_PATH", 'ffmpeg')

    for args in format_settings['args']:
        command = '%s -y -i "%s" %s %s %s "%s"' % (ffmpeg_path,
                                                   in_path,
                                                   args,
                                                   size_arg,
                                                   threads_arg,
                                                   out_path)

        logger.info(command)
        child = pexpect.spawn(command,
                              maxread=1,
                              timeout=settings.ALBUMS_CONVERSION_TIMEOUT,
                              cwd=os.path.dirname(in_path))
        child.expect(pexpect.EOF)

        exit_status = child.exitstatus

        if(exit_status == 1):
            raise Exception("Failed to convert %s to %s (ffmpeg exit status %s)" %
                            (in_path, format_settings['ext'], exit_status))
        elif(exit_status == 255):
            logger.info("Convert %s to %s with errors" %
                    (in_file, format_settings['ext']))

    logger.info("Successfully converted %s to %s" % (in_path, format_settings['ext']))

# Upload to S3
def file_to_s3(path_on_disk, key_name):
    '''
    Upload a file to our S3 bucket
    '''
    logger = get_default_logger()

    logger.info("Uploading %s to S3 %s %s" % (path_on_disk,
                                              settings.ALBUMS_AWS_S3_BUCKET,
                                              key_name))

    conn = S3Connection(settings.ALBUMS_AMAZON_KEY, settings.ALBUMS_AMAZON_SECRET_KEY)
    bucket = conn.get_bucket(settings.ALBUMS_AWS_S3_BUCKET)
    
    key = bucket.new_key(key_name)
    key.set_contents_from_filename(path_on_disk)

    logger.info("Uploaded S3 %s %s" % (settings.ALBUMS_AWS_S3_BUCKET,
                                       key_name))
                                       
def aws_cf_connection():
    return CloudFrontConnection(settings.ALBUMS_AMAZON_KEY, settings.ALBUMS_AMAZON_SECRET_KEY)

def video_to_cloudfront(path_on_disk, key_name):
    distribution = aws_cf_connection().get_streaming_distribution_info(settings.ALBUMS_AWS_CF_STREAMING_DISTRIBUTION)

    file_to_cloudfront(path_on_disk, key_name, distribution)

def image_to_cloudfront(path_on_disk, key_name):
    distribution = aws_cf_connection().get_distribution_info(settings.ALBUMS_AWS_CF_DOWNLOAD_DISTRIBUTION)

    file_to_cloudfront(path_on_disk, key_name, distribution)

def file_to_cloudfront(path_on_disk, key_name, distribution):
    '''
    Upload the file to cloudfront. Will actually wind up in S3, but boto is
    smart enough to give it all the permissions we need when we do it this
    way.
    '''
    logger = get_default_logger()

    logger.info("Uploading %s to CloudFront %s %s" % (path_on_disk,
                                                      distribution.domain_name,
                                                      key_name))

    obj = distribution.add_object(key_name, open(path_on_disk, 'rb'))

    logger.info("Uploaded S3 %s %s" % (distribution.domain_name,
                                       key_name))

def key_on_cloudfront(key_name):
    s3conn = S3Connection(settings.ALBUMS_AMAZON_KEY, settings.ALBUMS_AMAZON_SECRET_KEY)
    bucket = s3conn.get_bucket(settings.ALBUMS_AWS_S3_BUCKET)
    
    return bucket.get_key(key_name) is not None

# Bucket management
def s3_delete_folder(path):
    logger = get_default_logger()

    logger.info("Deleting S3 directory %s %s" % (settings.ALBUMS_AWS_S3_BUCKET,
                                                 path))

    conn = S3Connection(settings.ALBUMS_AMAZON_KEY, settings.ALBUMS_AMAZON_SECRET_KEY)
    bucket = conn.get_bucket(settings.ALBUMS_AWS_S3_BUCKET)

    for key in bucket.get_all_keys(prefix=path):
        logger.info("Deleting key %s %s" % (settings.ALBUMS_AWS_S3_BUCKET,
                                           key.name))
        key.delete()

