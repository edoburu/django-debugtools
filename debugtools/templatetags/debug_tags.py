"""
Debugging features in in the template.
"""
from django.core import context_processors

__author__ = "Diederik van der Boor"
__license__ = "Apache License, Version 2"


# Objects
from django.template import Library, Node, Variable
from django.db.models.query import QuerySet
from django.forms.forms import BoundField

# Util functions
from django.core.serializers import serialize
from django.template.defaultfilters import linebreaksbr
from django.utils.encoding import smart_str
from django.utils.html import escape, mark_safe, conditional_escape
from pprint import pformat
from itertools import chain
import re


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
            text = '<h6>Template context scope:</h6>\n'
            for i, part in enumerate(context):
                text += "<pre><small>%i: </small>%s</pre>" % (i, linebreaksbr(escape(_dump_var(part))))

        return mark_safe(text)


@register.tag('print')
def _print(parser, token):
    """
    A template tag which prints dumps the contents of objects.
    """
    varnames = token.contents.split()
    return PrintNode(varnames[1:])


@register.inclusion_tag('debugtools/sql_queries.html', takes_context=True)
def print_queries(context):
    return context_processors.debug(context['request'])


RE_SQL_NL = re.compile(r'\b(FROM|LEFT OUTER|RIGHT|LEFT|INNER|OUTER|WHERE|ORDER BY|GROUP BY)\b')
RE_SQL = re.compile(r'\b(SELECT|UPDATE|DELETE'
                    r'|COUNT|AVG|MAX|MIN|CASE'
                    r'|FROM|SET'
                    r'|ORDER|GROUP|BY|ASC|DESC'
                    r'|WHERE|AND|OR|IN|LIKE|BETWEEN|IS|NULL'
                    r'|LEFT|RIGHT|INNER|OUTER|JOIN|HAVING)\b')
@register.filter
def format_sql(sql):
    sql = escape(sql)
    sql = RE_SQL_NL.sub('<br>\n\\1', sql)
    sql = RE_SQL.sub('<strong>\\1</strong>', sql)
    return mark_safe(sql)


@register.filter
def format_sql_time(time):
    return time * 1000


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
        if hasattr(object, '__dict__'):
            # Instead of just printing <SomeType at 0xfoobar>, expand the fields
            # Construct a dictionary that will be passed to pformat()

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
            attrs['__str__'] = smart_str(object)  # smart_str() avoids crashes because of unicode chars.
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

                attrs[member] = value

            _format_values(attrs)
            object = attrs

        elif isinstance(object, dict):
            object = object.copy()
            _format_values(object)

        try:
            text = pformat(object)
        except Exception, e:
            text = "<caught %s while rendering: %s>" % (e.__class__.__name__, str(e) or "<no msg>")

        text = text.replace("'__ITER__'", '<iterator object>')
        text = text.replace("<django.utils.functional.__proxy__ object", '<proxy object')

    return text

def _format_values(attrs):
    # Format some values for better display
    for name, value in attrs.iteritems():
        if isinstance(value, BoundField):
            attrs[name] = str(value) + "???"
        elif isinstance(value, Node):
            # The Block node is very verbose, making debugging hard.
            attrs[name] = "<Block Node: %s, ...>" % value.name
