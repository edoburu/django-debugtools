"""
INTERNAL FUNCTIONS FOR XViewMiddleware and ViewPanel
"""
from django.conf import settings
from django.template import TemplateDoesNotExist
from django.template.loader import get_template
from django.utils import six


def track_view_name(request, view_func):
    if request.META.get('REMOTE_ADDR') in settings.INTERNAL_IPS or (request.user.is_active and request.user.is_staff):
        view_name = "{0}.{1}".format(view_func.__module__, get_view_name(view_func))
        request._xview = view_name
        return view_name


def get_view_name(view_func):
    if not hasattr(view_func, '__name__'):
        # e.g. django.contrib.formtools.views.FormWizard object with __call__() method
        return view_func.__class__.__name__
    else:
        return view_func.__name__


def get_used_view_name(request):
    return getattr(request, '_xview', None)


def get_used_template(response):
    """
    Get the template used in a TemplateResponse.
    This returns a tuple of "active choice, all choices"
    """
    if not hasattr(response, 'template_name'):
        return None, None

    template = response.template_name
    if template is None:
        return None, None

    if isinstance(template, (list, tuple)):
        # See which template name was really used.
        if len(template) == 1:
            return template[0], None
        else:
            used_name = _get_used_template_name(template)
            return used_name, template
    elif isinstance(template, six.string_types):
        # Single string
        return template, None
    else:
        # Template object.
        filename = _get_template_filename(template)
        template_name = '<template object from {0}>'.format(filename) if filename else '<template object>'
        return template_name, None



def _get_used_template_name(template_name_list):
    """
    Find which template of the template_names is selected by the Django loader.
    """
    for template_name in template_name_list:
        try:
            get_template(template_name)
            return template_name
        except TemplateDoesNotExist:
            continue


def _get_template_filename(template):
    # With TEMPLATE_DEBUG = True, each node tracks it's origin.
    try:
        return template.nodelist[0].origin[0].name
    except (AttributeError, IndexError):
        return None
