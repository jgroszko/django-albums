from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

class FavoriteItemManager(models.Manager):
    def for_user(self, user, content_types=[]):
        favorite_objects = []
        
        q = self.filter(from_user=user)
        if content_types is not []:
            cts = []
            for content_type in content_types:
                ct = ContentType.objects.get_for_model(content_type)
                cts.append(ct.id)
            q = q.filter(content_type__in=cts)
        
        for favorite in q:
            favorite_objects.append(favorite.to_object)
            
        return favorite_objects

    def get(self, from_user, to_object):
        ct = ContentType.objects.get_for_model(to_object)
        return super(FavoriteItemManager, self).get(from_user=from_user, content_type=ct, object_id=to_object.id)

    def exists(self, from_user, to_object):
        try:
            self.get(from_user, to_object)
            return True
        except Favorite.DoesNotExist:
            return False

    def toggle(self, from_user, to_object):
        try:
            f = self.get(from_user, to_object)
            f.delete()
            return False
        except Favorite.DoesNotExist:
            f = Favorite(from_user=from_user, to_object=to_object)
            f.save()
            return True

    def to_object(self, object):
        return self.filter(content_type=ContentType.objects.get_for_model(object),
                           object_id=object.id)

class Favorite(models.Model):
    from_user = models.ForeignKey(User)

    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    to_object = generic.GenericForeignKey()

    class Meta:
        unique_together = (('from_user', 'content_type', 'object_id'))

    objects = FavoriteItemManager()

    def __unicode__(self):
        return "User %s Item %s" % (self.from_user, self.to_object)
