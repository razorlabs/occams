import os

from webassets import Bundle

from . import log


def includeme(config):
    """
    Loads web assets
    """
    here = os.path.dirname(os.path.realpath(__file__))
    scripts = os.path.join(here, 'static/scripts')

    # Make sure the platform can find this app's assets
    env = config.get_webassets_env()
    env.append_path(os.path.join(here, 'static'), '/%s/static' % config.route_prefix)

    # "resolves" the path relative to this package
    def rel(path):
        return os.path.join(here, 'static', path)

    config.add_webasset('accounts-js', Bundle(
        # Dependency javascript libraries must be loaded in a specific order
        rel('bower_components/jquery/dist/jquery.min.js'),
        rel('bower_components/bootstrap/dist/js/bootstrap.min.js'),
        # App-specific scripts can be loaded in any order
        Bundle(
            *[os.path.join(root, filename)
                for root, dirnames, filenames in os.walk(scripts)
                for filename in filenames if filename.endswith('.js')],
            filters='jsmin'),
        output='gen/accounts.%(version)s.min.js'))

    config.add_webasset('accounts-css', Bundle(
        Bundle(
            rel('styles/main.less'),
            filters='less,cssmin',
            depends=rel('styles/*.less'),
            output='gen/accounts-main.%(version)s.min.css'),
        output='gen/accounts.%(version)s.css'))

    log.debug('Assets configurated')
