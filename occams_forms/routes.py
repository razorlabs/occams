from . import log, models


def includeme(config):
    """
    Configures URL routes
    """

    config.add_static_view('/static', 'occams_forms:static', cache_max_age=3600)

    config.add_route('forms',               '',                                           factory=models.FormFactory)

    config.add_route('version',             '/{form}/versions/{version}',                  factory=models.FormFactory, traverse='/{form}/versions/{version}')
    config.add_route('version_editor',      '/{form}/versions/{version}/editor',           factory=models.FormFactory, traverse='/{form}/versions/{version}')
    config.add_route('version_preview',     '/{form}/versions/{version}/preview',          factory=models.FormFactory, traverse='/{form}/versions/{version}')

    config.add_route('fields',              '/{form}/versions/{version}/fields',           factory=models.FormFactory, traverse='/{form}/versions/{version}/fields')
    config.add_route('field',               '/{form}/versions/{version}/fields/{field}',   factory=models.FormFactory, traverse='/{form}/versions/{version}/fields/{field}')

    config.add_route('workflow',            '/workflows/default')

    log.debug('Routes configured')
