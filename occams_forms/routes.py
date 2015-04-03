from . import log, models


def includeme(config):
    """
    Configures URL routes
    """

    config.add_static_view('/forms/static', 'occams_forms:static', cache_max_age=3600)

    config.add_route('forms.main',                '/forms',                                           factory=models.FormFactory)

    config.add_route('forms.version',             '/forms/{form}/versions/{version}',                  factory=models.FormFactory, traverse='/{form}/versions/{version}')
    config.add_route('forms.version_editor',      '/forms/{form}/versions/{version}/editor',           factory=models.FormFactory, traverse='/{form}/versions/{version}')
    config.add_route('forms.version_preview',     '/forms/{form}/versions/{version}/preview',          factory=models.FormFactory, traverse='/{form}/versions/{version}')

    config.add_route('forms.fields',              '/forms/{form}/versions/{version}/fields',           factory=models.FormFactory, traverse='/{form}/versions/{version}/fields')
    config.add_route('forms.field',               '/forms/{form}/versions/{version}/fields/{field}',   factory=models.FormFactory, traverse='/{form}/versions/{version}/fields/{field}')

    config.add_route('forms.workflow',            '/forms/workflows/default')

    log.debug('Routes configured')
