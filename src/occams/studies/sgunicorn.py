"""
Server integration with gunicorn

This module exists because the gevent-socketio integration for gunicorn
is not configurable and because we needed to get this module up and
running in time for deadlines.

Will (hopefully) be replaced with asyncio when we switch to Python 3.4
"""

try:
    from gunicorn.config import validate_bool

    from socketio.server import SocketIOServer
    from socketio.sgunicorn import (
        GeventSocketIOBaseWorker, GunicornWebSocketWSGIHandler,
        GunicornWSGIHandler)

    class GeventSocketIOWorker(GeventSocketIOBaseWorker):
        """
        Default gunicorn worker utilizing gevent

        Uses the namespace 'socket.io' and defaults to the flash policy server
        being disabled.
        """
        server_class = SocketIOServer
        wsgi_handler = GunicornWSGIHandler
        ws_wsgi_handler = GunicornWebSocketWSGIHandler

        def __init__(self, age, ppid, socket, app, timeout, cfg, log):
            self.resource = cfg.env.get('resource', 'socket.io')
            self.policy_server = (
                validate_bool(cfg.env.get('policy_server') or False))
            super(GeventSocketIOWorker, self).__init__(
                age, ppid, socket, app, timeout, cfg, log)
except ImportError:
    pass
