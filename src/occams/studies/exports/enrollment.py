"""
Patient enrollments report

The goal is to generate a patient's participation in a study

Formerly: avrcdataexport/sql/additional/Enrollment.sql
"""

from sqlalchemy.orm import aliased

from .. import _, models, Session
from .plan import ExportPlan
from .codebook import row, types


class EnrollmentPlan(ExportPlan):

    name = 'enrollment'

    title = _(u'Enrollments')

    def codebook(self):

        return iter([
            row('id', self.name, types.NUMERIC,
                is_system=True, is_required=True),
            row('enrollment_id', self.name, types.NUMERIC,
                is_system=True, is_required=True),
            row('study', self.name, types.STRING,
                is_system=True, is_required=True),
            row('site', self.name, types.STRING,
                is_system=True, is_required=True),
            row('pid', self.name, types.STRING,
                is_system=True, is_required=True),
            row('our', self.name, types.STRING,
                is_system=True, is_required=True),
            row('aeh_num', self.name, types.STRING, is_system=True),
            row('nurse', self.name, types.STRING, is_system=True),
            row('reference_number', self.name, types.STRING, is_system=True),
            row('consent_date', self.name, types.DATE,
                is_system=True, is_required=True),
            row('latest_consent_date', self.name, types.DATE, is_system=True),
            row('termination_date', self.name, types.DATE, is_system=True),
            row('create_date', self.name, types.DATE,
                is_required=True, is_system=True),
            row('create_user', self.name, types.STRING,
                is_required=True, is_system=True),
            row('modify_date', self.name, types.DATE,
                is_required=True, is_system=True),
            row('modify_user', self.name, types.STRING, is_required=True,
                is_system=True)
        ])

    def data(self, use_choice_labels=False, expand_collections=False):
        CreateUser = aliased(models.User)
        ModifyUser = aliased(models.User)
        query = (
            Session.query(
                models.Enrollment.id.label('id'),
                models.Enrollment.id.label('enrollment_id'),  # BBB
                models.Study.title.label('study'),  # BBB
                models.Site.name.label('site'),
                models.Patient.our.label('pid'),
                models.Patient.our.label('our'),  # BBB
                models.Patient.legacy_number.label('aeh_num'),  # BBB
                models.Patient.nurse.label('nurse'),  # BBB
                models.Enrollment.reference_number.label('reference_number'),
                models.Enrollment.consent_date.label('consent_date'),
                models.Enrollment.latest_consent_date.label(
                    'latest_consent_date'),
                models.Enrollment.termination_date.label('termination_date'),
                models.Enrollment.create_date,
                CreateUser.key.label('create_user'),
                models.Enrollment.modify_date,
                ModifyUser.key.label('modify_user'))
            .select_from(models.Enrollment)
            .join(models.Enrollment.patient)
            .join(models.Enrollment.study)
            .join(models.Patient.site)
            .join(CreateUser, models.Enrollment.create_user)
            .join(ModifyUser, models.Enrollment.modify_user)
            .order_by(models.Enrollment.id,
                      models.Study.title,
                      models.Patient.pid))
        return query
