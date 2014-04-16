from webassets import Bundle

from . import log


def includeme(config):
    """
    Loads web assets
    """

    config.add_webasset('default-js', Bundle(
        Bundle('libs/jquery.min.js'),
        Bundle('libs/knockout.min.js'),
        Bundle('libs/knockout.mapping.min.js'),
        Bundle('libs/sammy.min.js'),
        Bundle('libs/bootstrap/dist/js/bootstrap.min.js'),
        Bundle('libs/socket.io.min.js'),
        Bundle(
            'scripts/selectall.js',
            'scripts/tooltip.js',
            'scripts/modal.js',
            'scripts/button.js',
            'scripts/export-status.js',
            'scripts/export-faq.js',
            filters='jsmin'),
        output='gen/default.%(version)s.min.js'))

    config.add_webasset('default-css', Bundle(
        Bundle(
            'styles/main.less',
            filters='less,cssmin',
            depends='styles/*.less',
            output='gen/main.%(version)s.min.css'),
        output='gen/default.%(version)s.css'))

    log.debug('Assets configurated')
