from pyramid.events import subscriber, NewResponse


@subscriber(NewResponse)
def vary_json(event):
    """
    Prevent browser from overwriting HTML with JSON from the same URL.
    More info: http://stackoverflow.com/a/1975677/148781
    """
    if event.request.is_xhr:
        event.response.vary = 'Accept'
