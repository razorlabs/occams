from collections import namedtuple
from contextlib import closing
import csv
from itertools import imap as map
import tempfile
import zipfile

from pyramid.httpexceptions import HTTPFound
from pyramid_layout.layout import layout_config
from pyramid_layout.panel import panel_config
from pyramid.response import FileResponse
from pyramid.view import view_config
from sqlalchemy import func, orm, sql
import transaction

from occams.datastore import model as datastore, reporting
from occams.datastore import User

from .. import _, log, models, Session
from ..utils.iter import partition
from ..models import (
    Patient, Visit, Enrollment, Site, Study, Cycle, visit_cycle_table)


# Export profiles for builtin data tables
# Because the tables in the database may not be in the order we'd like
# we use this mapping to define how to export
BUILTINS = {
    'patient': (
        Patient.id,
        Patient.pid, Patient.site_id, Patient.initials, Patient.nurse,
        Patient.create_date, Patient.create_user_id,
        Patient.modify_date, Patient.modify_date),
    'enrollment': (
        Enrollment.id,
        Enrollment.patient_id,
        Enrollment.consent_date, Enrollment.latest_consent_date, Enrollment.termination_date,
        Enrollment.create_date, Enrollment.create_user_id,
        Enrollment.modify_date, Enrollment.modify_date),
    'user': (User.id, User.key.label('email'), User.create_date, User.modify_date),
    'site': (
        Site.id,
        Site.name, Site.title, Site.description,
        Site.create_date, Site.create_user_id,
        Site.modify_date, Site.modify_user_id),
    'visit': (
        Visit.id,
        Visit.patient_id, Visit.visit_date,
        Visit.create_date, Visit.create_user_id,
        Visit.modify_date, Visit.modify_user_id),
    'study': (
        Study.id,
        Study.name, Study.title, Study.code, Study.consent_date,
        Study.create_date, Study.create_user_id,
        Study.modify_date, Study.modify_user_id),
    'cycle': (
        Cycle.id,
        Cycle.study_id, Cycle.name, Cycle.title, Cycle.week,
        Cycle.create_date, Cycle.create_user_id,
        Cycle.modify_date, Cycle.modify_user_id),
    'visit_cycle': (visit_cycle_table.c.visit_id, visit_cycle_table.c.cycle_id)}


@view_config(
    route_name='export_list',
    permission='fia_view',
    renderer='occams.clinical:templates/export/list.pt')
def list_(request):
    request.layout_manager.layout.content_title = _(u'Downloads')
    ecrfs_query = query_ecrfs()
    return {
        'builtins': sorted(BUILTINS.keys()),
        'ecrfs': ecrfs_query,
        'ecrfs_count': ecrfs_query.count()}


@view_config(
    route_name='export_download',
    permission='fia_view',
    request_method='GET')
def download(request):

    if 'all' in request.GET:
        tables = BUILTINS.keys()
        ecrfs = query_ecrfs()
    else:
        names, ids = partition(lambda s: s.isdigit(), request.GET.getall('ids'))
        tables = filter(lambda s: s in BUILTINS, names)
        ecrfs = query_ecrfs().filter(datastore.Schema.id.in_(map(int, ids)))

    with tempfile.NamedTemporaryFile('wb') as temp_file:
        with closing(zipfile.ZipFile(temp_file, 'w')) as zip_file:
            for name in tables:
                with tempfile.NamedTemporaryFile('wb') as form_file:
                    cols = BUILTINS[name]
                    query2csv(form_file, Session.query(*cols).order_by(cols[0]))
                    zip_file.write(form_file.name, '{0}.csv'.format(name))

        response = FileResponse(temp_file.name, request)
        response.headers['Content-Disposition'] = \
            'attachment;filename=occams.clinical.zip'
        return response


def query_ecrfs():
    return (
        Session.query(datastore.Schema)
        .filter(datastore.Schema.publish_date != None)
        .order_by(
            datastore.Schema.name.asc(),
            datastore.Schema.publish_date.desc()))


def query2csv(file, query):
    writer = csv.writer(file)
    writer.writerow([d['name'] for d in query.column_descriptions])
    writer.writerows(query)
    file.flush()


def query_ecrf(id):
    []

