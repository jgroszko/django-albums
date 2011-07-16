from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from albums.models import AlbumConvertableItem
from albums.tasks import albumitem_generate_thumbnails

class Command(BaseCommand):
    help = 'Puts all albumitem thumbnails back in the queue for thumbnail generation'

    def handle(self, *args, **options):
        def mark_and_convert(aci):
            aci.preview_ready = False
            aci.save()
            
            self.stdout.writeln("Queueing %s" % aci.title)
            albumitem_generate_thumbnails(aci, settings.ALBUMS_THUMBSIZES, send_notifications=False, delete_on_fail=False)

        [mark_and_convert(aci) for aci in AlbumConvertableItem.objects.all()]
