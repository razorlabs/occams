from webassets import Bundle

from . import log


def includeme(config):
    """
    Loads web assets
    """

    config.add_webasset('default-js', Bundle(
        Bundle('libs/jquery.min.js'),
        Bundle('libs/jquery-ui.min.js'),
        Bundle('libs/jquery.cookie.js'),
        Bundle('libs/jquery.validate.min.js'),
        Bundle('libs/bootstrap/dist/js/bootstrap.min.js'),
        Bundle('libs/knockout.min.js'),
        Bundle('libs/knockout.mapping.min.js'),
        Bundle('libs/knockout-sortable.min.js'),
        Bundle('libs/select2.min.js'),
        Bundle('libs/moment.min.js'),
        Bundle('libs/bootstrap-datetimepicker/build/js/bootstrap-datetimepicker.min.js'),
        Bundle('libs/sammy.min.js'),
        Bundle('libs/socket.io.min.js'),
        Bundle(
            'scripts/*.js',
            'scripts/**/*.js',
            depends='scripts/**/*.js', filters='jsmin'),
        output='gen/default.%(version)s.min.js'))

    config.add_webasset('default-css', Bundle(
        Bundle(
            'styles/main.less',
            filters='less,cssmin',
            depends='styles/**/*.less',
            output='gen/main.%(version)s.min.css'),
        Bundle('libs/select2.css', filters=['cssmin', 'cssrewrite']),
        Bundle('libs/select2-bootstrap.css', filters='cssmin'),
        output='gen/default.%(version)s.css'))

    log.debug('Assets configurated')
