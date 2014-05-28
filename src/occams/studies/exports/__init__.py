"""
Report-generating modules

This module does the actual heavy-lifting wereas the others just
offer an interface (gui or cli, etc)
"""

try:
    import unicodecsv as csv
except ImportError:  # pragma: nocover
    import csv
try:
    from ordereddict import OrderedDict
except ImportError:  # pragma: nocover
    from collections import OrderedDict

from ..import Session
from . import codebook
from .enrollment import EnrollmentPlan
from .pid import PidPlan
from .lab import LabPlan
from .schema import SchemaPlan
from .visit import VisitPlan


def list_all(include_rand=True, include_private=True):
    """
    Lists all available data files

    Arguments:
    ids -- (Optional) Only list schemata with specific ids
    include_rand -- (Optional) Include randomization data files

    Returns:
    An ordered dictionary (name, plan) items.
    """
    # Precooked reports
    tables = [EnrollmentPlan(), PidPlan(), VisitPlan()]
    if 'aliquot' in Session.bind.table_names():
        # BBB: Lab is not part of the studies app, but needs to be
        #      generated anyway until we can implement LIMS, in which
        #      case it'll have it's own export page/process in that app.
        tables.append(LabPlan())
    schemata = SchemaPlan.list_all(include_rand=include_rand,
                                   include_private=include_private)
    merged = sorted(tables + schemata, key=lambda v: v.title)
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
    writer.writerows([r._asdict() for r in query])
    buffer.flush()


def write_codebook(buffer, rows):
    """
    Dumps a list of dictioanries to a CSV file using the specified buffer

    Arguments:
    buffer -- a file object which will be used to write data contents
    rows -- Code book rows. Seee `occams.studies.codebook`
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
