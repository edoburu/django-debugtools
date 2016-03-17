# following PEP 440
__version__ = "1.6"

VERSION = (1, 6, 0)

import django
if django.VERSION < (1, 9):
    # Make sure the ``{% print %}`` is always available, even without a {% load debugtools_tags %} call.
    # This feature is no longer available in Django 1.9, which adds an explicit configuration for it:
    # see: https://docs.djangoproject.com/en/1.9/releases/1.9/#django-template-base-add-to-builtins-is-removed
    #
    # This function is used here because the {% print %} tag is a debugging aid,
    # and not a tag that should remain permanently in your templates. Convenience is preferred here.
    #
    from django.template.base import add_to_builtins
    add_to_builtins("debugtools.templatetags.debugtools_tags")
