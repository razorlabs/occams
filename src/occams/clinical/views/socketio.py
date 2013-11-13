from __future__ import absolute_import
import itertools
import json

import gevent
from redis import StrictRedis
from pyramid.view import view_config
from pyramid.response import Response
from socketio import socketio_manage
from socketio.namespace import BaseNamespace

from occams.clinical import log, models, Session, redis

@view_config(route_name='socketio')
def socketio(request):
    """
    Main socket.io handler for the application
    """
    socketio_manage(request.environ, request=request, namespaces={
        '/export': ExportNamespace})
    return Response('')


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
        client = redis.pubsub()
        client.subscribe('export')

        pending_query = (
            Session.query(models.Export.id)
            .filter(models.Export.owner_user.has(key=self.session['user']))
            .filter_by(status='pending'))

        # emit current progress
        for (export_id,) in pending_query:
            data = redis.hgetall(export_id)
            log.debug('progress', data)
            self.emit('progress', data)

        # TODO: r.listen() is a blocking call
        # gevent needs to be configured in order for this to run concurrently
        for message in client.listen():
            if message['type'] != 'message':
                continue

            data = json.loads(message['data'])

            if data['owner_user'] == self.session['user']:
                log.debug('progress', data)
                self.emit('progress', data)

