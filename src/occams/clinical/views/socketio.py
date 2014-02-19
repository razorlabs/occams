from __future__ import absolute_import
import json

from pyramid.view import view_config
from pyramid.response import Response
from pyramid.security import authenticated_userid
from socketio import socketio_manage
from socketio.namespace import BaseNamespace

from occams.clinical import log, models, Session


@view_config(route_name='socketio')
def socketio(request):  # pragma: nocover: don't need to unittest socketio.io
    """
    Main socket.io handler for the application
    Pretty much registers socket.io namespaces
    """
    socketio_manage(request.environ, request=request, namespaces={
        '/export': ExportNamespace})
    return Response('OK')


class ExportNamespace(BaseNamespace):
    """
    This service will emit the progress of the current user's exports

    Note that this service is just a pass-through for export broadcasts,
    it simply takes what is published in the export channel and emits
    progress data with the message that was broadcast. The only key
    in the message that this service depends on is the ``owner_user``
    key (to ensure the broadcast goes to the appropriate user).
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
        log.debug('Initializing socket.io service')
        log.debug(self.request.has_permission('fia_view'))
        if self.request.has_permission('fia_view'):
            self.lift_acl_restrictions()
            self.session['user'] = authenticated_userid(self.request)
            self.session['redis'] = self.request.redis
            log.debug('socket.io for %s' % self.session['user'])
            self.spawn(self.listener)

    def listener(self):
        """
        Main process that listens for export progress broadcasts.
        All progress relating to the current user will be sent back.
        """
        userid = self.session['user']
        redis = self.session['redis']

        pending_query = (
            Session.query(models.Export.id)
            .filter(models.Export.owner_user.has(key=userid))
            .filter_by(status='pending'))

        # emit current progress
        for export_id, in pending_query:
            data = redis.hgetall(export_id)
            log.debug(data)
            self.emit('progress', data)

        pubsub = redis.pubsub()
        pubsub.subscribe('export')

        # emit subsequent progress
        for message in pubsub.listen():
            if message['type'] == 'message':
                data = json.loads(message['data'])
                if data['owner_user'] == userid:
                    log.debug(data)
                    self.emit('progress', data)
