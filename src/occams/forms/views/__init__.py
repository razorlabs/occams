from pyramid.events import subscriber, NewResponse


@subscriber(NewResponse)
def vary_json(event):
    """
    Make sure the browser doesn't override the cache for the JSON respnose.

    This will happen when two equivalent URLs return different responses
    (json or HTML dependeing on ajax call). So to prevent this we need
    to set the "Vary" header [1]

    [1] http://stackoverflow.com/a/1975677/148781
        If you have two copies of the same content at the same URL,
        differing only in Content-Type, then using Vary: Accept
        could be appropriate.
    """
    if event.request.is_xhr:
        event.response.vary = 'Accept'
