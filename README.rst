Introduction
============

The ``debugtools`` module offers some easy to use debugging utilities to assist Django development.

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

In Django templates, the following code can be used::

    {% load debug_tags %}

    {% print variable1 variable2 %}

To get a global overview of template variables::

    {% print %}

The template context variables are printed in a customized ``pprint.pformat`` format, for easy reading.

