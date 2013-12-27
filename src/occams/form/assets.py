from webassets import Bundle


def includeme(config):
    """
    Loads web assets
    """
    config.add_webasset('default-js', Bundle(
        Bundle('libs/jquery.min.js'),
        Bundle('libs/jquery-ui.min.js'),
        Bundle(
            'libs/bootstrap/js/transition.js',
            'libs/bootstrap/js/collapse.js',
            'libs/bootstrap/js/button.js',
            'libs/bootstrap/js/dropdown.js',
            'libs/bootstrap/js/modal.js',
            'libs/bootstrap/js/tooltip.js',
            filters='jsmin',
            output='bootstrap.%(version)s.min.js'),
        Bundle('libs/select2.min.js'),
        Bundle(
            'scripts/modal.js',
            'scripts/app.js',
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

    config.scan('occams.form.layouts')
    config.scan('occams.form.panels')

    return config
