from django.conf import settings
from albums.models import Album, Image, Video, AlbumConvertableItem
from django.template.loader import render_to_string
from django.template import Node, Library, Variable, TemplateSyntaxError, VariableDoesNotExist
from albums.utils import get_item_or_404

register = Library()

@register.inclusion_tag('albums/albumitem_preview.html', takes_context=True)
def albumitem_preview(context, albumitem):
    context['ai'] = get_item_or_404(albumitem.parent.slug, albumitem.slug) if hasattr(albumitem, 'parent') else Album.objects.get(id=albumitem.id)
    return context

@register.simple_tag
def albumitem_url(albumitem):
    return albumitem.get_absolute_url()

@register.simple_tag
def albumitem_thumb_url(albumitem, size=80):
    return albumitem.thumbnail(size)

@register.tag(name='albumitem_thumb')
def do_albumitem_thumb(parser, token):
    args = token.split_contents()
    try:
        if len(args) == 2:
            return AlbumItemThumb(args[1])
        else:
            return AlbumItemThumb(args[1], int(args[2]))
    except ValueError, IndexError:
        raise TemplateSyntaxError, "%r tag requires at least one argument, and an optional integer argument" % args[0]

def albumitem_to_string(context, albumitem, size, title):
    if(albumitem is None):
        return render_to_string('albums/albumitem_thumb.html', {'size': size,
                                                                'alt': title,},
                                context_instance=context)
    elif(albumitem.preview_ready):
        return render_to_string('albums/albumitem_thumb.html', {'thumb_url': albumitem.thumbnail(size),
                                                                'size': size,
                                                                'alt': title,},
                                context_instance=context)
    else:
        return render_to_string('albums/albumitem_waiting.html', {'ai': albumitem,
                                                                  'size': size,},
                                context_instance=context)
    
class AlbumItemThumb(Node):
    def __init__(self, albumitem, size=80):
        self.albumitem = Variable(albumitem)
        self.size = size

    def render(self, context):
        try:
            albumitem = self.albumitem.resolve(context)
        except VariableDoesNotExist:
            return ''
        
        title = albumitem.title

        if('highlight' in dir(albumitem) and
           albumitem.highlight is not None):
            albumitem = albumitem.highlight

        return albumitem_to_string(context, albumitem, self.size, title)
