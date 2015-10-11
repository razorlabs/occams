"""
Common helper tools for testing
"""

USERID = 'test_user'


def make_environ(userid=USERID, properties={}, groups=()):
    """
    Creates dummy environ variables for mock-authentication

    :param userid:      The currently authenticated userid
    :param properties:  Additional identity properties
    :param groups:      Optional group memberships
    """
    if userid:
        return {
            'REMOTE_USER': userid,
            'repoze.who.identity': {
                'repoze.who.userid': userid,
                'properties': properties,
                'groups': groups}}


def get_csrf_token(app, environ=None):
    """
    Request the app so csrf cookie is available

    :param app:     The testing application
    :param environ: The environ variables (if the user is logged in)
                    Default: None
    """
    app.get('/', extra_environ=environ)

    return app.cookies['csrf_token']
