from pyramid_layout.panel import panel_config


@panel_config(
    name='app_header',
    renderer='occams.form:templates/panels/app_header.pt')
@panel_config(
    name='app_footer',
    renderer='occams.form:templates/panels/app_footer.pt')
def panel(context, request, **kw):
    return kw


@panel_config(name='nav')
def render_nav(context, request):
    return render_panel(context, request, 'nav')


@panel_config(name='details')
def render_details(context, request):
    return render_panel(context, request, 'details')


@panel_config(name='menu')
def render_menu(context, request):
    return render_panel(context, request, 'menu')


def render_panel(context, request, panel):
    lm = request.layout_manager
    layout = lm.layout
    try:
        (name, args, kw) = getattr(layout, panel)
    except TypeError:
        return ''
    else:
        return lm.render_panel(name, *args, **kw) or ''
