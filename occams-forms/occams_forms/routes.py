from . import log, models


def includeme(config):
    """
    Configures URL routes
    """

    config.add_static_view(path='occams_forms:static', name='/static', cache_max_age=3600)

    config.add_route('forms.index',               '/',                                                  factory=models.FormFactory)

    config.add_route('forms.version',             '/{form}/versions/{version}',                   factory=models.FormFactory, traverse='/{form}/versions/{version}')
    config.add_route('forms.version_editor',      '/{form}/versions/{version}/editor',            factory=models.FormFactory, traverse='/{form}/versions/{version}')
    config.add_route('forms.version_preview',     '/{form}/versions/{version}/preview',           factory=models.FormFactory, traverse='/{form}/versions/{version}')

    config.add_route('forms.fields',              '/{form}/versions/{version}/fields',            factory=models.FormFactory, traverse='/{form}/versions/{version}/fields')
    config.add_route('forms.field',               '/{form}/versions/{version}/fields/{field}',    factory=models.FormFactory, traverse='/{form}/versions/{version}/fields/{field}')

    config.add_route('forms.workflow',            '/workflows/default')

    log.debug('Routes configured')
