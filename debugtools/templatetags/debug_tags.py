"""
Debugging features in in the template.
"""

# Objects
from django.template import Library, Node, Variable
from django.db.models.query import QuerySet
from django.forms.forms import BoundField

# Util functions
from django.core.serializers import serialize
from django.template.defaultfilters import linebreaksbr
from django.utils.html import escape, mark_safe
from pprint import pformat
from itertools import chain


register = Library()

class PrintNode(Node):
    def __init__(self, varnames):
        # Thread safety OK: the list of varnames won't change for this node.
        # Data is read only inside the render() function.
        self.variables = dict( (v,Variable(v)) for v in varnames )

    def render(self, context):
        text = ''
        if self.variables:
            for name, var in self.variables.iteritems():
                data = var.resolve(context)
                textdata = linebreaksbr(escape(_dump_var(data)))
                if isinstance(data, (bool,int,basestring,float)):
                    text += "<pre>%s = %s</pre>" % (name, textdata)
                else:
                    text += "<pre>%s = %s...\n%s</pre>" % (name, data.__class__.__name__, textdata)
        else:
            text = '<h3>Template context parts:</h3>\n'
            for part in context:
                text += "<pre>%s</pre>" % linebreaksbr(escape(_dump_var(part)))

        return mark_safe(text)


@register.tag('print')
def _print(parser, token):
    """
    A template tag which prints dumps the contents of objects.
    """
    varnames = token.contents.split()
    return PrintNode(varnames[1:])



# ---- Internal print helper ----

def _dump_var(object):
    """
    A variable dumper to generate sensible output for template context fields.
    """
    if isinstance(object, QuerySet):
        text = serialize('python', object)
    elif isinstance(object, basestring):
        text = repr(object)
    else:
        # Instead of just printing <SomeType at 0xfoobar>, expand the fields
        if hasattr(object, '__dict__'):
            all_attrs = object.__dict__.iteritems()
            if object.__class__:
                # Add class members too.
                all_attrs = chain(all_attrs, object.__class__.__dict__.iteritems())

            attrs = dict((k, v) for k, v in all_attrs if not k.startswith('_'))

            # Format property objects
            for name, value in attrs.iteritems():
                if isinstance(value, property):
                    try:
                        attrs[name] = getattr(object, name)
                    except (TypeError, AttributeError), e:
                        attrs[name] = e

            # Include representations which are relevant in template context.
            attrs['__str__'] = str(object)
            if hasattr(object, '__iter__'):
                attrs['__iter__'] = '__ITER__'
            if hasattr(object, '__getitem__'):
                attrs['__getitem__'] = '...'

            # Enrich members with values from dir (e.g. add auto_id)
            for member in dir(object):
                if member.startswith('_') or not hasattr(object, member):
                    continue

                value = getattr(object, member)
                if callable(value) or attrs.has_key(member):
                    continue

                if isinstance(value, BoundField):
                    attrs[member] = str(value) + "???"
                else:
                    attrs[member] = value

            object = attrs

        try:
            text = pformat(object)
        except Exception, e:
            text = "<caught %s while rendering: %s>" % (e.__class__.__name__, str(e) or "<no msg>")

        text = text.replace("'__ITER__'", '<iterator object>')
        text = text.replace("<django.utils.functional.__proxy__ object", '<proxy object')

    return text
