from pyramid_layout.panel import panel_config

@panel_config(name='app_header', renderer='occams.clinical:templates/panels/app_header.pt')
@panel_config(name='app_footer', renderer='occams.clinical:templates/panels/app_footer.pt')
@panel_config(name='study_details', renderer='occams.clinical:templates/study/panels/details.pt')
@panel_config(name='study_nav', renderer='occams.clinical:templates/study/panels/nav.pt')
@panel_config(name='study_view_menu', renderer='occams.clinical:templates/study/panels/view_menu.pt')
@panel_config(name='study_list_menu', renderer='occams.clinical:templates/study/panels/list_menu.pt')
@panel_config(name='home_menu', renderer='occams.clinical:templates/portal/panels/home_menu.pt')
@panel_config(name='data_nav', renderer='occams.clinical:templates/data/panels/nav.pt')
def panel(context, request, **kw):
    return kw


@panel_config(name='nav')
def render_nav(context, request):
    return render_layout_panel(context, request, 'nav')


@panel_config(name='details')
def render_details(context, request):
    return render_layout_panel(context, request, 'details')


@panel_config(name='menu')
def render_menu(context, request):
    return render_layout_panel(context, request, 'menu')


def render_layout_panel(context, request, panel):
    lm = request.layout_manager
    layout = lm.layout
    try:
        (name, args, kw) = getattr(layout, panel)
    except TypeError:
        return ''
    else:
        return lm.render_panel(name, *args, **kw) or ''


