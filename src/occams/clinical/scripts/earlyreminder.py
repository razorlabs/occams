"""
Generate a patient's test results with their contact information.
Incredibly-one-off-script-that-we-must-support

Not included as part of the standard export system so
as not to confuse users.

Formerly:
    avrcdataexport/sql/extractContactInfo.sql
    avrcdataexport/sql/extracttHivTestResults.sql

"""

import re

from sqlalchemy import cast, func, null, or_, Unicode

from occams.clinical import models, Session
from occams.clinical.reports.codebook import row, types
from occams.datastore.reporting import build_report


NAME = 'EarlyReminder'

TITLE = 'Early Test Reminder'


RE_NONASCII = re.compile(r'[^a-z]+', re.I)


def title2column(value, replace='_'):
    return RE_NONASCII.sub(replace, value)


def codebook():

    known = [
        row('phi_our', NAME, is_required=True),

        row('first_name', NAME, is_private=True),
        row('last_name', NAME, is_private=True),
        row('aliases', NAME, is_private=True),
        row('dob', NAME, is_private=True),

        row('zip_code', NAME, is_private=True),
        row('testing_reminder', NAME),
        row('email1', NAME, is_private=True),
        row('email2', NAME, is_private=True),

        row('hiv_our', NAME, is_required=True),
        row('visit_date', NAME, is_required=True),

        row('test_site', NAME),
        row('test_site_create_user', NAME),
        row('test_site_modify_user', NAME),

        row('rapid_result1', NAME),
        row('rapid_result2', NAME),
        row('rapid_create_user', NAME),
        row('rapid_modify_user', NAME),

        row('nat_result', NAME),
        row('nat_create_user', NAME),
        row('nat_modify_user', NAME)]

    for r in known:
        yield r

    for study in Session.query(models.Study).order_by(models.Study.title):
        yield row(title2column(study.title), NAME, types.STRING)


def query_report(from_=None, ignore_private=False):
    nat = build_report(Session, 'HivNAT',
                       attributes=['result'],
                       context='visit',
                       ignore_private=ignore_private)
    rapidtest = build_report(Session, 'RapidTest',
                             attributes=['result', 'verify_result'],
                             context='visit',
                             ignore_private=ignore_private)
    earlytest = build_report(Session, 'IEarlyTest',
                             attributes=['test_site'],
                             ignore_private=ignore_private,
                             context='visit',
                             use_choice_labels=True)
    bio = build_report(Session, 'IBio',
                       attributes=['first_name', 'last_name', 'aliases',
                                   'birth_date'],
                       context='patient',
                       ignore_private=ignore_private)
    contact = build_report(Session, 'IContact',
                           attributes=['zip_code',
                                       'testing_reminder',
                                       'email1', 'email2'],
                           context='patient',
                           ignore_private=ignore_private)

    query = (
        Session.query(
            models.Patient.our.label('phi_our'),

            bio.c.first_name.label('first_name'),
            bio.c.last_name.label('last_name'),
            bio.c.aliases.label('aliases'),
            bio.c.birth_date.label('dob'),

            contact.c.zip_code.label('zip_code'),
            contact.c.testing_reminder.label('testing_reminder'),
            contact.c.email1.label('email1'),
            contact.c.email2.label('email2'),

            models.Patient.our.label('hiv_our'),
            models.Visit.visit_date.label('visit_date'),

            earlytest.c.test_site.label('test_site'),
            earlytest.c.create_user.label('test_site_create_user'),
            earlytest.c.modify_user.label('test_site_modify_user'),

            rapidtest.c.result.label('rapid_result1'),
            rapidtest.c.verify_result.label('rapid_result2'),
            rapidtest.c.create_user.label('rapid_create_user'),
            rapidtest.c.modify_user.label('rapid_modify_user'),

            nat.c.result.label('nat_result'),
            nat.c.create_user.label('nat_create_user'),
            nat.c.modify_user.label('nat_modify_user')
            )
        .select_from(models.Visit)
        .join(models.Visit.patient)
        .outerjoin(nat, nat.c.context_key == models.Visit.id)
        .outerjoin(rapidtest, rapidtest.c.context_key == models.Visit.id)
        .outerjoin(earlytest, earlytest.c.context_key == models.Visit.id)
        .outerjoin(bio, bio.c.context_key == models.Patient.id)
        .outerjoin(contact, contact.c.context_key == models.Patient.id)
        .filter(or_(nat.c.result != null(),
                    rapidtest.c.result != null(),
                    earlytest.c.test_site != null())))

    if from_:
        query = query.filter(models.Visit.visit_date > from_)

    for study in Session.query(models.Study).order_by(models.Study.title):
        query = (
            query.add_column(
                Session.query(
                    func.coalesce(
                        func.max(models.Enrollment.reference_number),
                        cast(func.min(models.Enrollment.consent_date),
                             Unicode)))
                .join(models.Enrollment.study)
                .filter(models.Study.id == study.id)
                .filter(models.Enrollment.patient_id == models.Patient.id)
                .correlate(models.Patient)
                .as_scalar()
                .label(title2column(study.title))))

    query = query.order_by(models.Patient.our, models.Visit.visit_date)

    return query
