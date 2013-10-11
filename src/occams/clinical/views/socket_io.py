import json
from pyramid.response import Response
from pyramid.view import view_config
from socketio import socketio_manage
from socketio.namespace import BaseNamespace
from socketio.mixins import  BroadcastMixin


@view_config(route_name='socket_io')
def socket_io(request):
    """
    Main socket.io handler for the application
    """
    socketio_manage(request.environ, request=request, namespaces={
        '/export': ExportNamespace})
    return Response('')


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


