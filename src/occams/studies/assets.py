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
        'bower_components/bootstrap-fileinput/js/fileinput.min.js',
        'bower_components/bootstrap-switch/dist/js/bootstrap-switch.min.js',
        'bower_components/socket.io-client/dist/socket.io.min.js',
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
            filters='less,cssmin',
            depends='styles/*.less',
            output='gen/main.%(version)s.min.css'),
        Bundle('bower_components/select2/select2.css', filters='cssrewrite'),
        'bower_components/select2-bootstrap-css/select2-bootstrap.css',
        Bundle('bower_components/bootstrap-fileinput/css/fileinput.min.css', filters='cssrewrite'),
        'bower_components/bootstrap-switch/dist/css/bootstrap3/bootstrap-switch.min.css',
        output='gen/default.%(version)s.css'))

    log.debug('Assets configurated')
