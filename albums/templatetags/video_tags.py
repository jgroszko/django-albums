import os.path
import re

from django.conf import settings
from django.template.loader import render_to_string
from django.template import Node, Library, Variable, TemplateSyntaxError
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe

from albums.models import Video
from albums.aws_secure_url import secure_url

register = Library()

@register.tag(name='video_player')
def do_video_player(parser, token):
    args = token.split_contents()

    if len(args) == 2:
        return VideoPlayer(args[1])
    else:
        raise TemplateSyntaxError, "%r tag requires at least one argument" % args[0]

def render_video_player(context, video):
    if(not video.video_ready):
        return render_to_string("albums/video_waiting.html",
                                {'status_url': reverse('albums_video_status', args=[video.parent.slug, video.slug])},
                                context_instance=context)
    else:
        if hasattr(settings, "ALBUMS_AWS_CF_STREAMING_DOMAIN"):
            resource = video.converted_path(add_extension=False)
            remote_addr = context['request'].META['REMOTE_ADDR']
            if remote_addr == '127.0.0.1':
                remote_addr = None

            url = mark_safe('mp4:' + secure_url(resource, host=remote_addr))
            net_connect_url = 'rtmpe://' + settings.ALBUMS_AWS_CF_STREAMING_DOMAIN + '/cfx/st'
        else:
            url = os.path.join(settings.MEDIA_URL, video.converted_path())
            net_connect_url = None
        return render_to_string("albums/flowplayer.html",
                                {'mp4_url': url,
                                 'net_connect_url': net_connect_url},
                                context_instance=context)

class VideoPlayer(Node):
    def __init__(self, video):
        self.video = Variable(video)

    def render(self, context):
        video = self.video.resolve(context)

        return render_video_player(context, video)
