from django.forms import Form, ModelForm, CharField, BooleanField, FileField, HiddenInput, ValidationError, ModelChoiceField, Select, Textarea
from models import AlbumItem, Album, Image, Video, AlbumConvertableItem
from django.core.urlresolvers import reverse
from django.template.loader import render_to_string

from haystack_ext.forms import LimitedModelSearchForm

from django.utils.translation import ugettext_lazy as _

class SelectAlbum(Select):
    def render(self, *args, **kwargs):
        return render_to_string("albums/album_select.html",
                                {'select': super(SelectAlbum, self).render(*args, **kwargs)})
                                

class AlbumConvertableItemForm(ModelForm):
    #id = CharField(widget=HiddenInput, required=False)

    def clean(self):
        if('parent' in self.cleaned_data):
            query = AlbumConvertableItem.objects.filter(parent=self.cleaned_data['parent'], 
                                                        slug=self.cleaned_data['slug'])
            if(self.instance is not None):
                query = query.exclude(id=self.instance.id)
            count = query.count()
                
            if(count != 0):
                raise ValidationError("IDs must be unique within an album.")

        return self.cleaned_data
    
    def __init__(self, user=None, *args, **kwargs):
        kwargs['label_suffix'] = ''
        
        self.show_profile_albums = kwargs.pop("show_profile_albums", False)

        super(AlbumConvertableItemForm, self).__init__(*args, **kwargs)

        q = Album.objects.filter(owners=user)

        if(not self.show_profile_albums):
            q = q.filter(is_profile=False)

        self.fields['parent'] = ModelChoiceField(queryset=q, label="Album", empty_label=None, widget=SelectAlbum)

class AlbumForm(ModelForm):
    class Meta:
        model = Album
        fields = ('title', 'slug', 'description')

class ImageForm(AlbumConvertableItemForm):
    class Meta:
        model = Image
        fields = ('parent', 'title', 'slug', 'tags', 'description', 'allow_ratings', 'allow_comments')

class VideoForm(AlbumConvertableItemForm):
    class Meta:
        model = Video
        fields = ('parent', 'title', 'slug', 'tags', 'description', 'allow_ratings', 'allow_comments')


class SelectAlbumForm(Form):
    def __init__(self, user=None, *args, **kwargs):
        self.show_profile_albums = kwargs.pop("show_profile_albums", False)

        super(SelectAlbumForm, self).__init__(*args, **kwargs)

        q = Album.objects.filter(owners=user)
        
        if(not self.show_profile_albums):
            q = q.filter(is_profile=False)

        self.fields['parent'] = ModelChoiceField(queryset=q, label="Upload To", empty_label=None, widget=SelectAlbum,
                                                 initial=280) #kwargs['initial']['parent'] if ('initial' in kwargs and 'parent' in kwargs['initial']) else None),


class SmallImageForm(ModelForm):
    description = CharField(required=False,
                            widget=Textarea(attrs={'rows': 2,}))

    def __init__(self, *args, **kwargs):
        super(SmallImageForm, self).__init__(*args, **kwargs)

        if len(args) == 0:
            self.fields['preview'] = FileField(widget=HiddenInput())

        self.fields['parent'] = ModelChoiceField(queryset=Album.objects.all(), widget=HiddenInput())

    class Meta:
        fields = ('parent', 'preview', 'title', 'slug', 'description')
        model = Image

class SmallVideoForm(ModelForm):
    description = CharField(required=False,
                            widget=Textarea(attrs={'rows': 2,}))

    def __init__(self, *args, **kwargs):
        super(SmallVideoForm, self).__init__(*args, **kwargs)

        if len(args) == 0:
            self.fields['video'] = FileField(widget=HiddenInput())

        self.fields['parent'] = ModelChoiceField(queryset=Album.objects.all(), widget=HiddenInput())
        
    class Meta:
        fields = ('parent', 'video', 'title', 'slug', 'description')
        model = Video

class AlbumsSearchForm(LimitedModelSearchForm):
    choices = (("albums.album", _("Album")),
               ("albums.image", _("Image")),
               ("albums.video", _("Video")))
