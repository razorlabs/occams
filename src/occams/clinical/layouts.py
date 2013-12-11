from pyramid_layout.layout import layout_config


@layout_config(
    name='',
    template='occams.clinical:templates/layouts/default.pt')
@layout_config(
    name='ajax',
    template='occams.clinical:templates/layouts/ajax.pt')
class Layout(object):
    """
    Master layout for the application
    """

    title = None
    subtitle = None

    show_header = True

    styles_bundle = 'default-css'
    scripts_bundle = 'default-js'

    menu = None
    details = None
    nav = None

    @property
    def scripts(self):
        return self.request.webassets_env[self.scripts_bundle]

    @property
    def styles(self):
        return self.request.webassets_env[self.styles_bundle]

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def set_nav(self, name, *args, **kw):
        self.nav = (name, args, kw)

    def set_details(self, name, *args, **kw):
        self.details = (name, args, kw)

    def set_menu(self, name, *args, **kw):
        self.menu = (name, args, kw)

