import os
from webassets import Bundle

from . import log


def includeme(config):
    """
    Configures static assets
    """
    HERE = os.path.dirname(os.path.realpath(__file__))
    APP_SCRIPTS = os.path.join(HERE, 'static/scripts')

    config.include('pyramid_webassets')

    config.add_webasset('default-js', Bundle(
        # Dependency javascript libraries must be loaded in a specific order
        'bower_components/jquery/dist/jquery.min.js',
        'bower_components/jquery-ui/jquery-ui.min.js',
        Bundle('bower_components/jquery-cookie/jquery.cookie.js', filters='jsmin'),
        'bower_components/jquery-validate/dist/jquery.validate.min.js',
        'bower_components/bootstrap/dist/js/bootstrap.min.js',
        'bower_components/knockout/dist/knockout.js',
        'bower_components/knockout-sortable/build/knockout-sortable.min.js',
        'bower_components/select2/select2.min.js',
        'bower_components/moment/min/moment.min.js',
        'bower_components/eonasdan-bootstrap-datetimepicker/build/js/bootstrap-datetimepicker.min.js',
        # App-specific scripts can be loaded in any order
        Bundle(
            *[os.path.join(root, filename)
                for root, dirnames, filenames in os.walk(APP_SCRIPTS)
                for filename in filenames if filename.endswith('.js')],
            filters='jsmin'),
        output='gen/default.%(version)s.min.js'))

    config.add_webasset('default-css', Bundle(
        Bundle(
            'styles/main.less',
            filters='less',
            depends='styles/*.less',
            output='gen/main.%(version)s.min.css'),
        Bundle('bower_components/select2/select2.css', filters='cssrewrite'),
        'bower_components/select2-bootstrap-css/select2-bootstrap.css',
        filters='cssmin',
        output='gen/default.%(version)s.css'))

    log.debug('Assets configurated')
