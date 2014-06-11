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
                title=u'Date Started',
                desc=u'Date the patient started exhibiting the symptom.',  # NOQA
                is_required=True),
            row('partner_pid', self.name, types.DATE,
                title=u'Date Stopped',
                desc=u'Date the patient stopped exhibiting the symptom.'),  # NOQA

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

        metadata = MetaData()
        partner_table = Table(
            'partner', metadata, autoload=True, autoload_with=Session.bind)

        class Partner(object):
            pass

        mapper(Partner, partner_table)

        CreateUser = aliased(models.User)
        ModifyUser = aliased(models.User)
        PartnerPatient = aliased(models.Patient)

        query = (
            Session.query(
                Partner.id,
                models.Patient.our.label('pid'),
                models.Site.name.label('site'),

                Partner.report_date,
                PartnerPatient.our.label('partner_pid'),

                Partner.create_date,
                CreateUser.key.label('create_user'),
                Partner.modify_date,
                ModifyUser.key.label('modify_user'))
            .select_from(Partner)
            .join(models.Patient, Partner.patient_id == models.Patient.id)
            .join(models.Patient.site)
            .outerjoin(PartnerPatient, PartnerPatient.id == Partner.enrolled_patient_id)  # NOQA
            .join(CreateUser, Partner.create_user_id == CreateUser.id)
            .join(ModifyUser, Partner.modify_user_id == ModifyUser.id)
            .order_by(Partner.id))
        return query
