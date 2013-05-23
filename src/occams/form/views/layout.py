from pyramid_layout.layout import layout_config
from pyramid_layout.panel import panel_config


@layout_config(
    name='web_layout',
    template='occams.form:/templates/layout/web.pt')
@layout_config(
    name='ajax_layout',
    template='occams.form:/templates/layout/ajax.pt')
class Layout(object):
    """ Master layout for the application
    """

    def __init__(self, context, request):
        self.context = context
        self.request = request

        self.content_title = ''
        self.content_type = ''

        self.toolbar = None

    def set_toolbar(self, name, *args, **kw):
        self.toolbar = (name, args, kw)


@panel_config(name='toolbar')
def toolbar(context, request):
    lm = request.layout_manager
    panel = lm.layout.toolbar
    if panel:
        (name, args, kw) = panel
        return lm.render_panel(name, *args, **kw)
    return ''

