"""
Partner Linkage
"""

#
# BBB: This needs to be moved into a form.
#


from sqlalchemy import MetaData, Table
from sqlalchemy.orm import aliased, mapper

from .. import _, models, Session
from .plan import ExportPlan
from .codebook import row, types


class PartnerPlan(ExportPlan):

    name = 'PartnerLinkage'

    title = _(u'Partner Linkage')

    has_private = True

    @property
    def is_enabled(self):
        return 'aeh' in Session.bind.url.database

    def codebook(self):
        return iter([
            row('id', self.name, types.NUMERIC,
                is_system=True, is_required=True),
            row('pid', self.name, types.STRING,
                is_required=True, is_system=True),
            row('site', self.name, types.STRING,
                is_required=True, is_system=True),

            row('report_date', self.name, types.DATE,
                title=u'Date Partner Reported',
                desc=u'The date that the reporting patient reported this partner.',  # NOQA
                is_required=True),
            row('partner_pid', self.name, types.STRING,
                title=u'This Partner\'s Patient Entry',
                desc=u'This partner is also a patient; This property references that patient entry'),  # NOQA


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
        PartnerPatient = aliased(models.Patient)

        query = (
            Session.query(
                models.Partner.id,
                models.Patient.our.label('pid'),
                models.Site.name.label('site'),

                models.Partner.report_date,
                PartnerPatient.our.label('partner_pid'),

                models.Partner.create_date,
                CreateUser.key.label('create_user'),
                models.Partner.modify_date,
                ModifyUser.key.label('modify_user'))
            .select_from(modelsPartner)
            .join(models.Patient, models.Partner.patient_id == models.Patient.id)
            .join(models.Patient.site)
            .outerjoin(PartnerPatient, PartnerPatient.id == models.Partner.enrolled_patient_id)  # NOQA
            .join(CreateUser, models.Partner.create_user_id == CreateUser.id)
            .join(ModifyUser, models.Partner.modify_user_id == ModifyUser.id)
            .order_by(models.Partner.id))
        return query
