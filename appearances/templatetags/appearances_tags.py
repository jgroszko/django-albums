from django.template.loader import render_to_string
from django.template import Node, Library, Variable, TemplateSyntaxError, VariableDoesNotExist
from appearances.models import Appearance
from django.contrib.contenttypes.models import ContentType
from django.core import urlresolvers

register = Library()

@register.tag
def appearances(parser, token):
    try:
        tag_name, target = token.split_contents()
    except ValueError:
        raise TemplateSyntaxError, "%r tag requires exactly one argument" % token.contents.split()[0]

    return AppearancesNode(target)

class AppearancesNode(Node):
    def __init__(self, target):
        self.target = Variable(target)

    def render(self, context):
        try:
            target = self.target.resolve(context)

            ctype = str(target._meta)
            pk = target.pk

            current_user = context['request'].user
            can_edit = "can_edit" in dir(target) and target.can_edit(current_user)

            appearances = target.appearances.get_for_target_and_user(target, current_user)

            return render_to_string('appearances/block.html',
                                    {'appearances': appearances,
                                     'content_type': ctype,
                                     'object_pk': pk,
                                     'can_edit': can_edit,
                                     },
                                    context_instance=context)

        except VariableDoesNotExist:
            return ''

@register.tag
def appearance_item(parser, token):
    try:
        tag_name, appearance = token.split_contents()
    except ValueError:
        raise TemplateSyntaxError, "%r tag requires exactly one argument" % token.contents.split()[0]

    return AppearanceItemNode(appearance)

class AppearanceItemNode(Node):
    def __init__(self, appearance):
        self.appearance = Variable(appearance)

    def render(self, context):
        try:
            appearance = self.appearance.resolve(context)

            ctype = appearance.content_type.model_class()._meta
            pk = appearance.object_id

            show_status = (appearance.user == context['user'] or
                           (appearance.can_edit_target(context['user'])))

            return render_to_string('appearances/item.html',
                                    {'appearance': appearance,
                                     'content_type': ctype,
                                     'object_pk': pk,
                                     'can_confirm': appearance.can_confirm(context['user']),
                                     'can_ignore': appearance.can_ignore(context['user']),
                                     'can_delete': appearance.can_delete(context['user']),
                                     'show_status': show_status
                                     },
                                    context_instance=context)

        except VariableDoesNotExist:
            return ''
