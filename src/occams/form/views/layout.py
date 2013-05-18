from pyramid_layout.layout import layout_config
from pyramid_layout.panel import panel_config


@layout_config(
    name='master_layout',
    template='occams.form:/templates/layout/master.pt')
@layout_config(
    name='ajax_layout',
    template='occams.form:/templates/layout/ajax.pt')
@layout_config(
    name='modal_layout',
    template='occams.form:/templates/layout/modal.pt')
class Layout(object):
    """ Master layout for the application
    """

    def __init__(self, context, request):
        self.context = context
        self.request = request

        self.content_title = ''
        self.content_type = ''
