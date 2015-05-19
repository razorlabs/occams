"""
Patient's visit history

Formerly: avrcdataexport/sql/additional/VisitStudy.sql
"""

from sqlalchemy.orm import aliased

from .. import _, models, Session
from .plan import ExportPlan
from .codebook import row, types


class VisitPlan(ExportPlan):

    name = 'visit'

    title = _(u'Visits')

    def codebook(self):
        return iter([
            row('id', self.name, types.NUMERIC,
                is_system=True, is_required=True),
            row('pid', self.name, types.STRING,
                is_required=True, is_system=True),
            row('site', self.name, types.STRING,
                is_required=True, is_system=True),
            row('visit_date', self.name, types.DATE,
                is_required=True, is_system=True),
            row('cycle', self.name, types.STRING, is_system=True),
            row('study_name', self.name, types.STRING, is_system=True),
            row('create_date', self.name, types.DATE,
                is_required=True, is_system=True),
            row('create_user', self.name, types.STRING,
                is_required=True, is_system=True),
            row('modify_date', self.name, types.DATE,
                is_required=True, is_system=True),
            row('modify_user', self.name, types.STRING, is_required=True,
                is_system=True)
        ])

    def data(self,
             use_choice_labels=False,
             expand_collections=False,
             ignore_private=True):
        CreateUser = aliased(models.User)
        ModifyUser = aliased(models.User)
        query = (
            Session.query(
                models.Visit.id.label('id'),
                models.Patient.pid.label('pid'),
                models.Site.name.label('site'),
                models.Visit.visit_date.label('visit_date'),
                models.Cycle.week.label('cycle'),
                models.Study.title.label('study_name'),
                models.Visit.create_date,
                CreateUser.key.label('create_user'),
                models.Visit.modify_date,
                ModifyUser.key.label('modify_user'))
            .select_from(models.Patient)
            .join(models.Patient.visits)
            .join(models.Visit.cycles)
            .join(models.Cycle.study)
            .join(models.Patient.site)
            .join(CreateUser, models.Visit.create_user)
            .join(ModifyUser, models.Visit.modify_user)
            .order_by(models.Visit.id))
        return query
