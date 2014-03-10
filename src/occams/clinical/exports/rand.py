"""
Generate randomization values for a study

Formerly:
    avrcdataexport/sql/UsableRandomization594.sql
    avrcdataexport/sql/UsableRandomization595.sql
"""

from occams.datastore.reporting import build_report

from .. import models, Session
from .codebook import row, types


NAME = 'rand'


def codebook(code):
    known = [
        row('id', NAME, types.NUMERIC, is_required=True),
        row('pid', NAME, types.STRING),
        row('block_number', NAME, types.NUMERIC, is_required=True),
        row('randid', NAME, types.STRING, is_required=True),
        row('arm_name', NAME, types.STRING, is_required=True)]

    for r in known:
        yield r

    study = Session.query(models.Study).filter_by(code=code).one()
    schema = find_schema(study)

    for attribute in schema.attributes.values():
        row(attribute.name, NAME, attribute.type,
            title=attribute.title,
            description=attribute.description,
            choices=[(c.name, c.title) for c in attribute.choices],
            is_required=attribute.is_required,
            is_collection=attribute.is_collection)


def query_report(code):
    study = Session.query(models.Study).filter_by(code=code).one()
    schema = find_schema(study)
    report = build_report(Session, schema.name, context='stratum')

    query = (
        Session.query(
            models.Stratum.id.label('id'),
            models.Patient.pid.label('pid'),
            models.Stratum.block_number.label('block_number'),
            models.Stratum.randid.label('randid'),
            models.Arm.title.label('arm_name'))
        .select_from(models.Stratum)
        .join(models.Stratum.arm)
        .outerjoin(models.Stratum.patient)
        .join(report, report.c.context_key == models.Stratum.id))

    for attribute in schema.attributes.values():
        query = query.add_column(getattr(report.c, attribute.name))

    query = query.order_by(
        models.Stratum.randid.asc(),
        models.Stratum.block_number.asc(),
        models.Arm.title.asc())

    return query


def find_schema(study):
    for stratum in study.strata:
        for entity in stratum.entities:
            return entity.schema
