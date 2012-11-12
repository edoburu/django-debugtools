from django.conf import settings
from django.template import TemplateDoesNotExist
from django.template.loader import find_template


class XViewMiddleware(object):
    """
    Adds an X-View header to requests.

    If the request IP is internal or the user is a logged-in staff member,
    add an ``X-View`` header to the response.

    This is a variation of the default Django XViewMiddleware, which only works with HEAD requests
    as it is specifically designed for the documentation system.
    """
    def process_view(self, request, view_func, view_args, view_kwargs):
        assert hasattr(request, 'user'), (
            "The XView middleware requires authentication middleware to be "
            "installed. Edit your MIDDLEWARE_CLASSES setting to insert "
            "'django.contrib.auth.middleware.AuthenticationMiddleware'.")

        if request.META.get('REMOTE_ADDR') in settings.INTERNAL_IPS or (request.user.is_active and request.user.is_staff):
            if not hasattr(view_func, '__name__'):
                # e.g. django.contrib.formtools.views.FormWizard object with __call__() method
                request._xview = "{0}.{1}".format(view_func.__module__, view_func.__class__.__name__)
            else:
                request._xview = "{0}.{1}".format(view_func.__module__, view_func.__name__)


    def process_response(self, request, response):
        if hasattr(request, '_xview'):
            response['X-View'] = request._xview

        if hasattr(response, 'template_name'):
            template = response.template_name

            if isinstance(template, (list, tuple)):
                # See which template name was really used.
                if len(template) == 1:
                    response['X-View-Template'] = template[0]
                else:
                    used_name = _get_used_template_name(template)
                    response['X-View-Template'] = '{0}   (out of: {1})'.format(used_name, ', '.join(template))
            elif isinstance(template, basestring):
                # Single string
                response['X-View-Template'] = template
            else:
                # Template object.
                filename = _get_template_filename(template)
                response['X-View-Template'] = '<template object from {0}>'.format(filename) if filename else '<template object>'

        return response


def _get_used_template_name(template_name_list):
    """
    Find which template of the template_names is selected by the Django loader.
    """
    for template_name in template_name_list:
        try:
            find_template(template_name)
            return template_name
        except TemplateDoesNotExist:
            continue


def _get_template_filename(template):
    # With TEMPLATE_DEBUG = True, each node tracks it's origin.
    try:
        return template.nodelist[0].origin[0].name
    except (AttributeError, IndexError):
        return None
