from pkg_resources import resource_filename

import deform

# Define application-local renderers so we don't
# affect the entire python environment.

WEB_FORM_RENDERER = deform.ZPTRendererFactory([
    resource_filename('occams.form', 'templates/deform/overrides'),
    resource_filename('deform', 'templates')])


AJAX_FORM_RENDERER = deform.ZPTRendererFactory([
    resource_filename('occams.form', 'templates/deform/modal'),
    resource_filename('occams.form', 'templates/deform/overrides'),
    resource_filename('deform', 'templates')])

