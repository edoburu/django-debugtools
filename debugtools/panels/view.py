from __future__ import absolute_import, unicode_literals

from django.db.models import Model
from django.forms import BaseForm
from django.forms.models import BaseFormSet
from django.utils.translation import ugettext_lazy as _
from django.views.generic import View
from debug_toolbar.panels import Panel
from debugtools.utils.xview import get_view_name, get_used_template


class ViewPanel(Panel):
    """
    Shows versions of Python, Django, and installed apps if possible.
    """
    template = 'debugtools/view_panel.html'
    nav_title = _("View")

    def __init__(self, *args, **kwargs):
        super(ViewPanel, self).__init__(*args, **kwargs)
        self.view_module = None
        self.view_name = None

    def process_view(self, request, view_func, view_args, view_kwargs):
        # Store the information about the view being called.
        self.view_module = view_func.__module__
        self.view_name = get_view_name(view_func)

    def process_response(self, request, response):
        # Find out what template was used.
        template, choices = get_used_template(response)

        # See if more information can be read from the TemplateResponse object.
        if template and getattr(response, 'context_data', None):
            context_data = response.context_data
        else:
            context_data = None

        self.record_stats({
            'view_module': self.view_module,
            'view_name': self.view_name,
            'view_data': self._get_view_data(context_data) if context_data else None,
            'template': template,
            'template_choices': choices,
        })

    def _get_view_data(self, context_data):
        """
        Extract the used view from the TemplateResponse context (ContextMixin)
        """
        view = context_data.get('view')
        if not isinstance(view, View):
            view = None

        # Denote interesting objects in the template context
        template_context = []
        for key, obj in context_data.items():
            if isinstance(obj, (BaseForm, BaseFormSet, Model)):
                template_context.append((key, _format_path(obj.__class__)))

        return {
            'model': _get_view_model(view),
            'form': _get_form_class(view),
            'template_context': template_context,
        }

    @property
    def title(self):
        if self.view_name:
            return "%s (%s)" % (self.nav_title, self.view_name)
        else:
            return self.nav_subtitle

    @property
    def nav_subtitle(self):
        if self.view_name:
            return self.view_name
        else:
            return ''


def _get_form_class(view):
    if hasattr(view, 'get_form_class'):
        form = view.get_form_class()
    elif hasattr(view, 'form_class'):
        form = view.form_class
    else:
        return None

    if form is None:
        return None
    else:
        return _format_path(form)


def _get_view_model(view):
    if hasattr(view, 'model'):
        model = view.model
    elif hasattr(view, 'get_queryset'):
        model = view.get_queryset().model
    else:
        return None

    if model is None:
        return None
    else:
        return _format_path(model)


def _format_path(cls):
    return "{0}.{1}".format(cls.__module__, cls.__name__)
