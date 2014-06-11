"""
CCTG Patient Call Log
"""

#
# BBB: Call log is a form for CCTG that was custom-coded because
#      datastore does not support skip-logic. Said table should
#      really be transformed into a form ASAP.
#
# BBB: Also, the package is such a mess that the codes are defined here
#


from sqlalchemy import case
from sqlalchemy.orm import aliased

from occams.datastore.utils.sql import group_concat

from .. import _, models, Session
from .plan import ExportPlan
from .codebook import row, types


contact_reason_choices = {
    1: u'Appointment reminder',
    2: u'Module session',
    3: u'Multiple text',
    4: u'Noncompliance with text',
    5: u'Patient initiated contact',
    6: u'Tracking and outreach',
    7: u'Unrecognized text',
    8: u'Other',
}

contact_type_choices = {
    1: u'Answered - Patient answered',
    2: u'Call In - Patient Called',
    3: u'Message - Another person answered',
    4: u'Voicemail',
    5: u'No Message - No Answer',
    6: u'No Message - Number Changed',
    7: u'No Message - Mailbox Full',
    8: u'No Message - Number Disconnected',
    9: u'Other',
}

non_response_type_choices = {
    1: u'Broken phone',
    2: u'Difficulty texting',
    3: u'Misplaced phone',
    4: u'Service disruption',
    5: u'Unclear Instructions',
    6: u'Other'
}


class CallLogPlan(ExportPlan):

    name = 'calllog'

    title = _(u'Call Log')

    has_private = True

    @property
    def is_enabled(self):
        return 'cctg' in Session.bind.url.database

    def codebook(self):
        return iter([
            row('id', self.name, types.NUMERIC,
                is_system=True, is_required=True),
            row('pid', self.name, types.STRING,
                is_required=True, is_system=True),
            row('site', self.name, types.STRING,
                is_required=True, is_system=True),
            # patient_contact_date is too long
            row('contact_date', self.name, types.DATETIME,
                title=u'Date of Patient Contact',
                desc=u'When was the patient contact?',
                is_required=True),
            row('last_text_date', self.name, types.DATE,
                title=u'Date of Last Response ',
                desc=u'When was the last text response received from the patient?',  # NOQA
                ),
            row('contact_reason', self.name, types.CHOICE,
                title=u'Reason for Contact',
                desc=u'What is the reason for this patient contact?',
                choices=contact_reason_choices.items(),
                is_required=True),
            row('contact_type', self.name, types.CHOICE,
                title=u'Type of Contact',
                desc=u'What sort of contact did you have with the patient?',  # NOQA
                choices=contact_type_choices.items(),
                is_required=True),
            row('non_response_type', self.name, types.CHOICE,
                title=u'Difficulties',
                desc=u'Select all the difficulties described by the patient.',  # NOQA
                choices=non_response_type_choices.items(),
                is_collection=True
                ),
            row('non_response_other', self.name, types.STRING,
                title=u'Unlisted Difficulty',
                ),
            row('message_left', self.name, types.BOOLEAN),
            row('comments', self.name, types.STRING),
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
        # Import here in case it's not actually installed
        from cctg.patientlog import model as log
        CreateUser = aliased(models.User)
        ModifyUser = aliased(models.User)
        query = (
            Session.query(
                log.PatientLog.id.label('id'),
                models.Patient.our.label('pid'),
                models.Site.name.label('site'),

                log.PatientLog.patient_contact_date.label('contact_date'),
                log.PatientLog.last_text_date,

                case(value=log.PatientLog.contact_reason,
                     whens=[(v, k) for k, v in contact_reason_choices.items()])
                .label('contact_reason'),

                case(value=log.PatientLog.contact_type,
                     whens=[(v, k) for k, v in contact_type_choices.items()])
                .label('contact_type'),

                group_concat(
                    Session.query(
                        case(value=log.PatientLogNonResponseType.value,
                             whens=[(v, k) for k, v in non_response_type_choices.items()]))  # NOQA
                    .join(log.log_response_table)
                    .filter(log.log_response_table.patient_log_id == log.PatientLog.id)  # NOQA
                    .correlate(log.PatientLog)
                    .as_scalar(),
                    ';')
                .label('non_response_type'),

                log.PatientLog.non_response_other,
                log.PatientLog.message_left,
                log.PatientLog.comments,

                log.PatientLog.create_date,
                CreateUser.key.label('create_user'),
                log.PatientLog.modify_date,
                ModifyUser.key.label('modify_user'))
            .select_from(log.PatientLog)
            .join(models.PatientLog.patient)
            .join(models.Patient.site)
            .join(CreateUser, log.PatientLog.create_user)
            .join(ModifyUser, log.PatientLog.modify_user)
            .order_by(log.PatientLog.id))
        return query
