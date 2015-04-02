import os
from webassets import Bundle

from . import log


def includeme(config):
    """
    Configures static assets
    """
    here = os.path.dirname(os.path.realpath(__file__))
    scripts = os.path.join(here, 'static/scripts')

    env = config.get_webassets_env()
    env.append_path(os.path.join(here, 'static'), '/forms/static')

    # "resolves" the path relative to this package
    def rel(path):
        return os.path.join(here, 'static', path)

    config.add_webasset('forms-js', Bundle(
        # Dependency javascript libraries must be loaded in a specific order
        rel('bower_components/jquery/dist/jquery.min.js'),
        rel('bower_components/jquery-ui/jquery-ui.min.js'),
        Bundle(rel('bower_components/jquery-cookie/jquery.cookie.js'), filters='jsmin'),
        rel('bower_components/jquery-validate/dist/jquery.validate.min.js'),
        rel('bower_components/bootstrap/dist/js/bootstrap.min.js'),
        rel('bower_components/knockout/dist/knockout.js'),
        rel('bower_components/knockout-sortable/build/knockout-sortable.min.js'),
        rel('bower_components/select2/select2.min.js'),
        rel('bower_components/moment/min/moment.min.js'),
        rel('bower_components/eonasdan-bootstrap-datetimepicker/build/js/bootstrap-datetimepicker.min.js'),
        rel('bower_components/bootstrap-fileinput/js/fileinput.min.js'),
        # App-specific scripts can be loaded in any order
        Bundle(
            *[os.path.join(root, filename)
                for root, dirnames, filenames in os.walk(scripts)
                for filename in filenames if filename.endswith('.js')],
            filters='jsmin'),
        output='gen/forms.%(version)s.min.js'))

    config.add_webasset('forms-css', Bundle(
        Bundle(
            rel('styles/main.less'),
            filters='less',
            depends=rel('styles/*.less'),
            output='gen/forms-main.%(version)s.min.css'),
        Bundle(rel('bower_components/select2/select2.css'), filters='cssrewrite'),
        rel('bower_components/select2-bootstrap-css/select2-bootstrap.css'),
        Bundle(rel('bower_components/bootstrap-fileinput/css/fileinput.min.css'), filters='cssrewrite'),
        filters='cssmin',
        output='gen/forms.%(version)s.css'))

    log.debug('Assets configurated')
