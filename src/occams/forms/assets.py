import os
from webassets import Bundle

from . import log


def includeme(config):
    """
    Configures static assets
    """
    HERE = os.path.dirname(os.path.realpath(__file__))
    SCRIPTS = os.path.join(HERE, 'static/scripts')

    config.include('pyramid_webassets')

    config.add_webasset('default-js', Bundle(
        # Dependency javascript libraries must be loaded in a specific order
        'libs/jquery.min.js',
        'libs/jquery-ui.min.js',
        'libs/jquery.cookie.js',
        'libs/jquery.validate.min.js',
        'libs/bootstrap/dist/js/bootstrap.min.js',
        'libs/knockout.min.js',
        'libs/knockout-sortable.min.js',
        'libs/select2.min.js',
        'libs/moment.min.js',
        'libs/bootstrap-datetimepicker/build/js/bootstrap-datetimepicker.min.js',
        # App-specific scripts can be loaded in any order
        Bundle(
            *[os.path.join(root, filename)
                for root, dirnames, filenames in os.walk(SCRIPTS)
                for filename in filenames if filename.endswith('.js')],
            filters='jsmin'),
        output='gen/default.%(version)s.min.js'))

    config.add_webasset('default-css', Bundle(
        Bundle(
            'styles/main.less',
            filters='less',
            depends='styles/**/*.less',
            output='gen/main.%(version)s.min.css'),
        Bundle('libs/select2.css', filters='cssrewrite'),
        'libs/select2-bootstrap.css',
        filters='cssmin',
        output='gen/default.%(version)s.css'))

    log.debug('Assets configurated')
