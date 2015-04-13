"""
An enhanced ``pprint.pformat`` that prints data structures in a readable HTML style.
"""
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.core.urlresolvers import NoReverseMatch
from django.db import IntegrityError
from django.db.models.base import Model
from django.db.models.manager import Manager
from django.db.models.query import QuerySet
from django.forms.forms import BaseForm
from django.template import Node
from django.utils import six
from django.utils.encoding import smart_str
from django.utils.functional import Promise
from django.utils.html import escape
from itertools import chain
from pprint import pformat
import re
import inspect
import types
import sys
from django.utils.safestring import mark_safe

if sys.version_info[0] >= 3:
    py3_str = str
else:
    py3_str = unicode


DICT_EXPANDED_TYPES = (bool, int,) + six.string_types

RE_SQL_NL = re.compile(r'\b(FROM|LEFT OUTER|RIGHT|LEFT|INNER|OUTER|WHERE|ORDER BY|GROUP BY)\b')
RE_SQL = re.compile(r'\b(SELECT|UPDATE|DELETE'
                    r'|COUNT|AVG|MAX|MIN|CASE'
                    r'|FROM|SET'
                    r'|ORDER|GROUP|BY|ASC|DESC|LIMIT'
                    r'|WHERE|AND|OR|IN|LIKE|BETWEEN|IS|NULL'
                    r'|LEFT|RIGHT|INNER|OUTER|JOIN|HAVING)\b')

def pformat_sql_html(sql):
    """
    Highlight common SQL words in a string.
    """
    sql = escape(sql)
    sql = RE_SQL_NL.sub(u'<br>\n\\1', sql)
    sql = RE_SQL.sub(u'<strong>\\1</strong>', sql)
    return sql


def pformat_django_context_html(object):
    """
    Dump a variable to a HTML string with sensible output for template context fields.
    It filters out all fields which are not usable in a template context.
    """
    if isinstance(object, QuerySet):
        text = ''
        lineno = 0
        for item in object.all()[:21]:
            lineno += 1
            if lineno >= 21:
                text += u'   (remaining items truncated...)'
                break
            text += u'   {0}\n'.format(escape(repr(item)))
        return text
    elif isinstance(object, Manager):
        return mark_safe(u'    (use <kbd>.all</kbd> to read it)')
    elif isinstance(object, six.string_types):
        return escape(repr(object))
    elif isinstance(object, Promise):
        # lazy() object
        return escape(_format_lazy(object))
    else:
        if hasattr(object, '__dict__'):
            # Instead of just printing <SomeType at 0xfoobar>, expand the fields.
            # Construct a dictionary that will be passed to pformat()

            attrs = iter(object.__dict__.items())
            if object.__class__:
                # Add class members too.
                attrs = chain(attrs, iter(object.__class__.__dict__.items()))

            # Remove private and protected variables
            # Filter needless exception classes which are added to each model.
            # Filter unremoved form.Meta (unline model.Meta) which makes no sense either
            is_model = isinstance(object, Model)
            is_form = isinstance(object, BaseForm)
            attrs = dict(
                (k, v)
                for k, v in attrs
                    if not k.startswith('_')
                    and not getattr(v, 'alters_data', False)
                    and not (is_model and k in ('DoesNotExist', 'MultipleObjectsReturned'))
                    and not (is_form and k in ('Meta',))
            )

            # Add members which are not found in __dict__.
            # This includes values such as auto_id, c, errors in a form.
            for member in dir(object):
                if member.startswith('_') or not hasattr(object, member):
                    continue

                value = getattr(object, member)
                if callable(value) or member in attrs or getattr(value, 'alters_data', False):
                    continue

                attrs[member] = value

            # Format property objects
            for name, value in list(attrs.items()):  # not iteritems(), so can delete.
                if isinstance(value, property):
                    attrs[name] = _try_call(lambda: getattr(object, name))
                elif isinstance(value, types.FunctionType):
                    spec = inspect.getargspec(value)
                    if len(spec.args) == 1 or len(spec.args) == len(spec.defaults or ()) + 1:
                        if 'delete' in name or 'save' in name:
                            # The delete and save methods should have an alters_data = True set.
                            # however, when delete or save methods are overridden, this is often missed.
                            attrs[name] = LiteralStr('<Skipped for safety reasons (could alter the database)>')
                        else:
                            # should be simple method(self) signature to be callable in the template
                            # function may have args (e.g. BoundField.as_textarea) as long as they have defaults.
                            attrs[name] = _try_call(lambda: value(object))
                    else:
                        del attrs[name]
                elif hasattr(value, '__get__'):
                    # fetched the descriptor, e.g. django.db.models.fields.related.ForeignRelatedObjectsDescriptor
                    attrs[name] = value = _try_call(lambda: getattr(object, name))
                    if isinstance(value, Manager):
                        attrs[name] = LiteralStr('<{0} manager>'.format(value.__class__.__name__))
                    elif isinstance(value, AttributeError):
                        del attrs[name]  # e.g. Manager isn't accessible via Model instances.

            # Include representations which are relevant in template context.
            if getattr(object, '__str__', None) is not object.__str__:
                attrs['__str__'] = _try_call(lambda: smart_str(object))
            elif getattr(object, '__unicode__', None) is not object.__unicode__:
                attrs['__unicode__'] = _try_call(lambda: smart_str(object))

            if hasattr(object, '__iter__'):
                attrs['__iter__'] = LiteralStr('<iterator object>')
            if hasattr(object, '__getitem__'):
                attrs['__getitem__'] = LiteralStr('<dynamic item>')
            if hasattr(object, '__getattr__'):
                attrs['__getattr__'] = LiteralStr('<dynamic attribute>')

            # Add known __getattr__ members which are useful for template designers.
            if isinstance(object, BaseForm):
                for field_name in list(object.fields.keys()):
                    attrs[field_name] = object[field_name]
                del attrs['__getitem__']


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
        except Exception as e:
            return escape(u"<caught %s while rendering: %s>" % (e.__class__.__name__, py3_str(e) or "<no exception message>"))

        return _style_text(text)


def pformat_dict_summary_html(dict):
    """
    Briefly print the dictionary keys.
    """
    if not dict:
        return _style_text('{}')

    text = []
    for key in sorted(dict.keys()):
        value = dict[key]
        if isinstance(value, DICT_EXPANDED_TYPES):
            text.append(u"'{0}': {1}".format(key, value))
        else:
            text.append(u"'{0}': ...".format(key))

    return _style_text(u'{' + u',\n '.join(text) + u'}')


# The start marker helps to detect the beginning of a new element.
_start = r'([{\[ ])'  # Allow to start with {, [ or space.
RE_PROXY = re.compile(escape(_start + r'<django.utils.functional.__proxy__ object at 0x[0-9a-f]+>'))
RE_FUNCTION = re.compile(escape(_start + r'<function [^ ]+ at 0x[0-9a-f]+>'))
RE_GENERATOR = re.compile(escape(_start + r'<generator object [^ ]+ at 0x[0-9a-f]+>'))
RE_OBJECT_ADDRESS = re.compile(escape(_start + r'<([^ ]+) object at 0x[0-9a-f]+>'))
RE_MANAGER = re.compile(escape(_start + r'<([^ ]+) manager>'))
RE_CLASS_REPR = re.compile(escape(_start + r"<class '([^']+)'>"))
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
    text = text.replace(' &lt;iterator object&gt;', " <small>&lt;<var>this object can be used in a 'for' loop</var>&gt;</small>")
    text = text.replace(' &lt;dynamic item&gt;', ' <small>&lt;<var>this object may have extra field names</var>&gt;</small>')
    text = text.replace(' &lt;dynamic attribute&gt;', ' <small>&lt;<var>this object may have extra field names</var>&gt;</small>')
    text = RE_PROXY.sub('\g<1><small>&lt;<var>proxy object</var>&gt;</small>', text)
    text = RE_FUNCTION.sub('\g<1><small>&lt;<var>object method</var>&gt;</small>', text)
    text = RE_GENERATOR.sub("\g<1><small>&lt;<var>generator, use 'for' to traverse it</var>&gt;</small>", text)
    text = RE_OBJECT_ADDRESS.sub('\g<1><small>&lt;<var>\g<2> object</var>&gt;</small>', text)
    text = RE_MANAGER.sub('\g<1><small>&lt;<var>manager, use <kbd>.all</kbd> to traverse it</var>&gt;</small>', text)
    text = RE_CLASS_REPR.sub('\g<1><small>&lt;<var>\g<2> class</var>&gt;</small>', text)
    text = RE_FIELD_END.sub('\g<1>', text)
    text = RE_FIELDNAME.sub('   <strong style="color: #222;">\g<1></strong>: ', text)  # need 3 spaces indent to compensate for missing '..'

    # Since Django's WSGIRequest does a pprint like format for it's __repr__, make that styling consistent
    text = RE_REQUEST_FIELDNAME.sub('\g<1>:\n   <strong style="color: #222;">\g<2></strong>: ', text)
    text = RE_REQUEST_CLEANUP1.sub('\g<1>', text)
    text = RE_REQUEST_CLEANUP2.sub(')', text)

    return mark_safe(text)


def _format_dict_values(attrs):
    # Format some values for better display
    for name, value in attrs.items():
        attrs[name] = _format_value(value)


def _format_value(value):
    if isinstance(value, Node):
        # The Block node is very verbose, making debugging hard.
        return LiteralStr(u"<Block Node: {0}, ...>".format(value.name))
    elif isinstance(value, Promise):
        # lazy() object
        return _format_lazy(value)
    else:
        return value


def _format_lazy(value):
    args = value._proxy____args
    kw = value._proxy____kw
    if not kw and len(args) == 1 and isinstance(args[0], six.string_types):
        # Found one of the Xgettext_lazy() calls.
        return LiteralStr(u'ugettext_lazy({0})'.format(repr(value._proxy____args[0])))

    # Prints <django.functional.utils.__proxy__ object at ..>
    return value


def _try_call(func, extra_exceptions=()):
    try:
        return func()
    except (TypeError, KeyError, AttributeError, ValueError,
            ObjectDoesNotExist, MultipleObjectsReturned, IntegrityError, NoReverseMatch,
            AssertionError, NotImplementedError) as e:
        return e
    except extra_exceptions as e:
        return e


class LiteralStr(object):
    """
    A trick to make pformat() print a custom string without quotes.
    """
    def __init__(self, rawvalue):
        self.rawvalue = rawvalue

    def __repr__(self):
        if isinstance(self.rawvalue, six.string_types):
            return self.rawvalue
        else:
            return repr(self.rawvalue)
