import os

from webassets import Bundle

from . import log


def includeme(config):
    """
    Loads web assets
    """
    HERE = os.path.dirname(os.path.realpath(__file__))
    SCRIPTS = os.path.join(HERE, 'static/scripts')

    config.add_webasset('default-js', Bundle(
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
        'libs/bootstrap-switch.min.js',
        'libs/socket.io.min.js',
        Bundle(
            *[os.path.join(root, filename)
                for root, dirnames, filenames in os.walk(SCRIPTS)
                for filename in filenames if filename.endswith('.js')],
            filters='jsmin'),
        output='gen/default.%(version)s.min.js'))

    config.add_webasset('default-css', Bundle(
        Bundle(
            'styles/main.less',
            filters='less,cssmin',
            depends='styles/*.less',
            output='gen/main.%(version)s.min.css'),
        Bundle('libs/select2.css', filters=['cssmin', 'cssrewrite']),
        Bundle('libs/select2-bootstrap.css', filters='cssmin'),
        'libs/bootstrap-switch.min.css',
        output='gen/default.%(version)s.css'))

    log.debug('Assets configurated')
