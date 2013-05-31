from pkg_resources import resource_filename

from webassets import Bundle
from webassets.filter import get_filter
from webassets.loaders import PythonLoader


def config_assets(config):
    """
    Loads web assets
    """
    bundles = PythonLoader('occams.form.assets').load_bundles()
    for name, bundle in bundles.items():
        config.add_webasset(name, bundle)
    return config


bootstrap_css = Bundle(
    'styles/bootstrap-2.3.1.min.css',
    debug=False,
    filters=get_filter('cssrewrite',
        replace=lambda url: url.replace('/img/', '/images/')),
    output='gen/bootstrap.css')
bootstrap_js = Bundle('scripts/bootstrap-2.3.1.min.js')

# GOTCHA: The bootstrap responsive sheet needs to be specified at the
# very end in order to take into effect properly
bootstrap_responsive = Bundle('styles/bootstrap-responsive-2.3.1.min.css')

jquery = Bundle('scripts/jquery-2.0.0.min.js')

# We don't use the jquery-ui theme because of bootstrap
jquery_ui_js = Bundle('scripts/jquery-ui-1.10.2.min.js')

select2_css = Bundle('styles/select2-3.3.2.css', filters=('cssmin',))
select2_js = Bundle('scripts/select2-3.3.2.min.js')

deform_js = Bundle(
    resource_filename('deform', 'static/scripts/jquery.form-3.09.js'),
    resource_filename('deform', 'static/scripts/deform.js'),
    filters=('jsmin',),
    output='gen/deform-dependencies.js')


app_css = Bundle(
   'styles/main.css',
   filters=('cssmin',))
app_js = Bundle(
    'scripts/modal.js',
    'scripts/app.js',
    filters=('jsmin',))


default_css = Bundle(
    bootstrap_css,
    select2_css,
    app_css,
    bootstrap_responsive,
    output='gen/default.css')

default_js = Bundle(
    jquery,
    jquery_ui_js,
    bootstrap_js,
    select2_js,
    deform_js,
    app_js,
    output='gen/default.js')

