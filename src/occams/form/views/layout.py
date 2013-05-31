from pyramid_layout.layout import layout_config
from pyramid_layout.panel import panel_config


@layout_config(
    name='web_layout',
    template='occams.form:/templates/layout/web.pt')
@layout_config(
    name='ajax_layout',
    template='occams.form:/templates/layout/ajax.pt')
class Layout(object):
    """
    Master layout for the application
    """

    @property
    def scripts(self):
        return self.request.webassets_env[self.scripts_bundle].urls()

    @property
    def styles(self):
        return self.request.webassets_env[self.styles_bundle].urls()

    def __init__(self, context, request):
        self.context = context
        self.request = request

        self.content_title = ''
        self.content_type = ''

        self.styles_bundle = 'default_css'
        self.scripts_bundle = 'default_js'

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


@panel_config(
    name='global_header',
    renderer='occams.form:templates/layout/panels/global_header.pt')
def global_header(context, request):
    return {}


@panel_config(
    name='global_footer',
    renderer='occams.form:templates/layout/panels/global_footer.pt')
def global_footer(context, request):
    return {}

