Introduction
============

The ``debugtools`` module offers some easy to use debugging utilities to assist Django development.
It features:

* A template tag to print context.
* A ``XViewMiddleware`` variation which works for all request types.


Installation
============

First install the module, preferably in a virtual environment. It can be installed from PyPI::

    pip install django-debugtools

Or the current folder can be installed::

    pip install .

Configuration
-------------

Add the module to the installed apps::

    INSTALLED_APPS += (
        'debugtools',
    )

Usage
-----

Template tag
~~~~~~~~~~~~

In Django templates, the following code can be used::

    {% load debug_tags %}

    {% print variable1 variable2 %}

To get a global overview of template variables::

    {% print %}

The template context variables are printed in a customized ``pprint.pformat`` format, for easy reading.


Middleware
~~~~~~~~~~

Add the following setting::

    INTERNAL_IPS = (
        '127.0.0.1',
    )

    MIDDLEWARE_CLASSES += (
        'debugtools.middleware.XViewMiddleware',
    )

All requests from the internal IP, or made admin user will have a ``X-View`` header
which reveals the view code handled the current request.

