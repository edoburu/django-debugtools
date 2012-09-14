Changes in version 1.1.0 (dev)
------------------------------

* Added ``debug_tags`` as template build-ins, can always use ``{% print %}`` now.
* Added default compact view for long cluttering template context levels.
* Improve ``X-Template-Name`` to show the actually used template name out of the available choices.
* Improve appearance of collapsed context scope levels.
* Improve appearance of ``Model``, ``Manager`` and ``BoundField`` classes.
* Fix displaying functions when all arguments have default values.
* Fix displaying ``__unicode__`` if ``__str__`` is not present.
* Fix ``z-index`` issues in the output.
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
