"""
Report-generating modules

This module does the actual heavy-lifting wereas the others just
offer an interface (gui or cli, etc)
"""

import inspect

try:
    import unicodecsv as csv
except ImportError:  # pragma: nocover
    import csv
try:
    from ordereddict import OrderedDict
except ImportError:  # pragma: nocover
    from collections import OrderedDict

from pyramid.config import aslist
from pyramid.path import DottedNameResolver

from .. import log
from . import codebook


def includeme(config):
    resolver = DottedNameResolver()
    settings = config.registry.settings
    names = aslist(settings.get('studies.export.plans') or '')
    settings['studies.export.plans'] = [resolver.resolve(n) for n in names]


def list_all(plans, db_session, include_rand=True, include_private=True):
    """
    Lists all available data files

    Arguments:
    ids -- (Optional) Only list schemata with specific ids
    include_rand -- (Optional) Include randomization data files

    Returns:
    An ordered dictionary (name, plan) items.
    """

    def iterplans():
        for plan in plans:
            if inspect.isclass(plan):
                yield plan(db_session)
            elif inspect.ismethod(plan):
                exportables = plan(
                    db_session,
                    include_rand=include_rand,
                    include_private=include_private
                )

                for exportable in exportables:
                    yield exportable
            else:
                log.error('{} is unsupported plan type'.format(plan))

    merged = sorted(iterplans(), key=lambda v: v.title.lower())
    all = OrderedDict((i.name, i) for i in merged)
    return all


def write_data(buffer, query):
    """
    Dumps a query to a CSV file using the specified buffer
    Each record in the query is accessed as a `namedtuple`.

    See `namedtuple`.

    Arguments:
    buffer -- a file object which will be used to write data contents
    query -- SQLAlchemy query that will be writen to a CSV file.
             Note that the column names will be used as the header.
    """
    fieldnames = [d['name'] for d in query.column_descriptions]
    writer = csv.DictWriter(buffer, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(r._asdict() for r in query)
    buffer.flush()


def write_codebook(buffer, rows):
    """
    Dumps a list of dictioanries to a CSV file using the specified buffer

    Arguments:
    buffer -- a file object which will be used to write data contents
    rows -- Code book rows. Seee `occams_studies.codebook`
    """
    writer = csv.DictWriter(buffer, codebook.HEADER)
    writer.writeheader()

    def choices2string(choices):
        choices = choices or []
        return ';'.join(['%s=%s' % c for c in choices])

    for row in rows:
        row['choices'] = choices2string(row['choices'])
        writer.writerow(row)

    buffer.flush()
