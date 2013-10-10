import json
import tempfile
import zipfile
from contextlib import closing
from itertools import imap as map
import csv

from pyramid.response import Response
from pyramid.view import view_config
from socketio import socketio_manage
from socketio.namespace import BaseNamespace
from socketio.mixins import  BroadcastMixin
from sqlalchemy import func, orm, sql
import transaction

from occams.datastore import model as datastore, reporting

from .. import _, log, models, Session


@view_config(route_name='socket_io')
def socket_io(request):
    """
    Main socket.io handler for the application
    """
    socketio_manage(request.environ, request=request, namespaces={
        '/export': ExportNamespace})
    return Response('')


class ExportNamespace(BaseNamespace, BroadcastMixin):
    """
    Export thread
    """

    def get_initial_acl(self):
        """
        Everything is locked at first
        """
        return []

    def initialize(self):
        if self.request.has_permission('view'):
            self.lift_acl_restrictions()

    def on_wtf(self, *args, **kwargs):
        self.emit('hello', 'world')

    def on_export(self, *args, **kwargs):
        self.spawn(self._export)

    def _process():
        if csrf != request.POST['csrf']:
            request.session.flash(_(u'CSRF token mismatch!!'), 'error')
            return default_values()

        selected = set(request.POST.getall('ids'))

        # Nothing submitted
        if not selected:
            request.session.flash(_(u'No values selected!!'), 'error')
            return default_values()

        #query = (
            #Session.query(datastore.Schema.id)
            #.filter(datastore.Schema.publish_date != None))
        #return [r.id for r in query]

        valid_names = set(BUILTINS.keys())
        valid_ids = set(get_published_ecrf_ids())
        names, ids = partition(lambda s: s.isdigit(), selected)
        names, ids = set(names), set(map(int, ids))

        # Submitted, but some items aren't even in the valid choices
        if not names <= valid_names or not ids <= valid_ids:
            request.session.flash(_(u'Invalid selection!'), 'error')
            return default_values()

        request.session.flash(_(u'Success! Your export is being processed...'), 'success')

        attachment_fp = tempfile.NamedTemporaryFile()
        zip_fp = zipfile.ZipFile(attachment_fp, 'w', zipfile.ZIP_DEFLATED)

        for name, cols in filter(lambda i: i[0] in names, BUILTINS.items()):
            query = Session.query(*cols).order_by(cols[0])
            dump_table_datadict(zip_fp, name + 'datadict.csv', query)
            dump_query(zip_fp, name + '.csv', query)

        for schema in ecrfs_query.filter(datastore.Schema.id.in_(ids)):
            query = Session.query(reporting.export(schema))
            arcname = schema.name + '-' + str(schema.publish_date) + '.csv'
            dump_query(zip_fp, arcname, query)

        zip_fp.close()

        attachment_fp.seek(0)

    def on_subscribe(self, *args, **kwargs):
        self.spawn(self.listener)

    def on_chat(self, msg):
        r = redis.Redis()
        r.publish('chat', dumps(msg))


def dump_query(zip_fp, arcname, query):
    with tempfile.NamedTemporaryFile() as fp:
        writer = csv.writer(fp)
        writer.writerow([d['name'] for d in query.column_descriptions])
        writer.writerows(query)
        fp.flush()
        zip_fp.write(fp.name, arcname)


def dump_table_datadict(zip_fp, arcname, query):
    pass


def dump_ecrf_datadict(zip_fp, arcname, query):
    pass

