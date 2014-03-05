"""
Patient's visit history

Formerly: avrcdataexport/sql/additional/VisitStudy.sql
"""


from occams.clinical import models, Session
from occams.clinical.reports._base import Report
from occams.clinical.reports.codebook import row, types


class VisitReport(Report):

    name = 'VisitStudy'

    title = 'Visits'

    def codebook(self):
        return iter([
            row('our', self.name, types.STRING, is_required=True),
            row('aeh_num', self.name, types.STRING),
            row('visit_date', self.name, types.STRING, is_required=True),
            row('cycle', self.name, types.STRING),
            row('study_name', self.name, types.STRING),
            ])

    def data(self):
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
            .join(models.Cycle.study))
        return query
