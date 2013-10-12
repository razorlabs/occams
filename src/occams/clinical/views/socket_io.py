import json

from pyramid.view import view_config
from socketio import socketio_manage
from socketio.namespace import BaseNamespace

from .. import log, redis


PROGRESS_KEY = 'progress'
EXPORT_ROOM_KEY = 'export'


@view_config(route_name='socketio')
def socketio(request):
    """
    Main socket.io handler for the application
    """
    socketio_manage(request.environ, request=request, namespaces={
        '/export': ExportNamespace})
    return request.response


class ExportNamespace(BaseNamespace):
    """
    This thread will emit the progress of the export processes
    """


    def get_initial_acl(self):
        """
        Everything is locked at first
        """
        return []

    def initialize(self):
        """
        Determines from the request if this socket has can accept events
        """
        if self.request.has_permission('fia_view'):
            self.lift_acl_restrictions()
        self.session['user'] = self.request.user.email
        self.spawn(self.listener)

    def listener(self):
        pubsub = redis.pubsub()
        pubsub.subscribe(EXPORT_ROOM_KEY)
        for message in pubsub.listen():
            if message['type'] == 'message':
                self.emit(PROGRESS_KEY, json.loads(message['data']))

