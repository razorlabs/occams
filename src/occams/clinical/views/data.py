from collections import namedtuple
from contextlib import closing
import csv
from itertools import imap as map
import tempfile
import zipfile

from pyramid.httpexceptions import HTTPFound
from pyramid_layout.layout import layout_config
from pyramid_layout.panel import panel_config
from pyramid.response import FileResponse, FileIter
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
        Enrollment.reference_number,
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
    route_name='data_list',
    permission='fia_view',
    renderer='occams.clinical:templates/data/list.pt')
def list_(request):
    layout = request.layout_manager.layout
    layout.title = _(u'Data')
    layout.set_nav('data_nav')

    ecrfs_query = query_published_ecrfs()
    ecrfs_count = ecrfs_query.count()

    return {
        'builtins': sorted(BUILTINS.keys()),
        'ecrfs': ecrfs_query,
        'has_ecrfs': ecrfs_count > 0,
        'ecrfs_count': ecrfs_count}


@view_config(
    route_name='data_download',
    permission='fia_view',
    renderer='occams.clinical:templates/data/download.pt')
def download(request):
    layout = request.layout_manager.layout
    layout.title = _(u'Data')
    layout.set_nav('data_nav')

    return {}

def process(request):
    selected = set(request.POST.getall('ids'))

    # Nothing submitted
    if not selected:
        return default_values()

    valid_names = set(BUILTINS.keys())
    valid_ids = set(get_published_ecrf_ids())
    names, ids = partition(lambda s: s.isdigit(), selected)
    names, ids = set(names), set(map(int, ids))

    # Submitted, but some items aren't even in the valid choices
    if not names <= valid_names or not ids <= valid_ids:
        request.session.flash(_(u'Invalid selection!'), 'error')
        return default_values()

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

    response = request.response
    response.app_iter = FileIter(attachment_fp)
    response.content_disposition = 'attachment;filename=clinical.zip'
    return response

def query_published_ecrfs():
    return (
        Session.query(datastore.Schema)
        .filter(datastore.Schema.publish_date != None)
        .order_by(
            datastore.Schema.name.asc(),
            datastore.Schema.publish_date.desc()))


def get_published_ecrf_ids():
    query = (
        Session.query(datastore.Schema.id)
        .filter(datastore.Schema.publish_date != None))
    return [r.id for r in query]


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

