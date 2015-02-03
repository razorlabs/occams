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
        'bower_components/bootstrap/dist/js/bootstrap.min.js',
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
        output='gen/default.%(version)s.css'))

    log.debug('Assets configurated')
