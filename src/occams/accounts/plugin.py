
_LOGOUT_KEY = 'accounts.logout_url'


def includeme(config):

    assert config.registry.settings.get(_LOGOUT_KEY) is not None, \
        'Must specify %s' % _LOGOUT_KEY

    config.add_request_method(
        lambda r: r.registry.settings[_LOGOUT_KEY],
        name='accounts_logout_url',
        reify=True)

    config.include('.links')
