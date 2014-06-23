from webassets import Bundle

from . import log


def includeme(config):
    """
    Loads web assets
    """
    log.debug('Initializing assets...')

    config.add_webasset('default-js', Bundle(
        Bundle('libs/jquery.min.js'),
        Bundle('libs/bootstrap/dist/js/bootstrap.min.js'),
        Bundle('libs/knockout.min.js'),
        Bundle('libs/knockout.mapping.min.js'),
        Bundle('libs/select2.min.js'),
        Bundle(
            'scripts/modal.js',
            'scripts/form-list.js',
            filters='jsmin'),
        output='gen/default.%(version)s.min.js'))

    config.add_webasset('default-css', Bundle(
        Bundle('libs/select2.css', filters='cssmin'),
        Bundle(
            'styles/main.less',
            filters='less,cssmin',
            depends='styles/*.less',
            output='gen/main.%(version)s.min.css'),
        output='gen/default.%(version)s.css'))
