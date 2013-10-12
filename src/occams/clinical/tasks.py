import json
import tempfile
import zipfile
import csv

import celery
from celery.utils.log import get_task_logger
import transaction

from occams.datastore import model as datastore, reporting

from . import models, Session, redis


# Need to use a separate logger for celery threads
log = get_task_logger(__name__)


@celery.task
def make_export(export_id, table_names, ecrf_ids):
    # Get the export instance attached to this thread
    #export = Session.query(models.Export).get(export_id)

    user = 'foo@bar.com'

    total = float(len(table_names) + len(ecrf_ids))
    count = 0

    redis.hset(user, export_id, count/total)

    print('Starting...')

    progress = {'user': user, 'export_id': export_id, 'progress': 0}

    attachment_fp = tempfile.NamedTemporaryFile()
    zip_fp = zipfile.ZipFile(attachment_fp, 'w', zipfile.ZIP_DEFLATED)

    for name in table_names:
        cols = models.BUILTINS[name]
        print('Generating %s' % name)
        query = Session.query(*cols).order_by(cols[0])
        dump_table_datadict(zip_fp, name + 'datadict.csv', query)
        dump_query(zip_fp, name + '.csv', query)
        count += 1
        redis.hset(user, export_id, count/total)
        progress['progress'] = count/total
        redis.publish('export', json.dumps(progress))

    ecrfs_query = (
        Session.query(datastore.Schema)
        .filter(datastore.Schema.id.in_(ecrf_ids)))

    for ecrf in ecrfs_query:
        print('Generating %s' % ecrf.name)
        query = Session.query(reporting.export(ecrf))
        arcname = ecrf.name + '-' + str(ecrf.publish_date) + '.csv'
        dump_query(zip_fp, arcname, query)
        count += 1
        redis.hset(user, export_id, count/total)
        progress['progress'] = count/total
        redis.publish('export', json.dumps(progress))

    redis.hdel(user, export_id)
    print('Done...')

    zip_fp.close()

    attachment_fp.seek(0)


@celery.task
def cleanup_export():
    """
    Cleans up the database of expired exports
    """


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

