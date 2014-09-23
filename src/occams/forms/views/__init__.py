from pyramid.events import subscriber, NewResponse


@subscriber(NewResponse)
def vary_json(event):
    """
    Make sure the browser doesn't override the cache for the JSON respnose.

    This will happen when two equivalent URLs return different responses
    (json or HTML dependeing on ajax call). So to prevent this we need
    to set the "Vary" header.
    """
    if event.request.is_xhr:
        event.response.vary = 'Accept'
