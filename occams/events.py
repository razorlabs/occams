"""
Pyramid-specific events
"""

from pyramid.events import subscriber, NewResponse, NewRequest

from occams_datastore import models as datastore


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
    db_session = request.db_session

    if request.authenticated_userid is not None:
        db_session.info['blame'] = (
            db_session.query(datastore.User)
            .filter_by(key=request.authenticated_userid)
            .one())

    # Store the CSRF token in a cookie since we'll need to sent it back
    # frequently in single-page views.
    # https://docs.djangoproject.com/en/dev/ref/contrib/csrf/
    # The attacker cannot read or change the value of the cookie due to the
    # same-origin policy, and thus cannot guess the right GET/POST parameter
    request.response.set_cookie('csrf_token', request.session.get_csrf_token())
