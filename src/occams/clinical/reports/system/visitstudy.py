"""
Patient's visit history

Formerly: avrcdataexport/sql/additional/VisitStudy.sql
"""


from occams.clinical import models, Session
from occams.clinical.reports.codebook import row, types


NAME = 'VisitStudy'


def codebook():
    return iter([
        row('our', NAME, types.STRING, is_required=True),
        row('aeh_num', NAME, types.STRING),
        row('visit_date', NAME, types.STRING, is_required=True),
        row('cycle', NAME, types.STRING),
        row('study_name', NAME, types.STRING),
        ])


def query_report():
    query = (
        Session.query(
            models.Patient.our.label('our'),
            models.Patient.legacy_number.label('aeh_num'),
            models.Visit.visit_date.label('visit_date'),
            models.Cycle.week.label('cycle'),
            models.Study.title.label('study_name'))
        .select_from(models.Patient)
        .join(models.Patient.visits)
        .join(models.Visit.cycles)
        .join(models.Cycle.Study))
    return query
