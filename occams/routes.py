
def includeme(config):
    """
    Helper method to configure available routes for the application
    """

    config.add_static_view('static', 'occams:static', cache_max_age=3600)
    config.add_route('occams', '/')
