"""
Debugging features in in the template.
"""

__author__ = "Diederik van der Boor"
__license__ = "Apache License, Version 2"

from django.core import context_processors
from django.core.exceptions import ObjectDoesNotExist
from django.core.serializers import serialize
from django.db.models.query import QuerySet
from django.forms.forms import BoundField
from django.template import Library, Node, Variable, VariableDoesNotExist
from django.template.defaultfilters import linebreaksbr
from django.utils.encoding import smart_str
from django.utils.functional import Promise
from django.utils.html import escape, mark_safe, conditional_escape
from itertools import chain
from pprint import pformat
import re

# Twitter bootstrap <pre> style:
PRE_STYLE = """clear: both; font-family: Menlo,Monaco,"Courier new",monospace; color: #333; background-color: #f5f5f5; border: 1px solid rgba(0, 0, 0, 0.15); border-radius: 4px 4px 4px 4px; font-size: 12.025px; line-height: 18px; margin: 9px; padding: 8px;"""


register = Library()

class PrintNode(Node):
    @classmethod
    def parse(cls, parser, token):
        varnames = token.contents.split()[1:]
        return cls(
            variables=[(name, parser.compile_filter(name)) for name in varnames]
        )

    def __init__(self, variables):
        # Thread safety OK: the list of varnames won't change for this node.
        # Data is read only inside the render() function.
        self.variables = list(variables)

    def render(self, context):
        if self.variables:
            return self.print_variables(context)
        else:
            return self.print_context(context)

    def print_context(self, context):
        text = ['<h6 style="color: #999999; font-size: 11px; margin: 9px 0;">TEMPLATE CONTEXT SCOPE:</h6>\n']
        for i, part in enumerate(context):
            code = "<pre style='{style}'>" \
                   "<small><a href='#' onclick='var s1=this.parentNode.nextSibling, s2=s1.nextSibling, d1=s1.style.display, d2=s2.style.display; s1.style.display=d2; s2.style.display=d1; return false'>{num}:</a> </small>" \
                   "<span>{dump1}</span><span style='display:none'>{dump2}</span></pre>"
            text.append(code.format(style=PRE_STYLE, num=i, dump1=linebreaksbr(escape(_dump_var(part))), dump2=escape(_dict_summary(part))))
        return mark_safe(''.join(text))

    def print_variables(self, context):
        text = []
        for name, expr in self.variables:
            # Some extended resolving, to handle unknonw variables
            data = ''
            try:
                if isinstance(expr.var, Variable):
                    data = expr.var.resolve(context)
                else:
                    data = expr.resolve(context)  # could return TEMPLATE_STRING_IF_INVALID
            except VariableDoesNotExist as e:
                textdata = '<span style="color: #B94A48;">{0}</span>'.format(escape('<{0}>'.format(e)))
            else:
                textdata = linebreaksbr(escape(_dump_var(data)))

            # At top level, prefix class name if it's a longer result
            if isinstance(data, (bool,int,basestring,float, Promise)):
                text.append("<pre style='{0}'>{1} = {2}</pre>".format(PRE_STYLE, name, textdata))
            else:
                text.append("<pre style='{0}'>{1} = {2}...\n{3}</pre>".format(PRE_STYLE, name, data.__class__.__name__, textdata))
        return mark_safe(''.join(text))


@register.tag('print')
def _print(parser, token):
    """
    A template tag which prints dumps the contents of objects.
    """
    return PrintNode.parse(parser, token)


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



# ---- Internal print helper ----

def _dump_var(object):
    """
    A variable dumper to generate sensible output for template context fields.
    """
    if isinstance(object, QuerySet):
        return serialize('python', object)
    elif isinstance(object, basestring):
        return repr(object)
    elif isinstance(object, Promise):
        # lazy() object
        return _format_lazy(object)
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
                    except (TypeError, AttributeError, ObjectDoesNotExist) as e:
                        attrs[name] = e

            # Include representations which are relevant in template context.
            try:
                attrs['__str__'] = smart_str(object)  # smart_str() avoids crashes because of unicode chars.
            except (TypeError, AttributeError, ObjectDoesNotExist) as e:
                attrs['__str__'] = e

            if hasattr(object, '__iter__'):
                attrs['__iter__'] = LiteralStr('<iterator object>')
            if hasattr(object, '__getitem__'):
                attrs['__getitem__'] = LiteralStr('...')

            # Enrich members with values from dir (e.g. add auto_id)
            for member in dir(object):
                if member.startswith('_') or not hasattr(object, member):
                    continue

                value = getattr(object, member)
                if callable(value) or attrs.has_key(member):
                    continue

                attrs[member] = value

            _format_dict_values(attrs)
            object = attrs

        elif isinstance(object, dict):
            object = object.copy()
            _format_dict_values(object)

        elif isinstance(object, list):
            object = object[:]
            for i, value in enumerate(object):
                object[i] = _format_value(value)

        try:
            text = pformat(object)
        except Exception, e:
            return "<caught %s while rendering: %s>" % (e.__class__.__name__, str(e) or "<no exception message>")

        text = text.replace("<django.utils.functional.__proxy__ object", '<proxy object')
        return text


def _dict_summary(dict):
    return '{' + ', '.join("'{0}': ...".format(key) for key in dict.iterkeys()) + '}'


def _format_dict_values(attrs):
    # Format some values for better display
    for name, value in attrs.iteritems():
        attrs[name] = _format_value(value)


def _format_value(value):
    if isinstance(value, BoundField):
        return str(value) + "???"
    elif isinstance(value, Node):
        # The Block node is very verbose, making debugging hard.
        return "<Block Node: %s, ...>" % value.name
    elif isinstance(value, Promise):
        # lazy() object
        return _format_lazy(value)
    else:
        return value


def _format_lazy(value):
    args = value._proxy____args
    kw = value._proxy____kw
    if not kw and len(args) == 1 and isinstance(args[0], basestring):
        # Found one of the Xgettext_lazy() calls.
        return LiteralStr(u'ugettext_lazy({0})'.format(repr(value._proxy____args[0])))

    # Prints <django.functional.utils.__proxy__ object at ..>
    return value


class LiteralStr(object):
    # Avoid string quotes in pprint()
    def __init__(self, rawvalue):
        self.rawvalue = rawvalue

    def __repr__(self):
        if isinstance(self.rawvalue, basestring):
            return self.rawvalue
        else:
            return repr(self.rawvalue)
