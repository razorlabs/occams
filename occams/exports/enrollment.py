"""
Patient enrollments report

The goal is to generate a patient's participation in a study

Formerly: avrcdataexport/sql/additional/Enrollment.sql
"""

from .. import _, models
from .plan import ExportPlan
from .codebook import row, types


class EnrollmentPlan(ExportPlan):

    name = 'enrollment'

    title = _(u'Enrollments')

    def codebook(self):

        return iter([
            row('id', self.name, types.NUMBER, decimal_places=0,
                is_system=True, is_required=True),
            row('pid', self.name, types.STRING,
                is_system=True, is_required=True),
            row('site', self.name, types.STRING,
                is_system=True, is_required=True),
            row('enrollment_id', self.name, types.NUMBER, decimal_places=0,
                is_system=True, is_required=True),
            row('study', self.name, types.STRING,
                is_system=True, is_required=True),
            row('nurse', self.name, types.STRING, is_system=True),
            row('reference_number', self.name, types.STRING, is_system=True),
            row('consent_date', self.name, types.DATE,
                is_system=True, is_required=True),
            row('latest_consent_date', self.name, types.DATE, is_system=True),
            row('termination_date', self.name, types.DATE, is_system=True),
            row('created_at', self.name, types.DATE,
                is_required=True, is_system=True),
            row('created_by', self.name, types.STRING,
                is_required=True, is_system=True),
            row('modified_at', self.name, types.DATE,
                is_required=True, is_system=True),
            row('modified_by', self.name, types.STRING, is_required=True,
                is_system=True)
        ])

    def data(self,
             use_choice_labels=False,
             expand_collections=False,
             ignore_private=True):
        session = self.dbsession
        query = (
            session.query(
                models.Enrollment.id.label('id'),
                models.Patient.pid.label('pid'),
                models.Site.name.label('site'),
                models.Enrollment.id.label('enrollment_id'),  # BBB
                models.Study.title.label('study'),
                models.Patient.nurse.label('nurse'),  # BBB
                models.Enrollment.reference_number.label('reference_number'),
                models.Enrollment.consent_date.label('consent_date'),
                models.Enrollment.latest_consent_date.label(
                    'latest_consent_date'),
                models.Enrollment.termination_date.label('termination_date'),
                models.Enrollment.created_at,
                models.Enrollment.created_by,
                models.Enrollment.modified_at,
                models.Enrollment.modified_by
            )
            .select_from(models.Enrollment)
            .join(models.Enrollment.patient)
            .join(models.Enrollment.study)
            .join(models.Patient.site)
            .order_by(models.Enrollment.id,
                      models.Study.title,
                      models.Patient.pid))
        return query
