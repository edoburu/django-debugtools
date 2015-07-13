from debugtools.utils.xview import track_view_name, get_used_view_name, get_used_template


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

        track_view_name(request, view_func)


    def process_response(self, request, response):
        view_name = get_used_view_name(request)
        if view_name:
            response['X-View'] = view_name

        template_name, choices = get_used_template(response)
        if template_name:
            if choices:
                response['X-View-Template'] = '{0}   (out of: {1})'.format(template_name, ', '.join(choices))
            else:
                response['X-View-Template'] = template_name
        return response
