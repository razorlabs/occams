"""
Report-generating modules

This module does the actual heavy-lifting wereas the others just
offer an interface (gui or cli, etc)
"""

try:
    import unicodecsv as csv
except ImportError:  # pragma: nocover
    import csv  # NOQA (py3, hopefully)
try:
    from ordereddict import OrderedDict
except ImportError:
    from collections import OrderedDict
from itertools import chain
import os

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
    Iterator of exportable data files.
    """

    # Precooked reports
    tables = [EnrollmentPlan(), PidPlan(), LabPlan(), VisitPlan()]
    schemata = SchemaPlan.list_all(include_rand, include_private)
    merged = sorted(tables + schemata, key=lambda v: v.title)
    all = OrderedDict((i.name, i) for i in merged)
    return all


def write_reports(path, items):
    codebooks = []

    for item in items:
        codebooks.append(item.codebook())
        with open(os.path.join(path, item.file_name), 'w+b') as fp:
            write_data(fp, item.data())

    with open(os.path.join(path, codebook.FILE_NAME), 'w+b') as fp:
        write_codebook(fp, chain.from_iterable(codebooks))


def write_data(buffer, query):
    """
    Dumps a query to a CSV file using the specified buffer
    Each record in the query is accessed as a "namedtuple".
    """
    fieldnames = [d['name'] for d in query.column_descriptions]
    writer = csv.DictWriter(buffer, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows([r._asdict() for r in query])
    buffer.flush()


def write_codebook(buffer, rows):
    """
    Dumps a list of dictioanries to a CSV file using the specified buffer
    """
    #TODO this might not even be needed
    writer = csv.DictWriter(buffer, codebook.HEADER)
    writer.writeheader()
    writer.writerows(rows)
    buffer.flush()
