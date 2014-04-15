import datetime

from occams.form import log


def includeme(config):
    """
    Helper method to configure available routes for the application
    """
    log.debug('Registering views...')

    config.include('pyramid_rewrite')
    config.add_rewrite_rule(r'/(?P<path>.*)/', r'/%(path)s')

    str_to_version = versions('version')
    config.add_static_view('static', 'static', cache_max_age=3600)

    config.add_route('home', '/')

    config.add_route('account_login', '/login')
    config.add_route('account_logout', '/logout')
    config.add_route('account', '/account')

    config.add_route('form_add', '/add')
    config.add_route('form_view', '/{form}/{version}')
    config.add_route('form_delete', '/{form}/{version}/delete')

    config.add_route('field_add', '/{form_name}/{version}/add',
        custom_predicates=(str_to_version,))
    config.add_route('field_view', '/{form_name}/{version}/{field}',
        custom_predicates=(str_to_version,))
    config.add_route('field_edit', '/{form_name}/{version}/{field}/edit',
        custom_predicates=(str_to_version,))
    config.add_route('field_move', '/{form_name}/{version}/field}/move',
        custom_predicates=(str_to_version,))
    config.add_route('field_delete', '/{form_name}/{version}/{field}/delete',
        custom_predicates=(str_to_version,))


def versions(*segment_names):
    """
    Creates function to parse version segments in URL on dispatch.
    """
    def predicate(info, request):
        strpdate = lambda s: datetime.datetime.strptime(s, '%Y-%m-%d').date()
        match = info['match']
        for segment_name in segment_names:
            try:
                raw = match[segment_name]
                parsed = int(raw) if raw.isdigit() else strpdate(raw)
                match[segment_name] = parsed
            except ValueError:
                return False
        return True
    return predicate
