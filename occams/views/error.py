from pyramid.httpexceptions import HTTPForbidden, HTTPNotFound
from pyramid.view import \
    forbidden_view_config, notfound_view_config, view_config


@notfound_view_config(append_slash=True)
def notfound(request):
    """
    Tries appending a slash at the end of the URL before giving up

    Note that this does not work for POST requests as they will
    be turned into GET requests:
    http://docs.pylonsproject.org/projects/pyramid/en/latest/narr/urldispatch.html#redirecting-to-slash-appended-routes
    This is a small price to pay instead of using pyramid_rewrite
    """

    return HTTPNotFound()


@forbidden_view_config(renderer='../templates/error/forbidden.pt')
def forbidden(request):
    """
    Error handler when a user has insufficient privilidges.

    Note that Pyramid combines unauthorized actions into the Forbidden HTTP
    exception, which means we have to check if the user is authenticated and
    does not have sufficient prilidges or is not logged in. If they user
    is not logged in we need to continue the Forbidden exception so it gets
    picked up by the single-sign-on mechanism (hopefully)
    """

    is_logged_in = bool(request.authenticated_userid)

    if not is_logged_in:
        return HTTPForbidden()

    return {}


@view_config(context=Exception, renderer='../templates/error/uncaught.pt')
def uncaught(exc, request):
    """
    Handler for unexpected exceptions (Coding bugs, etc)

    This handler will present a user-friendly page in production
    systems, but otherwise will defer to pyramid_debugtoolbar debugging.
    """

    if request.registry.settings.get('debugtoolbar.enabled'):
        raise
    return {}
