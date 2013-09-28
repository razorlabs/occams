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

    title = ''
    section = ''

    styles_bundle = 'default_css'
    scripts_bundle = 'default_js'

    @property
    def scripts(self):
        return self.request.webassets_env[self.scripts_bundle]

    @property
    def styles(self):
        return self.request.webassets_env[self.styles_bundle]

    def set_header(self, name, *args, **kw):
        self._header = (name, args, kw)

    def __init__(self, context, request):
        self.context = context
        self.request = request


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


@panel_config(name='header')
def header(context, request):
    """
    Rederst the registered content header
    """
    lm = request.layout_manager
    panel = getattr(lm.layout, '_header', None)
    if panel:
        (name, args, kw) = panel
        return lm.render_panel(name, *args, **kw)
    return ''

