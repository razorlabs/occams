import json

from pyramid.view import view_config
from socketio import socketio_manage
from socketio.namespace import BaseNamespace

from .. import log, redis


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
    This service will emit the progress of the current user's exports
    """

    def get_initial_acl(self):
        """
        Everything is locked at first
        """
        return []

    def initialize(self):
        """
        Determines from the request if this socket can accept events
        """
        if self.request.has_permission('fia_view'):
            self.lift_acl_restrictions()
            self.session['user'] = self.request.user.email
            self.spawn(self.listener)

    def listener(self):
        """
        Main process that listens for export porgress broadcasts.
        All progress relating to the current user will be sent back.
        """
        pubsub = redis.pubsub()
        pubsub.subscribe('export')

        # TODO: Need to send back iniital progress

        for message in pubsub.listen():
            if message['type'] != 'message':
                continue

            data = json.loads(message['data'])

            if data['owner_user'] == self.session['user']:
                self.emit('progress', data)

