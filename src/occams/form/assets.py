from pkg_resources import resource_filename

from webassets import Bundle
from webassets.loaders import PythonLoader


def includeme(config):
    """
    Loads web assets
    """
    bundles = PythonLoader('occams.form.assets').load_bundles()
    for name, bundle in bundles.items():
        config.add_webasset(name, bundle)
    return config


#
# Third-Pary Libraries
# These won't usually require filtering if the developer supplies them
#

bootstrap_css = Bundle('styles/bootstrap-2.3.2.min.css')
bootstrap_js = Bundle('scripts/bootstrap-2.3.2.min.js')

jquery = Bundle('scripts/jquery-2.0.0.min.js')

# We don't use the jquery-ui theme because of bootstrap
jquery_ui_js = Bundle('scripts/jquery-ui-1.10.2.min.js')

select2_css = Bundle('styles/select2-3.3.2.css', filters='cssmin')
select2_js = Bundle('scripts/select2-3.3.2.min.js')

deform_js = Bundle(
    resource_filename('deform', 'static/scripts/jquery.form-3.09.js'),
    resource_filename('deform', 'static/scripts/deform.js'),
    filters='jsmin')

#
# In-house Libraries
#

#TODO modalize here

#
# Application-wide Assets
# These should be avaialble globally throughout the application
#

app_css = Bundle('styles/app.*', filters='cssmin')
app_js = Bundle(
    'scripts/modal.js',
    'scripts/app.js',
    filters='jsmin')

#
# Layout-specific Assets
#

default_css = Bundle(
    bootstrap_css,
    select2_css,
    app_css,
    output='gen/default.%(version)s.css')

default_js = Bundle(
    jquery,
    jquery_ui_js,
    bootstrap_js,
    select2_js,
    deform_js,
    app_js,
    output='gen/default.%(version)s.js')
