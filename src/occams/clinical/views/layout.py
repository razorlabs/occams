from pyramid_layout.layout import layout_config
from pyramid_layout.panel import panel_config


@layout_config(
    name='',
    template='occams.clinical:templates/layout/default.pt')
@layout_config(
    name='ajax_layout',
    template='occams.clinical:templates/layout/ajax.pt')
class Layout(object):
    """
    Master layout for the application
    """

    content_title = ''
    content_type = ''

    styles_bundle = 'default_css'
    scripts_bundle = 'default_js'

    @property
    def scripts(self):
        return self.request.webassets_env[self.scripts_bundle]

    @property
    def styles(self):
        return self.request.webassets_env[self.styles_bundle]

    def config_toolbar(self, name, *args, **kw):
        self._toolbar = (name, args, kw)

    @property
    def toolbar(self):
        return getattr(self, '_toolbar')

    def __init__(self, context, request):
        self.context = context
        self.request = request


@panel_config(name='toolbar')
def toolbar(context, request):
    lm = request.layout_manager
    panel = lm.layout.toolbar
    if panel:
        (name, args, kw) = panel
        return lm.render_panel(name, *args, **kw)
    return ''


@panel_config(
    name='global_header',
    renderer='occams.clinical:templates/layout/panels/global_header.pt')
def global_header(context, request):
    return {}


@panel_config(
    name='global_footer',
    renderer='occams.clinical:templates/layout/panels/global_footer.pt')
def global_footer(context, request):
    return {}

