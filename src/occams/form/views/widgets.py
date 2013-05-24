from pkg_resources import resource_filename

import colander
import deform
import deform.widget

# Define application-local renderers so we don't
# affect the entire python environment.

WEB_FORM_RENDERER = deform.ZPTRendererFactory([
    resource_filename('occams.form', 'templates/deform/overrides'),
    resource_filename('deform', 'templates')])


AJAX_FORM_RENDERER = deform.ZPTRendererFactory([
    resource_filename('occams.form', 'templates/deform/modal'),
    resource_filename('occams.form', 'templates/deform/overrides'),
    resource_filename('deform', 'templates')])


class FormSelectWidget(deform.widget.Widget):
    """
    Input widget for select a form + version
    """

    template = 'form_select'
    readonly_template = 'readonly/form_select'

    def serialize(self, field, cstruct=None, readonly=False):
        pass

    def deserialize(self, field, pstruct=None):
        pass
