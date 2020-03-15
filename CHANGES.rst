Changes in version 1.8 (2020-03-15)
-----------------------------------

* Added Django 3.0 support.
* Reformatted with isort and black.


Changes in version 1.7.4 (2019-02-11)
-------------------------------------

* Fixed Python 3.6 function display.


Changes in version 1.7.3 (2018-02-13)
-------------------------------------

* Fixed Django 2.0 imports.
* Add ``__len__`` to the output of objects.


Changes in version 1.7.2 (2017-01-27)
-------------------------------------

* Fixed raising exceptions on ``hasattr()`` check, which may invoke the property too
* Fixed displaying ``RuntimeError`` on invalid attributes.
* Fixed appearance of exception messages, and other informative output.


Changes in version 1.7.1 (2017-01-04)
-------------------------------------

* Added Django 1.10 MiddlewareMixin for ``XViewMiddleware``.
* Fixed Python 3 compatibility.
* Avoid calling functions like ``clean*`` and ``copy`` in debugging functions.
  This is an extra safety guard, which protects Wagtail 1.7 and below from copying pages.


Changes in version 1.7 (2016-08-07)
-----------------------------------

* Improved the debug panel to show models, forms and formsets too.
* Fixed Python 3 compatibility.


Changes in version 1.6 (2016-03-17)
-----------------------------------

* Improved appearance of output.

 * Better dict/list expansion.
 * Better appearance of exceptions.
 * Simplier appearance of BlockNode
 * Fixed ``,`` sign at the end of values.


Changes in version 1.5.1 (2016-02-16)
-------------------------------------

* Fixed Django 1.7+ block rendering in general ``{% print %}`` display.
* Fixed HTML of 'empty dict' message.
* Fixed deprecation warning.


Changes in version 1.5 (2016-01-06)
-----------------------------------

* Added Django 1.9 support, use ``builtins`` in the settings to add the tag, or ``{% load debugtools_tags %}`` instaed.
* Fixed manifest, added missing ``static/debugtools/jquery.debug.js`` file in the package.
* Dropped Django 1.5- support for   ``{% print_queries %}``.


Changes in version 1.4 (2015-07-29)
-----------------------------------

* Avoid ``X-View-Template`` output when ``template_name`` is ``None``.
* Added django-debug-toolbar_ panel: ``debugtools.panels.ViewPanel``.


Changes in version 1.3 (2015-04-13)
-----------------------------------

* Added Django 1.8 support
* Clarify the ``<skipped for safety reasons ..>`` message for ``...delete...()`` and ``...save...()`` methods in the ``{% print %}`` output.


Changes in version 1.2.1 (2014-10-01)
-------------------------------------

* Added Django 1.7 support


Changes in version 1.2 (2014-10-01)
-----------------------------------

* Added Python 3 support
* Dropped Django 1.3 support


Changes in version 1.1.2 (2014-03-20)
-------------------------------------

* Better CSS clearing
* Avoid calling ``save()`` or ``delete()`` even when ``alters_data`` flag is missing.
  That typically happens when those methods are overwritten.


Changes in version 1.1.1 (2013-09-25)
-------------------------------------

* Better error message for ``{% print non_existing_var %}``.
* Optimize ``XViewMiddleware``, using ``find_template()`` instead of ``get_template()``.
* Fix ``XViewMiddleware`` error with custom object-based views (e.g. the old ``FormWizard``)
* Fix formatting the first object in a dictionary.
* Handle ``NoReverseMatch`` error in ``{% print %}`` tag.
* Add ``text-align: left;`` to ``{% print %}`` tag.


Changes in version 1.1.0 (2012-09-14)
-------------------------------------

* Improved ``print`` tag:

 * Better support printing ``Model``, ``Manager`` and ``BoundField`` classes.
 * Reduce clutter of context levels, by collapsing long variables and improving display.
 * No longer need to use ``{% load debug_tags %}``, can always use ``{% print %}`` directly.
 * Fix displaying functions when all arguments have default values.
 * Fix displaying ``__unicode__`` if ``__str__`` is not present.
 * Fix ``z-index`` issues in the output.

* The ``X-Template-Name`` header shows the chosen template name if there is a list of choices.
* Fix missing template for ``{% print_queries %}`` tag.


Changes in version 1.0.0 (2012-08-17)
-------------------------------------

* Enhanced ``print`` tag:

 * Added CSS styling.
 * Added JavaScript collapsing for context blocks.
 * Support printing of ``ugettext_lazy`` values.
 * Support printing template expressions.
 * Support printing ``BaseForm.__getitem__`` values.
 * Support printing functions that are callable by Django templates.

* Added ``XViewMiddleware`` to print view + template name.
* Added simple ``print_queries`` template tag.
* Added jQuery ``debug()`` function.


Changes in version 0.9.0 (2012-04-02)
-------------------------------------

First public beta release

* ``print`` template tag


.. _django-debug-toolbar: https://github.com/django-debug-toolbar/django-debug-toolbar
