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

    config.add_route('workflow_list', '/workflows')

    config.add_route('category_add', '/categories/add')
    config.add_route('category_list', '/categories')
    config.add_route('category_view', '/categories/{category_name}')
    config.add_route('category_delete', '/categories/{category_name}/delete')

    config.add_route('form_add', '/add')
    config.add_route('form_view', '/{form_name}')
    config.add_route('form_delete', '/{form_name}/delete')

    config.add_route('version_add', '/{form_name}/add')
    config.add_route('version_view', '/{form_name}/{version}',
        custom_predicates=(str_to_version,))
    config.add_route('version_edit', '/{form_name}/{version}/edit',
        custom_predicates=(str_to_version,))
    config.add_route('version_copy', '/{form_name}/{version}/copy',
        custom_predicates=(str_to_version,))
    config.add_route('version_delete', '/{form_name}/{version}/delete',
        custom_predicates=(str_to_version,))

    config.add_route('group_add', '/{form_name}/{version}/add',
        custom_predicates=(str_to_version,))
    config.add_route('group_edit', '/{form_name}/{version}/{group_name}/edit',
        custom_predicates=(str_to_version,))

    config.add_route('field_add', '/{form_name}/{version}/{group_name}/add',
        custom_predicates=(str_to_version,))
    config.add_route('field_view', '/{form_name}/{version}/{group_name}/{field_name}',
        custom_predicates=(str_to_version,))
    config.add_route('field_edit', '/{form_name}/{version}/{group_name}/{field_name}/edit',
        custom_predicates=(str_to_version,))
    config.add_route('field_move', '/{form_name}/{version}/{group_name}/field_name}/move',
        custom_predicates=(str_to_version,))
    config.add_route('field_delete', '/{form_name}/{version}/{group_name}/{field_name}/delete',
        custom_predicates=(str_to_version,))

    config.scan('occams.form.views')
    config.scan('occams.form.layouts')
    config.scan('occams.form.panels')


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
