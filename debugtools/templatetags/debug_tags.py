"""
Debugging features in in the template.
"""

__author__ = "Diederik van der Boor"
__license__ = "Apache License, Version 2"

from django.core import context_processors
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.core.serializers import serialize
from django.db.models.query import QuerySet
from django.forms.forms import BoundField, BaseForm
from django.template import Library, Node, Variable, VariableDoesNotExist
from django.template.defaultfilters import linebreaksbr
from django.utils.encoding import smart_str
from django.utils.functional import Promise
from django.utils.html import escape, mark_safe, conditional_escape
from itertools import chain
from pprint import pformat
import re
import inspect
import types


# Twitter bootstrap <pre> style:
PRE_STYLE = u"""clear: both; font-family: Menlo,Monaco,"Courier new",monospace; color: #333; background-color: #f5f5f5; border: 1px solid rgba(0, 0, 0, 0.15); border-radius: 4px 4px 4px 4px; font-size: 12.025px; line-height: 18px; margin: 9px; padding: 8px;"""


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
        text = [u'<h6 style="color: #999999; font-size: 11px; margin: 9px 0;">TEMPLATE CONTEXT SCOPE:</h6>\n']
        for i, part in enumerate(context):
            code = u"<pre style='{style}; position: relative;'>" \
                   u"<small style='position:absolute; top: 9px; left: 5px; background-color: #f5f5f5;'><a href='#' onclick='var s1=this.parentNode.nextSibling, s2=s1.nextSibling, d1=s1.style.display, d2=s2.style.display; s1.style.display=d2; s2.style.display=d1; return false'>{num}:</a></small>" \
                   u"<span>{dump1}</span><span style='display:none'>{dump2}</span></pre>"
            text.append(code.format(style=PRE_STYLE, num=i, dump1=linebreaksbr(_dump_var_html(part)), dump2=_dict_summary_html(part)))
        return mark_safe(u''.join(text))

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
                textdata = u'<span style="color: #B94A48;">{0}</span>'.format(escape('<{0}>'.format(e)))
            else:
                textdata = linebreaksbr(_dump_var_html(data))

            # At top level, prefix class name if it's a longer result
            if isinstance(data, (bool,int,basestring,float, Promise)):
                text.append(u"<pre style='{0}'>{1} = {2}</pre>".format(PRE_STYLE, name, textdata))
            else:
                text.append(u"<pre style='{0}'>{1} = <small>{2}</small>:\n{3}</pre>".format(PRE_STYLE, name, data.__class__.__name__, textdata))
        return mark_safe(u''.join(text))


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
    sql = RE_SQL_NL.sub(u'<br>\n\\1', sql)
    sql = RE_SQL.sub(u'<strong>\\1</strong>', sql)
    return mark_safe(sql)



# ---- Internal print helper ----

def _dump_var_html(object):
    """
    A variable dumper to generate sensible output for template context fields.
    """
    if isinstance(object, QuerySet):
        return escape(serialize('python', object))
    elif isinstance(object, basestring):
        return escape(repr(object))
    elif isinstance(object, Promise):
        # lazy() object
        return escape(_format_lazy(object))
    else:
        if hasattr(object, '__dict__'):
            # Instead of just printing <SomeType at 0xfoobar>, expand the fields.
            # Construct a dictionary that will be passed to pformat()

            attrs = object.__dict__.iteritems()
            if object.__class__:
                # Add class members too.
                attrs = chain(attrs, object.__class__.__dict__.iteritems())

            # Remove private and protected variables
            # Filter needless exception classes which are added to each model.
            attrs = dict(
                (k, v)
                for k, v in attrs
                    if not k.startswith('_')
                    and not getattr(v, 'alters_data', False)
                    and not (isinstance(v, type) and issubclass(v, (ObjectDoesNotExist, MultipleObjectsReturned)))
            )

            # Add members which are not found in __dict__.
            # This includes values such as auto_id, c, errors in a form.
            for member in dir(object):
                if member.startswith('_') or not hasattr(object, member):
                    continue

                value = getattr(object, member)
                if callable(value) or attrs.has_key(member) or getattr(value, 'alters_data', False):
                    continue

                attrs[member] = value

            # Add known __getattr__ members which are useful for template designers.
            if isinstance(object, BaseForm):
                for field_name in object.fields.keys():
                    attrs[field_name] = object[field_name]


            # Format property objects
            for name, value in attrs.items():  # not iteritems(), so can delete.
                if isinstance(value, property):
                    attrs[name] = _try_call(lambda: getattr(object, name))
                elif isinstance(value, types.FunctionType):
                    spec = inspect.getargspec(value)
                    if len(spec.args) != 1:
                        # should be simple method(self) signature to be callable in the template
                        del attrs[name]
                    #else:
                    #    attrs[name] = _try_call(lambda: value(object))


            # Include representations which are relevant in template context.
            attrs['__str__'] = _try_call(lambda: smart_str(object))

            if hasattr(object, '__iter__'):
                attrs['__iter__'] = LiteralStr('<iterator object>')
            if hasattr(object, '__getitem__'):
                attrs['__getitem__'] = LiteralStr('<dynamic attribute>')

            _format_dict_values(attrs)
            object = attrs

        elif isinstance(object, dict):
            object = object.copy()
            _format_dict_values(object)

        elif isinstance(object, list):
            object = object[:]
            for i, value in enumerate(object):
                object[i] = _format_value(value)

        # Format it
        try:
            text = pformat(object)
        except Exception, e:
            return u"<caught %s while rendering: %s>" % (e.__class__.__name__, str(e) or "<no exception message>")

        return _style_text(text)


def _dict_summary_html(dict):
    return _style_text('{' + ',\n '.join("'{0}': ...".format(key) for key in sorted(dict.iterkeys())) + '}')


RE_PROXY = re.compile(escape(r'([\[ ])' + r'<django.utils.functional.__proxy__ object at 0x[0-9a-f]+>'))
RE_FUNCTION = re.compile(escape(r'([\[ ])' + r'<function [^ ]+ at 0x[0-9a-f]+>'))
RE_GENERATOR = re.compile(escape(r'([\[ ])' + r'<generator object [^ ]+ at 0x[0-9a-f]+>'))
RE_OBJECT_ADDRESS = re.compile(escape(r'([\[ ])' + r'<([^ ]+) object at 0x[0-9a-f]+>'))
RE_CLASS_REPR = re.compile(escape(r'([\[ ])' + r"<class '([^']+)'>"))
RE_FIELD_END = re.compile(escape(r",([\r\n] ')"))
RE_FIELDNAME = re.compile(escape(r"^ u?'([^']+)': "), re.MULTILINE)
RE_REQUEST_FIELDNAME = re.compile(escape(r"^(\w+):\{'([^']+)': "), re.MULTILINE)
RE_REQUEST_CLEANUP1 = re.compile(escape(r"\},([\r\n]META:)"))
RE_REQUEST_CLEANUP2 = re.compile(escape(r"\)\}>$"))

def _style_text(text):
    # Escape text and apply some formatting.
    # To have really good highlighting, pprint would have to be re-implemented.

    # Remove dictionary sign. that was just a trick for pprint
    if text == '{}':
        return '   <small>(<var>empty dict</var>)</small>'
    if text[0] == '{':  text = ' ' + text[1:]
    if text[-1] == '}': text = text[:-1]

    text = escape(text)
    text = text.replace(' &lt;iterator object&gt;', ' <small>&lt;<var>iterator object</var>&gt;</small>')
    text = text.replace(' &lt;dynamic attribute&gt;', ' <small>&lt;<var>dynamic attribute</var>&gt;</small>')
    text = RE_PROXY.sub('\g<1><small>&lt;<var>proxy object</var>&gt;</small>', text)
    text = RE_FUNCTION.sub('\g<1><small>&lt;<var>object method</var>&gt;</small>', text)
    text = RE_GENERATOR.sub('\g<1><small>&lt;<var>generator object</var>&gt;</small>', text)
    text = RE_OBJECT_ADDRESS.sub('\g<1><small>&lt;\g<2> object</var>&gt;</small>', text)
    text = RE_CLASS_REPR.sub('\g<1><small>&lt;\g<2> class</var>&gt;</small>', text)
    text = RE_FIELD_END.sub('\g<1>', text)
    text = RE_FIELDNAME.sub('   <strong style="color: #222;">\g<1></strong>: ', text)  # need 3 spaces indent to compensate for missing '..'

    # Since Django's WSGIRequest does a pprint like format for it's __repr__, make that styling consistent
    text = RE_REQUEST_FIELDNAME.sub('\g<1>:\n   <strong style="color: #222;">\g<2></strong>: ', text)
    text = RE_REQUEST_CLEANUP1.sub('\g<1>', text)
    text = RE_REQUEST_CLEANUP2.sub(')', text)

    return text


def _format_dict_values(attrs):
    # Format some values for better display
    for name, value in attrs.iteritems():
        attrs[name] = _format_value(value)


def _format_value(value):
    if isinstance(value, Node):
        # The Block node is very verbose, making debugging hard.
        return LiteralStr(u"<Block Node: %s, ...>" % value.name)
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


def _try_call(func, extra_exceptions=()):
    try:
        return func()
    except (TypeError, KeyError, AttributeError, ObjectDoesNotExist) as e:
        return e
    except extra_exceptions:
        return e


class LiteralStr(object):
    # Avoid string quotes in pprint()
    def __init__(self, rawvalue):
        self.rawvalue = rawvalue

    def __repr__(self):
        if isinstance(self.rawvalue, basestring):
            return self.rawvalue
        else:
            return repr(self.rawvalue)
