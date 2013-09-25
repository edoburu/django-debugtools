# following PEP 386
__version__ = "1.1.0"

VERSION = (1, 1, 0)

# Make sure the ``{% print %}`` is always available, even without a {% load debug_tags %} call.
# **NOTE** this uses the undocumented, unofficial add_to_builtins() call. It's not promoted
# by Django developers because it's better to be explicit with a {% load .. %} in the templates.
#
# This function is used here nevertheless because the {% print %} tag is a debugging aid,
# and not a tag that should remain permanently in your templates. Convenience is preferred here.
#
from django.template.loader import add_to_builtins
add_to_builtins("debugtools.templatetags.debug_tags")
