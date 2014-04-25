"""
Patient's visit history

Formerly: avrcdataexport/sql/additional/VisitStudy.sql
"""

from .. import _, models, Session
from .plan import ExportPlan
from .codebook import row, types


class VisitPlan(ExportPlan):

    name = 'visit'

    title = _(u'Visits')

    def codebook(self):
        return iter([
            row('our', self.name, types.STRING,
                is_required=True, is_system=True),
            row('aeh_num', self.name, types.STRING, is_system=True),
            row('visit_date', self.name, types.DATE,
                is_required=True, is_system=True),
            row('cycle', self.name, types.STRING, is_system=True),
            row('study_name', self.name, types.STRING, is_system=True),
            ])

    def data(self, use_choice_labels=False, expand_collections=False):

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
