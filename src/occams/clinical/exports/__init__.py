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

from sqlalchemy import orm, null, func, literal_column

from .. import Session, models
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

    InnerSchema = orm.aliased(models.Schema)
    OuterSchema = orm.aliased(models.Schema)

    schemata_query = (
        Session.query(OuterSchema.name)
        .add_column(literal_column("'schema'").label('type'))
        .add_column(
            Session.query(models.Attribute)
            .filter(models.Attribute.is_private)
            .join(InnerSchema)
            .filter(InnerSchema.name == OuterSchema.name)
            .correlate(OuterSchema)
            .exists()
            .label('has_private'))
        .add_column(
            Session.query(models.Entity)
            .join(models.Entity.contexts)
            .filter(models.Context.external == 'stratum')
            .join(models.Stratum, models.Context.key == models.Stratum.id)
            .join(InnerSchema, models.Entity.schema)
            .filter(InnerSchema.name == OuterSchema.name)
            .correlate(OuterSchema)
            .exists()
            .label('has_rand'))
        .add_column(
            Session.query(InnerSchema.title)
            .select_from(InnerSchema)
            .filter(InnerSchema.name == OuterSchema.name)
            .filter(InnerSchema.publish_date != null())
            .filter(InnerSchema.retract_date == null())
            .order_by(InnerSchema.publish_date.desc())
            .limit(1)
            .correlate(OuterSchema)
            .as_scalar()
            .label('title'))
        .add_column(
            func.array(
                Session.query(InnerSchema.publish_date)
                .distinct()
                .filter(InnerSchema.name == OuterSchema.name)
                .filter(InnerSchema.publish_date != null())
                .filter(InnerSchema.retract_date == null())
                .order_by(InnerSchema.publish_date.desc())
                .correlate(OuterSchema)
                .as_scalar())
            .label('versions'))
        .filter(OuterSchema.publish_date != null())
        .filter(OuterSchema.retract_date == null()))

    schemata_query = (
        schemata_query
        .group_by(OuterSchema.name)
        .from_self())

    if not include_rand:
        schemata_query = schemata_query.filter('NOT has_rand')

    if not include_private:
        schemata_query = schemata_query.filter('NOT has_private')

    schemata_query = schemata_query.order_by('title')

    # Precooked reports
    tables = [EnrollmentPlan(), PidPlan(), LabPlan(), VisitPlan()]
    schemata = list(map(SchemaPlan.from_sql, schemata_query))
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
