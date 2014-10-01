Changes in version 1.2.1
------------------------

* Added Django 1.7 support


Changes in version 1.2
----------------------

* Added Python 3 support
* Dropped Django 1.3 support


Changes in version 1.1.2
------------------------

* Better CSS clearing
* Avoid calling ``save()`` or ``delete()`` even when ``alters_data`` flag is missing.
  That typically happens when those methods are overwritten.


Changes in version 1.1.1
------------------------

* Better error message for ``{% print non_existing_var %}``.
* Optimize ``XViewMiddleware``, using ``find_template()`` instead of ``get_template()``.
* Fix ``XViewMiddleware`` error with custom object-based views (e.g. the old ``FormWizard``)
* Fix formatting the first object in a dictionary.
* Handle ``NoReverseMatch`` error in ``{% print %}`` tag.
* Add ``text-align: left;`` to ``{% print %}`` tag.


Changes in version 1.1.0
------------------------

* Improved ``print`` tag:

 * Better support printing ``Model``, ``Manager`` and ``BoundField`` classes.
 * Reduce clutter of context levels, by collapsing long variables and improving display.
 * No longer need to use ``{% load debug_tags %}``, can always use ``{% print %}`` directly.
 * Fix displaying functions when all arguments have default values.
 * Fix displaying ``__unicode__`` if ``__str__`` is not present.
 * Fix ``z-index`` issues in the output.

* The ``X-Template-Name`` header shows the chosen template name if there is a list of choices.
* Fix missing template for ``{% print_queries %}`` tag.


Changes in version 1.0.0
------------------------

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


Changes in version 0.9.0
------------------------

First public beta release

* ``print`` template tag
