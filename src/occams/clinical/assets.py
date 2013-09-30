from pkg_resources import resource_filename

from pyramid.settings import asbool
from webassets import Bundle
from webassets.loaders import PythonLoader


def config_assets(config):
    """
    Loads web assets
    """
    env = config.get_webassets_env()

    config.add_webasset('default_css', Bundle(
        'styles/main.less',
        filters='less,cssmin',
        depends='styles/*.less',
        output='gen/default.%(version)s.css'))

    config.add_webasset('default_js', Bundle(
        'libs/jquery.min.js',
        'libs/bootstrap/js/affix.js',
        'libs/bootstrap/js/button.js',
        'libs/bootstrap/js/dropdown.js',
        'libs/bootstrap/js/modal.js',
        'libs/bootstrap/js/tooltip.js',
        'libs/bootstrap/js/transition.js',
        'scripts/selectall.js',
        filters='jsmin',
        output='gen/default.%(version)s.js'))

    return config



