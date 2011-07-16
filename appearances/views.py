from django.utils import simplejson
from django.http import HttpResponse, HttpResponseRedirect
from django.db import IntegrityError
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404, render_to_response
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from models import Appearance
from django.shortcuts import render_to_response

@login_required
def list(request, status=None):
    status_int = 2
    if status is not None:
        for s in Appearance.STATUS_ARR:
            if status.lower() == s[1].lower():
                status_int = int(s[0])
                break

    if request.method == 'POST':
        appearance = get_object_or_404(Appearance, id=int(request.POST['id']))
        if("delete.x" in request.POST and
           appearance.can_delete(request.user)):
            appearance.delete()
        
        if("confirm.x" in request.POST and
           appearance.can_confirm(request.user)):
            appearance.status = Appearance.STATUS_CONFIRMED
            appearance.save()

        if("ignore.x" in request.POST and
           appearance.can_ignore(request.user)):
            appearance.status = Appearance.STATUS_IGNORED
            appearance.save()

    appearances = [{'a': x,
                    'can_confirm': x.can_confirm(request.user),
                    'can_ignore': x.can_ignore(request.user),
                    'can_delete': x.can_delete(request.user),
                    } for x in Appearance.objects.filter(user=request.user)
                   .filter(status=str(status_int))]
    
    confirmed_count = Appearance.objects.filter(user=request.user, status=Appearance.STATUS_CONFIRMED).count()
    pending_count = Appearance.objects.filter(user=request.user, status=Appearance.STATUS_PENDING).count()
    ignored_count = Appearance.objects.filter(user=request.user, status=Appearance.STATUS_IGNORED).count()
    
    return render_to_response('appearances/list.html',
                              {
            'status_str': Appearance.STATUS_ARR[status_int-1][1],
            'confirmed_count': confirmed_count,
            'ignored_count': ignored_count,
            'pending_count': pending_count,
            'appearances': appearances,
            },
                              context_instance=RequestContext(request))

def ajax_required(f):
    def wrap(request, *args, **kwargs):
        if not request.is_ajax():
            return HttpResponseBadRequest()
        return f(request, *args, **kwargs)
    return wrap

def make_list_for_json(context, appearance, user):
    can_edit = appearance.can_edit_target(user)

    appearances = Appearance.objects.get_for_target_and_user(appearance.to_object, user)

    return render_to_string('appearances/list_for_object.html',
                            {'appearances': appearances,
                             'content_type': appearance.content_type,
                             'object_pk': appearance.object_id,
                             'can_edit': can_edit,},
                            context_instance=context)

def json_fail(reason):
    return HttpResponse(simplejson.dumps({'success': False,
                                          'reason': reason}))


@login_required
@require_POST
def add(request):
    try:
        data = request.POST.copy()

        username = data['user']

        user = User.objects.get(username__iexact=username)

        app, model = request.POST['content_type'].split('.')
        type = ContentType.objects.get(app_label=app, model=model)
        target = type.get_object_for_this_type(id=request.POST['object_pk'])

        new = Appearance(user=user, to_object=target)
        new.save()

        if request.is_ajax():
            return HttpResponse(simplejson.dumps({'success': True,
                                                  'new_list': make_list_for_json(RequestContext(request), new, request.user),
                                                  }))
        else:
            return HttpResponseRedirect(target.get_absolute_url())

    except User.DoesNotExist:
        return json_fail("User does not exist")
    except IntegrityError:
        return json_fail("User has already been selected")

@login_required
@require_POST
def update(request):
    appearance = get_object_or_404(Appearance, id=request.POST['id'])
    
    success = True

    if("confirm.x" in request.POST and
       appearance.can_confirm(request.user)):
        appearance.status = Appearance.STATUS_CONFIRMED
        appearance.save()
    elif("ignore.x" in request.POST and
         appearance.can_ignore(request.user)):
        appearance.status = Appearance.STATUS_IGNORED
        appearance.save()
    elif("delete.x" in request.POST and
         appearance.can_delete(request.user)):
        appearance.delete()
    elif("new_description" in request.POST and
         appearance.can_edit_target(request.user)):
        appearance.description = request.POST['new_description']
        appearance.save()
    else:
        success = False

    if(request.is_ajax()):
        if success:
            return HttpResponse(simplejson.dumps({'success': success,
                                                  'new_list': make_list_for_json(RequestContext(request), appearance, request.user),
                                                  }))
        else:
            return json_fail("Update failed")
    else:
        return HttpResponseRedirect(appearance.to_object.get_absolute_url())
