import json

import colander
from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config
from socketio import socketio_manage
from socketio.namespace import BaseNamespace
from sqlalchemy import func, orm, sql
import transaction

from occams.datastore import model as datastore

from .. import _, log, models, Session


class ExportNamespace(BaseNamespace):
    def listener(self):
        r = redis.StrictRedis()
        r = r.pubsub()

        r.subscribe('chat')

        for m in r.listen():
            if m['type'] == 'message':
                data = loads(m['data'])
                self.emit("chat", data)

    def on_subscribe(self, *args, **kwargs):
        self.spawn(self.listener)

    def on_chat(self, msg):
        r = redis.Redis()
        r.publish('chat', dumps(msg))


@view_config(route_name='socket_io')
def socketio_service(request):
    return socketio_manage(request.environ, {
        '/export': ExportNamespace })

