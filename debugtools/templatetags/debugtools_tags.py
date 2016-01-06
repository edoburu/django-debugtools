"""
Debugging features in in the template.
"""
from django.template import Library, Node, Variable, VariableDoesNotExist
from django.template.defaultfilters import linebreaksbr
from django.utils import six
from django.utils.functional import Promise
from django.utils.html import escape, mark_safe

from debugtools.formatter import pformat_sql_html, pformat_django_context_html, pformat_dict_summary_html

try:
    from django.template import context_processors  # Django 1.8+
except ImportError:
    from django.core import context_processors


SHORT_NAME_TYPES = (bool,int,float,Promise) + six.string_types

DEBUG_WRAPPER_BLOCK = u'<div class="django-debugtools-output" style="z-index: 10001; position: relative; clear: both;">{0}</div>'

# Twitter Bootstrap <pre> style:
PRE_STYLE = u"""clear: both; font-family: Menlo,Monaco,"Courier new",monospace; color: #333; background-color: #f5f5f5; border: 1px solid rgba(0, 0, 0, 0.15); border-radius: 4px 4px 4px 4px; font-size: 12.025px; text-align: left; line-height: 18px; margin: 9px; padding: 8px;"""

PRE_ALERT_STYLE = u"""clear: both; font-family: Menlo,Monaco,"Courier new",monospace; color: #C09853; background-color: #FCF8E3; border: 1px solid #FBEED5; border-radius: 4px 4px 4px 4px; font-size: 12.025px; text-align: left; line-height: 18px; margin-bottom: 18px; padding: 8px 35px 8px 14px; text-shadow: 0 1px 0 rgba(255, 255, 255, 0.5); white-space: pre-wrap; word-break: normal; word-wrap: normal;"""  # different word-wrap then Twitter Bootstrap

CONTEXT_TITLE = u'<h6 style="color: #999999; font-size: 11px; margin: 9px 0;">TEMPLATE CONTEXT SCOPE:</h6>\n'

CONTEXT_BLOCK = \
    u"<pre style='{style}; position: relative;'>" \
    u"<small style='position:absolute; top: 9px; left: 5px; background-color: #f5f5f5;'><a href='#' onclick='var s1=this.parentNode.nextSibling, s2=s1.nextSibling, d1=s1.style.display, d2=s2.style.display; s1.style.display=d2; s2.style.display=d1; return false'>{num}:</a></small>" \
    u"<span>{dump1}</span><span style='display:none'>{dump2}</span></pre>"

BASIC_TYPE_BLOCK = u"<pre style='{style}'>{name} = {value}</pre>"

ERROR_TYPE_BLOCK = u"<pre style='{style}'>{error}</pre>"

OBJECT_TYPE_BLOCK = u"<pre style='{style}'>{name} = <small>{type}</small>:\n{value}</pre>"



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
            text = self.print_variables(context)
        else:
            text = self.print_context(context)
        return mark_safe(DEBUG_WRAPPER_BLOCK.format(text))

    def print_context(self, context):
        """
        Print the entire template context
        """
        text = [CONTEXT_TITLE]
        for i, context_scope in enumerate(context):
            dump1 = linebreaksbr(pformat_django_context_html(context_scope))
            dump2 = pformat_dict_summary_html(context_scope)

            # Collapse long objects by default (e.g. request, LANGUAGES and sql_queries)
            if len(context_scope) <= 3 and dump1.count('<br />') > 20:
                (dump1, dump2) = (dump2, dump1)

            text.append(CONTEXT_BLOCK.format(
                style=PRE_STYLE,
                num=i,
                dump1=dump1,
                dump2=dump2
            ))
        return u''.join(text)

    def print_variables(self, context):
        """
        Print a set of variables
        """
        text = []
        for name, expr in self.variables:
            # Some extended resolving, to handle unknown variables
            data = ''
            try:
                if isinstance(expr.var, Variable):
                    data = expr.var.resolve(context)
                else:
                    data = expr.resolve(context)  # could return TEMPLATE_STRING_IF_INVALID
            except VariableDoesNotExist as e:
                # Failed to resolve, display exception inline
                keys = []
                for scope in context:
                    keys += scope.keys()
                keys = sorted(set(keys))  # Remove duplicates, e.g. csrf_token
                return ERROR_TYPE_BLOCK.format(style=PRE_ALERT_STYLE, error=escape(u"Variable '{0}' not found!  Available context variables are:\n\n{1}".format(expr, u', '.join(keys))))
            else:
                # Regular format
                textdata = linebreaksbr(pformat_django_context_html(data))

            # At top level, prefix class name if it's a longer result
            if isinstance(data, SHORT_NAME_TYPES):
                text.append(BASIC_TYPE_BLOCK.format(style=PRE_STYLE, name=name, value=textdata))
            else:
                text.append(OBJECT_TYPE_BLOCK.format(style=PRE_STYLE, name=name, type=data.__class__.__name__, value=textdata))
        return u''.join(text)


@register.tag('print')
def _print(parser, token):
    """
    A template tag which prints dumps the contents of objects.
    """
    return PrintNode.parse(parser, token)


@register.inclusion_tag('debugtools/sql_queries.html', takes_context=True)
def print_queries(context):
    return context_processors.debug(context['request'])


@register.filter
def format_sql(sql):
    return mark_safe(pformat_sql_html(sql))


def _format_exception(exception):
    return u'<span style="color: #B94A48;">{0}</span>'.format(escape('<{0}>'.format(exception)))
