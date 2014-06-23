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

    r('workflow_add',        '/workflows/add')
    r('workflow_view',       '/workflows/{workflow}')
    r('workflow_edit',       '/workflows/{workflow}/edit')
    r('workflow_delete',     '/workflows/{workflow}/delete')

    r('state_add',           '/workflows/{workflow}/add')
    r('state_view',          '/workflows/{workflow}/{state}')
    r('state_edit',          '/workflows/{workflow}/{state}/edit')
    r('state_delete',        '/workflows/{workflow}/{state}/delete')

    r('form_add',            '/add')

    r('version_view',        '/{form}/{version}')
    r('version_edit',        '/{form}/{version}/edit')
    r('version_delete',      '/{form}/{version}/delete')
    r('version_preview',     '/{form}/{version}/preview')
    r('version_download',    '/{form}/{version}/download')
    r('version_copy',        '/{form}/{version}/copy')
    r('version_draft',       '/{form}/{version}/draft')

    r('field_list',          '/{form}/{version}/fields')
    r('field_add',           '/{form}/{version}/fields/add/{type}')
    r('field_view',          '/{form}/{version}/fields/{field}')
    r('field_edit',          '/{form}/{version}/fields/{field}/edit')
    r('field_move',          '/{form}/{version}/fields/field}/move')
    r('field_delete',        '/{form}/{version}/fields/{field}/delete')
