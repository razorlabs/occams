"""
Contains long-running tasks that cannot interrupt the user experience.

Tasks in this module will be run in a separate process so the user
can continue to use the application and download their exports at a
later time.
"""

try:
    import unicodecsv as csv
except ImportError:  # pragma: nocover
    import csv  # NOQA (py3, hopefully)
from contextlib import closing
import json
import os
import tempfile
import zipfile

from celery import Celery
from celery.bin import Option
from celery.signals import worker_init
from celery.utils.log import get_task_logger
from pyramid.paster import bootstrap
from sqlalchemy import orm, func, literal
from webob.multidict import MultiDict
import transaction

from occams.clinical import _, models, Session
from occams.datastore import reporting


app = Celery(__name__)

app.user_options['worker'].add(
    Option('--ini', help='Pyramid config file'))

log = get_task_logger(__name__)


def in_transaction(func):
    """
    Function decoratator that commits on successul execution, aborts otherwise.

    Also releases connection to prevent leaked open connections.

    The pyramid application-portion relies on ``pyramid_tm`` to commit at
    the end of each request. Tasks don't have this luxury and must
    be committed manually after each successful call.
    """
    def decorated(*args, **kw):
        with transaction.manager:
            result = func(*args, **kw)
        Session.remove()
        return result
    return decorated


@worker_init.connect
def init(signal, sender):
    """
    Configure the database connections when the celery daemon starts
    """
    # Have the pyramid app initialize all settings
    env = bootstrap(sender.options['ini'])
    sender.app.settings = env['registry'].settings
    sender.app.redis = env['request'].redis


@app.task(ignore_result=True)
@in_transaction
def make_export(export_id):
    """
    Handles generating exports in a separate process.

    Because the export is handled in a different process, this method
    can only accept the id of the entry. This is to avoid race
    conditions,
    (http://docs.celeryproject.org/en/latest/userguide/tasks.html#state)

    All progress will be broadcast to the redis **export** channel with the
    following dictionary:
    export_id -- the export being processed
    owner_user -- the user who this export belongs to
    count -- the current number of files processed
    total -- the total number of files that will be processed
    status -- current status of the export

    Parameters:
    export_id -- export to process

    """
    export = Session.query(models.Export).filter_by(id=export_id).one()
    export_dir = app.settings['app.export_dir']

    assert export.schemata, \
        _(u'The specified export job has no schemata: %s' % export)
    assert export.status not in ('complete', 'failed'), \
        _(u'The specified export is not pending: %s' % export)

    # Organize the forms so we know which schemata go where
    codebooks = MultiDict([(s.name, s.id) for s in export.schemata])

    redis = app.redis

    redis.hmset(export.id, {
        'export_id': export.id,
        'owner_user': export.owner_user.key,
        'status': export.status,
        'count': 0,
        'total': len(export.schemata) + len(set(codebooks.keys()))})

    path = os.path.join(export_dir, '%s.zip' % export.id)

    def publish_done(arcname):
        redis.hincrby(export.id, 'count')
        redis.publish('export', json.dumps(redis.hgetall(export.id)))
        count, total = redis.hmget(export.id, 'count', 'total')
        log.info(', '.join([count, total, arcname]))

    with closing(zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED)) as zfp:
        # Generate the data files
        for schema in export.schemata:
            arcname = '{0}-{1}.csv'.format(schema.name, schema.publish_date)
            archive_query(zfp, arcname, query_report(schema))
            publish_done(arcname)

        # Generate the ecrf codebooks
        for name, ids in codebooks.dict_of_lists().items():
            arcname = '{0}-codebook.csv'.format(name)
            archive_codebook(zfp, arcname, name, ids)
            publish_done(arcname)

    # Need to commit this somehow...
    export.status = 'complete'
    Session.flush()

    redis.hset(export_id, 'status', export.status)
    redis.publish('export', json.dumps(redis.hgetall(export_id)))


def query_report(schema):
    """
    Generates a clinical report containing the patient's metadata
    that relates to the form.

    Clinical metadadata includes:
        * site -- Patient's site
        * pid -- Patient's PID number
        * enrollment -- The applicable enrollment
        * cycles - The applicable visit's cycles

    Parameters:
    schema -- The schema to generate the report for

    Returns:
    A SQLAlchemy query
    """

    def aggregate(expr):
        if Session.bind.url.drivername == 'postgresql':
            return func.array_to_string(func.array_agg(expr), literal(','))
        else:
            return func.group_concat(expr)

    report = reporting.export(schema)
    query = (
        Session.query(report.c.entity_id)
        .add_column(
            Session.query(models.Site.name)
            .select_from(models.Patient)
            .join(models.Site)
            .join(models.Context,
                  (models.Context.external == 'patient')
                  & (models.Context.key == models.Patient.id))
            .filter(models.Context.entity_id == report.c.entity_id)
            .correlate(report)
            .as_scalar()
            .label('site'))
        .add_column(
            Session.query(models.Patient.pid)
            .join(models.Context,
                  (models.Context.external == 'patient')
                  & (models.Context.key == models.Patient.id))
            .filter(models.Context.entity_id == report.c.entity_id)
            .correlate(report)
            .as_scalar()
            .label('pid'))
        .add_column(
            Session.query(models.Study.name)
            .select_from(models.Enrollment)
            .join(models.Study)
            .join(models.Context,
                  (models.Context.external == 'enrollment')
                  & (models.Context.key == models.Enrollment.id))
            .filter(models.Context.entity_id == report.c.entity_id)
            .correlate(report)
            .as_scalar()
            .label('enrollment'))
        .add_column(
            Session.query(aggregate(models.Cycle.name))
            .select_from(models.Visit)
            .join(models.Visit.cycles)
            .join(models.Context,
                  (models.Context.external == 'visit')
                  & (models.Context.key == models.Visit.id))
            .filter(models.Context.entity_id == report.c.entity_id)
            .correlate(report)
            .as_scalar()
            .label('cycles'))
        .add_columns(*[c for c in report.columns if c.name != 'entity_id']))
    return query


def archive_query(zfp, arcname, query):
    """
    Dumps an arbitrary query to a CSV file inside an archive file

    Parameters:
    zfp -- the zip file pointer
    arcname -- the name inside the archive
    query -- the source query

    """
    with tempfile.NamedTemporaryFile() as tfp:
        writer = csv.writer(tfp)
        writer.writerow([d['name'] for d in query.column_descriptions])
        writer.writerows(query)
        tfp.flush()  # ensure everything's on disk
        zfp.write(tfp.name, arcname)


def archive_codebook(zfp, arcname, name, ids=None):
    """
    Dumps the ecrf into a CSV codebook file inside an archive file

    Parameters:
    zfp -- the zip file pointer
    arcname -- the name inside the archive
    name -- the ecrf schema name
    ids -- (optional) the specific ids of the schema

    """
    query = (
        Session.query(models.Attribute)
        .join(models.Schema)
        .filter(models.Schema.name == name)
        .filter(models.Schema.id.in_(ids))
        .order_by(
            models.Attribute.order,
            models.Schema.publish_date))

    with tempfile.NamedTemporaryFile() as tfp:
        writer = csv.writer(tfp)
        writer.writerow([
            'form_name',
            'form_title',
            'form_publish_date',
            'field_name',
            'field_title',
            'field_description',
            'field_is_required',
            'field_is_collection',
            'field_type',
            'field_choices',
            'field_order'])

        for attribute in query:
            schema = attribute.schema
            choices = attribute.choices
            writer.writerow([
                schema.name,
                schema.title,
                schema.publish_date,
                attribute.name,
                attribute.title,
                attribute.description,
                attribute.is_required,
                attribute.is_collection,
                attribute.type,
                '\r'.join(['%s - %s' % (c.name, c.title) for c in choices]),
                attribute.order])

        tfp.flush()  # ensure everything's on disk
        zfp.write(tfp.name, arcname)
