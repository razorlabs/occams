from . import log


def includeme(config):
    """
    Helper method to configure available routes for the application
    """
    log.debug('Registering views...')

    config.add_static_view('static', 'static', cache_max_age=3600)

    r = config.add_route

    r('home',                '/')

    r('account_login',       '/login')
    r('account_logout',      '/logout')

    r('workflow_view',       '/workflows/{workflow}')

    r('form_add',            '/add')

    r('version_view',        '/{form}/{version}')
    r('version_edit',        '/{form}/{version}/edit')
    r('version_manage',      '/{form}/{version}/manage')
    r('version_publish',     '/{form}/{version}/publish')
    r('version_delete',      '/{form}/{version}/delete')
    r('version_preview',     '/{form}/{version}/preview')
    r('version_download',    '/{form}/{version}/download')
    r('version_copy',        '/{form}/{version}/copy')
    r('version_draft',       '/{form}/{version}/draft')

    r('section_add',           '/{form}/{version}/sections/add')
    r('section_view',          '/{form}/{version}/sections/{section}')
    r('section_edit',          '/{form}/{version}/sections/{section}/edit')
    r('section_move',          '/{form}/{version}/sections/{section}/move')
    r('section_delete',        '/{form}/{version}/sections/{section}/delete')

    r('field_list',          '/{form}/{version}/fields')
    r('field_add',           '/{form}/{version}/fields/add/{type}')
    r('field_view',          '/{form}/{version}/fields/{field}')
    r('field_edit',          '/{form}/{version}/fields/{field}/edit')
    r('field_move',          '/{form}/{version}/fields/{field}/move')
    r('field_delete',        '/{form}/{version}/fields/{field}/delete')
