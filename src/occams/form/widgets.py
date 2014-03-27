from pkg_resources import resource_filename

import deform.widget

from occams.form import log


# Define application-local renderers so we don't
# affect the entire python environment.

DEFAULT_RENDERER = deform.ZPTRendererFactory((
    resource_filename('occams.form', 'templates/deform'),
    resource_filename('deform', 'templates'),))


class ModalFormWidget(deform.widget.FormWidget):
    """
    Extends deform's default form for modal containers
    """

    template = 'modal_form'
    readonly_template = 'readonly/modal_form'


class GroupInputWidget(deform.widget.MappingWidget):

    template = 'groupinput'
    readonly_template = None
    size = None

    before = None
    after = None


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


def includeme(config):
    log.debug('Overriding deform templates...')
    deform.Form.set_default_renderer(DEFAULT_RENDERER)
