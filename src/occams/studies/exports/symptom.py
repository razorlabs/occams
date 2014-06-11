"""
Symptom Log
"""

#
# BBB: Until symptom gets moved to its own form, it will have to live here
#
# BBB: Also, the package is such a mess that the codes are defined here
#


from sqlalchemy import case, MetaData, Table
from sqlalchemy.orm import aliased, mapper

from .. import _, models, Session
from .plan import ExportPlan
from .codebook import row, types


type_choices = {
    1: u'Headache',
    2: u'Pharyngitis',
    3: u'Skin rash',
    4: u'Myalgia',
    5: u'Fatigue',
    6: u'Fever',
    7: u'Night sweats',
    8: u'General gastrointestinal symptoms (nausea, vomiting or diarrhea)',
    9: u'Arthralgia',
    10: u'Weight loss (greater than 5 lbs/2.5 kg)',
    11: u'Lymphadenopathy',
    12: u'Other'
}


class SymptomPlan(ExportPlan):

    name = 'Symptom'

    title = _(u'Symptom')

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

            row('start_date', self.name, types.DATE,
                title=u'Date Started',
                desc=u'Date the patient started exhibiting the symptom.',  # NOQA
                is_required=True),
            row('stop_date', self.name, types.DATE,
                title=u'Date Stopped',
                desc=u'Date the patient stopped exhibiting the symptom.'),  # NOQA
            row('type', self.name, types.CHOICE,  # symptom_type
                title=u'Type',
                choices=type_choices.items(),
                is_required=True),
            row('type_other', self.name, types.STRING,
                title=u'Other'),
            row('is_attended', self.name, types.BOOLEAN,
                title=u'Did the patient seek medical attention?'),
            row('notes', self.name, types.STRING),

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
        symptom_table = Table(
            'symptom', metadata, autoload=True, autoload_with=Session.bind)
        symptom_type_table = Table(
            'symptom_type', metadata, autoload=True,
            autoload_with=Session.bind)

        class Symptom(object):
            pass

        class SymptomType(object):
            pass

        mapper(Symptom, symptom_table)
        mapper(SymptomType, symptom_type_table)

        CreateUser = aliased(models.User)
        ModifyUser = aliased(models.User)

        query = (
            Session.query(
                Symptom.id,
                models.Patient.our.label('pid'),
                models.Site.name.label('site'),

                Symptom.start_date,
                Symptom.stop_date,
                case(value=SymptomType.value,
                     whens=[(v, k) for k, v in type_choices.items()])
                .label('type'),
                Symptom.type_other,
                Symptom.is_attended,
                Symptom.notes,

                Symptom.create_date,
                CreateUser.key.label('create_user'),
                Symptom.modify_date,
                ModifyUser.key.label('modify_user'))
            .select_from(Symptom)
            .join(models.Patient, Symptom.patient_id == models.Patient.id)
            .join(models.Patient.site)
            .join(SymptomType, SymptomType.id == Symptom.symptom_type_id)
            .join(CreateUser, Symptom.create_user_id == CreateUser.id)
            .join(ModifyUser, Symptom.modify_user_id == ModifyUser.id)
            .order_by(Symptom.id))
        return query
