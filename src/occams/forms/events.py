"""
Pyramid-specific events
"""

from pyramid.events import subscriber, NewResponse, NewRequest

from . import Session, models


@subscriber(NewResponse)
def vary_json(event):
    """
    Prevent browser from overwriting HTML with JSON from the same URL.
    More info: http://stackoverflow.com/a/1975677/148781
    """
    if event.request.is_xhr:
        event.response.vary = 'Accept'


@subscriber(NewRequest)
def track_user_on_request(event):
    """
    Annotates the database session with the current user.
    """
    request = event.request

    # Keep track of the request so we can generate model URLs
    Session.info['request'] = request
    Session.info['blame'] = (
        Session.query(models.User)
        .filter_by(key=request.authenticated_userid)
        .one())

    # Store the CSRF token in a cookie since we'll need to sent it back
    # frequently in single-page views.
    # https://docs.djangoproject.com/en/dev/ref/contrib/csrf/
    # The attacker cannot read or change the value of the cookie due to the
    # same-origin policy, and thus cannot guess the right GET/POST parameter
    request.response.set_cookie('csrf_token', request.session.get_csrf_token())
