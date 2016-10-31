"""
Patient's visit history

Formerly: avrcdataexport/sql/additional/VisitStudy.sql
"""

from .. import _, models
from .plan import ExportPlan
from .codebook import row, types


class VisitPlan(ExportPlan):

    name = 'visit'

    title = _(u'Visits')

    def codebook(self):
        return iter([
            row('id', self.name, types.NUMBER, decimal_places=0,
                is_system=True, is_required=True),
            row('pid', self.name, types.STRING,
                is_required=True, is_system=True),
            row('site', self.name, types.STRING,
                is_required=True, is_system=True),
            row('visit_date', self.name, types.DATE,
                is_required=True, is_system=True),
            row('cycle', self.name, types.STRING, is_system=True),
            row('study_name', self.name, types.STRING, is_system=True),
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
                models.Visit.id.label('id'),
                models.Patient.pid.label('pid'),
                models.Site.name.label('site'),
                models.Visit.visit_date.label('visit_date'),
                models.Cycle.week.label('cycle'),
                models.Study.title.label('study_name'),
                models.Visit.created_at,
                models.Visit.created_by,
                models.Visit.modified_at,
                models.Visit.modified_by
            )
            .select_from(models.Patient)
            .join(models.Patient.visits)
            .join(models.Visit.cycles)
            .join(models.Cycle.study)
            .join(models.Patient.site)
            .order_by(models.Visit.id))
        return query
