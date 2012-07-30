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

Features
--------

Print Template Tag
~~~~~~~~~~~~~~~~~~

In Django templates, the following code can be used::

    {% load debug_tags %}
    {% print variable1 variable2 %}

For example, when adding ``{% print inline_admin_formset %}`` to an admin template it produces::

    inline_admin_formset = InlineAdminFormSet...
    {'__iter__': <iterator object>,
     '__str__': '<django.contrib.admin.helpers.InlineAdminFormSet object at 0x1120c8810>',
     'fields': <function fields at 0x110dc2578>,
     'fieldsets': [(None, {'fields': ['slot', 'role', 'title']})],
     'formset': <django.forms.formsets.PlaceholderFormFormSet object at 0x11209ef10>,
     'media': <django.forms.widgets.Media object at 0x111ec75d0>,
     'model_admin': <fluent_pages.pagetypes.fluentpage.admin.FluentPageAdmin object at 0x111a19a50>,
     'opts': <fluent_contents.admin.placeholdereditor.PlaceholderEditorInline object at 0x11202f510>,
     'prepopulated_fields': {},
     'readonly_fields': []}

Subsequently, using::

    {% for form in inline_admin_formset %}{% print form %}{% endfor %}

produces the following results::

    form = InlineAdminForm...
    {'__iter__': <iterator object>,
     '__str__': '<django.contrib.admin.helpers.InlineAdminForm object at 0x11209ee10>',
     'deletion_field': <function deletion_field at 0x110dc2938>,
     'field_count': <function field_count at 0x110dc27d0>,
     'fieldsets': [(None, {'fields': ['slot', 'role', 'title']})],
     'fk_field': <function fk_field at 0x110dc28c0>,
     'form': <django.forms.models.PlaceholderForm object at 0x1124ffb90>,
     'formset': <django.forms.formsets.PlaceholderFormFormSet object at 0x1122fcc90>,
     'has_auto_field': <function has_auto_field at 0x110dc2758>,
     'media': <django.forms.widgets.Media object at 0x112743bd0>,
     'model_admin': <fluent_contents.admin.placeholdereditor.PlaceholderEditorInline object at 0x11273ca10>,
     'ordering_field': <function ordering_field at 0x110dc29b0>,
     'original': <Placeholder: Main>,
     'original_content_type_id': 10L,
     'pk_field': <function pk_field at 0x110dc2848>,
     'prepopulated_fields': [],
     'readonly_fields': [],
     'show_url': True}

This makes it much easier to understand what the code provides to templates.

When no variables are given, all context variables are displayed::

    {% print %}

The template context variables are printed in a customized ``pprint.pformat`` format, for easy reading.

Print Queries template tag
~~~~~~~~~~~~~~~~~~~~~~~~~~

For convenience, there is also a ``{% print_queries %}`` tag,
based on http://djangosnippets.org/snippets/93/

For more sophisticated debugging, you may want to use the *django-debug-toolbar* for this job.


X-View Middleware
~~~~~~~~~~~~~~~~~

Add the following setting::

    INTERNAL_IPS = (
        '127.0.0.1',
    )

    MIDDLEWARE_CLASSES += (
        'debugtools.middleware.XViewMiddleware',
    )

All requests from the internal IP, or made by the admin user will have a ``X-View`` header
and ``X-View-Template`` header. This reveals which view code and template handled the current request.


jQuery debug print
~~~~~~~~~~~~~~~~~~

Add the following to the page::

    <script type="text/javscript" src="{{ STATIC_URL }}debugtools/jquery.debug.js"></script>

Now you can print the jQuery selector context to the console::

    $("#foo").children('li').debug().addClass('bar');

This will print the matched ``<li>`` elements in the console, among with the current jQuery selector.
Optionally, a prefix can be included in the ``debug()`` call::

    $("#foo").debug("at baz: ").addClass('bar');

