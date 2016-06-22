from pyramid.exceptions import URLDecodeError
from pyramid.httpexceptions import (
    HTTPBadRequest,
    HTTPForbidden,
    HTTPUnauthorized,
)
from pyramid.view import (
    forbidden_view_config,
    notfound_view_config,
    view_config
)


@notfound_view_config(append_slash=True)
def notfound(exc, request):
    """"
    Returns HTTP Not Found only after trying to append a slash to the URL
    """
    return exc


@forbidden_view_config()
def forbidden(request):
    """
    Error handler when a user has insufficient privilidges.

    Note that Pyramid combines unauthorized actions into the Forbidden HTTP
    exception, which means we have to check if the user is authenticated and
    does not have sufficient priviliges or is not logged in. If the user
    is not logged in, we need to continue the Forbidden exception so it gets
    picked up by the single-sign-on mechanism.

    This distinction between 401 and 403 is related to the below ticket:
    Issue 436 of Pylons/pyramid -  Authorisation incorrectly implements
    403 Forbidden against RFC 2616
    """
    is_logged_in = bool(request.authenticated_userid)
    return HTTPForbidden() if is_logged_in else HTTPUnauthorized()


@view_config(context=URLDecodeError)
def invalid_url_encoding(exc, request):
    """
    Handler whent he URL contains malformed encoded strings (i.e. %c5, %80)
    """
    return HTTPBadRequest()
