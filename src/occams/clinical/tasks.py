"""
Contains long-running tasks that cannot interrupt the user experience.

Tasks in this module will be run in a separate process so the user
can continue to use the application and download their exports at a
later time.
"""

try:
    import unicodecsv as csv
except ImportError:
    import csv  # NOQA (py3, hopefully)
from contextlib import closing
import json
import os
import tempfile
import zipfile

from celery import Celery, Task
from celery.bin import Option
from celery.signals import worker_init
from celery.utils.log import get_task_logger
from pyramid.paster import bootstrap
from webob.multidict import MultiDict
import transaction

from occams.clinical import _, models, Session
from occams.datastore import reporting


app = Celery(__name__)

app.user_options['worker'].add(
    Option('--ini', help='Pyramid config file'))

log = get_task_logger(__name__)


class SqlAlchemyTask(Task):
    """
    Base class for tasks that use SQLAlchemy.

    This abstract class ensures that the connection the the database is
    closed on task completion to prevent leaked open connections
    """

    abstract = True

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        Session.remove()


@worker_init.connect
def init(signal, sender):
    """
    Configure the database connections when the celery daemon starts
    """
    # Have the pyramid app initialize all settings
    env = bootstrap(sender.options['ini'])
    sender.app.settings = env['registry'].settings
    sender.app.redis = env['request'].redis


@app.task(base=SqlAlchemyTask)
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

    # File has been closed/flushed, it's ready for consumption
    with transaction.manager:
        update_query = Session.query(models.Export).filter_by(id=export_id)
        update_query.update({'status': u'complete'}, 'fetch')

    redis.hset(export_id, 'status', 'complete')
    redis.publish('export', json.dumps(redis.hgetall(export_id)))


@app.task
def handle_error(uuid):
    """
    Handles asynchronous errors
    """
    log.error('Oh snap, there was an error')


def query_report(schema):
    report = reporting.export(schema)
    query = (
        Session.query(report.c.entity_id)
        .add_column(
            Session.query(models.Patient.pid)
            .distinct()
            .join(models.Visit)
            .join(models.Context,
                  (models.Context.external == 'visit')
                  & (models.Context.key == models.Visit.id))
            .filter(models.Context.entity_id == report.c.entity_id)
            .correlate(report)
            .as_scalar()
            .label('pid'))
        .add_columns(
            *[c for c in report.columns if c.name != 'entity_id']))
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
