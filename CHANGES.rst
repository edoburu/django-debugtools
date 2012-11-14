Changes in upcoming version (dev)
---------------------------------

* Better error message for ``{% print non_existing_var %}``.
* Optimize ``XViewMiddleware``, using ``find_template()`` instead of ``get_template()``.
* Fix ``XViewMiddleware`` error with custom object-based views (e.g. the old ``FormWizard``)
* Fix formatting the first object in a dictionary.
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
