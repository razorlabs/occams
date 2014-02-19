from webassets import Bundle

from occams.clinical import log


def includeme(config):
    """
    Loads web assets
    """
    log.debug('Initializing assets...')

    config.add_webasset('default-js', Bundle(
        Bundle('libs/jquery.min.js'),
        Bundle('libs/knockout.min.js'),
        Bundle('libs/knockout.mapping.min.js'),
        Bundle('libs/sammy.min.js'),
        Bundle(
            'libs/bootstrap/js/transition.js',
            'libs/bootstrap/js/collapse.js',
            'libs/bootstrap/js/button.js',
            'libs/bootstrap/js/dropdown.js',
            'libs/bootstrap/js/modal.js',
            'libs/bootstrap/js/tooltip.js',
            'libs/bootstrap/js/alert.js',
            filters='jsmin',
            output='bootstrap.%(version)s.min.js'),
        Bundle('libs/socket.io.min.js'),
        Bundle(
            'scripts/selectall.js',
            'scripts/tooltip.js',
            'scripts/modal.js',
            'scripts/button.js',
            'scripts/export.js',
            filters='jsmin'),
        output='gen/default.%(version)s.min.js'))

    config.add_webasset('default-css', Bundle(
        Bundle(
            'styles/main.less',
            filters='less,cssmin',
            depends='styles/*.less',
            output='gen/main.%(version)s.min.css'),
        output='gen/default.%(version)s.css'))
