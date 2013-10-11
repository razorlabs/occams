import tempfile
import zipfile
from contextlib import closing
import csv

import celery
from sqlalchemy import func, orm, sql
import transaction

from occams.datastore import model as datastore, reporting

from . import models, Session


@celery.task
def export(user, names, ids):
    attachment_fp = tempfile.NamedTemporaryFile()
    zip_fp = zipfile.ZipFile(attachment_fp, 'w', zipfile.ZIP_DEFLATED)

    for name, cols in filter(lambda i: i[0] in names, models.BUILTINS.items()):
        print('Generating %s' % name)
        query = Session.query(*cols).order_by(cols[0])
        dump_table_datadict(zip_fp, name + 'datadict.csv', query)
        dump_query(zip_fp, name + '.csv', query)

    ecrfs_query = (
        Session.query(datastore.Schema)
        .filter(datastore.Schema.id.in_(ids)))

    for ecrf in ecrfs_query:
        print('Generating %s' % ecrf.name)
        query = Session.query(reporting.export(ecrf))
        arcname = ecrf.name + '-' + str(ecrf.publish_date) + '.csv'
        dump_query(zip_fp, arcname, query)

    zip_fp.close()

    attachment_fp.seek(0)


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

