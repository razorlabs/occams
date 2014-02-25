"""
PID Conversion report

The goal is to generate a mapping of a patient's study IDs and secondary IDs.

Patient IDs are idendification numbers assigned globally by the organization.
(e.g. OUR Numbers)

Study IDs are identification numbers assigned only within a study scope.
(e.g. AEH Early Test)

Secondary IDs are identication numbers assigned in external  systems.
(e.g. Medical Record Numbers, AIDRP number)

Formerly: avrcdataexport/sql/additional/OurEarlyTest.sql
"""

from sqlalchemy import literal_column
from sqlalchemy.orm import aliased

from occams.clinical import models, Session
from occams.clinical.reports.codebook import row, types
from occams.datastore.utils.sql import list_concat


NAME = 'pid'


def codebook():

    sites_query = Session.query(models.Site).order_by(models.Site.id)
    sites = [(s.id, s.title) for s in sites_query]

    yield row('id', NAME, types.NUMERIC, is_required=True)
    yield row('siteid', NAME, types.CHOICE, choices=sites, is_required=True)
    yield row('pid', NAME, types.STRING, is_required=True)
    yield row('our', NAME, types.STRING)
    yield row('earlyid', NAME, types.STRING)

    for reftype in Session.query(models.RefType).order_by(models.RefType.name):
        yield row(reftype.name, NAME, types.STRING, is_collection=True)


def query_report():

    query = (
        Session.query(
            models.Patient.id.label('id'),
            models.Site.id.label('siteid'),
            models.Patient.pid.label('pid'))
        .join(models.Site))

    # BBB 2014-02-20 (Marco): AEH needs OUR and aeh_num
    # New organizations SHOULD NOT USE legacy number, use ref tables
    query = query.add_columns(
        models.Patient.our.label('our'),
        models.Patient.legacy_number.label('aeh_num'))

    # BBB 2014-02-20 (Marco): AEH needs Early Test
    EarlyTest = aliased(models.Enrollment)
    subquery = (
        Session.query(EarlyTest.patient_id, EarlyTest.reference_number)
        .filter(EarlyTest.study.has(
            models.Study.code.in_([literal_column("'ET'"),
                                   literal_column("'LTW'"),
                                   literal_column("'CVCT'")])))
        .subquery())
    query = (
        query
        .outerjoin(subquery, subquery.c.patient_id == models.Patient.id)
        .add_column(subquery.c.reference_number.label('early_id')))

    # Add every known reference number
    for reftype in Session.query(models.RefType).order_by(models.RefType.name):
        query = query.add_column(
            Session.query(list_concat(
                Session.query(models.PatientReference.reference_number)
                .filter(
                    models.PatientReference.patient_id == models.Patient.id)
                .filter(models.PatientReference.reftype_id == reftype.id)
                .correlate(models.Patient)
                .subquery()
                .as_scalar(),
                literal_column("';'"))).as_scalar().label(reftype.name))

    query = query.order_by(models.Patient.pid)

    return query
