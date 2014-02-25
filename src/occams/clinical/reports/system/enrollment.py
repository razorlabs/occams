"""
Patient enrollments report

The goal is to generate a patient's participation in a study

Formerly: avrcdataexport/sql/additional/Enrollment.sql
"""

from occams.clinical import models, Session
from occams.clinical.reports.codebook import row, types


NAME = 'Enrollment'


def codebook():

    return iter([
        row('id', NAME, types.NUMERIC, is_required=True),
        row('enrollment_id', NAME, types.NUMERIC, is_required=True),
        row('study', NAME, types.STRING, is_required=True),
        row('pid', NAME, types.STRING, is_required=True),
        row('our', NAME, types.STRING, is_required=True),
        row('aeh_num', NAME, types.STRING),
        row('nurse', NAME, types.STRING),
        row('reference_number', NAME, types.STRING),
        row('consent_date', NAME, types.DATE, is_required=True),
        row('latest_consent_date', NAME, types.DATE),
        row('termination_date', NAME, types.DATE)
        ])


def query_report():

    query = (
        Session.query(
            models.Enrollment.id.label('id'),
            models.Enrollment.id.label('enrollment_id'),  # BBB
            models.Study.title.label('study'),  # BBB
            models.Patient.our.label('pid'),
            models.Patient.our.label('our'),  # BBB
            models.Patient.legacy_number.label('aeh_num'),  # BBB
            models.Patient.nurse.label('nurse'),  # BBB
            models.Enrollment.reference_number.label('reference_number'),
            models.Enrollment.consent_date.label('consent_date'),
            models.Enrollment.latest_consent_date.label('latest_consent_date'),
            models.Enrollment.termination_date.label('termination_date'))
        .select_from(models.Enrollment)
        .join(models.Enrollment.patient)
        .join(models.Enrollment.study)
        .order_by(models.Enrollment.id,
                  models.Study.title,
                  models.Patient.pid))

    return query
