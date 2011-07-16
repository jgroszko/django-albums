import datetime

from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.db.models import signals
import notification.models as notification

class AppearanceManager(models.Manager):
    def get_for_target_and_user(self, target, user):
        result = target.appearances.filter(Q(status=str(Appearance.STATUS_CONFIRMED)) |
                                           Q(user=user))

        if("can_edit" in dir(target) and
           target.can_edit(user)):
            result = target.appearances.all()

        return result.order_by('status', 'created_date')

class Appearance(models.Model):
    user = models.ForeignKey(User)
    description = models.CharField(max_length=255)

    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    to_object = generic.GenericForeignKey()

    created_date = models.DateTimeField()
    updated_date = models.DateTimeField()

    STATUS_CONFIRMED = "1"
    STATUS_PENDING = "2"
    STATUS_IGNORED = "3"

    STATUS_ARR = (
        (STATUS_CONFIRMED, "Confirmed"),
        (STATUS_PENDING, "Pending"),
        (STATUS_IGNORED, "Ignored"),
        )

    status = models.CharField(max_length=1, choices=STATUS_ARR)

    def status_str(self):
        return self.STATUS_ARR[int(self.status)-1][1]
    status_str.short_description = "Status"

    def can_edit_target(self, user):
        return ("can_edit" in dir(self.to_object) and
                self.to_object.can_edit(user))

    def can_confirm(self, user):
        return (self.status != self.STATUS_CONFIRMED and
                self.user == user)

    def can_ignore(self, user):
        return (self.status != self.STATUS_IGNORED and
                self.user == user)

    def can_delete(self, user): 
        return (self.user == user or
                (self.status != self.STATUS_IGNORED and
                 self.can_edit_target(user)))

    class Meta:
        unique_together = (('user', 'content_type', 'object_id'))

    def __unicode__(self):
        return "%s in %s" % (self.user, self.to_object)

    objects = AppearanceManager()

def new_appearance(sender, instance, **kwargs):
    if(instance.id is None):
        instance.status = Appearance.STATUS_PENDING
        if(hasattr(instance.to_object, 'submitter') and
           instance.to_object.submitter == instance.user):
            instance.status = Appearance.STATUS_CONFIRMED

        instance.created_date = datetime.datetime.now()
        
        notification.send([instance.user], "appearances_new", {"a": instance})

    instance.updated_date = datetime.datetime.now()
        
signals.pre_save.connect(new_appearance, sender=Appearance)
