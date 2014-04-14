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

from pyramid.decorator import reify
from sqlalchemy import literal_column
from sqlalchemy.orm import aliased

from occams.datastore.utils.sql import group_concat

from .. import _, models, Session
from .plan import ExportPlan
from .codebook import row, types


class PidPlan(ExportPlan):

    name = 'pid'

    title = _(u'Patient Identifiers')

    @reify
    def reftypes(self):
        return list(
            Session.query(models.RefType)
            .order_by(models.RefType.name))

    @reify
    def sites(self):
        sites_query = Session.query(models.Site).order_by(models.Site.id)
        sites = [(s.id, s.title) for s in sites_query]
        return sites

    def codebook(self):
        name = self.name
        knowns = [
            row('id', name, types.NUMERIC, is_required=True),
            row('site', name, types.CHOICE,
                choices=self.sites, is_required=True),
            row('pid', name, types.STRING, is_required=True),
            row('our', name, types.STRING),
            row('aeh_num', name, types.STRING),
            row('early_id', name, types.STRING),
        ]

        for known in knowns:
            yield known

        for reftype in self.reftypes:
            yield row(reftype.name, name, types.STRING, is_collection=True)

    def data(self, use_choice_labels=False, expand_collections=False):

        query = (
            Session.query(
                models.Patient.id.label('id'),
                models.Site.name.label('site'),
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
        for reftype in self.reftypes:
            query = query.add_column(
                Session.query(
                    group_concat(
                        models.PatientReference.reference_number, ';'))
                .filter(
                    models.PatientReference.patient_id == models.Patient.id)
                .filter(models.PatientReference.reftype_id == reftype.id)
                .group_by(models.PatientReference.patient_id)
                .correlate(models.Patient)
                .as_scalar()
                .label(reftype.name))

        query = query.order_by(models.Patient.pid)

        return query
