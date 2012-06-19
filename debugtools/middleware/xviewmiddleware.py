from django.conf import settings
from django import http

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
            request._xview = "{0}.{1}".format(view_func.__module__, view_func.__name__)

    def process_response(self, request, response):
        if hasattr(request, '_xview'):
            response['X-View'] = request._xview
        if hasattr(response, 'template_name'):
            response['X-View-Template'] = response.template_name
        return response
